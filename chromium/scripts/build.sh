#!/usr/bin/env bash
# Applies Resolute's patches to the Chromium tree and builds the APK.
#
# RES_WORK      folder holding src/ (from sync.sh)
# RES_CPU       GN target_cpu, e.g. arm64
# RES_DEADLINE  optional Unix time. The build stops there and exits 124 so the
#               next CI stage can resume from out/ (chained builds).
# RES_PACKAGES  where the finished APK is copied
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
work="${RES_WORK:?}"
cpu="${RES_CPU:-arm64}"
packages="${RES_PACKAGES:?}"
out="out/android-${cpu}"
mkdir -p "$packages"
cd "$work/src"

# Clean tree, then apply patches in filename order.
git reset -q --hard HEAD
git clean -q -fd -e out
for p in "$here"/patches/*.patch; do
  [ -e "$p" ] || continue
  echo "applying $(basename "$p")"
  git apply "$p"
done

# Resumed stages run on a fresh machine with a fresh checkout. Give every source
# file the same old timestamp so ninja doesn't think the restored out/ is stale.
if [ -n "${RES_DEADLINE:-}" ]; then
  find . -path ./out -prune -o -newermt "2001-01-02" -print0 \
    | xargs -0 -r touch -h -d "2001-01-01"
  # Files our patches change must look new, so a saved build from an earlier
  # run rebuilds them (this is what makes small-change rebuilds fast).
  git diff --name-only -z | xargs -0 -r touch -h
fi

mkdir -p "$out"
{ cat "$here/args.gn"; echo "target_cpu = \"${cpu}\""; } > "$work/args.new"
# Only rewrite args.gn if it changed, otherwise ninja regenerates everything.
cmp -s "$work/args.new" "$out/args.gn" || cp "$work/args.new" "$out/args.gn"
[ -e "$out/build.ninja" ] || gn gen "$out"

echo "build start $(date -Iseconds)"
if [ -n "${RES_DEADLINE:-}" ]; then
  left=$(( RES_DEADLINE - $(date +%s) ))
  if [ "$left" -le 0 ]; then echo "no time left"; exit 124; fi
  rc=0
  timeout --signal=INT --kill-after=5m "$left" autoninja -C "$out" chrome_public_apk chrome_public_bundle || rc=$?
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 130 ]; then
    echo "stopped at deadline $(date -Iseconds); next stage resumes"
    exit 124
  fi
  [ "$rc" -eq 0 ] || exit "$rc"
else
  autoninja -C "$out" chrome_public_apk chrome_public_bundle
fi
echo "build done $(date -Iseconds)"

cp "$out/apks/ChromePublic.apk" "$packages/resolute-chromium-${cpu}.apk"
# The Android App Bundle (.aab) is what Google Play takes. Play then sends each
# phone only the parts it needs (its language, screen density), so downloads
# are much smaller than the APK. Not yet signed with the upload key.
aab=$(find "$out/apks" -maxdepth 1 -name '*.aab' | head -1)
[ -n "$aab" ] && cp "$aab" "$packages/resolute-chromium-${cpu}.aab"
ls -l "$packages"
