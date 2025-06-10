# Grayjay Desktop Flatpak

This is a flatpak for Grayjay Desktop. Please help test and report any issues you find.

## Building Locally

1. install `flatpak-builder` (required) and `just` (optional)
2. run `just build` or `flatpak-builder --user --install build-dir app.grayjay.Grayjay.yaml` to build the flatpak
   1. there is also the `clean-build` shortcut which adds the `--force-clean` arg
3. run `just run` or `flatpak run app.grayjay.Grayjay` or open it from your system menu to run the flatpak.


## Updating for future Grayjay versions

When new grayjay tags come out, here are, at a minimum, the things that should happen to create a new flatpak release:

Prerequisite: Have a local clone of the Grayjay.Desktop source code. It is recommended to set `GIT_LFS_SKIP_SMUDGE=1` in your environment variables or otherwise disable git LFS when doing git operations if you dont want to download 6 GB of prebuilt libcef stuff. Cloning the submodules (or running `git submodule update --init` after cloning) will likely be helpful.


1. Verify the metadata has been updated in the main grayjay repo (mostly screenshots, but also release version numbers/dates/changelogs, and any store descriptions that need updating)
2. Ensure that the `commit` value of the first source under the `grayjay` module in `./app.grayjay.Grayjay.yaml` has been updated to the commit hash corresponding to the git tag (or hotfix commit) you want to release.
3. Run `python3 ./scripts/flatpak-submodules-generator.py <path to your checked out grayjay source repo> <tag name to build, i.e. 7>` to update `submodule-sources.json`
4. Start a build, and then stop it about 15-20 seconds after the grayjay module starts building. Then run `flatpak-builder --run build-dir ./app.grayjay.Grayjay.yaml ./scripts/npm-deps.sh npm-sources.json /run/build/grayjay/Grayjay.Desktop.Web/package-lock.json` to update the `npm-sources.json`
5. Run `python3 ./flatpak-builder-tools/dotnet/flatpak-dotnet-generator.py nuget-sources.json <path to your checked out grayjay source repo>/Grayjay.Desktop.sln --freedesktop 24.08 --dotnet 9` to update `nuget-sources.json`

You should now be able to run `just build` to completion to make sure everything works or make any adjustments based on what changed in the specific version of Grayjay.


## Documentation

Here is some documentation on building flatpaks that has been helpful

- https://docs.flathub.org/docs/for-app-authors/requirements/
- https://docs.flathub.org/docs/for-app-authors/submission/#before-submission
- https://docs.flathub.org/docs/for-app-authors/requirements/#dependency-manifest
- https://docs.flathub.org/docs/for-app-authors/metainfo-guidelines/
- https://flatpak-docs.readthedocs.io/en/latest/first-build.html
- https://docs.flatpak.org/en/latest/sandbox-permissions.html


## Licensing

Grayjay is [licensed](https://github.com/futo-org/Grayjay.Desktop/blob/master/LICENSE.md) under the FUTO Source First License 1.1, a source-available noncommercial license.

Original scripts in this repo are licensed MIT to the extent that they can be (some, such as `scripts/flatpak-submodules-generator.py` were initially created with generative AI).

These scripts should be marked with SPDX license identifiers. Where not marked, files should be treated as being under the MIT license.
