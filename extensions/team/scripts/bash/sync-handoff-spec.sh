#!/usr/bin/env bash
# AI Team extension: fetch handoff requirement URL and build spec.override.md
#
# Usage: sync-handoff-spec.sh [--json] [argument text...]

set -e

JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json] [arguments...]"
            exit 0
            ;;
        *) ARGS+=("$arg") ;;
    esac
done

ARGS_TEXT="${ARGS[*]}"

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=handoff-spec-common.sh
source "$SCRIPT_DIR/handoff-spec-common.sh"

REPO_ROOT="$(handoff_spec_repo_root)"
cd "$REPO_ROOT"

WORK_DIR=$(resolve_team_work_dir "$REPO_ROOT" "$ARGS_TEXT") || {
    if $JSON_MODE && ! resolve_handoff_requirement_url "$REPO_ROOT" "$ARGS_TEXT" >/dev/null; then
        emit_handoff_json true "" "" "" "" false
        exit 0
    fi
    echo "ERROR: work_type and work_id are required to resolve the Team work directory" >&2
    exit 1
}
mkdir -p "$WORK_DIR"

OVERRIDE_NAME="$(_override_file_name "$REPO_ROOT")"
OVERRIDE_FILE="$WORK_DIR/$OVERRIDE_NAME"
SPEC_FILE="$WORK_DIR/spec.md"
EFFECTIVE_SPEC="$(resolve_effective_spec "$WORK_DIR" "$OVERRIDE_NAME")"

if ! url=$(resolve_handoff_requirement_url "$REPO_ROOT" "$ARGS_TEXT"); then
    if $JSON_MODE; then
        emit_handoff_json true "$WORK_DIR" "$SPEC_FILE" "$EFFECTIVE_SPEC" "" false
    else
        echo "SKIPPED: no handoff_requirement_url found"
    fi
    exit 0
fi

bootstrapped=false
if [[ ! -f "$SPEC_FILE" ]]; then
    write_spec_pointer "$SPEC_FILE" "$url"
    bootstrapped=true
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
fetched="$tmpdir/fetched.md"

if ! fetch_remote_requirement "$url" "$fetched"; then
    echo "ERROR: Failed to fetch handoff requirement URL: $url" >&2
    exit 1
fi

write_merged_override "$OVERRIDE_FILE" "$url" "$SPEC_FILE" "$fetched"
ensure_gitignore_pattern "$REPO_ROOT" "**/$OVERRIDE_NAME"

EFFECTIVE_SPEC="$(resolve_effective_spec "$WORK_DIR" "$OVERRIDE_NAME")"

bootstrapped_json=false
if [[ "$bootstrapped" == true ]]; then
    bootstrapped_json=true
fi

if $JSON_MODE; then
    emit_handoff_json false "$WORK_DIR" "$SPEC_FILE" "$EFFECTIVE_SPEC" "$url" "$bootstrapped_json"
else
    echo "WORK_DIR: $WORK_DIR"
    echo "SPEC: $SPEC_FILE"
    echo "EFFECTIVE_SPEC: $EFFECTIVE_SPEC"
    echo "HANDOFF_REQUIREMENT_URL: $url"
    echo "SPEC_BOOTSTRAPPED: $bootstrapped"
fi
