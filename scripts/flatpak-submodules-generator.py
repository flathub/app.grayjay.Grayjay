# While flatpak module sources supports git submodules, it does not support git-lfs. This generator sets up each submodule as an archive source, because gitlab zips seem to include files stored in LFS.

# SPDX-License-Identifier: MIT

# Requirements for use:
# - a clone of the Grayjay.Desktop repository (no submodule checkout needed)

# Usage: run `python3 ./scripts/flatpak-submodules-generator.py ./path/to/Grayjay.Desktop 6` (where 6 is the git ref to use, in this case the version 6 tag, defaults to HEAD)

# Behavior: This script will calculate the intended target version of each submodule, download that submodule from GitLab as a zip, calculate its hash, and generate the submodule-sources.json file for the flatpak build


import os
import json
import subprocess
import requests
from pathlib import Path
import argparse
from urllib.parse import urlparse
import hashlib
import time
from dataclasses import dataclass

@dataclass
class Submodule:
	name: str
	url: str
	commit: str

	def to_json(self):
		return {
			"name": self.name,
			"url": self.url,
			"commit": self.commit
		}

	@classmethod
	def from_url(cls, zip_url:str):
		# Remove the .zip suffix and split by '/'
		parts = []

		if not zip_url.endswith(".zip"):
			parts = zip_url.split("/")
		else:
			parts = zip_url[:-4].split("/")

		# We're expecting: ... /-/archive/<commit>/<name>
		if len(parts) < 4 or parts[-4] != "-":
			raise ValueError("Unexpected archive URL format")

		name = parts[-1]
		commit = parts[-2]
		base_url = "/".join(parts[:-4])

		original_git_url = f"{base_url}.git"
		return cls(name, original_git_url, commit)

	@property
	def zip_url(self):
		url = self.url
		if url.endswith("/"):
			url = url[:-1]
		if url.endswith(".git"):
			url = url[:-4]
		return f"{url}/-/archive/{self.commit}/{self.name}.zip"

@dataclass
class Source:
	url: str
	sha256: str
	dest: str

	@classmethod
	def from_submodule(cls, submodule:Submodule, quiet=False):
		sha = get_sha_for_submodule(submodule, progress=not quiet)
	
		return cls(
			submodule.zip_url,
			sha,
			submodule.name,
		)

	def to_submodule(self):
		return Submodule.from_url(self.url)

	@classmethod
	def from_json(cls, data:dict):
		return cls(
			data.get("url"),
			data.get("sha256"),
			data.get("dest")
		)

	def to_json(self):
		return {
			"type": "archive",
			"url": self.url,
			"sha256": self.sha256,
			"dest": self.dest

		}


def parse_submodule_target_hashes(root, ref):
   # https://stackoverflow.com/questions/20655073/how-to-see-which-commit-a-git-submodule-points-at?rq=3
    result = subprocess.run(["git", "-C", root, "ls-tree", "-r", ref], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tree = result.stdout.decode("utf-8").strip()
    tree = tree.split("\n")

    target_hashes = {}
    for item in tree:
        if not '\t' in item:
            continue
        info, path = item.split("\t")
        mode, obj_type, obj_hash = info.split(" ")
        if obj_type == "commit":
            target_hashes[path] = obj_hash
    
    return target_hashes

def get_git_submodules(repo_path, repo_ref, upstream_url=None):
	"""Retrieve submodule details from a Git repository."""
	submodules = []

	target_hash_map = parse_submodule_target_hashes(repo_path, repo_ref)
	
	for path, commit in target_hash_map.items():
		url = subprocess.run(["git", "config", f"--file=.gitmodules", f"submodule.{path}.url"],
							capture_output=True, text=True, check=True, cwd=repo_path).stdout.strip()
		if url.startswith("..") and upstream_url is not None:
			urlparsed = urlparse(upstream_url)
			# this is unconventional, but it works
			modified_url_path = Path(urlparsed.path).joinpath(url).resolve()

			url = urlparsed._replace(path=str(modified_url_path)).geturl()

		submodules.append(Submodule(
			path.replace("/", "-"),
			url,
			commit
		))
	return submodules


def generate_flatpak_sources(sources, output_file):
	"""Generate a Flatpak sources JSON file from the submodule list."""
	
	with open(output_file, "w") as f:
		json.dump([s.to_json() for s in sources], f, indent=4)
	print(f"Flatpak sources JSON saved to {output_file}")

def get_sha_for_submodule(submodule, progress=False):
	zip_url = submodule.zip_url
	print(f"Downloading and hashing {zip_url}...")
	response = requests.get(zip_url, stream=True)
	if progress:
		chunk_start_time = time.perf_counter()
		total_length = int(response.headers.get('content-length') or "0")
		dl_total = 0
		dl_chunk = 0
		MEASUREMENT_INTERVAL_BYTES = 5 * 1024 * 1024 # 2 Mi bytes
		MEGABYTE = 1024* 1024
	sha256 = hashlib.sha256()
	if response.status_code == 200:
		# with open(zip_path, "wb") as f:
		for chunk in response.iter_content(chunk_size=1024):
			sha256.update(chunk)
			if progress:
				dl_chunk += len(chunk)
				if dl_chunk > MEASUREMENT_INTERVAL_BYTES:
					chunk_elapsed = (time.perf_counter() - chunk_start_time)
					
					if total_length > 0:
						overall_fmt = "{:03.2%}"
						overall_progress = overall_fmt.format(dl_total/total_length)
					else:
						overall_progress = f"Unknown % {(dl_total/MEGABYTE):5.2f} MiB downloaded"
					# avg_speed = 
					chunk_bytes_per_sec = dl_chunk/chunk_elapsed
					chunk_speed = int(chunk_bytes_per_sec/MEGABYTE)
					print(f"\r {chunk_speed:03d} MiB/s ({overall_progress} complete)", end="")
					dl_total += dl_chunk
					dl_chunk = 0
					chunk_start_time = time.perf_counter()
		
	return sha256.hexdigest()    


def get_all_sources(repo_path, repo_version, upstream_url, existing_source_map) -> list[Source]:

	submodules = get_git_submodules(repo_path, repo_version, upstream_url)
	sources = []
	for submodule in submodules:
		existing_source = existing_source_map.get((submodule.commit, submodule.name))
		if existing_source is not None:
			print(f"Hash for {submodule.name} unchanged.")
			sources.append(existing_source)
			continue
		source = Source.from_submodule(submodule)
		sources.append(source)
	return sources



def main():

	parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

	parser.add_argument('repopath', help="the path to the repository to extract", default=".")

	parser.add_argument('repoversion', help="the git ref to use when extracting", default="HEAD")

	parser.add_argument('--upstream-url', help="the url to the upstream repository", default="https://gitlab.futo.org/videostreaming/thispartoftheurldoesntmatterbutneedstobehere")
	parser.add_argument("--quiet", "-q", action="store_true", default=False, help="make output quieter"  )
	parser.add_argument('--output', default=Path("submodule-sources.json"), help="the path to the file to write the final json to")
	args = parser.parse_args()

	repo_path = Path(args.repopath).resolve()

	if not (repo_path / ".gitmodules").exists():
		print("No .gitmodules file found.")
		generate_flatpak_sources([], Path(args.output))
		return

	# map of the git commit SHA of each submodule to its Source object
	# for easy lookups of things that havent changed
	existing_source_map = {}
		
	if Path(args.output).resolve().exists():
		# read existing ones and skip any
		for j in json.loads(Path(args.output).read_text(encoding='utf8')):
			src = Source.from_json(j)
			sub = src.to_submodule()
			existing_source_map[(sub.commit, sub.name)] = src

	sources = get_all_sources(repo_path, args.repoversion, args.upstream_url, existing_source_map)


	generate_flatpak_sources(sources, Path(args.output))

if __name__ == "__main__":
	main()
