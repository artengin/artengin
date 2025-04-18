import requests
import os
import re
from collections import defaultdict
from datetime import datetime

class GitHubStatsAnalyzer:
    def __init__(self):
        self.username = "artengin"
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}
        self.request_timeout = 10  # Таймаут запросов в секундах

    def get_all_repos(self):
        """Получает список всех репозиториев пользователя с пагинацией"""
        repos = []
        page = 1
        
        while True:
            try:
                url = f"https://api.github.com/users/{self.username}/repos?page={page}&per_page=100"
                response = requests.get(url, headers=self.headers, timeout=self.request_timeout)
                response.raise_for_status()
                
                data = response.json()
                if not data:
                    break
                    
                repos.extend(repo['name'] for repo in data if not repo['fork'])  # Исключаем форки
                page += 1
                
                # Проверяем лимит API
                self.check_rate_limit(response.headers)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Ошибка при получении репозиториев: {e}")
                break
                
        return repos

    def get_repo_stats(self, repo_name):
        """Получает статистику по языкам для конкретного репозитория"""
        try:
            url = f"https://api.github.com/repos/{self.username}/{repo_name}/languages"
            response = requests.get(url, headers=self.headers, timeout=self.request_timeout)
            response.raise_for_status()
            self.check_rate_limit(response.headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Ошибка при получении статистики для {repo_name}: {e}")
            return {}

    def check_rate_limit(self, headers):
        """Проверяет и выводит информацию об ограничениях API"""
        remaining = int(headers.get('X-RateLimit-Remaining', 0))
        if remaining < 10:
            reset_time = datetime.fromtimestamp(int(headers.get('X-RateLimit-Reset', 0)))
            print(f"⚠️ Внимание: Осталось {remaining} запросов. Лимит сбросится в {reset_time}")

    def generate_stats_table(self, language_stats):
        """Генерирует красивую таблицу со статистикой"""
        total_lines = sum(language_stats.values())
        if total_lines == 0:
            return "## 📊 Код-статистика\n\nНет данных о строках кода\n"

        table = "## 📊 Код-статистика\n\n"
        table += "| Язык | Строк кода | Процент |\n"
        table += "|------|-----------:|--------:|\n"
        
        for lang, lines in sorted(language_stats.items(), key=lambda x: -x[1]):
            percent = (lines / total_lines) * 100
            table += f"| {lang} | {lines:,} | {percent:.1f}% |\n"
        
        table += f"\n**Всего строк кода:** {total_lines:,}\n"
        table += f"\n*Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        return table

    def update_readme(self, stats_table):
        """Обновляет README.md с новой статистикой"""
        try:
            with open("README.md", "r+", encoding='utf-8') as f:
                content = f.read()
                
                # Ищем существующую секцию статистики
                pattern = re.compile(
                    r'## 📊 Код-статистика.*?(?=^##|\Z)',
                    re.DOTALL | re.MULTILINE
                )
                
                updated_content = pattern.sub(stats_table, content)
                
                # Если секция не найдена, добавляем в конец
                if updated_content == content:
                    updated_content = f"{content.rstrip()}\n\n{stats_table}\n"
                
                f.seek(0)
                f.write(updated_content)
                f.truncate()
                
        except Exception as e:
            print(f"❌ Ошибка при обновлении README.md: {e}")
            raise

    def run(self):
        """Основной метод выполнения анализа"""
        print("🔍 Начинаю сбор статистики...")
        try:
            repos = self.get_all_repos()
            if not repos:
                print("ℹ️ Репозитории не найдены")
                return False

            print(f"📂 Найдено репозиториев: {len(repos)}")
            language_stats = defaultdict(int)
            
            for repo in repos:
                print(f"🔎 Анализирую {repo}...", end=' ', flush=True)
                stats = self.get_repo_stats(repo)
                for lang, lines in stats.items():
                    language_stats[lang] += lines
                print("✅")
            
            stats_table = self.generate_stats_table(language_stats)
            self.update_readme(stats_table)
            print("🎉 README.md успешно обновлён!")
            return True
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            return False

if __name__ == "__main__":
    analyzer = GitHubStatsAnalyzer()
    success = analyzer.run()
    exit(0 if success else 1)