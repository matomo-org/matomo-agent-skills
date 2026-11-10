#!/usr/bin/env bash
# Print the path of a vendor/ directory installed from a Matomo revision's composer.lock,
# building it on first use.  See --help.
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") -r <repo> -H <rev> [-c <cache>]

  -r, --repo <dir>     Matomo checkout that has the revision
  -H, --head <rev>     revision whose composer.json and composer.lock to install
  -c, --cache <dir>    cache root, one directory per composer.lock blob   [$cache]

Prints the vendor directory on stdout.  Installs are cached by the blob ID of composer.lock,
so every revision with the same lock file shares one install, and two runs with the same lock
see the same dependency code.  The install runs composer with --no-scripts --no-plugins
--no-autoloader: only the package sources are needed, for reading.  Concurrent callers for
one lock wait for each other.  Exit status 1 when the install fails (the caller then runs
without vendor/), 2 on bad arguments.

Keep the cache outside the results tree, away from other runs' reports.
EOF
}

die() { echo "$(basename "$0"): $*" >&2; exit 2; }

repo='' head=''
cache=/data/matomo/review-vendor
while (( $# )); do
  case $1 in
    -h|--help) usage; exit 0 ;;
    -r|--repo|-H|--head|-c|--cache)
      [[ $# -ge 2 && -n $2 ]] || die "$1 needs a value"
      case $1 in
        -r|--repo)  repo=$2 ;;
        -H|--head)  head=$2 ;;
        -c|--cache) cache=$2 ;;
      esac
      shift 2 ;;
    *) usage >&2; die "unknown argument: $1" ;;
  esac
done
[[ -n $repo && -n $head ]] || { usage >&2; die "--repo and --head are required"; }
command -v composer >/dev/null || { echo "$(basename "$0"): composer not found on PATH" >&2; exit 1; }

lock=$(git -C "$repo" rev-parse --verify -q "$head:composer.lock") \
  || { echo "$(basename "$0"): no composer.lock at $head" >&2; exit 1; }
json=$(git -C "$repo" rev-parse --verify -q "$head:composer.json") \
  || { echo "$(basename "$0"): no composer.json at $head" >&2; exit 1; }
mkdir -p "$cache"
dir=$cache/$lock

exec 9>"$dir.lock"
flock 9
if [[ ! -d $dir/vendor ]]; then
  tmp=$(mktemp -d "$cache/.build.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT
  git -C "$repo" cat-file blob "$json" >"$tmp/composer.json"
  git -C "$repo" cat-file blob "$lock" >"$tmp/composer.lock"
  echo "installing composer dependencies for lock ${lock:0:10} into $dir" >&2
  if ! COMPOSER_NO_INTERACTION=1 composer install --quiet --working-dir "$tmp" \
      --no-scripts --no-plugins --no-autoloader --no-progress >&2; then
    echo "$(basename "$0"): composer install failed for lock ${lock:0:10}" >&2
    exit 1
  fi
  rm -rf "$dir"
  mv "$tmp" "$dir"
  trap - EXIT
fi
echo "$dir/vendor"
