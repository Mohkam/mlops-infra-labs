#!/usr/bin/env bash
# ops/seal/rotate-controller-key.sh
# Usage:
#   bash ops/seal/rotate-controller-key.sh
# Options:
#   INCLUDE_BOOTSTRAP=1  # also re-seal notifications
#   DRY_RUN=1            # dry-run: do not patch/seal/commit
# Notes:
#   Do NOT delete old keys first! (will cause decryption failures)

set -euo pipefail

SS_NS="${SS_NS:-kube-system}"
DEPLOY="${DEPLOY:-sealed-secrets}"
RENEW_SHORT="${RENEW_SHORT:-1m}"   # temporary shortened renew period
RENEW_NORMAL="${RENEW_NORMAL:-720h}"  # restore period (30 days)
INCLUDE_BOOTSTRAP="${INCLUDE_BOOTSTRAP:-0}"
DRY_RUN="${DRY_RUN:-0}"
TIMEOUT="${TIMEOUT:-420}"  # wait for new key addition (seconds)

need(){ command -v "$1" >/dev/null 2>&1 || { echo "❌ need $1"; exit 1; }; }
need kubectl; need yq; command -v argocd >/dev/null 2>&1 || true

say(){ echo -e "$*"; }

backup_keys () {
  mkdir -p /root/backup
  local out="/root/backup/sealed-secrets-keys-$(date +%F-%H%M%S).yaml"
  say "[1/6] Backing up existing key → $out"
  if [[ "$DRY_RUN" != "1" ]]; then
    kubectl -n "$SS_NS" get secret -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > "$out"
  fi
}

get_key_count () {
  kubectl -n "$SS_NS" get secret -l sealedsecrets.bitnami.com/sealed-secrets-key -o json \
    | yq '.items | length'
}

patch_args_temp_short () {
  say "[2/6] Prompt controller to add new key (temporarily shorten renew period: $RENEW_SHORT)"
  if [[ "$DRY_RUN" == "1" ]]; then
    say "  (dry-run) patch args to --key-renew-period=$RENEW_SHORT"
    return 0
  fi

  # Backup current args (for restore)
  kubectl -n "$SS_NS" get deploy "$DEPLOY" -o json | yq '.spec.template.spec.containers[0].args' > /tmp/ss-args-backup.json

  # If args missing or renew arg absent, add it; otherwise replace
  if yq -e '.[0]' /tmp/ss-args-backup.json >/dev/null 2>&1; then
    # If array exists → replace/add renew arg
    if yq -e 'map(select(test("^--key-renew-period="))) | length > 0' /tmp/ss-args-backup.json >/dev/null 2>&1; then
      NEW_ARGS=$(yq "(map(if test(\"^--key-renew-period=\") then \"--key-renew-period=$RENEW_SHORT\" else . end))" /tmp/ss-args-backup.json -o=json)
    else
      NEW_ARGS=$(yq ". + [\"--key-renew-period=$RENEW_SHORT\"]" /tmp/ss-args-backup.json -o=json)
    fi
  else
    # args empty → create new array
    NEW_ARGS=$(printf '["--key-renew-period=%s"]' "$RENEW_SHORT")
  fi

  kubectl -n "$SS_NS" patch deploy "$DEPLOY" \
    --type='json' \
    -p="[ {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/args\",\"value\": $NEW_ARGS } ]"

  # Wait for new key creation: expect +1 key compared to before
  local before after waited=0
  before=$(get_key_count)
  say "  Current key count: $before → waiting for new key..."
  until [[ $waited -ge $TIMEOUT ]]; do
    sleep 6; waited=$(( waited + 6 ))
    after=$(get_key_count)
    if (( after > before )); then
      say "  ✅ New key detected: $before → $after (elapsed ${waited}s)"
      return 0
    fi
    say "  ...waiting(${waited}s) (key count $after)"
  done
  say "⚠️  Timeout: failed to confirm new key creation. (check controller logs/config)"
  exit 1
}

reseal_all () {
  say "[3/6] dev re-seal (verify)"
  local cmd="SHOW_DIFF=1 INCLUDE_BOOTSTRAP=${INCLUDE_BOOTSTRAP} bash ops/seal/re-seal.sh dev"
  if [[ "$DRY_RUN" == "1" ]]; then
    say "  (dry-run) $cmd"
  else
    eval "$cmd"
    git push || true
  fi

  # (if present) quick status check via argocd
  if command -v argocd >/dev/null 2>&1; then
    argocd app get dev-secrets || true
    [[ "$INCLUDE_BOOTSTRAP" == "1" ]] && argocd app get notifications || true
  fi

  say "[4/6] prod re-seal (apply)"
  cmd="SHOW_DIFF=1 INCLUDE_BOOTSTRAP=${INCLUDE_BOOTSTRAP} bash ops/seal/re-seal.sh prod"
  if [[ "$DRY_RUN" == "1" ]]; then
    say "  (dry-run) $cmd"
  else
    eval "$cmd"
    git push || true
  fi

  if command -v argocd >/dev/null 2>&1; then
    argocd app get prod-secrets || true
  fi
}

restore_args_normal () {
  say "[5/6] restore renew period: $RENEW_NORMAL"
  if [[ "$DRY_RUN" == "1" ]]; then
    say "  (dry-run) restore args to $RENEW_NORMAL"
    return 0
  fi
  if [[ -s /tmp/ss-args-backup.json ]]; then
    # Restore: replace/add renew arg from backup args
    if yq -e '.[0]' /tmp/ss-args-backup.json >/dev/null 2>&1; then
      if yq -e 'map(select(test("^--key-renew-period="))) | length > 0' /tmp/ss-args-backup.json >/dev/null 2>&1; then
        NEW_ARGS=$(yq "(map(if test(\"^--key-renew-period=\") then \"--key-renew-period=$RENEW_NORMAL\" else . end))" /tmp/ss-args-backup.json -o=json)
      else
        NEW_ARGS=$(yq ". + [\"--key-renew-period=$RENEW_NORMAL\"]" /tmp/ss-args-backup.json -o=json)
      fi
    else
      NEW_ARGS=$(printf '["--key-renew-period=%s"]' "$RENEW_NORMAL")
    fi

    kubectl -n "$SS_NS" patch deploy "$DEPLOY" \
      --type='json' \
      -p="[ {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/args\",\"value\": $NEW_ARGS } ]"
  else
    echo "⚠️  /tmp/ss-args-backup.json missing (skipping restore). Manual check recommended."
  fi
}

final_check () {
  say "[6/6] Final check"
  if command -v argocd >/dev/null 2>&1; then
    argocd app get dev-secrets || true
    argocd app get prod-secrets || true
    [[ "$INCLUDE_BOOTSTRAP" == "1" ]] && argocd app get notifications || true
  fi
  say "✅ Key rotation & re-seal procedure complete"
  say "ℹ️ (optional) Old key cleanup recommended after all environments are healthy and multiple deploy cycles have passed"
}

# Execution flow
backup_keys
patch_args_temp_short
reseal_all
restore_args_normal
final_check
