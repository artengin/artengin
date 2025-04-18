import requests
import os
import subprocess
import json
import re
from collections import defaultdict
from datetime import datetime

class CodeLineCounter:
    def __init__(self):
        self.username = "artengin"
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}
        self.clone_dir = "temp_repos"
        self.tokei_cmd = ["tokei", "-f", "-o", "json"]
        # Языки, которые нужно исключить из отчета
        self.excluded_languages = {
            'Total', 'Makefile', 'YAML', 'Dockerfile', 
            'SQL', 'SVG', 'Markdown', 'Plain Text', 'XML', 'JSON'
        }

    def get_repos(self):
        """Получает список репозиториев, где пользователь является автором"""
        repos = []
        page = 1
        
        while True:
            url = f"https://api.github.com/users/{self.username}/repos?page={page}&per_page=100&type=owner"
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                    
                for repo in data:
                    # Проверяем, что пользователь является владельцем (не форк или не организация)
                    if repo['owner']['login'] == self.username and not repo['fork']:
                        repos.append(repo['clone_url'])
                
                # Проверяем, есть ли еще страницы
                if 'next' not in response.links:
                    break
                    
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Ошибка получения репозиториев: {e}")
                break
                
        return repos

    def analyze_repo(self, repo_url):
    """Анализирует репозиторий и возвращает статистику строк"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    clone_path = os.path.join(self.clone_dir, repo_name)
    stats = defaultdict(int)
    
    try:
        # Клонируем репозиторий
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, clone_path],
            check=True,
            capture_output=True
        )
        
        # Запускаем tokei
        result = subprocess.run(
            self.tokei_cmd + [clone_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for lang, metrics in data.items():
                if (isinstance(metrics, dict) and 'code' in metrics and \
                   lang not in self.excluded_languages and \
                   metrics['code'] >= 100):  # Фильтр по количеству строк
                    stats[lang] += metrics['code']
    
    except Exception as e:
        print(f"⚠️ Ошибка анализа {repo_name}: {e}")
    finally:
        # Очищаем
        subprocess.run(["rm", "-rf", clone_path], capture_output=True)
        
    return stats

    def generate_stats(self, language_stats):
        """Генерирует Markdown с результатами"""
        total = sum(language_stats.values())
        if total == 0:
            return "## 📊 Статистика строк кода\n\nНет данных, соответствующих критериям\n"
            
        md = "## 📊 Статистика строк кода (только мои репозитории)\n\n"
        md += "| Язык | Строк кода | Доля |\n"
        md += "|------|-----------:|-----:|\n"
        
        for lang, lines in sorted(language_stats.items(), key=lambda x: -x[1]):
            percent = (lines / total) * 100
            md += f"| {lang} | {lines:,} | {percent:.1f}% |\n"
            
        md += f"\n**Всего строк кода:** {total:,}\n"
        md += f"\n*Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}*"
        md += "\n\n*Примечание: анализируются только репозитории, где я являюсь автором"
        md += ", исключены форки и служебные файлы*"
        return md

    def update_readme(self, stats_md):
        """Обновляет README.md"""
        try:
            with open("README.md", "r+", encoding='utf-8') as f:
                content = f.read()
                
                # Ищем и заменяем существующую секцию
                pattern = re.compile(
                    r'## 📊 Статистика строк кода.*?(?=^##|\Z)',
                    re.DOTALL|re.MULTILINE
                )
                
                updated = pattern.sub(stats_md, content)
                
                # Если секция не найдена, добавляем в конец
                if updated == content:
                    updated = content.rstrip() + "\n\n" + stats_md
                
                # Перезаписываем файл
                f.seek(0)
                f.write(updated)
                f.truncate()
                
        except Exception as e:
            print(f"❌ Ошибка обновления README: {e}")
            raise

    def run(self):
        """Основной процесс"""
        print("🔄 Сбор статистики строк кода...")
        os.makedirs(self.clone_dir, exist_ok=True)
        
        try:
            repos = self.get_repos()
            if not repos:
                print("ℹ️ Нет репозиториев для анализа")
                return False
                
            print(f"📂 Найдено репозиториев: {len(repos)}")
            total_stats = defaultdict(int)
            
            for repo in repos:
                repo_name = repo.split('/')[-1]
                print(f"🔍 Анализ {repo_name}...", end=' ', flush=True)
                repo_stats = self.analyze_repo(repo)
                
                if repo_stats:
                    print(f"найдено {sum(repo_stats.values()):,} строк")
                    for lang, lines in repo_stats.items():
                        total_stats[lang] += lines
                else:
                    print("пропуск (нет данных)")
            
            stats_md = self.generate_stats(total_stats)
            self.update_readme(stats_md)
            print("✅ README.md успешно обновлён!")
            return True
            
        finally:
            if os.path.exists(self.clone_dir):
                subprocess.run(["rm", "-rf", self.clone_dir], capture_output=True)

if __name__ == "__main__":
    counter = CodeLineCounter()
    success = counter.run()
    exit(0 if success else 1)