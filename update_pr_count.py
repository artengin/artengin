import requests
import os

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

target_string = "![PRs](https://img.shields.io/badge/Merged_PRs-\d+-blue)"
if target_string not in readme:
    print(f"Ошибка: Строка '{target_string}' не найдена в README.md!")
    exit(1)

updated_readme = readme.replace(
    target_string,
    f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)"
)

with open("README.md", "w") as f:
    f.write(updated_readme)

print("README.md успешно обновлён!")