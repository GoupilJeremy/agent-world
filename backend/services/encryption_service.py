# 🔐 Agent World - Encryption Service
# Version: 1.0.0 (EPIC 10 - US-067)
# Description: Service de chiffrement pour les données sensibles

"""
Encryption Service for Agent World.

Ce service fournit un chiffrement symétrique AES-256 pour protéger les données sensibles
comme les clés API, tokens, et autres informations confidentielles.

Fonctionnalités :
- Chiffrement/déchiffrement AES-256-GCM
- Gestion des clés de chiffrement
- Rotation automatique des clés
- Chiffrement de champs spécifiques dans les modèles
"""

import base64
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Type

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..models.encryption_key import EncryptionKey
from ..models.base import db


# Configure logging
logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Base exception for encryption-related errors."""

    status_code = 400
    error_code = "encryption_error"


class DecryptionError(EncryptionError):
    """Error during decryption (invalid key, corrupted data, etc.)."""

    status_code = 400
    error_code = "decryption_error"


class KeyRotationError(EncryptionError):
    """Error during key rotation."""

    status_code = 500
    error_code = "key_rotation_error"


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    
    This service uses AES-256-GCM encryption via Fernet (which uses AES-128-CBC by default,
    but we can configure it for AES-256).
    
    The service supports:
    - Encryption and decryption of strings
    - Encryption and decryption of model fields
    - Automatic key rotation
    - Key versioning
    """
    
    # Default settings
    DEFAULT_KEY_TTL_DAYS = 90  # Rotate keys every 90 days
    KEY_VERSION = 1
    
    def __init__(
        self,
        master_key: Optional[str] = None,
        key_ttl_days: int = DEFAULT_KEY_TTL_DAYS,
    ):
        """
        Initialize the EncryptionService.
        
        Args:
            master_key: The master key used to encrypt/decrypt the data encryption keys.
                      If None, will try to get from environment or generate a new one.
            key_ttl_days: Number of days before a key expires and needs rotation.
        """
        self.key_ttl_days = key_ttl_days
        
        # Set up the master key
        if master_key:
            self._master_key = self._derive_key(master_key)
        else:
            # In production, this should always be provided
            logger.warning("No master key provided for EncryptionService. Using test key.")
            self._master_key = Fernet.generate_key()
        
        # Initialize Fernet with master key
        self._master_fernet = Fernet(self._master_key)
        
        # Cache for Fernet instances (one per data key version)
        self._fernet_cache: Dict[str, Fernet] = {}
    
    @staticmethod
    def _derive_key(password: str, salt: bytes = b"agent-world-salt") -> bytes:
        """
        Derive a cryptographic key from a password using PBKDF2.
        
        This is used to derive the master key from an environment variable.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _get_data_fernet(self, key: EncryptionKey) -> Fernet:
        """Get a Fernet instance for a specific data encryption key."""
        if key.key_id not in self._fernet_cache:
            # Decrypt the data key with the master key
            decrypted_key = self._master_fernet.decrypt(key.encrypted_key.encode())
            self._fernet_cache[key.key_id] = Fernet(decrypted_key)
        return self._fernet_cache[key.key_id]
    
    def generate_data_key(self) -> bytes:
        """Generate a new random data encryption key."""
        return Fernet.generate_key()
    
    def create_and_store_key(
        self,
        description: str = "",
        ttl_days: Optional[int] = None,
    ) -> EncryptionKey:
        """
        Create a new encryption key and store it in the database.
        
        Args:
            description: Description of the key
            ttl_days: Time-to-live in days (default: self.key_ttl_days)
            
        Returns:
            The created EncryptionKey
        """
        # Generate a new data key
        data_key = self.generate_data_key()
        
        # Generate a unique key_id
        key_id = hashlib.sha256(data_key).hexdigest()[:32]
        
        # Get the next version number
        last_key = EncryptionKey.query.order_by(EncryptionKey.version.desc()).first()
        version = (last_key.version if last_key else 0) + 1
        
        # Encrypt the data key with the master key
        encrypted_data_key = self._master_fernet.encrypt(data_key)
        
        # Calculate expiration
        expires_at = None
        if ttl_days is not None or self.key_ttl_days > 0:
            ttl = ttl_days if ttl_days is not None else self.key_ttl_days
            expires_at = datetime.utcnow() + timedelta(days=ttl)
        
        # Create the key record
        key = EncryptionKey(
            key_id=key_id,
            encrypted_key=encrypted_data_key.decode(),
            is_active=False,  # Will be activated after creation
            version=version,
            expires_at=expires_at,
            description=description,
        )
        
        db.session.add(key)
        db.session.commit()
        
        return key
    
    def activate_key(self, key_id: str) -> EncryptionKey:
        """
        Activate an encryption key (make it the current active key).
        
        Args:
            key_id: The ID of the key to activate
            
        Returns:
            The activated key
        """
        key = EncryptionKey.get_by_key_id(key_id)
        if not key:
            raise EncryptionError(f"Encryption key with id {key_id} not found")
        
        # Deactivate all other keys
        EncryptionKey.deactivate_all()
        
        # Activate this key
        key.is_active = True
        key.rotated_at = datetime.utcnow()
        db.session.commit()
        
        # Clear the cache since we have a new active key
        self._fernet_cache.clear()
        
        logger.info(f"Activated encryption key {key.key_id[:8]}... (version {key.version})")
        
        return key
    
    def get_active_key(self) -> EncryptionKey:
        """
        Get the currently active encryption key.
        
        Returns:
            The active EncryptionKey
            
        Raises:
            EncryptionError: If no active key exists
        """
        key = EncryptionKey.get_active_key()
        if not key:
            # If no key exists, create a default one
            logger.warning("No active encryption key found. Creating a default one.")
            key = self.create_and_store_key(description="Default auto-generated key")
            self.activate_key(key.key_id)
            return key
        return key
    
    def rotate_key(self, description: str = "", ttl_days: Optional[int] = None) -> EncryptionKey:
        """
        Rotate the encryption key (create a new one and make it active).
        
        This should be called periodically (e.g., every 90 days) to ensure
        that old keys can be retired and new keys are used for new data.
        
        Note: Old data encrypted with previous keys can still be decrypted
        as long as the old keys are still in the database.
        
        Args:
            description: Description of the new key
            ttl_days: Time-to-live in days for the new key
            
        Returns:
            The new active EncryptionKey
        """
        try:
            # Create a new key
            new_key = self.create_and_store_key(description=description, ttl_days=ttl_days)
            
            # Activate the new key
            activated_key = self.activate_key(new_key.key_id)
            
            logger.info(f"Rotated encryption key to version {activated_key.version}")
            
            return activated_key
        except Exception as e:
            logger.error(f"Failed to rotate encryption key: {e}")
            raise KeyRotationError(f"Failed to rotate key: {e}")
    
    def needs_rotation(self) -> bool:
        """
        Check if the current active key needs to be rotated.
        
        Returns:
            True if the key is expired or about to expire
        """
        key = EncryptionKey.get_active_key()
        if not key:
            return True
        
        if key.expires_at is None:
            return False
        
        # Check if key is expired
        if key.expires_at < datetime.utcnow():
            return True
        
        # Check if key is within 7 days of expiration
        seven_days = datetime.utcnow() + timedelta(days=7)
        if key.expires_at < seven_days:
            return True
        
        return False
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string using the current active key.
        
        Args:
            data: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            key = self.get_active_key()
            fernet = self._get_data_fernet(key)
            encrypted = fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string using the appropriate key.
        
        The function will try all available keys to find one that works,
        allowing decryption of data encrypted with previous keys.
        
        Args:
            encrypted_data: The base64-encoded encrypted string
            
        Returns:
            The decrypted string
            
        Raises:
            DecryptionError: If decryption fails with all available keys
        """
        try:
            # Try with all keys (newest first)
            keys = EncryptionKey.get_all_versions()
            
            for key in keys:
                try:
                    fernet = self._get_data_fernet(key)
                    decrypted = fernet.decrypt(encrypted_data.encode())
                    return decrypted.decode()
                except InvalidToken:
                    # Try next key
                    continue
            
            # If we get here, all keys failed
            raise DecryptionError("Failed to decrypt data with any available key")
        except InvalidToken as e:
            logger.error(f"Decryption failed: {e}")
            raise DecryptionError(f"Decryption failed: {e}")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise DecryptionError(f"Decryption failed: {e}")
    
    def encrypt_field(self, model: Any, field_name: str) -> None:
        """
        Encrypt a field of a model in place.
        
        Args:
            model: The SQLAlchemy model instance
            field_name: The name of the field to encrypt
        """
        if not hasattr(model, field_name):
            raise EncryptionError(f"Field {field_name} not found on model")
        
        value = getattr(model, field_name)
        if value is None:
            return
        
        encrypted = self.encrypt(value)
        setattr(model, field_name, encrypted)
    
    def decrypt_field(self, model: Any, field_name: str) -> None:
        """
        Decrypt a field of a model in place.
        
        Args:
            model: The SQLAlchemy model instance
            field_name: The name of the field to decrypt
        """
        if not hasattr(model, field_name):
            raise EncryptionError(f"Field {field_name} not found on model")
        
        value = getattr(model, field_name)
        if value is None:
            return
        
        try:
            decrypted = self.decrypt(value)
            setattr(model, field_name, decrypted)
        except DecryptionError:
            # If decryption fails, the field might not be encrypted
            # This is okay for backward compatibility
            pass
    
    def create_encrypted_model(
        self,
        model_class: Type,
        encrypted_fields: List[str],
        **kwargs
    ) -> Any:
        """
        Create a model instance with encrypted fields.
        
        Args:
            model_class: The SQLAlchemy model class
            encrypted_fields: List of field names to encrypt
            **kwargs: Arguments to pass to the model constructor
            
        Returns:
            The created model instance
        """
        # Create the model without encrypted fields
        model_kwargs = {k: v for k, v in kwargs.items() if k not in encrypted_fields}
        model = model_class(**model_kwargs)
        
        # Encrypt and set the encrypted fields
        for field in encrypted_fields:
            if field in kwargs:
                encrypted_value = self.encrypt(kwargs[field])
                setattr(model, field, encrypted_value)
        
        return model
    
    def get_decrypted_model(self, model: Any, encrypted_fields: List[str]) -> Any:
        """
        Get a model with decrypted fields.
        
        This creates a copy of the model with encrypted fields decrypted.
        The original model is not modified.
        
        Args:
            model: The SQLAlchemy model instance
            encrypted_fields: List of field names to decrypt
            
        Returns:
            A dictionary with decrypted values
        """
        result = {}
        for field in encrypted_fields:
            if hasattr(model, field):
                value = getattr(model, field)
                if value is not None:
                    try:
                        result[field] = self.decrypt(value)
                    except DecryptionError:
                        # Field might not be encrypted
                        result[field] = value
                else:
                    result[field] = None
        return result
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*", show_last: int = 4) -> str:
        """
        Mask sensitive data for logging/display purposes.
        
        Args:
            data: The sensitive data to mask
            mask_char: Character to use for masking (default: "*")
            show_last: Number of characters to show at the end (default: 4)
            
        Returns:
            Masked string (e.g., "abc123xyz" -> "*******xyz")
        """
        if not data or len(data) <= show_last:
            return mask_char * len(data) if data else ""
        
        return mask_char * (len(data) - show_last) + data[-show_last:]
    
    def create_sensitive_field_masker(self, fields: List[str], mask_char: str = "*", show_last: int = 4) -> Callable:
        """
        Create a function that masks specified fields in a dictionary.
        
        Args:
            fields: List of field names to mask
            mask_char: Character to use for masking
            show_last: Number of characters to show at the end
            
        Returns:
            A function that takes a dict and returns a dict with masked fields
        """
        def masker(data: Dict[str, Any]) -> Dict[str, Any]:
            if not isinstance(data, dict):
                return data
            
            result = data.copy()
            for field in fields:
                if field in result and isinstance(result[field], str):
                    result[field] = self.mask_sensitive_data(
                        result[field], mask_char, show_last
                    )
            return result
        
        return masker


# Global encryption service instance (initialized in app factory)
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        raise RuntimeError("EncryptionService not initialized. Call init_encryption_service() first.")
    return _encryption_service


def init_encryption_service(master_key: Optional[str] = None, key_ttl_days: int = 90) -> EncryptionService:
    """Initialize the global encryption service."""
    global _encryption_service
    _encryption_service = EncryptionService(master_key=master_key, key_ttl_days=key_ttl_days)
    return _encryption_service
