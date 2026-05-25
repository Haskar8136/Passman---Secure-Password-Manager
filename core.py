# core.py - Backend logic with basic corruption protection

import os
import json
import time
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class PassmanCore:
    def __init__(self):
        self.app_dir = os.path.expanduser("~/.passman")
        self.data_file = os.path.join(self.app_dir, "passwords.json")
        self.key_file = os.path.join(self.app_dir, "key.key")
        self.current_password = None
        self.data = {}
        
        # Rate limiting
        self.failed_attempts = 0
        self.lockout_time = None
        self.max_attempts = 5
        self.lockout_duration = 300
    
    def _derive_key(self, master_password: str, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key, salt
    
    def _encrypt(self, data: dict, password: str):
        key, salt = self._derive_key(password)
        f = Fernet(key)
        encrypted = f.encrypt(json.dumps(data).encode())
        return salt + encrypted
    
    def _decrypt(self, encrypted_data: bytes, password: str):
        # === PROTECCIÓN BÁSICA CONTRA CORRUPCIÓN ===
        
        # 1. Verificar que el archivo no está vacío
        if not encrypted_data:
            raise ValueError("Database file is empty")
        
        # 2. Verificar tamaño mínimo (salt = 16 bytes)
        if len(encrypted_data) < 16:
            raise ValueError("Database file is corrupted (file too small)")
        
        # 3. Verificar que el salt no está corrupto (opcional pero útil)
        try:
            salt = encrypted_data[:16]
            if not isinstance(salt, bytes) or len(salt) != 16:
                raise ValueError("Invalid salt format")
        except:
            raise ValueError("Database file is corrupted (invalid salt)")
        
        # === FIN DE PROTECCIÓN ===
        
        salt = encrypted_data[:16]
        encrypted = encrypted_data[16:]
        
        key, _ = self._derive_key(password, salt)
        f = Fernet(key)
        
        try:
            decrypted = f.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            # Distinguir entre contraseña incorrecta y datos corruptos
            raise ValueError(f"Failed to decrypt: {str(e)}")
    
    def exists(self):
        return os.path.exists(self.key_file)
    
    def init_db(self, master_password: str):
        os.makedirs(self.app_dir, exist_ok=True)
        encrypted = self._encrypt({}, master_password)
        with open(self.data_file, "wb") as f:
            f.write(encrypted)
        with open(self.key_file, "wb") as f:
            f.write(b"initialized")
        return True
    
    def authenticate(self, password: str):
        # Check lockout
        if self.lockout_time:
            elapsed = time.time() - self.lockout_time
            if elapsed < self.lockout_duration:
                return False, self.lockout_duration - elapsed
        
        try:
            with open(self.data_file, "rb") as f:
                encrypted = f.read()
            self.data = self._decrypt(encrypted, password)
            self.current_password = password
            self.failed_attempts = 0
            return True, 0
        except ValueError as e:
            # Error de corrupción o formato inválido
            return False, -2  # -2 significa "database corrupted"
        except:
            self.failed_attempts += 1
            if self.failed_attempts >= self.max_attempts:
                self.lockout_time = time.time()
                return False, -1  # Locked out
            return False, self.max_attempts - self.failed_attempts
    
    def is_locked(self):
        """Returns (is_locked, remaining_seconds)"""
        if self.lockout_time:
            elapsed = time.time() - self.lockout_time
            if elapsed < self.lockout_duration:
                return True, self.lockout_duration - elapsed
            else:
                self.failed_attempts = 0
                self.lockout_time = None
        return False, 0
    
    def get_remaining_attempts(self):
        return self.max_attempts - self.failed_attempts
    
    def save(self):
        try:
            encrypted = self._encrypt(self.data, self.current_password)
            # Guardar con respaldo temporal (protección contra escritura corrupta)
            temp_file = self.data_file + ".tmp"
            with open(temp_file, "wb") as f:
                f.write(encrypted)
            os.replace(temp_file, self.data_file)  # Atomic operation
            return True
        except:
            return False
    
    def get_all(self):
        return self.data
    
    def add(self, service: str, username: str, password: str):
        self.data[service] = {"username": username, "password": password}
        return self.save()
    
    def update(self, service: str, username: str, password: str):
        self.data[service] = {"username": username, "password": password}
        return self.save()
    
    def delete(self, service: str):
        if service in self.data:
            del self.data[service]
            return self.save()
        return False
    
    def get(self, service: str):
        return self.data.get(service)
    
    def generate_password(self, length=16):
        import secrets
        import string
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))
