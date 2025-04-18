import requests
import os
import re

USERNAME = "artengin"
TOKEN = os.getenv("GITHUB_TOKEN")
URL = f"https://api.github.com/search/issues?q=is:pr+is:merged+author:{USERNAME}"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

response = requests.get(URL, headers=headers).json()
count = response.get("total_count", 0)

try:
    with open("README.md", "r") as f:
        readme = f.read()
except FileNotFoundError:
    exit(1)

target_pattern = re.compile(r'!\[PRs\]\(https://img\.shields\.io/badge/Merged_PRs-\d+-blue\)')

if not target_pattern.search(readme):
    exit(1)

updated_readme = target_pattern.sub(
    f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)",
    readme
)

with open("README.md", "w") as f:
    f.write(updated_readme)