import requests
import os
import subprocess
from collections import defaultdict
from datetime import datetime

class CodeStatsAnalyzer:
    def __init__(self):
        self.username = "artengin"
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}
        self.temp_clone_dir = "temp_repos"

    def get_all_repos(self):
        """Получает список нефоркнутых репозиториев"""
        repos = []
        page = 1
        
        while True:
            url = f"https://api.github.com/users/{self.username}/repos?page={page}&per_page=100"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            repos.extend(repo['clone_url'] for repo in data if not repo['fork'])
            page += 1
            
        return repos

    def count_lines(self, repo_url):
        """Клонирует репозиторий и считает строки по языкам"""
        try:
            # Клонируем репозиторий
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            clone_path = os.path.join(self.temp_clone_dir, repo_name)
            
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, clone_path],
                check=True,
                capture_output=True
            )
            
            # Используем tokei для анализа строк кода
            result = subprocess.run(
                ['tokei', '-f', '-o', 'json', clone_path],
                capture_output=True,
                text=True
            )
            
            # Удаляем временный репозиторий
            subprocess.run(['rm', '-rf', clone_path])
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Ошибка при анализе {repo_url}: {e.stderr}")
            return None

    def process_tokei_output(self, json_data):
        """Парсит вывод tokei и возвращает статистику по языкам"""
        try:
            import json
            data = json.loads(json_data)
            stats = defaultdict(int)
            
            for lang, details in data['report'].items():
                if lang != 'Total':
                    stats[lang] = details['code']
                    
            return dict(stats)
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга tokei: {e}")
            return {}

    def generate_stats_table(self, language_stats):
        """Генерирует Markdown таблицу"""
        total_lines = sum(language_stats.values())
        table = "## 📊 Код-статистика (строки)\n\n"
        table += "| Язык | Строк кода | Процент |\n"
        table += "|------|-----------:|--------:|\n"
        
        for lang, lines in sorted(language_stats.items(), key=lambda x: -x[1]):
            percent = (lines / total_lines) * 100
            table += f"| {lang} | {lines:,} | {percent:.1f}% |\n"
        
        table += f"\n**Всего строк кода:** {total_lines:,}\n"
        table += f"\n*Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        return table

    def update_readme(self, stats_table):
        """Обновляет README.md"""
        try:
            with open("README.md", "r+", encoding='utf-8') as f:
                content = f.read()
                updated = re.sub(
                    r'## 📊 Код-статистика.*?(?=^##|\Z)',
                    stats_table,
                    content,
                    flags=re.DOTALL|re.MULTILINE
                )
                
                f.seek(0)
                f.write(updated)
                f.truncate()
                
        except Exception as e:
            print(f"❌ Ошибка при записи README.md: {e}")
            raise

    def run(self):
        """Основной процесс"""
        print("🔍 Начинаю анализ строк кода...")
        
        # Создаем временную директорию
        os.makedirs(self.temp_clone_dir, exist_ok=True)
        
        try:
            repos = self.get_all_repos()
            if not repos:
                print("ℹ️ Репозитории не найдены")
                return False
                
            print(f"📂 Найдено репозиториев: {len(repos)}")
            language_stats = defaultdict(int)
            
            for repo_url in repos:
                print(f"🔎 Анализирую {repo_url}...")
                tokei_output = self.count_lines(repo_url)
                if tokei_output:
                    stats = self.process_tokei_output(tokei_output)
                    for lang, lines in stats.items():
                        language_stats[lang] += lines
            
            stats_table = self.generate_stats_table(language_stats)
            self.update_readme(stats_table)
            print("✅ README.md успешно обновлён!")
            return True
            
        finally:
            # Очищаем временные файлы
            subprocess.run(['rm', '-rf', self.temp_clone_dir])

if __name__ == "__main__":
    analyzer = CodeStatsAnalyzer()
    success = analyzer.run()
    exit(0 if success else 1)