#!/usr/bin/env bash
# Link this checkout's config and wording skill into the active omp profile.
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source_file="$repo_dir/omp/config.yml"
[[ -f "$source_file" ]] || { printf 'Missing config: %s\n' "$source_file" >&2; exit 1; }
skill_dir="$repo_dir/omp/skills/wording"
for file in "$skill_dir/SKILL.md" "$skill_dir/references/wording-rules.md"; do
    [[ -f "$file" ]] || { printf 'Missing skill file: %s\n' "$file" >&2; exit 1; }
done
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
