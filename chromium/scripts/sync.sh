#!/usr/bin/env bash
# Downloads Chromium at the version in chromium/VERSION into $RES_WORK/src, with
# the Android dependencies, without git history (much smaller and faster).
# Test-only downloads are skipped, and large unused parts removed, to fit the
# free GitHub runner's disk.
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
  "custom_deps": {
    # Test-only (Java unit tests); several GB.
    "src/third_party/robolectric/cipd": None,
    "src/third_party/espresso": None,
    "src/third_party/junit/src": None,
    "src/third_party/google-truth/src": None,
    "src/third_party/hamcrest/cipd": None,
  },
  "custom_vars": {
    "checkout_configuration": "small",
    "checkout_js_coverage_modules": False,
    "checkout_openxr": False,
  },
}]
target_os = ["android"]
EOF

show_disk() { df -h "$work" | tail -1; }

echo "::group::gclient sync ${version}"
date; show_disk
# Limit parallel fetches: googlesource.com rate-limits busy addresses.
gclient sync --revision "src@refs/tags/${version}" \
  --no-history --nohooks --force -D --jobs 8 || {
    echo "sync failed; disk:"; show_disk
    du -xsh "$work"/src/third_party/* 2>/dev/null | sort -h | tail -25
    exit 1
  }
show_disk
echo "::endgroup::"

echo "::group::gclient runhooks"
gclient runhooks --jobs "$(nproc)"
echo "::endgroup::"

# Remove parts of the checkout the APK build never reads.
rm -rf "$work"/.cipd/pkgs \
  "$work"/src/third_party/robolectric/cipd \
  "$work"/src/third_party/android_sdk/public/emulator \
  "$work"/src/third_party/android_sdk/public/system-images 2>/dev/null || true

echo "::group::disk usage"
du -xsh "$work/src"
du -xsh "$work"/src/third_party/* 2>/dev/null | sort -h | tail -15
show_disk
echo "::endgroup::"
