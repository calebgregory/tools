from pathlib import Path
import argparse
import subprocess


def _git_repo_remote_url():
    git_remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    xf_map = {
        "git@": "https://",
        ".com:": ".com/",
        ".git": "",
    }
    for from_, to in xf_map.items():
        git_remote = git_remote.replace(from_, to, 1)
    return git_remote


def _xf(git_repo_remote_url: str, md: str) -> str:
    return md.replace("](/", f"]({git_repo_remote_url}/blob/main/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    with open(args.file, "r") as f:
        md = f.read()

    xfed = _xf(_git_repo_remote_url(), md)

    with open(args.file, "w") as f:
        f.write(xfed)


if __name__ == "__main__":
    main()
