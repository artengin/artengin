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
    """Получает список всех репозиториев (включая приватные)"""
    repos = []
    page = 1
    
    while True:
        # Используем /user/repos вместо /users/{username}/repos
        url = f"https://api.github.com/user/repos?page={page}&per_page=100&affiliation=owner"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            for repo in data:
                # Берем все репозитории, где пользователь является владельцем
                if repo['owner']['login'] == self.username:
                    repos.append({
                        'clone_url': repo['clone_url'],
                        'private': repo['private']
                    })
            
            # Проверяем, есть ли еще страницы
            if 'next' not in response.links:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Ошибка получения репозиториев: {e}")
            break
                
    return repos

def analyze_repo(self, repo_info):
    """Анализирует репозиторий (публичный или приватный)"""
    repo_url = repo_info['clone_url']
    is_private = repo_info['private']
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    clone_path = os.path.join(self.clone_dir, repo_name)
    stats = defaultdict(int)
    
    try:
        # Формируем URL для клонирования с токеном (для приватных репозиториев)
        auth_url = repo_url
        if is_private and self.token:
            auth_url = repo_url.replace(
                'https://github.com/',
                f'https://{self.username}:{self.token}@github.com/'
            )
        
        # Клонируем репозиторий
        subprocess.run(
            ["git", "clone", "--depth", "1", auth_url, clone_path],
            check=True,
            capture_output=True,
            timeout=300
        )
        
        # Остальной код анализа остается без изменений
        result = subprocess.run(
            self.tokei_cmd + [clone_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for lang, metrics in data.items():
                if (isinstance(metrics, dict) and \
                   'code' in metrics and \
                   lang not in self.excluded_languages and \
                   metrics['code'] >= 100):
                    stats[lang] += metrics['code']
    
    except subprocess.TimeoutExpired:
        print(f"⏳ Таймаут при анализе {repo_name}, пропускаем...")
    except Exception as e:
        print(f"⚠️ Ошибка анализа {repo_name}: {str(e)[:200]}...")
    finally:
        if os.path.exists(clone_path):
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