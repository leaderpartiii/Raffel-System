import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RPC_URL = os.getenv('RPC_URL')
    CHAIN_ID = int(os.getenv('CHAIN_ID', 11155111))
    
    RAFFLE_CONTRACT_ADDRESS = os.getenv('RAFFLE_CONTRACT_ADDRESS')
    USDT_CONTRACT_ADDRESS = os.getenv('USDT_CONTRACT_ADDRESS')
    
    VRF_COORDINATOR_ADDRESS = os.getenv('VRF_COORDINATOR_ADDRESS')
    SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')
    
    ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY')
    ADMIN_PUBLIC_ADDRESS = os.getenv('ADMIN_PUBLIC_ADDRESS')
    
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///raffle.db')
    
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default_32_char_key_for_dev!!!')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/raffle.log')

config = Config()
