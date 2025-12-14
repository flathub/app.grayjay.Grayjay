# Grayjay Desktop Flatpak

This is a flatpak for Grayjay Desktop. Please help test and report any issues you find.

## Building Locally

### Prerequisites
1. at least version 1.4.6 of Flatpak Builder (either from your system package repo or flatpak) 
2. `just` (optional)

### Building
1. run `just build` or `<your flatpak-builder> --user --install build-dir app.grayjay.Grayjay.yaml` to build the flatpak
   1. there is also the `clean-build` shortcut which adds the `--force-clean` arg
2. run `just run` or `flatpak run app.grayjay.Grayjay` or open it from your system menu to run the flatpak.


## Updating for future Grayjay versions

When new grayjay tags come out, here are, at a minimum, the things that should happen to create a new flatpak release:

Prerequisite: Have a local clone of the Grayjay.Desktop source code. It is recommended to set `GIT_LFS_SKIP_SMUDGE=1` in your environment variables or otherwise disable git LFS when doing git operations if you don't want to download 6 GB of prebuilt libcef stuff. Cloning the submodules (or running `git submodule update --init` after cloning) will likely be helpful.


1. Verify the metadata has been updated in the main grayjay repo. This includes:
   - release version numbers/dates/changelogs have been added for the current version, and any store descriptions or screenshots that need updating for this release have been done
   - verifying that the `Grayjay.ClientServer/AppVersion.json` file reflects the correct version as this is used for the builds and will show up in the app interface.
2. Ensure that the `commit` values of the `git` module sources underneath each module in `./app.grayjay.Grayjay.yaml` has been updated to the commit hash corresponding to the git tag (or hotfix commit) you want to release. This includes:
  - the `Grayjay.Desktop` commit for the `grayjay` module
  - the `JustCef` commit for the `dotcefnative` module
3. Ensure that all relevant binary files have been updated. This includes:
  - the CEF sources (which are custom-built by FUTO) within the `dotcefnative` module
4. Run `just npm-deps` or `./scripts/npm-deps.sh https://gitlab.futo.org/videostreaming/Grayjay.Desktop/-/raw/master/Grayjay.Desktop.Web/` to generate an updated `npm-sources.json`.
   - you can also pass in a local on-disk path to the `Grayjay.Desktop.Web` directory (no trailing slash)
5. Regenerate the two nuget sources files:
   1. From an x86 machine, run `python3 ./flatpak-builder-tools/dotnet/flatpak-dotnet-generator.py nuget-sources.json <path to your checked out grayjay source repo>/Grayjay.Desktop.sln --freedesktop 24.08 --dotnet 8 --runtime linux-x86 --only-arches x86_64` to update `nuget-sources.json`
   2. From an arm64 machine, run `python3 ./flatpak-builder-tools/dotnet/flatpak-dotnet-generator.py nuget-sources-arm.json <path to your checked out grayjay source repo>/Grayjay.Desktop.sln --freedesktop 24.08 --dotnet 8 --runtime linux-arm --runtime linux-arm64 --only-arches aarch64` to update `nuget-sources-arm.json`
6. Check the `patches` folder and the [patch sources](https://docs.flatpak.org/en/latest/module-sources.html#patch-sources) of all the modules (mostly `grayjay` and `dotcefnative`) and enable/disable patches as necessary
   - These patches allow for things to be hotfixed (such as version numbers) before things make it to prod. Ideally they are a last resort that are meant for cases where Grayjay has already shipped or the patch cannot be upstreamed in time.

You should now be able to run `just build` to completion to make sure everything works before pushing to the repo/making a PR.

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
