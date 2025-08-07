"""
User DAO for user management operations
"""
from typing import Optional
from sqlalchemy.orm import Session
from dao.base import BaseDAO
from models.user import User
import hashlib
import secrets
from loguru import logger

class UserDAO(BaseDAO[User]):
    """Data Access Object for User model"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def create_user(
        self,
        db: Session,
        email: str,
        username: str,
        password: str,
        **kwargs
    ) -> User:
        """Create a new user with hashed password"""
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user
        return self.create(
            db,
            email=email,
            username=username,
            password_hash=password_hash,
            **kwargs
        )
    
    def verify_password(self, user: User, password: str) -> bool:
        """Verify user password"""
        return user.password_hash == self._hash_password(password)
    
    def update_password(
        self,
        db: Session,
        user_id: str,
        new_password: str
    ) -> bool:
        """Update user password"""
        password_hash = self._hash_password(new_password)
        user = self.update(db, user_id, password_hash=password_hash)
        return user is not None
    
    def update_api_keys(
        self,
        db: Session,
        user_id: str,
        api_key: str,
        api_secret: str
    ) -> bool:
        """Update user's Binance API keys (encrypted)"""
        # In production, use proper encryption
        # For now, just store them (you should encrypt these!)
        encrypted_key = self._simple_encrypt(api_key)
        encrypted_secret = self._simple_encrypt(api_secret)
        
        user = self.update(
            db,
            user_id,
            binance_api_key_encrypted=encrypted_key,
            binance_api_secret_encrypted=encrypted_secret
        )
        return user is not None
    
    def get_decrypted_api_keys(self, user: User) -> tuple[Optional[str], Optional[str]]:
        """Get decrypted API keys for a user"""
        if not user.binance_api_key_encrypted or not user.binance_api_secret_encrypted:
            return None, None
        
        api_key = self._simple_decrypt(user.binance_api_key_encrypted)
        api_secret = self._simple_decrypt(user.binance_api_secret_encrypted)
        
        return api_key, api_secret
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256 (use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _simple_encrypt(self, text: str) -> str:
        """Simple encryption (use proper encryption in production)"""
        # This is NOT secure - use proper encryption like Fernet in production
        return text[::-1]  # Just reverse for demo
    
    def _simple_decrypt(self, text: str) -> str:
        """Simple decryption (use proper decryption in production)"""
        # This is NOT secure - use proper decryption in production
        return text[::-1]  # Just reverse for demo