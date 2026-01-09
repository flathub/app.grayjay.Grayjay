#!/bin/bash
# returns a dotnet system ref 9i.e. linux-x64) based on the flatpak architecture
if [ "${FLATPAK_ARCH}" == "x86_64" ]; then
  echo "linux-x64"
elif [ "${FLATPAK_ARCH}" == "aarch64" ]; then
  echo "linux-arm64"
else
#   echo "Unsupported Arch present $FLATPAK_ARCH"
  exit 1
fi