import requests
import os

USERNAME = "artengin"
URL = f"https://api.github.com/search/issues?q=is:pr+is:merged+user:{USERNAME}"  # Используем user вместо author

# 1. Получаем данные PR
response = requests.get(URL).json()
count = response.get("total_count", 0)
print(f"🔍 Найдено PR: {count}")
print(f"Ответ API: {response}")  # Для отладки

# 2. Читаем README.md
try:
    with open("README.md", "r") as f:
        readme = f.read()
except FileNotFoundError:
    print("❌ Ошибка: Файл README.md не найден!")
    exit(1)

# 3. Проверяем, есть ли целевая строка для замены
target_string = "![PRs](https://img.shields.io/badge/Merged_PRs-0-blue)"
if target_string not in readme:
    print(f"❌ Ошибка: Строка '{target_string}' не найдена в README.md!")
    exit(1)

# 4. Заменяем и записываем
updated_readme = readme.replace(
    target_string,
    f"![PRs](https://img.shields.io/badge/Merged_PRs-{count}-blue)"
)

with open("README.md", "w") as f:
    f.write(updated_readme)

print("✅ README.md успешно обновлён!")