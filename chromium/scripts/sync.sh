#!/usr/bin/env bash
# Downloads Chromium at the version in chromium/VERSION into $RES_WORK/src, with
# the Android dependencies, without git history (much smaller and faster).
set -euo pipefail

version="$(cat "$(dirname "$0")/../VERSION")"
work="${RES_WORK:?RES_WORK must be set}"
mkdir -p "$work"
cd "$work"

cat > .gclient <<EOF
solutions = [{
  "name": "src",
  "url": "https://chromium.googlesource.com/chromium/src.git",
  "managed": False,
  "custom_deps": {},
  "custom_vars": {},
}]
target_os = ["android"]
EOF

echo "::group::gclient sync ${version}"
date
# Limit parallel fetches: googlesource.com rate-limits busy addresses.
gclient sync --revision "src@refs/tags/${version}" \
  --no-history --nohooks --force -D --jobs 8
echo "::endgroup::"

echo "::group::gclient runhooks"
gclient runhooks --jobs "$(nproc)"
echo "::endgroup::"

du -sh "$work/src"
df -h "$work"
