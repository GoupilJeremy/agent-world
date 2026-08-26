# 🔐 Agent World - Encryption Key Model
# Version: 1.0.0 (EPIC 10 - US-067)
# Description: Modèle pour stocker les clés de chiffrement

"""
Encryption Key Model for Agent World.

Ce modèle stocke les clés de chiffrement utilisées pour protéger les données sensibles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseModel, db


class EncryptionKey(BaseModel):
    """
    Model for storing encryption keys in the database.
    
    Each key has:
    - A unique identifier
    - The encrypted key material (encrypted with a master key)
    - Creation and expiration timestamps
    - A version number
    - A flag indicating if it's the current active key
    """
    
    __tablename__ = "encryption_keys"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key_id = db.Column(db.String(64), nullable=False, unique=True)  # Unique identifier for the key
    encrypted_key = db.Column(db.Text, nullable=False)  # The actual encryption key, encrypted with master key
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    rotated_at = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    
    def __init__(
        self,
        key_id: str,
        encrypted_key: str,
        is_active: bool = False,
        version: int = 1,
        expires_at: Optional[datetime] = None,
        description: str = "",
    ):
        self.key_id = key_id
        self.encrypted_key = encrypted_key
        self.is_active = is_active
        self.version = version
        self.expires_at = expires_at
        self.description = description
    
    def __repr__(self) -> str:
        return f"<EncryptionKey(id={self.id}, key_id={self.key_id[:8]}..., version={self.version}, is_active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without the encrypted key)."""
        return {
            "id": self.id,
            "key_id": self.key_id,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "description": self.description,
        }
    
    @classmethod
    def get_active_key(cls) -> Optional["EncryptionKey"]:
        """Get the currently active encryption key."""
        return cls.query.filter_by(is_active=True).first()
    
    @classmethod
    def get_by_key_id(cls, key_id: str) -> Optional["EncryptionKey"]:
        """Get an encryption key by its key_id."""
        return cls.query.filter_by(key_id=key_id).first()
    
    @classmethod
    def get_all_versions(cls) -> List["EncryptionKey"]:
        """Get all encryption keys, ordered by version."""
        return cls.query.order_by(cls.version.desc()).all()
    
    @classmethod
    def deactivate_all(cls) -> None:
        """Deactivate all encryption keys."""
        cls.query.update({"is_active": False})
        db.session.commit()
