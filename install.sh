#!/usr/bin/env bash
# Link this checkout's config into the active omp profile; preserve existing files.
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source_file="$repo_dir/omp/config.yml"
[[ -f "$source_file" ]] || { printf 'Missing config: %s\n' "$source_file" >&2; exit 1; }
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

if [[ -L "$target" && "$(readlink -- "$target")" == "$source_file" ]]; then
    printf 'Already linked: %s\n' "$target"
    exit 0
fi
if [[ -d "$target" ]]; then
    printf 'Refusing to replace a directory: %s\n' "$target" >&2
    exit 1
fi
if [[ -e "$target" || -L "$target" ]]; then
    backup_dir=$(mktemp -d "$agent_dir/config-backup.XXXXXX")
    mv -- "$target" "$backup_dir/"
    printf 'Backup: %s/%s\n' "$backup_dir" "${target##*/}"
fi
ln -s -- "$source_file" "$target"
printf 'Linked: %s -> %s\n' "$target" "$source_file"
