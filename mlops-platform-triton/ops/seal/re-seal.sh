#!/usr/bin/env bash
# ops/seal/re-seal.sh
# Usage:
#   bash ops/seal/re-seal.sh dev
#   SHOW_DIFF=1 bash ops/seal/re-seal.sh prod
# Options:
#   INCLUDE_BOOTSTRAP=1  # include bootstrap/notifications during processing
#   DRY_RUN=1            # dry-run: print plan only

set -euo pipefail

ENV="${1:-dev}"  # dev | prod
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TARGET_DIR="$ROOT/envs/$ENV/sealed-secrets"
SS_NS="${SS_NS:-kube-system}"
SS_CTL="${SS_CTL:-sealed-secrets}"
DRY_RUN="${DRY_RUN:-0}"
SHOW_DIFF="${SHOW_DIFF:-0}"
INCLUDE_BOOTSTRAP="${INCLUDE_BOOTSTRAP:-0}"

need(){ command -v "$1" >/dev/null 2>&1 || { echo "❌ need $1"; exit 1; }; }
need kubectl; need kubeseal; need yq; need git; command -v openssl >/dev/null || true

# Current controller public key fingerprint (for commit message reference)
CERT="/tmp/ss-cert.pem"
kubeseal --controller-namespace "$SS_NS" --controller-name "$SS_CTL" --fetch-cert > "$CERT"
FPR=$(openssl x509 -in "$CERT" -noout -fingerprint -sha256 | sed 's/^.*=//')
echo "[info] controller fingerprint: $FPR"
echo "[info] ENV=$ENV DRY_RUN=$DRY_RUN INCLUDE_BOOTSTRAP=$INCLUDE_BOOTSTRAP"
[[ -d "$TARGET_DIR" ]] || echo "⚠️  $TARGET_DIR directory not found (continuing)."

mapfile -d '' FILES < <(find "$TARGET_DIR" -type f -name '*.yaml' -print0 2>/dev/null || true)
echo "[info] sealed files to process: ${#FILES[@]}"

reseal_file () {
  local f="$1"
  # extract name/ns
  local name ns scope comp
  name=$(yq -r '.metadata.name // .spec.template.metadata.name' "$f")
  ns=$(yq -r '.metadata.namespace // .spec.template.metadata.namespace' "$f")
  if yq -e '.metadata.annotations."sealedsecrets.bitnami.com/namespace-wide" == "true" or .spec.template.metadata.annotations."sealedsecrets.bitnami.com/namespace-wide" == "true"' "$f" >/dev/null 2>&1; then
    scope="namespace-wide"
  else
    scope=""
  fi
  # infer ns (envs/<env>/sealed-secrets/<comp>/...)
  if [[ -z "${ns:-}" || "$ns" == "null" ]]; then
    if [[ "$f" =~ /sealed-secrets/([^/]+)/ ]]; then
      comp="${BASH_REMATCH[1]}"
      ns="${comp}-${ENV}"
      echo "[hint] inferred ns: $f → $ns"
    else
      echo "⚠️  $f: namespace not found; skipping."; return 0
    fi
  fi
  if [[ -z "${name:-}" || "$name" == "null" ]]; then
    echo "⚠️  $f: metadata.name missing. Skipping."; return 0
  fi
  echo "[reseal] ns=$ns name=$name file=$f scope=${scope:-default}"

  if ! kubectl -n "$ns" get secret "$name" >/dev/null 2>&1; then
    echo "⚠️  $ns/$name: cluster Secret missing → reissue/plaintext required. Skipping."
    return 0
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  (dry-run) kubectl -n $ns get secret $name -o yaml | kubeseal ..."
    return 0
  fi

  if [[ -n "$scope" ]]; then
    kubectl -n "$ns" get secret "$name" -o yaml \
      | kubeseal --controller-namespace "$SS_NS" --controller-name "$SS_CTL" \
                 --scope namespace-wide --format yaml > "$f"
  else
    kubectl -n "$ns" get secret "$name" -o yaml \
      | kubeseal --controller-namespace "$SS_NS" --controller-name "$SS_CTL" \
                 --format yaml > "$f"
  fi

  [[ "$SHOW_DIFF" == "1" ]] && git --no-pager diff -- "$f" || true
}

# 1) env re-seal
for f in "${FILES[@]}"; do
  reseal_file "$f"
done

# 2) (Optional) Include notifications bootstrap
if [[ "$INCLUDE_BOOTSTRAP" == "1" ]]; then
  BOOT_DIR="$ROOT/bootstrap/notifications"
  PLAIN="$BOOT_DIR/argocd-notifications-secret.yaml"   # plaintext if present
  SEALED="$BOOT_DIR/secret-sealed.yaml"
  echo "[info] INCLUDE_BOOTSTRAP=1 → attempting to refresh $SEALED"
  if [[ "$DRY_RUN" != "1" ]]; then
    if [[ -f "$PLAIN" ]]; then
      kubeseal --controller-namespace "$SS_NS" --controller-name "$SS_CTL" \
        --format yaml < "$PLAIN" > "$SEALED"
    elif kubectl -n argocd get secret argocd-notifications-secret >/dev/null 2>&1; then
      kubectl -n argocd get secret argocd-notifications-secret -o yaml \
        | kubeseal --controller-namespace "$SS_NS" --controller-name "$SS_CTL" \
                   --format yaml > "$SEALED"
    else
      echo "⚠️  argocd/argocd-notifications-secret not found. skipping bootstrap."
    fi
  fi
  [[ "$SHOW_DIFF" == "1" ]] && git --no-pager diff -- "$SEALED" || true
  git add "$SEALED" 2>/dev/null || true
fi

if [[ "$DRY_RUN" != "1" ]]; then
  git add "$TARGET_DIR" 2>/dev/null || true
  git commit -m "re-seal($ENV): sealed secrets with current controller key [$FPR]" || true
fi

echo "✅ done. (ENV=$ENV, DRY_RUN=$DRY_RUN, INCLUDE_BOOTSTRAP=$INCLUDE_BOOTSTRAP)"
echo "→ If needed: git push"
