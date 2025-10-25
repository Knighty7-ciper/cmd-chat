import os
import base64
import secrets
from typing import Optional
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from cmd_chat.client.core.abs.abs_crypto import CryptoService


class CryptoServiceExtended(CryptoService):
    """Crypto service with modern security practices"""
    
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.symmetric_key = None
        self.fernet = None
        self._generate_keys()

    def _encrypt(self, message: str) -> str:
        """Encryption with error handling"""
        try:
            return self.fernet.encrypt(message.encode()).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    def _decrypt(self, message: str) -> str:
        """Decryption with error handling"""
        try:
            return self.fernet.decrypt(message.encode()).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def _request_key(self, url: str, username: str, password: str | None = None):
        """Request encrypted symmetric key from server"""
        try:
            # Convert keys to PEM format
            pubkey_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            response = requests.post(
                url,
                files={"pubkey": ("public.pem", pubkey_bytes)},
                data={"username": username, "password": password or ""},
                timeout=10,
                stream=True,
            )
            response.raise_for_status()
            
            # Read encrypted response
            encrypted_data = response.content
            if len(encrypted_data) == 0:
                raise ValueError("Empty response from server")
            
            # Decrypt the symmetric key using modern RSA
            self.symmetric_key = self._decrypt_with_private_key(encrypted_data)
            
            if not self.symmetric_key:
                raise ValueError("Failed to decrypt symmetric key")
                
            self.fernet = Fernet(self.symmetric_key)
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
        except Exception as e:
            raise ValueError(f"Key exchange failed: {e}")

    def _generate_keys(self):
        """Generate RSA 2048-bit keypair (upgraded from 512)"""
        try:
            # Generate RSA 2048-bit keypair with modern parameters
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            self.public_key = self.private_key.public_key()
        except Exception as e:
            raise RuntimeError(f"Key generation failed: {e}")

    def _get_generated_keys(self):
        """Get generated keys in PEM format"""
        try:
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return private_pem, public_pem
        except Exception as e:
            raise RuntimeError(f"Failed to export keys: {e}")

    def _decrypt_with_private_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using RSA private key with modern padding"""
        try:
            # Use modern OAEP padding instead of PKCS1 v1.5
            decrypted = self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted
        except Exception as e:
            # Fallback to old RSA library if needed
            try:
                # Convert our key to old format for compatibility
                old_private_key = self._convert_to_old_rsa_format()
                return rsa.decrypt(encrypted_data, old_private_key)
            except Exception:
                raise ValueError(f"Decryption failed: {e}")

    def _convert_to_old_rsa_format(self):
        """Convert keys to old rsa library format for compatibility"""
        from rsa import PrivateKey, PublicKey
        
        # Extract key components
        numbers = self.private_key.private_numbers()
        
        # Create old format private key
        old_private_key = PrivateKey(
            n=numbers.public_numbers.n,
            e=numbers.public_numbers.e,
            d=numbers.d,
            p=numbers.p,
            q=numbers.q,
            dmp1=numbers.dmp1,
            dmq1=numbers.dmq1,
            iqmp=numbers.iqmp
        )
        
        return old_private_key

    def _remove_keys(self):
        """Securely remove keys from memory"""
        self.public_key = None
        self.private_key = None
        self.symmetric_key = None
        self.fernet = None

    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt

    def hash_password(self, password: str) -> str:
        """Securely hash password"""
        salt = os.urandom(32)
        key, _ = self.derive_key_from_password(password, salt)
        return f"{base64.b64encode(salt).decode()}:{base64.b64encode(key).decode()}"


# Keep the old class name for backward compatibility
class RSAService(CryptoServiceExtended):
    """Backward compatible alias"""
    pass