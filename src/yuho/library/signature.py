"""
Ed25519 signature verification for Yuho packages.

Provides cryptographic signing and verification of statute packages
to ensure authenticity and integrity.
"""

from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import base64
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


# Try to import cryptography library
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Ed25519PrivateKey = None
    Ed25519PublicKey = None


@dataclass
class KeyPair:
    """Ed25519 key pair for signing packages."""
    private_key: bytes  # PEM-encoded private key
    public_key: bytes   # PEM-encoded public key
    key_id: str         # Fingerprint/identifier for the key


@dataclass
class Signature:
    """Package signature with metadata."""
    signature: str   # Base64-encoded signature
    key_id: str      # Key identifier used to sign
    algorithm: str   # Always "ed25519"
    content_hash: str  # SHA-256 hash of signed content


class SignatureManager:
    """
    Manages Ed25519 key pairs and package signatures.
    
    Keys are stored in ~/.yuho/keys/ directory.
    """
    
    DEFAULT_KEY_DIR = Path.home() / ".yuho" / "keys"
    
    def __init__(self, key_dir: Optional[Path] = None):
        """
        Initialize signature manager.
        
        Args:
            key_dir: Directory for key storage
        """
        self.key_dir = key_dir or self.DEFAULT_KEY_DIR
        self.key_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def is_available() -> bool:
        """Check if cryptography library is available."""
        return CRYPTO_AVAILABLE
    
    def generate_keypair(self, name: str = "default") -> KeyPair:
        """
        Generate a new Ed25519 key pair.
        
        Args:
            name: Key name for storage
            
        Returns:
            Generated KeyPair
            
        Raises:
            ImportError: If cryptography not installed
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "Cryptography library not installed. "
                "Install with: pip install cryptography"
            )
        
        # Generate private key
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize to PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        
        # Generate key ID (fingerprint of public key)
        key_id = hashlib.sha256(public_pem).hexdigest()[:16]
        
        keypair = KeyPair(
            private_key=private_pem,
            public_key=public_pem,
            key_id=key_id,
        )
        
        # Save to disk
        self._save_keypair(name, keypair)
        
        return keypair
    
    def _save_keypair(self, name: str, keypair: KeyPair) -> None:
        """Save key pair to disk."""
        private_path = self.key_dir / f"{name}.key"
        public_path = self.key_dir / f"{name}.pub"
        
        private_path.write_bytes(keypair.private_key)
        private_path.chmod(0o600)  # Owner read/write only
        
        public_path.write_bytes(keypair.public_key)
    
    def load_keypair(self, name: str = "default") -> Optional[KeyPair]:
        """
        Load key pair from disk.
        
        Args:
            name: Key name
            
        Returns:
            KeyPair or None if not found
        """
        private_path = self.key_dir / f"{name}.key"
        public_path = self.key_dir / f"{name}.pub"
        
        if not private_path.exists() or not public_path.exists():
            return None
        
        private_pem = private_path.read_bytes()
        public_pem = public_path.read_bytes()
        key_id = hashlib.sha256(public_pem).hexdigest()[:16]
        
        return KeyPair(
            private_key=private_pem,
            public_key=public_pem,
            key_id=key_id,
        )
    
    def load_public_key(self, name: str = "default") -> Optional[bytes]:
        """Load just the public key."""
        public_path = self.key_dir / f"{name}.pub"
        if public_path.exists():
            return public_path.read_bytes()
        return None
    
    def list_keys(self) -> list:
        """List available key names."""
        keys = []
        for path in self.key_dir.glob("*.pub"):
            keys.append(path.stem)
        return keys
    
    def sign_content(self, content: bytes, keypair: KeyPair) -> Signature:
        """
        Sign content with Ed25519 private key.
        
        Args:
            content: Content to sign
            keypair: Key pair to use
            
        Returns:
            Signature object
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography library not installed")
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            keypair.private_key,
            password=None,
        )
        
        # Sign
        signature_bytes = private_key.sign(content)
        
        return Signature(
            signature=base64.b64encode(signature_bytes).decode("ascii"),
            key_id=keypair.key_id,
            algorithm="ed25519",
            content_hash=hashlib.sha256(content).hexdigest(),
        )
    
    def verify_signature(
        self,
        content: bytes,
        signature: Signature,
        public_key_pem: bytes,
    ) -> Tuple[bool, str]:
        """
        Verify content signature.
        
        Args:
            content: Content that was signed
            signature: Signature to verify
            public_key_pem: PEM-encoded public key
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not CRYPTO_AVAILABLE:
            return (False, "Cryptography library not installed")
        
        # Verify content hash
        content_hash = hashlib.sha256(content).hexdigest()
        if content_hash != signature.content_hash:
            return (False, "Content hash mismatch - content may have been modified")
        
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(public_key_pem)
            
            # Verify signature
            signature_bytes = base64.b64decode(signature.signature)
            public_key.verify(signature_bytes, content)
            
            return (True, "Signature verified successfully")
            
        except InvalidSignature:
            return (False, "Invalid signature - content may have been tampered with")
        except Exception as e:
            return (False, f"Verification error: {e}")


def sign_package(
    package_path: Path,
    key_name: str = "default",
    key_dir: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Sign a package file.
    
    Args:
        package_path: Path to .yhpkg file
        key_name: Name of key to use
        key_dir: Key directory
        
    Returns:
        Tuple of (success, message)
    """
    manager = SignatureManager(key_dir)
    
    keypair = manager.load_keypair(key_name)
    if not keypair:
        return (False, f"Key '{key_name}' not found. Generate with: yuho key generate")
    
    try:
        content = package_path.read_bytes()
        signature = manager.sign_content(content, keypair)
        
        # Write signature file
        sig_path = package_path.with_suffix(".yhpkg.sig")
        sig_data = {
            "signature": signature.signature,
            "key_id": signature.key_id,
            "algorithm": signature.algorithm,
            "content_hash": signature.content_hash,
        }
        sig_path.write_text(json.dumps(sig_data, indent=2))
        
        return (True, f"Package signed with key {signature.key_id}")
        
    except Exception as e:
        return (False, f"Signing failed: {e}")


def verify_package(
    package_path: Path,
    trusted_keys_dir: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Verify a package signature.
    
    Args:
        package_path: Path to .yhpkg file
        trusted_keys_dir: Directory containing trusted public keys
        
    Returns:
        Tuple of (is_valid, message)
    """
    manager = SignatureManager(trusted_keys_dir)
    
    sig_path = package_path.with_suffix(".yhpkg.sig")
    if not sig_path.exists():
        return (False, "No signature file found")
    
    try:
        # Load signature
        sig_data = json.loads(sig_path.read_text())
        signature = Signature(
            signature=sig_data["signature"],
            key_id=sig_data["key_id"],
            algorithm=sig_data["algorithm"],
            content_hash=sig_data["content_hash"],
        )
        
        # Find matching public key
        public_key = None
        for key_name in manager.list_keys():
            key_pem = manager.load_public_key(key_name)
            if key_pem:
                key_id = hashlib.sha256(key_pem).hexdigest()[:16]
                if key_id == signature.key_id:
                    public_key = key_pem
                    break
        
        if not public_key:
            return (False, f"No trusted key found for key_id {signature.key_id}")
        
        # Verify
        content = package_path.read_bytes()
        return manager.verify_signature(content, signature, public_key)
        
    except Exception as e:
        return (False, f"Verification failed: {e}")
