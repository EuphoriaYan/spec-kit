#!/usr/bin/env bash
# AI Team extension: shared helpers for handoff spec sync.

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

has_jq() { command -v jq >/dev/null 2>&1; }

json_escape() {
    local value="$1"
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//$'\n'/\\n}
    printf '%s' "$value"
}

_find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.specify" ]] || [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

handoff_spec_repo_root() {
    _find_project_root "$SCRIPT_DIR" || pwd
}

resolve_effective_spec() {
    local feature_dir="$1"
    local override_file="${2:-spec.override.md}"
    local override="$feature_dir/$override_file"
    if [[ -f "$override" ]]; then
        echo "$override"
    else
        echo "$feature_dir/spec.md"
    fi
}

_override_file_name() {
    local repo_root="$1"
    local config="$repo_root/.specify/extensions/team/ai-team-config.yml"
    local name="spec.override.md"
    if [[ -f "$config" ]]; then
        local parsed
        parsed=$(grep -E 'private_handoff_override_file:' "$config" 2>/dev/null | head -1 | sed 's/.*private_handoff_override_file:[[:space:]]*//' | tr -d ' "\r' || true)
        [[ -n "$parsed" ]] && name="$parsed"
    fi
    echo "$name"
}

_extract_https_url() {
    local raw="$1"
    local url=""
    if [[ "$raw" =~ (https://[^[:space:]\"\'\>]+) ]]; then
        url="${BASH_REMATCH[1]}"
        url="${url%/}"
    fi
    [[ "$url" == https://* ]] && echo "$url"
}

_parse_url_from_text() {
    local text="$1"
    local key value url
    for key in handoff_requirement_url published_requirement_url; do
        if [[ "$text" =~ ${key}[[:space:]]*=[[:space:]]*(https://[^[:space:]\"\'\>]+) ]]; then
            url="${BASH_REMATCH[1]}"
            url="${url%/}"
            echo "$url"
            return 0
        fi
    done
    while IFS= read -r line; do
        for key in handoff_requirement_url published_requirement_url; do
            if [[ "$line" =~ ^[[:space:]]*${key}:[[:space:]]*(https://[^[:space:]\"\'\#]+) ]]; then
                url="${BASH_REMATCH[1]}"
                url="${url%/}"
                echo "$url"
                return 0
            fi
        done
    done <<< "$text"
    return 1
}

_read_url_from_spec_frontmatter() {
    local spec_file="$1"
    [[ -f "$spec_file" ]] || return 1
    _parse_url_from_text "$(head -40 "$spec_file")"
}

_read_url_from_work_context() {
    local repo_root="$1"
    local args_text="${2:-}"
    local work_id="" category=""
    if [[ "$args_text" =~ work_id=([^[:space:]\"\'\>]+) ]]; then
        work_id="${BASH_REMATCH[1]}"
    fi
    if [[ "$args_text" =~ work_type=([^[:space:]\"\'\>]+) ]]; then
        category="${BASH_REMATCH[1]}"
        [[ "$category" == "bug" ]] && category="bugfix"
        [[ "$category" == "new-project" || "$category" == "template" ]] && category="feature"
    fi
    if [[ -n "$work_id" && ( "$category" == "feature" || "$category" == "bugfix" ) ]]; then
        local ctx="$repo_root/.specify/$category/$work_id/work-context.yml"
        [[ -f "$ctx" ]] && _parse_url_from_text "$(cat "$ctx")" && return 0
    fi
    return 1
}

resolve_team_work_dir() {
    local repo_root="$1" args_text="${2:-}" work_id="" category=""
    [[ "$args_text" =~ work_id=([^[:space:]\"\'\>]+) ]] && work_id="${BASH_REMATCH[1]}"
    [[ "$args_text" =~ work_type=([^[:space:]\"\'\>]+) ]] && category="${BASH_REMATCH[1]}"
    [[ "$category" == "bug" ]] && category="bugfix"
    [[ "$category" == "new-project" || "$category" == "template" ]] && category="feature"
    [[ "$category" == "feature" || "$category" == "bugfix" ]] || return 1
    [[ "$work_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || return 1
    echo "$repo_root/.specify/$category/$work_id"
}

resolve_handoff_requirement_url() {
    local repo_root="$1"
    local args_text="${2:-}"
    local url=""

    url=$(_extract_https_url "${HANDOFF_REQUIREMENT_URL:-}") && { echo "$url"; return 0; }
    url=$(_extract_https_url "${PUBLISHED_REQUIREMENT_URL:-}") && { echo "$url"; return 0; }
    url=$(_parse_url_from_text "$args_text") && { echo "$url"; return 0; }
    url=$(_read_url_from_work_context "$repo_root" "$args_text") && { echo "$url"; return 0; }

    local work_dir spec_file
    if work_dir=$(resolve_team_work_dir "$repo_root" "$args_text"); then
        spec_file="$work_dir/spec.md"
        url=$(_read_url_from_spec_frontmatter "$spec_file") && { echo "$url"; return 0; }
    fi
    return 1
}

ensure_gitignore_pattern() {
    local repo_root="$1"
    local pattern="${2:-**/spec.override.md}"
    local gitignore="$repo_root/.gitignore"
    if [[ -f "$gitignore" ]] && grep -qxF "$pattern" "$gitignore" 2>/dev/null; then
        return 0
    fi
    {
        echo ""
        echo "# Spec Kit AI Team remote handoff cache (auto-generated)"
        echo "$pattern"
    } >> "$gitignore"
}

spec_is_pointer_only() {
    local spec_file="$1"
    [[ -f "$spec_file" ]] || return 1
    if grep -q '^spec_source:[[:space:]]*remote' "$spec_file" 2>/dev/null; then
        return 0
    fi
    if grep -q 'Remote Reference' "$spec_file" 2>/dev/null; then
        return 0
    fi
    return 1
}

write_spec_pointer() {
    local spec_file="$1"
    local url="$2"
    mkdir -p "$(dirname "$spec_file")"
    cat > "$spec_file" <<EOF
---
handoff_requirement_url: $url
spec_source: remote
---

# Feature Specification (Remote Reference)

**Handoff Requirement URL**: $url

**Local cache**: \`spec.override.md\` (gitignored, generated by \`speckit.team.plan-and-task\`)

> Do not edit this file for full requirement content. Re-run handoff sync or update the remote source.
EOF
}

fetch_remote_requirement() {
    local url="$1"
    local dest="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$dest" "$url"
    else
        echo "ERROR: curl or wget required to fetch handoff requirement URL" >&2
        return 1
    fi
}

write_merged_override() {
    local override_file="$1"
    local url="$2"
    local spec_file="$3"
    local fetched_file="$4"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    {
        echo "# Effective Feature Specification (AI Team Handoff)"
        echo ""
        echo "**Source URL**: $url"
        echo "**Generated**: $timestamp"
        echo "**Public baseline**: \`spec.md\` (preserved unchanged)"
        echo ""
        echo "---"
        echo ""
    } > "$override_file"

    if [[ -f "$spec_file" ]] && ! spec_is_pointer_only "$spec_file"; then
        {
            echo "## Public baseline (from spec.md)"
            echo ""
            cat "$spec_file"
            echo ""
            echo "---"
            echo ""
            echo "## Handoff requirement (fetched)"
            echo ""
            cat "$fetched_file"
        } >> "$override_file"
    else
        {
            echo "## Handoff requirement (fetched)"
            echo ""
            cat "$fetched_file"
        } >> "$override_file"
    fi
}

emit_handoff_json() {
    local skipped="$1"
    local feature_dir="$2"
    local feature_spec="$3"
    local effective_spec="$4"
    local url="${5:-}"
    local bootstrapped="${6:-false}"

    if has_jq; then
        jq -cn \
            --argjson skipped "$skipped" \
            --arg feature_dir "$feature_dir" \
            --arg feature_spec "$feature_spec" \
            --arg effective_spec "$effective_spec" \
            --arg handoff_url "$url" \
            --argjson spec_bootstrapped "$bootstrapped" \
            '{SKIPPED:$skipped,WORK_DIR:$feature_dir,SPEC:$feature_spec,EFFECTIVE_SPEC:$effective_spec,HANDOFF_REQUIREMENT_URL:$handoff_url,SPEC_BOOTSTRAPPED:$spec_bootstrapped}'
    else
        printf '{"SKIPPED":%s,"WORK_DIR":"%s","SPEC":"%s","EFFECTIVE_SPEC":"%s","HANDOFF_REQUIREMENT_URL":"%s","SPEC_BOOTSTRAPPED":%s}\n' \
            "$skipped" \
            "$(json_escape "$feature_dir")" \
            "$(json_escape "$feature_spec")" \
            "$(json_escape "$effective_spec")" \
            "$(json_escape "$url")" \
            "$bootstrapped"
    fi
}
