"""
Encryption Utilities

Provides encryption/decryption functions for sensitive client data.
Integrates with PostgreSQL pgcrypto for database-level encryption.
"""

import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from .security_config import get_security_manager


logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data.
    
    Uses PostgreSQL pgcrypto extension for database-level encryption
    to ensure data is encrypted at rest.
    """
    
    def __init__(self, session: Session):
        """
        Initialize encryption manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.security_manager = get_security_manager()
        self.encryption_key = self.security_manager.get_encryption_key()
    
    def encrypt_email(self, email: str) -> bytes:
        """
        Encrypt email address using pgcrypto.
        
        Args:
            email: Plain text email address
            
        Returns:
            Encrypted email as bytes
        """
        try:
            query = text("""
                SELECT encrypt_sensitive_data(:data, :key)
            """)
            
            result = self.session.execute(
                query,
                {'data': email, 'key': self.encryption_key}
            ).scalar()
            
            logger.debug(f"Encrypted email address")
            return result
            
        except Exception as e:
            logger.error(f"Failed to encrypt email: {e}")
            raise
    
    def decrypt_email(self, encrypted_email: bytes) -> Optional[str]:
        """
        Decrypt email address using pgcrypto.
        
        Args:
            encrypted_email: Encrypted email as bytes
            
        Returns:
            Decrypted email address or None if decryption fails
        """
        if not encrypted_email:
            return None
        
        try:
            query = text("""
                SELECT decrypt_sensitive_data(:encrypted_data, :key)
            """)
            
            result = self.session.execute(
                query,
                {'encrypted_data': encrypted_email, 'key': self.encryption_key}
            ).scalar()
            
            logger.debug(f"Decrypted email address")
            return result
            
        except Exception as e:
            logger.error(f"Failed to decrypt email: {e}")
            return None
    
    def encrypt_phone_number(self, phone_number: str) -> bytes:
        """
        Encrypt phone number using pgcrypto.
        
        Args:
            phone_number: Plain text phone number
            
        Returns:
            Encrypted phone number as bytes
        """
        try:
            query = text("""
                SELECT encrypt_sensitive_data(:data, :key)
            """)
            
            result = self.session.execute(
                query,
                {'data': phone_number, 'key': self.encryption_key}
            ).scalar()
            
            logger.debug(f"Encrypted phone number")
            return result
            
        except Exception as e:
            logger.error(f"Failed to encrypt phone number: {e}")
            raise
    
    def decrypt_phone_number(self, encrypted_phone: bytes) -> Optional[str]:
        """
        Decrypt phone number using pgcrypto.
        
        Args:
            encrypted_phone: Encrypted phone number as bytes
            
        Returns:
            Decrypted phone number or None if decryption fails
        """
        if not encrypted_phone:
            return None
        
        try:
            query = text("""
                SELECT decrypt_sensitive_data(:encrypted_data, :key)
            """)
            
            result = self.session.execute(
                query,
                {'encrypted_data': encrypted_phone, 'key': self.encryption_key}
            ).scalar()
            
            logger.debug(f"Decrypted phone number")
            return result
            
        except Exception as e:
            logger.error(f"Failed to decrypt phone number: {e}")
            return None
    
    def encrypt_full_name(self, full_name: str) -> bytes:
        """
        Encrypt full name using pgcrypto.
        
        Args:
            full_name: Plain text full name
            
        Returns:
            Encrypted full name as bytes
        """
        try:
            query = text("""
                SELECT encrypt_sensitive_data(:data, :key)
            """)
            
            result = self.session.execute(
                query,
                {'data': full_name, 'key': self.encryption_key}
            ).scalar()
            
            logger.debug(f"Encrypted full name")
            return result
            
        except Exception as e:
            logger.error(f"Failed to encrypt full name: {e}")
            raise
    
    def decrypt_full_name(self, encrypted_name: bytes) -> Optional[str]:
        """
        Decrypt full name using pgcrypto.
        
        Args:
            encrypted_name: Encrypted full name as bytes
            
        Returns:
            Decrypted full name or None if decryption fails
        """
        if not encrypted_name:
            return None
        
        try:
            query = text("""
                SELECT decrypt_sensitive_data(:encrypted_data, :key)
            """)
            
            result = self.session.execute(
                query,
                {'encrypted_data': encrypted_name, 'key': self.encryption_key}
            ).scalar()
            
            logger.debug(f"Decrypted full name")
            return result
            
        except Exception as e:
            logger.error(f"Failed to decrypt full name: {e}")
            return None
    
    def save_encrypted_client_data(
        self,
        client_id: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> bool:
        """
        Save encrypted client data to database.
        
        Args:
            client_id: Client identifier
            email: Optional email address to encrypt and save
            phone_number: Optional phone number to encrypt and save
            full_name: Optional full name to encrypt and save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_parts = []
            params = {'client_id': client_id}
            
            if email:
                encrypted_email = self.encrypt_email(email)
                update_parts.append("email_encrypted = :email_encrypted")
                params['email_encrypted'] = encrypted_email
            
            if phone_number:
                encrypted_phone = self.encrypt_phone_number(phone_number)
                update_parts.append("phone_number_encrypted = :phone_encrypted")
                params['phone_encrypted'] = encrypted_phone
            
            if full_name:
                encrypted_name = self.encrypt_full_name(full_name)
                update_parts.append("full_name_encrypted = :name_encrypted")
                params['name_encrypted'] = encrypted_name
            
            if not update_parts:
                logger.warning("No data provided to encrypt")
                return False
            
            query = text(f"""
                UPDATE crm_client_preferences
                SET {', '.join(update_parts)}
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(query, params)
            self.session.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.info(f"Saved encrypted data for client {client_id}")
            else:
                logger.warning(f"No client found with ID {client_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to save encrypted client data: {e}")
            self.session.rollback()
            return False
    
    def get_decrypted_client_data(
        self,
        client_id: str
    ) -> Optional[dict]:
        """
        Retrieve and decrypt client data from database.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with decrypted data or None if not found
        """
        try:
            query = text("""
                SELECT 
                    email_encrypted,
                    phone_number_encrypted,
                    full_name_encrypted
                FROM crm_client_preferences
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(query, {'client_id': client_id}).fetchone()
            
            if not result:
                logger.warning(f"No encrypted data found for client {client_id}")
                return None
            
            decrypted_data = {
                'client_id': client_id,
                'email': self.decrypt_email(result[0]) if result[0] else None,
                'phone_number': self.decrypt_phone_number(result[1]) if result[1] else None,
                'full_name': self.decrypt_full_name(result[2]) if result[2] else None
            }
            
            logger.info(f"Retrieved and decrypted data for client {client_id}")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve decrypted client data: {e}")
            return None


def encrypt_api_credential(credential: str, encryption_key: str) -> bytes:
    """
    Encrypt API credential for storage in database.
    
    Args:
        credential: Plain text credential
        encryption_key: Encryption key
        
    Returns:
        Encrypted credential as bytes
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    # Derive a Fernet key from the encryption key
    key_bytes = hashlib.sha256(encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)
    
    encrypted = fernet.encrypt(credential.encode())
    return encrypted


def decrypt_api_credential(encrypted_credential: bytes, encryption_key: str) -> str:
    """
    Decrypt API credential from database.
    
    Args:
        encrypted_credential: Encrypted credential as bytes
        encryption_key: Encryption key
        
    Returns:
        Decrypted credential string
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    # Derive a Fernet key from the encryption key
    key_bytes = hashlib.sha256(encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)
    
    decrypted = fernet.decrypt(encrypted_credential)
    return decrypted.decode()
