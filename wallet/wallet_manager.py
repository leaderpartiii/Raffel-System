import logging
from eth_keys import keys
from web3 import Web3
from cryptography.fernet import Fernet
from config.settings import config

logger = logging.getLogger(__name__)


class WalletManager:
    def __init__(self):
        self.encryption_key = config.ENCRYPTION_KEY
        if isinstance(self.encryption_key, str):
            self.encryption_key = self.encryption_key.encode()
        
        if len(self.encryption_key) != 32:
            raise ValueError("Encryption key must be exactly 32 characters long")
        
        import base64
        encoded_key = base64.urlsafe_b64encode(self.encryption_key)
        self.cipher = Fernet(encoded_key)
    
    def generate_wallet(self) -> dict:
        """
        Генерирует новый EVM кошелек
        
        Returns:
            {
                'address': '0x...',
                'private_key': '0x...',
                'encrypted_private_key': '...' (для хранения в БД)
            }
        """
        try:
            account = Web3().eth.account.create()
            
            private_key = account.key.hex()
            address = account.address
            
            encrypted_key = self.encrypt_private_key(private_key)
            
            logger.info(f"Generated new wallet: {address}")
            
            return {
                'address': address,
                'private_key': private_key,
                'encrypted_private_key': encrypted_key
            }
        
        except Exception as e:
            logger.error(f"Error generating wallet: {e}")
            raise
    
    def encrypt_private_key(self, private_key: str) -> str:
        """Шифрует приватный ключ"""
        try:
            if isinstance(private_key, str):
                private_key = private_key.encode()
            
            encrypted = self.cipher.encrypt(private_key)
            return encrypted.decode()
        
        except Exception as e:
            logger.error(f"Error encrypting private key: {e}")
            raise
    
    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Расшифровывает приватный ключ"""
        try:
            if isinstance(encrypted_key, str):
                encrypted_key = encrypted_key.encode()
            
            decrypted = self.cipher.decrypt(encrypted_key)
            return decrypted.decode()
        
        except Exception as e:
            logger.error(f"Error decrypting private key: {e}")
            raise
    
    def validate_address(self, address: str) -> bool:
        """Проверяет валидность адреса"""
        return Web3.is_address(address)
    
    def validate_private_key(self, private_key: str) -> bool:
        """Проверяет валидность приватного ключа"""
        try:
            Web3().eth.account.from_key(private_key)
            return True
        except Exception:
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = WalletManager()
    
    wallet = manager.generate_wallet()
    print(f"Generated wallet: {wallet['address']}")
    
    encrypted = manager.encrypt_private_key(wallet['private_key'])
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = manager.decrypt_private_key(encrypted)
    print(f"Decrypted matches: {decrypted == wallet['private_key']}")
