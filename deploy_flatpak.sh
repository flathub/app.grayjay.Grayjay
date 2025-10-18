#!/bin/bash
# This is a copy of the linux build steps from FUTO, except modified for Flatpak.

# SPDX-License-Identifier: LicenseRef-Source-First-1.1


# Changes include:
# - removing upload of artifacts to server
# - removing cleanup of artifacts (flatpak builds run from a clean clone)

# cause script to fail as soon as one command has a failing exit code,
# rather than trying to continue. See: https://stackoverflow.com/a/1379904/
set -e


version=$(cat Grayjay.ClientServer/AppVersion.json | jq '.Version')

if [[ "$1" != "" ]]; then
  destination="$1"
else
  echo -n "Install Destination:"
  read destination
fi

packagecache=""
if [[ "$2" != "" ]]; then
  packagecache="$2"
fi

echo "$packagecache"

printf "Version to deploy: $version\n"

dotnet_version="8.0"

if [ "${FLATPAK_ARCH}" == "x86_64" ]; then
  runtime="linux-x64"
elif [ "${FLATPAK_ARCH}" == "aarch64" ]; then
  runtime="linux-arm64"
else
  echo "Unsupported Arch present $FLATPAK_ARCH"
  exit 1
fi
echo "Building for $runtime"

OWD=$(pwd)

# Publish CEF
cd Grayjay.Desktop.CEF
DOTNET_CLI_TELEMETRY_OPTOUT=true DOTNET_SKIP_FIRST_TIME_EXPERIENCE=true dotnet publish --source "$packagecache" -r $runtime -c Release -p:AssemblyVersion=1.$version.0.0

cd Grayjay.Desktop.CEF/bin/Release/net$dotnet_version/$runtime/publish	

chmod u=rwx Grayjay
chmod u=rwx FUTO.Updater.Client
chmod u=rwx ffmpeg

cd ../
mv publish/* "${destination}"

cd "${OWD}"


