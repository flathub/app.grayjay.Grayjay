build:
	flatpak run org.flatpak.Builder --user --install --force-clean build-dir app.grayjay.Grayjay.yaml

build-offline:
	flatpak run org.flatpak.Builder --user --install --disable-download --force-clean build-dir app.grayjay.Grayjay.yaml


build-sandbox:
	flatpak run org.flatpak.Builder --force-clean --sandbox --user --install --install-deps-from=flathub --ccache --mirror-screenshots-url=https://dl.flathub.org/media/ --repo=repo ./build-dir app.grayjay.Grayjay.yaml


run:
	flatpak run app.grayjay.Grayjay

debugshell:
	flatpak-builder --run ./build-dir ./app.grayjay.Grayjay.yaml sh

bundle:
	flatpak build-bundle ~/.local/share/flatpak/repo GrayjayDesktop.flatpak app.grayjay.Grayjay

prep-npm:
	./scripts/npm-deps.sh https://raw.githubusercontent.com/futo-org/Grayjay.Desktop/refs/heads/master/Grayjay.Desktop.Web

# this expects to be run in a full clone of the grayjay desktop repo tree checked out on the host machine at ../Grayjay.Desktop
# also, do not set the runtimes here. It creates missing dependencies that need to be looked into (something weird with macos and windows dependencies probably being mislabeled for linux or something)
prep-nuget:
	# git -C ../Grayjay.Desktop checkout  $(yq -r .modules[1].sources[0].commit app.grayjay.Grayjay.yaml)  && git -C ../Grayjay.Desktop submodule  update
	python3 ./flatpak-builder-tools/dotnet/flatpak-dotnet-generator.py nuget-sources.json ../Grayjay.Desktop/Grayjay.Desktop.sln --freedesktop 24.08 --dotnet 9

lint:
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest ./app.grayjay.Grayjay.yaml
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo
