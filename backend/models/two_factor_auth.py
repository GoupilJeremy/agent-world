# 🔐 Agent World - Two-Factor Authentication Model
# Version: 1.0.0 (EPIC 10 - US-065)
# Description: Modèle pour stocker les configurations 2FA des utilisateurs

"""
Two-Factor Authentication Model for Agent World.

Ce modèle stocke les clés secrètes TOTP et les codes de secours
pour l'authentification à deux facteurs des utilisateurs.
"""

from datetime import datetime
from typing import List, Optional

from .base import BaseModel, db


class TwoFactorAuth(BaseModel):
    """
    Model for storing TOTP (Time-based One-Time Password) configurations.

    Attributes:
        id: Unique identifier
        user_id: Foreign key to the user
        secret_key: Encrypted TOTP secret key
        is_enabled: Whether 2FA is enabled for this user
        recovery_codes: Encrypted list of recovery codes (JSON string)
        created_at: Timestamp when 2FA was set up
        updated_at: Timestamp when 2FA was last updated
    """

    __tablename__ = "two_factor_auth"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    secret_key = db.Column(db.String(255), nullable=False)  # Encrypted TOTP secret
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    recovery_codes = db.Column(db.Text, nullable=True)  # Encrypted JSON array of codes
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationship
    user = db.relationship("User", back_populates="two_factor_auth")

    def __init__(
        self,
        user_id: int,
        secret_key: str,
        is_enabled: bool = False,
        recovery_codes: Optional[List[str]] = None,
    ):
        """
        Initialize a new TwoFactorAuth instance.

        Args:
            user_id: ID of the user
            secret_key: Encrypted TOTP secret key
            is_enabled: Whether 2FA is enabled (default: False)
            recovery_codes: List of recovery codes (will be encrypted)
        """
        self.user_id = user_id
        self.secret_key = secret_key
        self.is_enabled = is_enabled
        self.recovery_codes = self._serialize_recovery_codes(recovery_codes)

    def __repr__(self) -> str:
        return (
            f"<TwoFactorAuth(id={self.id}, user_id={self.user_id}, "
            f"is_enabled={self.is_enabled})>"
        )

    @staticmethod
    def _serialize_recovery_codes(codes: Optional[List[str]]) -> Optional[str]:
        """Serialize recovery codes to a JSON string."""
        if codes is None:
            return None
        import json
        return json.dumps(codes)

    @staticmethod
    def _deserialize_recovery_codes(serialized: Optional[str]) -> List[str]:
        """Deserialize recovery codes from a JSON string."""
        if serialized is None:
            return []
        import json
        return json.loads(serialized)

    @property
    def recovery_codes_list(self) -> List[str]:
        """Get recovery codes as a list."""
        return self._deserialize_recovery_codes(self.recovery_codes)

    @recovery_codes_list.setter
    def recovery_codes_list(self, codes: List[str]) -> None:
        """Set recovery codes from a list."""
        self.recovery_codes = self._serialize_recovery_codes(codes)

    def enable(self) -> None:
        """Enable 2FA for this user."""
        self.is_enabled = True
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def disable(self) -> None:
        """Disable 2FA for this user."""
        self.is_enabled = False
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def use_recovery_code(self, code: str) -> bool:
        """
        Use a recovery code and remove it from the list.

        Args:
            code: The recovery code to use

        Returns:
            True if the code was found and removed, False otherwise
        """
        codes = self.recovery_codes_list
        if code in codes:
            codes.remove(code)
            self.recovery_codes_list = codes
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    def regenerate_recovery_codes(self, new_codes: List[str]) -> None:
        """
        Replace all recovery codes with new ones.

        Args:
            new_codes: List of new recovery codes
        """
        self.recovery_codes_list = new_codes
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses (excludes sensitive data)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "recovery_codes_count": len(self.recovery_codes_list),
        }

    @classmethod
    def get_by_user_id(cls, user_id: int) -> Optional["TwoFactorAuth"]:
        """Get TwoFactorAuth configuration for a specific user."""
        return cls.query.filter_by(user_id=user_id).first()

    @classmethod
    def is_enabled_for_user(cls, user_id: int) -> bool:
        """Check if 2FA is enabled for a specific user."""
        tfa = cls.query.filter_by(user_id=user_id, is_enabled=True).first()
        return tfa is not None
