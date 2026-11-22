#!/usr/bin/env bash
# Build the standalone macOS app.
#
#   bash packaging/build_macos.sh            # this Mac's architecture
#   bash packaging/build_macos.sh x86_64     # Intel build (on Apple Silicon
#                                            # it runs through Rosetta)
#   bash packaging/build_macos.sh arm64      # Apple Silicon build
#
# Needs internet the first time (it downloads a private Python and the
# pinned packages into packaging/.build-cache/, which is never committed;
# set VISOLAB_BUILD_CACHE to share one cache between several apps). The
# app it produces needs neither Python nor internet.
#
# Output: dist/macOS/<App>-macOS-<Apple-Silicon|Intel>.zip (the .app itself is
# in packaging/.build-cache/build-<App>-<arch>/dist/). The build fails unless the
# packaged app passes its own --selftest.
set -euo pipefail

ARCH="${1:-$(uname -m)}"
case "$ARCH" in
  arm64)  PLATFORM=osx-arm64; UVPLAT=aarch64-apple-darwin; MIN_MACOS=12.0; LABEL=Apple-Silicon ;;
  x86_64) PLATFORM=osx-64;    UVPLAT=x86_64-apple-darwin;  MIN_MACOS=11.0; LABEL=Intel ;;
  *) echo "Unknown architecture: $ARCH (use arm64 or x86_64)"; exit 1 ;;
esac

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
APP="$(sed -n 's/^APP_NAME = "\(.*\)"$/\1/p' packaging/build.spec)"
CACHE="${VISOLAB_BUILD_CACHE:-$REPO/packaging/.build-cache}"
ENV="$CACHE/env-$ARCH"
mkdir -p "$CACHE"

# ── Private Python (conda-forge: Tk linked the way Pillow's ImageTk needs)
MM="$CACHE/micromamba/bin/micromamba"
if [ ! -x "$MM" ]; then
  host=$([ "$(uname -m)" = arm64 ] && echo osx-arm64 || echo osx-64)
  echo "Downloading micromamba ($host)..."
  mkdir -p "$CACHE/micromamba"
  curl -fsSL "https://micro.mamba.pm/api/micromamba/$host/latest" \
    | tar -xj -C "$CACHE/micromamba" bin/micromamba
fi
export MAMBA_ROOT_PREFIX="$CACHE/mamba-root"
if [ ! -x "$ENV/bin/python" ]; then
  echo "Creating the build environment ($ARCH)..."
  "$MM" create -y -q -p "$ENV" --platform "$PLATFORM" -c conda-forge \
    python=3.12.10 tk=8.6 pip
fi

RUN=(arch "-$ARCH")
"${RUN[@]}" "$ENV/bin/python" -m pip install -q --upgrade uv
# Wheels built for the oldest supported macOS, so the app also runs on
# Macs older than the one building it.
MACOSX_DEPLOYMENT_TARGET="$MIN_MACOS" "${RUN[@]}" "$ENV/bin/python" -m uv pip install -q \
  --python "$ENV/bin/python" --python-platform "$UVPLAT" --only-binary :all: \
  -r packaging/requirements-lock.txt pyinstaller==6.16.0

# ── Build ──────────────────────────────────────────────────────────────
DIST="$CACHE/build-$APP-$ARCH/dist"
WORK="$CACHE/build-$APP-$ARCH/work"
rm -rf "$DIST" "$WORK"
"${RUN[@]}" "$ENV/bin/python" -m PyInstaller --noconfirm --clean \
  --distpath "$DIST" --workpath "$WORK" packaging/build.spec

# ── Every bundled library must run on the declared minimum macOS ───────
PLIST="$DIST/$APP.app/Contents/Info.plist"
DECLARED="$(/usr/libexec/PlistBuddy -c 'Print :LSMinimumSystemVersion' "$PLIST")"
NEEDED="$(find "$DIST/$APP.app/Contents" \( -name '*.so' -o -name '*.dylib' \) \
  -exec vtool -show-build {} \; 2>/dev/null \
  | awk '/minos/ {print $2}' | sort -t. -k1,1n -k2,2n | tail -n 1)"
if [ -n "$NEEDED" ] && [ "$(printf '%s\n%s\n' "$DECLARED" "$NEEDED" \
     | sort -t. -k1,1n -k2,2n | tail -n 1)" != "$DECLARED" ]; then
  echo "A bundled library needs macOS $NEEDED, but the app declares $DECLARED."
  echo "Raise LSMinimumSystemVersion in packaging/build.spec (and the README)."
  exit 1
fi
echo "Minimum macOS: $DECLARED (bundled libraries need ${NEEDED:-less})"

# ── Self-test the packaged app itself ─────────────────────────────────
echo "Running the packaged app's self-test..."
if ! "${RUN[@]}" "$DIST/$APP.app/Contents/MacOS/$APP" --selftest; then
  echo "SELF-TEST FAILED. Log:"
  tail -n 60 "$HOME/Library/Logs/$APP/$APP.log" || true
  exit 1
fi
tail -n 6 "$HOME/Library/Logs/$APP/$APP.log" || true

# ── Package ────────────────────────────────────────────────────────────
mkdir -p "$REPO/dist/macOS"
ZIP="$REPO/dist/macOS/$APP-macOS-$LABEL.zip"
rm -f "$ZIP"
ditto -c -k --sequesterRsrc --keepParent "$DIST/$APP.app" "$ZIP"
echo "Done: $ZIP"
