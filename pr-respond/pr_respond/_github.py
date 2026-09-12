import os
import subprocess

from github import Auth, Github


def get_client() -> Github:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True
        )
        if result.returncode == 0:
            token = result.stdout.strip()
    if not token:
        raise RuntimeError(
            "No GitHub token found. Set GITHUB_TOKEN or run 'gh auth login'."
        )
    return Github(auth=Auth.Token(token))
