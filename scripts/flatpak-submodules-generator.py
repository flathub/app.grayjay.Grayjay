# While flatpak module sources supports git submodules, it does not support git-lfs. This generator sets up each submodule as an archive source, because gitlab zips seem to include files stored in LFS.

# SPDX-License-Identifier: MIT

import os
import json
import subprocess
import requests
from pathlib import Path
import argparse
from urllib.parse import urlparse
import hashlib
import time

def parse_submodule_target_hashes(root, ref):
   # https://stackoverflow.com/questions/20655073/how-to-see-which-commit-a-git-submodule-points-at?rq=3
    result = subprocess.run(["git", "-C", root, "ls-tree", "-r", ref], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tree = result.stdout.decode("utf-8").strip()
    tree = tree.split("\n")

    target_hashes = {}
    for item in tree:
        info, path = item.split("\t")
        mode, obj_type, obj_hash = info.split(" ")
        if obj_type == "commit":
            target_hashes[path] = obj_hash
    
    return target_hashes

def get_git_submodules(repo_path, repo_ref, upstream_url=None):
	"""Retrieve submodule details from a Git repository."""
	os.chdir(repo_path)
	submodules = []

	target_hash_map = parse_submodule_target_hashes(repo_path, repo_ref)
	
	for path, commit in target_hash_map.items():
		url = subprocess.run(["git", "config", f"--file=.gitmodules", f"submodule.{path}.url"],
							capture_output=True, text=True, check=True).stdout.strip()
		if url.startswith("..") and upstream_url is not None:
			urlparsed = urlparse(upstream_url)
			# this is unconventional, but it works
			modified_url_path = Path(urlparsed.path).joinpath(url).resolve()

			url = urlparsed._replace(path=str(modified_url_path)).geturl()

		submodules.append({
			"name": path.replace("/", "-"),
			"url": url,
			"commit": commit.lstrip("+-")  # Remove leading `+` or `-`
		})
	return submodules


def generate_flatpak_sources(submodules, output_file):
	"""Generate a Flatpak sources JSON file from the submodule list."""
	sources = []
	
	for submodule in submodules:
		sources.append({
			"type": "archive",
			"url": transform_url_for_zip_download(submodule["url"], submodule["commit"], submodule["name"]),
			"sha256": submodule["filesha"],
			# "commit": submodule["commit"],
			"dest": submodule["name"]
		})
	
	with open(output_file, "w") as f:
		json.dump(sources, f, indent=4)
	print(f"Flatpak sources JSON saved to {output_file}")

def get_sha_for_submodule(submodule, progress=False):
	zip_url = transform_url_for_zip_download(submodule["url"], submodule["commit"], submodule["name"])
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
						overall_progress = f"Unknown % {(dl_total/MEGABYTE):5.2d} MiB downloaded"
					# avg_speed = 
					chunk_bytes_per_sec = dl_chunk/chunk_elapsed
					chunk_speed = int(chunk_bytes_per_sec/MEGABYTE)
					print(f"\r {chunk_speed:03d} MiB/s ({overall_progress} complete)", end="")
					dl_total += dl_chunk
					dl_chunk = 0
					chunk_start_time = time.perf_counter()
		
	return sha256.hexdigest()

def transform_url_for_zip_download(url, commit, name):
	if url.endswith("/"):
		url = url[:-1]
	if url.endswith(".git"):
		url = url[:-4]
	return f"{url}/-/archive/{commit}/{name}.zip"

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

	submodules = get_git_submodules(repo_path, args.repoversion, args.upstream_url)

	for submodule in submodules:
		sha = get_sha_for_submodule(submodule, progress=not args.quiet)
		submodule["filesha"] = sha

	generate_flatpak_sources(submodules, Path(args.output))

if __name__ == "__main__":
	main()
