import requests
import os

USERNAME = "artengin"
URL = f"https://api.github.com/search/issues?q=is:pr+is:merged+author:{USERNAME}"

response = requests.get(URL).json()
count = response.get("total_count", 0)

print(f"🔍 Найдено PR: {count}")

with open("README.md", "r") as f:
    readme = f.read()

updated_readme = readme.replace(
    "![PRs](https://img.shields.io/badge/Merged_PRs-0-blue)",
    f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)"
)

with open("README.md", "w") as f:
    f.write(updated_readme)