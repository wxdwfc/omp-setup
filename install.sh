#!/usr/bin/env bash
# Link omp and/or Antigravity (agy) configurations, skills, themes, and statusline.
# Usage: ./install.sh [all|omp|agy]
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
command -v jq >/dev/null || { printf 'Install jq before running this script.\n' >&2; exit 1; }

skill_dir="$repo_dir/omp/skills/wording"
for file in "$skill_dir/SKILL.md" "$skill_dir/references/wording-rules.md"; do
    [[ -f "$file" ]] || { printf 'Missing skill file: %s\n' "$file" >&2; exit 1; }
done

link_path() {
    local source="$1" target="$2" backup_root="$3" backup_dir
    if [[ -L "$target" && "$(readlink -- "$target")" == "$source" ]]; then
        printf 'Already linked: %s\n' "$target"
        return
    fi
    if [[ -e "$target" || -L "$target" ]]; then
        backup_dir=$(mktemp -d "$backup_root/config-backup.XXXXXX")
        mv -- "$target" "$backup_dir/"
        printf 'Backup: %s/%s\n' "$backup_dir" "${target##*/}"
    fi
    ln -s -- "$source" "$target"
    printf 'Linked: %s -> %s\n' "$target" "$source"
}

install_omp() {
    local source_file="$repo_dir/omp/config.yml"
    [[ -f "$source_file" ]] || { printf 'Missing config: %s\n' "$source_file" >&2; exit 1; }
    local theme_dir="$repo_dir/omp/themes"
    local theme_files=(research-night.json research-day.json)
    local file
    for file in "${theme_files[@]}"; do
        [[ -f "$theme_dir/$file" ]] || { printf 'Missing theme file: %s\n' "$theme_dir/$file" >&2; exit 1; }
    done
    local plugin_file="$repo_dir/omp/plugins.txt"
    [[ -f "$plugin_file" ]] || { printf 'Missing plugin list: %s\n' "$plugin_file" >&2; exit 1; }
    command -v omp >/dev/null || { printf 'Install omp before running "./install.sh omp".\n' >&2; exit 1; }

    local agent_dir
    agent_dir=$(omp config path)
    [[ -n "$agent_dir" ]] || { printf 'omp returned an empty config directory\n' >&2; exit 1; }
    mkdir -p -- "$agent_dir"
    local target="$agent_dir/config.yml"
    # omp also supports an existing config.yaml; do not leave two competing files.
    if [[ ! -e "$target" && ! -L "$target" ]]; then
        if [[ -e "$agent_dir/config.yaml" || -L "$agent_dir/config.yaml" ]]; then
            target="$agent_dir/config.yaml"
        fi
    fi

    # Config must be a file; the wording target may be an existing skill directory.
    if [[ -d "$target" ]]; then
        printf 'Refusing to replace a directory: %s\n' "$target" >&2
        exit 1
    fi
    for file in "${theme_files[@]}"; do
        if [[ -d "$agent_dir/themes/$file" ]]; then
            printf 'Refusing to replace a directory: %s\n' "$agent_dir/themes/$file" >&2
            exit 1
        fi
    done

    link_path "$source_file" "$target" "$agent_dir"
    mkdir -p -- "$agent_dir/skills"
    link_path "$skill_dir" "$agent_dir/skills/wording" "$agent_dir"
    mkdir -p -- "$agent_dir/themes"
    for file in "${theme_files[@]}"; do
        link_path "$theme_dir/$file" "$agent_dir/themes/$file" "$agent_dir"
    done

    # Use omp's inventory rather than copying machine-specific plugin state.
    local installed marketplaces
    installed=$(omp plugin list --json)
    marketplaces=$(omp plugin marketplace list)
    has_marketplace() {
        local name rest
        while read -r name rest; do
            [[ "$name" != "$1" ]] || return 0
        done <<< "$marketplaces"
        return 1
    }

    local source plugin marketplace
    while read -r source plugin || [[ -n "$source" ]]; do
        [[ -n "$source" && "$source" != \#* ]] || continue
        marketplace=${plugin##*@}
        if ! has_marketplace "$marketplace"; then
            omp plugin marketplace add "$source"
            marketplaces+=$'\n'"$marketplace $source"
        fi
        if jq -e --arg id "$plugin" \
            'any(.marketplace[]; .id == $id and any(.entries[]; .scope == "user"))' \
            <<< "$installed" >/dev/null; then
            printf 'Already installed: %s (user)\n' "$plugin"
        else
            omp plugin install --scope user "$plugin"
            installed=$(omp plugin list --json)
        fi
    done < "$plugin_file"
}

install_agy() {
    local statusline_src="$repo_dir/agy/omp-statusline.py"
    [[ -f "$statusline_src" ]] || { printf 'Missing agy statusline: %s\n' "$statusline_src" >&2; exit 1; }
    chmod +x -- "$statusline_src"

    local agy_cfg_dir="$HOME/.config/agy"
    mkdir -p -- "$agy_cfg_dir"
    local statusline_target="$agy_cfg_dir/omp-statusline.py"
    if [[ -d "$statusline_target" ]]; then
        printf 'Refusing to replace a directory: %s\n' "$statusline_target" >&2
        exit 1
    fi
    link_path "$statusline_src" "$statusline_target" "$agy_cfg_dir"

    local agy_global_dir="$HOME/.gemini/config"
    mkdir -p -- "$agy_global_dir/skills"
    link_path "$skill_dir" "$agy_global_dir/skills/wording" "$agy_global_dir"

    local agy_cli_dir="$HOME/.gemini/antigravity-cli"
    local settings_file="$agy_cli_dir/settings.json"
    mkdir -p -- "$agy_cli_dir"
    if [[ -d "$settings_file" ]]; then
        printf 'Refusing to replace a directory: %s\n' "$settings_file" >&2
        exit 1
    fi

    if [[ -f "$settings_file" ]]; then
        if jq -e --arg cmd "$statusline_target" \
            '.statusLine.type == "command" and .statusLine.command == $cmd' \
            "$settings_file" >/dev/null 2>&1; then
            printf 'Already configured: %s (statusLine)\n' "$settings_file"
            return
        fi
        local backup_dir tmp_file
        backup_dir=$(mktemp -d "$agy_cfg_dir/config-backup.XXXXXX")
        cp -p -- "$settings_file" "$backup_dir/settings.json"
        printf 'Backup: %s/settings.json\n' "$backup_dir"
        tmp_file=$(mktemp "$agy_cli_dir/settings.json.XXXXXX")
        jq --arg cmd "$statusline_target" \
            '.statusLine = (.statusLine // {} | .type = "command" | .command = $cmd)' \
            "$settings_file" > "$tmp_file"
        mv -- "$tmp_file" "$settings_file"
        printf 'Configured statusLine in %s -> %s\n' "$settings_file" "$statusline_target"
    else
        jq -n --arg cmd "$statusline_target" \
            '{statusLine: {type: "command", command: $cmd}}' > "$settings_file"
        printf 'Created %s with statusLine -> %s\n' "$settings_file" "$statusline_target"
    fi
}

targets=("${@:-all}")
run_omp=0
run_agy=0
for arg in "${targets[@]}"; do
    case "$arg" in
        all)
            run_omp=1
            run_agy=1
            ;;
        omp)
            run_omp=1
            ;;
        agy|antigravity)
            run_agy=1
            ;;
        -h|--help)
            printf 'Usage: %s [all|omp|agy]\n' "$0"
            exit 0
            ;;
        *)
            printf 'Unknown target: %s (expected: all, omp, or agy)\n' "$arg" >&2
            exit 1
            ;;
    esac
done

if (( run_omp )); then
    install_omp
fi
if (( run_agy )); then
    install_agy
fi
