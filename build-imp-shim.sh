#!/usr/bin/env bash
set -euo pipefail

command -v patchelf >/dev/null 2>&1 || {
  echo "patchelf is required (to set SONAME to libcurl-impersonate.so)." >&2
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
NATIVE_DIR="${ROOT_DIR}/native/desktop"

OUT_DIR_X64="${ROOT_DIR}/out/linux-x64"
OUT_DIR_ARM64="${ROOT_DIR}/out/linux-arm64"
mkdir -p "${OUT_DIR_X64}" "${OUT_DIR_ARM64}"

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/curlshim.XXXXXX")"
trap 'rm -rf "${WORK_DIR}"' EXIT


find_first() {
  local root="$1"
  local pattern="$2"

  find "${root}" -maxdepth 6 -type f -name "${pattern}" | head -n1 || true
}

build_shim() {
  local out_dir="$1"
  local cc="$2"
  local strip_bin="$3"

  local so="${out_dir}/libcurlshim.so"

  "${cc}" \
    -fPIC -O2 -DLIBCURL_IMPERSONATE \
    -I "${NATIVE_DIR}" \
    "${NATIVE_DIR}/curlshim.c" \
    -shared -Wl,-soname,libcurlshim.so -Wl,-rpath,'$ORIGIN' \
    -L "${out_dir}" -lcurl-impersonate \
    -o "${so}"

  if command -v "${strip_bin}" >/dev/null 2>&1; then
    "${strip_bin}" -x "${so}" || true
  fi

  echo "Built ${so}"
}

# will already be extracted to
# libcurl-impersonate-linux-gnu

LIB="$(find_first "${WORK_DIR}/libcurl-impersonate-linux-gnu" 'libcurl-impersonate*.so*')"

[[ -n "${LIB}" ]]  || { echo "Could not find libcurl-impersonate .so in archive." >&2; exit 1; }

cp -f "${LIB}"  "${OUT_DIR}/libcurl-impersonate.so"

patchelf --set-soname libcurl-impersonate.so "${OUT_DIR}/libcurl-impersonate.so"


if [ "${FLATPAK_ARCH}" == "x86_64" ]; then
  CC="${CC:-gcc}"
  STRIP="${STRIP:-strip}"
elif [ "${FLATPAK_ARCH}" == "aarch64" ]; then
  CC="${AARCH64_CC:-aarch64-linux-gnu-gcc}"
  STRIP="${AARCH64_STRIP:-aarch64-linux-gnu-strip}"
else
  echo "Unsupported Arch present $FLATPAK_ARCH"
  exit 1
fi

echo "== Building shim for ${FLATPAK_ARCH} =="

build_shim "${OUT_DIR_X64}" "${CC}" "${STRIP}"

if ! command -v "${CC}" >/dev/null 2>&1; then
  echo "Missing cross-compiler ${CC}. Set AARCH64_CC or install it." >&2
  exit 1
fi