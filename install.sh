#!/usr/bin/env bash
# Link config and wording, then install missing user-scoped marketplace plugins.
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source_file="$repo_dir/omp/config.yml"
[[ -f "$source_file" ]] || { printf 'Missing config: %s\n' "$source_file" >&2; exit 1; }
skill_dir="$repo_dir/omp/skills/wording"
for file in "$skill_dir/SKILL.md" "$skill_dir/references/wording-rules.md"; do
    [[ -f "$file" ]] || { printf 'Missing skill file: %s\n' "$file" >&2; exit 1; }
done
plugin_file="$repo_dir/omp/plugins.txt"
[[ -f "$plugin_file" ]] || { printf 'Missing plugin list: %s\n' "$plugin_file" >&2; exit 1; }
command -v jq >/dev/null || { printf 'Install jq before running this script.\n' >&2; exit 1; }
agent_dir=$(omp config path)
[[ -n "$agent_dir" ]] || { printf 'omp returned an empty config directory\n' >&2; exit 1; }
mkdir -p -- "$agent_dir"
target="$agent_dir/config.yml"
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
link_path() {
    local source="$1" target="$2" backup_dir
    if [[ -L "$target" && "$(readlink -- "$target")" == "$source" ]]; then
        printf 'Already linked: %s\n' "$target"
        return
    fi
    if [[ -e "$target" || -L "$target" ]]; then
        backup_dir=$(mktemp -d "$agent_dir/config-backup.XXXXXX")
        mv -- "$target" "$backup_dir/"
        printf 'Backup: %s/%s\n' "$backup_dir" "${target##*/}"
    fi
    ln -s -- "$source" "$target"
    printf 'Linked: %s -> %s\n' "$target" "$source"
}

link_path "$source_file" "$target"
mkdir -p -- "$agent_dir/skills"
link_path "$skill_dir" "$agent_dir/skills/wording"

# Use omp's inventory rather than copying machine-specific plugin state.
installed=$(omp plugin list --json)
marketplaces=$(omp plugin marketplace list)
has_marketplace() {
    local name rest
    while read -r name rest; do
        [[ "$name" != "$1" ]] || return 0
    done <<< "$marketplaces"
    return 1
}

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
