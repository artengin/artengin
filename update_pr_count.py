import requests
import os
import re

USERNAME = "artengin"
URL = f"https://api.github.com/search/issues?q=is:pr+is:merged+author:{USERNAME}"

response = requests.get(URL).json()
count = response.get("total_count", 0)
print(f"Найдено PR: {count}")

try:
    with open("README.md", "r") as f:
        readme = f.read()
except FileNotFoundError:
    print("Ошибка: Файл README.md не найден!")
    exit(1)

target_pattern = re.compile(r'!\[PRs\]\(https://img\.shields\.io/badge/Merged_PRs-\d+-blue\)')

if not target_pattern.search(readme):
    print("Ошибка: Бейдж с PR не найден в README.md!")
    print("Убедитесь, что в файле есть строка вида:")
    print("![PRs](https://img.shields.io/badge/Merged_PRs-0-blue)")
    exit(1)

updated_readme = target_pattern.sub(
    f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)",
    readme
)

with open("README.md", "w") as f:
    f.write(updated_readme)

print("README.md успешно обновлён!")