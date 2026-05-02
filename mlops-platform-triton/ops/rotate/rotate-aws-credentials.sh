#!/usr/bin/env bash
# ops/rotate/rotate-aws-credentials.sh
set -euo pipefail

# ===== Default parameters =====
ENV="${1:-dev}"                              # dev | prod
REGION="${REGION:-ap-northeast-2}"
SS_CTL="${SS_CTL:-sealed-secrets}"
SS_NS="${SS_NS:-kube-system}"
ARGO_APP="${ENV}-secrets"

info(){ echo "[$(date +%H:%M:%S)] $*"; }
kseal(){ kubeseal --controller-name "$SS_CTL" --controller-namespace "$SS_NS" -o yaml; }

# ===== Pre-checks =====
for bin in aws jq kubectl kubeseal git; do
  command -v "$bin" >/dev/null || { echo "ERROR: $bin required"; exit 1; }
done

# ===== ENV → Automatically determine profile (prioritize AWS_PROFILE_ROTATOR if provided externally) =====
: "${AWS_PROFILE_PREFIX:=rotator}"   # change prefix via export AWS_PROFILE_PREFIX=myrotator
if [[ -z "${AWS_PROFILE_ROTATOR:-}" ]]; then
  case "$ENV" in
    dev)  AWS_PROFILE_ROTATOR="${AWS_PROFILE_PREFIX}-dev"  ;;
    prod) AWS_PROFILE_ROTATOR="${AWS_PROFILE_PREFIX}-prod" ;;
    *)    echo "❌ Unsupported ENV: $ENV (dev|prod)"; exit 1 ;;
  esac
fi

# ===== Fix repo root =====
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"
APP_GIT_PATH="$REPO_ROOT/envs/${ENV}/sealed-secrets"
mkdir -p "$APP_GIT_PATH/airflow" "$APP_GIT_PATH/fastapi" "$APP_GIT_PATH/mlflow" /root/backup

# ===== Decide AWS call mode =====
# 1) If NEW_ID/NEW_SECRET not provided => create new key via IAM API (profile verification required)
# 2) If NEW_ID/NEW_SECRET provided => use given values (no profile verification needed)
USE_AWS_API=1
if [[ -n "${NEW_ID:-}" && -n "${NEW_SECRET:-}" ]]; then
  USE_AWS_API=0
  info "Use provided NEW_ID/NEW_SECRET (proceed without IAM API call)"
fi

AWS_CLI=(aws --profile "$AWS_PROFILE_ROTATOR")

# ===== (API mode only) Pre-verify profile =====
if [[ "$USE_AWS_API" -eq 1 ]]; then
  if ! "${AWS_CLI[@]}" sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ STS check failed with AWS profile '$AWS_PROFILE_ROTATOR'"
    echo "   Prepare one of the following and retry:"
    echo "   1) aws configure --profile $AWS_PROFILE_ROTATOR (set access key/secret)"
    echo "   2) Configure profile using SSO/Assume-Role per your org standards"
    echo "   3) Or provide NEW_ID/NEW_SECRET as env vars to skip IAM API mode"
    exit 1
  fi
fi

# ===== Determine target IAM user / old key & create new key (API mode only) =====
OLD_KEY_ID=""
TARGET_USER="${TARGET_USER:-}"

if [[ "$USE_AWS_API" -eq 1 ]]; then
  if [[ -z "$TARGET_USER" ]]; then
    TARGET_USER="$("${AWS_CLI[@]}" sts get-caller-identity --query 'Arn' --output text | awk -F'/' '{print $NF}')"
  fi
  info "IAM user: $TARGET_USER"

  OLD_KEY_ID="$("${AWS_CLI[@]}" iam list-access-keys --user-name "$TARGET_USER" | jq -r '.AccessKeyMetadata[0].AccessKeyId // empty')"
  if [[ -n "${OLD_KEY_ID}" ]]; then
    info "Old key detected: ${OLD_KEY_ID:0:4}********${OLD_KEY_ID: -4}"
  else
    info "No existing access key found (slot empty)"
  fi

  COUNT="$("${AWS_CLI[@]}" iam list-access-keys --user-name "$TARGET_USER" | jq '.AccessKeyMetadata | length')"
  if [[ "$COUNT" -ge 2 ]]; then
    echo "ERROR: ${TARGET_USER} already has 2 keys. Deactivate/delete one and retry."; exit 1
  fi

  NEW_JSON="$("${AWS_CLI[@]}" iam create-access-key --user-name "$TARGET_USER")"
  export NEW_ID="$(echo "$NEW_JSON" | jq -r .AccessKey.AccessKeyId)"
  export NEW_SECRET="$(echo "$NEW_JSON" | jq -r .AccessKey.SecretAccessKey)"
  info "Created new key: ${NEW_ID:0:4}********${NEW_ID: -4}"

  BK="/root/backup/${TARGET_USER}-${ENV}-new-access-key-$(date +%F-%H%M%S).json"
  umask 077; echo "$NEW_JSON" > "$BK"
  info "Backed up new key JSON -> $BK (600)"
else
  info "Not using TARGET_USER (using provided credentials)"
fi

# ===== SealedSecret creation/update =====
AF_FILE="$APP_GIT_PATH/airflow/sealed-aws-credentials-secret.yaml"
cat > /tmp/aws.ini <<EOF_INI
[default]
aws_access_key_id = ${NEW_ID}
aws_secret_access_key = ${NEW_SECRET}
region = ${REGION}
EOF_INI
kubectl -n "airflow-${ENV}" create secret generic aws-credentials-secret \
  --from-file=credentials=/tmp/aws.ini \
  --dry-run=client -o yaml \
| kubeseal --controller-name "$SS_CTL" --controller-namespace "$SS_NS" --scope namespace-wide -o yaml \
> "$AF_FILE"

FA_FILE="$APP_GIT_PATH/fastapi/sealed-aws-credentials-secret.yaml"
kubectl -n "fastapi-${ENV}" create secret generic aws-credentials-secret \
  --from-literal=AWS_ACCESS_KEY_ID="$NEW_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$NEW_SECRET" \
  --from-literal=AWS_DEFAULT_REGION="$REGION" \
  --dry-run=client -o yaml | kseal > "$FA_FILE"

MF_FILE="$APP_GIT_PATH/mlflow/sealed-aws-credentials-secret.yaml"
kubectl -n "mlflow-${ENV}" create secret generic aws-credentials-secret \
  --from-literal=AWS_ACCESS_KEY_ID="$NEW_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$NEW_SECRET" \
  --from-literal=AWS_DEFAULT_REGION="$REGION" \
  --dry-run=client -o yaml | kseal > "$MF_FILE"

# ===== Git commit/push =====
git add "$AF_FILE" "$FA_FILE" "$MF_FILE"
git commit -m "feat(${ENV}): rotate AWS credentials across airflow/fastapi/mlflow"
git push

## ===== ArgoCD sync (optional) =====
#if command -v argocd >/dev/null 2>&1; then
#  if [[ -n "${ARGOCD_HOST:-}" && -n "${ARGOCD_USERNAME:-}" && -n "${ARGOCD_PASSWORD:-}" ]]; then
#    argocd login "$ARGOCD_HOST" \
#      --username "$ARGOCD_USERNAME" --password "$ARGOCD_PASSWORD" \
#      --insecure --grpc-web || true
#  fi
#  argocd app sync "$ARGO_APP" --grpc-web || {
#    echo "HINT: 'argocd login <HOST> --username ... --password ... --insecure --grpc-web' afterwards"
#    echo "      'argocd app sync ${ARGO_APP} --grpc-web' to execute."
#  }
#fi

# ===== Update local AWS credentials (optional) =====
: "${UPDATE_LOCAL:=1}"   # 1=perform update, 0=skip
PROFILE="$AWS_PROFILE_ROTATOR"      # keep explicit to avoid default

if [[ "$UPDATE_LOCAL" -eq 1 ]]; then
  CRED_FILE="${AWS_SHARED_CREDENTIALS_FILE:-$HOME/.aws/credentials}"
  CRED_DIR="$(dirname "$CRED_FILE")"

  mkdir -p "$CRED_DIR"
  [[ -f "$CRED_FILE" ]] && cp -p "$CRED_FILE" "$CRED_FILE.bak.$(date +%F-%H%M%S)"

  tmpfile="$(mktemp)"
  if [[ -f "$CRED_FILE" ]]; then
    awk -v p="[$PROFILE]" -v id="$NEW_ID" -v sec="$NEW_SECRET" -v reg="$REGION" '
      BEGIN { in_target=0 }
      {
        if ($0 ~ /^[[:space:]]*\[.*\][[:space:]]*$/) {
          if (in_target==1) in_target=0
        }
        if ($0 ~ "^[[:space:]]*\\[" && $0 ~ "\\]") {
          in_target = ($0 == p) ? 1 : 0
          if (!in_target) print $0
        } else if (!in_target) {
          print $0
        }
      }
      END {
        print p
        print "aws_access_key_id = " id
        print "aws_secret_access_key = " sec
        print "region = " reg
      }
    ' "$CRED_FILE" > "$tmpfile"
  else
    cat > "$tmpfile" <<EOF
[$PROFILE]
aws_access_key_id = $NEW_ID
aws_secret_access_key = $NEW_SECRET
region = $REGION
EOF
  fi

  umask 077
  mv "$tmpfile" "$CRED_FILE"
  chmod 600 "$CRED_FILE"

  info "Updated local AWS credentials: file=$CRED_FILE profile=$PROFILE"

  if AWS_PROFILE="$PROFILE" aws sts get-caller-identity >/dev/null 2>&1; then
    info "Local AWS CLI verification OK (profile=$PROFILE)"
  else
    echo "WARN: Local AWS CLI verification FAILED (profile=$PROFILE)."
    echo "      Check $CRED_FILE. You can restore from backup: ${CRED_FILE}.bak.*"
  fi
else
  info "Skipped local credentials update (UPDATE_LOCAL=0)"
fi

# ===== Apply verification =====
for ns in "airflow-${ENV}" "fastapi-${ENV}" "mlflow-${ENV}"; do
  rv="$(kubectl -n "$ns" get secret aws-credentials-secret -o jsonpath='{.metadata.resourceVersion}' 2>/dev/null || true)"
  echo "$ns resourceVersion=$rv"
done

if [[ -n "${OLD_KEY_ID:-}" ]]; then
  info "After verifying services are healthy, set old key (${OLD_KEY_ID:0:4}********${OLD_KEY_ID: -4}) Inactive → delete it."
else
  info "No old key (or using provided ID/SECRET mode)."
fi
