import requests
import os
import re
import sys

USERNAME = "artengin"
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    sys.exit(1)

URL = f"https://api.github.com/search/issues?q=is:pr+is:merged+author:{USERNAME}"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

try:
    resp = requests.get(URL, headers=headers)
    resp.raise_for_status()
    data = resp.json()
except requests.exceptions.RequestException as e:
    sys.exit(1)

count = data.get("total_count", 0)

try:
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()
except FileNotFoundError:
    sys.exit(1)

pattern = re.compile(r'!\[PRs\]\(https://img\.shields\.io/badge/Merged_PRs-\d+-blue\)')

if not pattern.search(readme):
    sys.exit(1)

new_badge = f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)"
updated_readme = pattern.sub(new_badge, readme)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated_readme)

