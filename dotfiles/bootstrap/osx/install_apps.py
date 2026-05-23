#!/usr/bin/env python
"""'Installs' apps"""

import json
import subprocess
from os import path

JSON_FILE = path.abspath(path.join(path.dirname(__file__), "apps.json"))


def main() -> None:
    """Basically, open the URLs in apps.json"""
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        apps = json.load(f)

    for app in apps:
        answer = input(f'Open {app["name"]}? (type "ok") ')
        if answer == "ok":
            subprocess.call(["open", app["url"]])


if __name__ == "__main__":
    main()
