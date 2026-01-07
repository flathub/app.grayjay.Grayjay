#!/usr/bin/env bash
set -euo pipefail

VERSION="1.2.3"

URL_X64="https://github.com/lexiforest/curl-impersonate/releases/download/v${VERSION}/libcurl-impersonate-v${VERSION}.x86_64-linux-gnu.tar.gz"
URL_ARM64="https://github.com/lexiforest/curl-impersonate/releases/download/v${VERSION}/libcurl-impersonate-v${VERSION}.aarch64-linux-gnu.tar.gz"

[[ "$(uname -s)" == "Linux" ]] || { echo "This script must run on Linux." >&2; exit 1; }
[[ "$(uname -m)" == "x86_64" ]] || { echo "This script uses an x86_64 host toolchain." >&2; exit 1; }

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

download_and_extract() {
  local url="$1"
  local out="$2"

  mkdir -p "${out}"
  local tgt="${WORK_DIR}/tmp.tar.gz"
  curl -fsSL --retry 3 -o "${tgt}" "${url}"
  tar -xzf "${tgt}" -C "${out}"
}

find_first() {
  local root="$1"
  local pattern="$2"

  find "${root}" -maxdepth 6 -type f -name "${pattern}" | head -n1 || true
}

build_shim() {
  local arch="$1"
  local out_dir="$2"
  local cc="$3"
  local strip_bin="$4"

  local so="${out_dir}/libcurlshim.so"

  echo "== Building shim (${arch}) =="

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

echo "== Download: libcurl-impersonate (x86_64) =="
download_and_extract "${URL_X64}" "${WORK_DIR}/x64"

echo "== Download: libcurl-impersonate (aarch64) =="
download_and_extract "${URL_ARM64}" "${WORK_DIR}/arm64"

LIB_X64="$(find_first "${WORK_DIR}/x64" 'libcurl-impersonate*.so*')"
LIB_ARM64="$(find_first "${WORK_DIR}/arm64" 'libcurl-impersonate*.so*')"

[[ -n "${LIB_X64}" ]]  || { echo "Could not find libcurl-impersonate .so in x86_64 archive." >&2; exit 1; }
[[ -n "${LIB_ARM64}" ]] || { echo "Could not find libcurl-impersonate .so in aarch64 archive." >&2; exit 1; }

cp -f "${LIB_X64}"  "${OUT_DIR_X64}/libcurl-impersonate.so"
cp -f "${LIB_ARM64}" "${OUT_DIR_ARM64}/libcurl-impersonate.so"

patchelf --set-soname libcurl-impersonate.so "${OUT_DIR_X64}/libcurl-impersonate.so"
patchelf --set-soname libcurl-impersonate.so "${OUT_DIR_ARM64}/libcurl-impersonate.so"

CC_X64="${CC:-gcc}"
CC_ARM64="${AARCH64_CC:-aarch64-linux-gnu-gcc}"

STRIP_X64="${STRIP:-strip}"
STRIP_ARM64="${AARCH64_STRIP:-aarch64-linux-gnu-strip}"

build_shim "x86_64" "${OUT_DIR_X64}" "${CC_X64}" "${STRIP_X64}"

if ! command -v "${CC_ARM64}" >/dev/null 2>&1; then
  echo "Missing cross-compiler ${CC_ARM64}. Set AARCH64_CC or install it." >&2
  exit 1
fi

build_shim "aarch64" "${OUT_DIR_ARM64}" "${CC_ARM64}" "${STRIP_ARM64}"

echo
echo "== Outputs =="
ls -lh "${OUT_DIR_X64}" "${OUT_DIR_ARM64}"
