import requests
import os

# Замените на ваш username
USERNAME = os.getenv('GITHUB_USERNAME') or "artengin"
URL = f"https://api.github.com/search/issues?q=is:pr+is:merged+author:{USERNAME}"

response = requests.get(URL).json()
count = response["total_count"]

with open("README.md", "r") as f:
    readme = f.read()

# Обновляем значение в README (например, ищем строку `![PRs]`)
updated_readme = readme.replace(
    "![PRs](https://img.shields.io/badge/Merged_PRs-0-blue)",
    f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)"
)

with open("README.md", "w") as f:
    f.write(updated_readme)