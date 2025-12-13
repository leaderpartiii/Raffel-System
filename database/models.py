import logging
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import config

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(String(255), unique=True, nullable=False, index=True)
    evm_address = Column(String(255), unique=True, nullable=False, index=True)
    encrypted_private_key = Column(Text, nullable=False)
    
    is_in_current_raffle = Column(Boolean, default=False)
    deposit_amount = Column(Integer, default=0)  # в wei
    deposit_tx_hash = Column(String(255), nullable=True)
    
    total_entries = Column(Integer, default=0)
    total_winnings = Column(Integer, default=0)  # в wei
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User tg_id={self.tg_id} address={self.evm_address[:10]}...>"


class Raffle(Base):
    __tablename__ = 'raffles'
    
    id = Column(Integer, primary_key=True)
    raffle_id = Column(Integer, unique=True, nullable=False, index=True)
    
    status = Column(String(50), default='OPEN')  # OPEN, CALCULATING, CLOSED
    
    total_participants = Column(Integer, default=0)
    total_pool = Column(Integer, default=0)  # в wei
    
    winner_address = Column(String(255), nullable=True)
    prize_amount = Column(Integer, nullable=True)  # в wei
    vrf_request_id = Column(String(255), nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Raffle id={self.raffle_id} status={self.status} participants={self.total_participants}>"


class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(String(255), nullable=False, index=True)
    tx_hash = Column(String(255), unique=True, nullable=False, index=True)
    tx_type = Column(String(50), nullable=False)  # 'DEPOSIT', 'ENTER_RAFFLE', 'WIN_PRIZE'
    
    from_address = Column(String(255), nullable=False)
    to_address = Column(String(255), nullable=False)
    amount = Column(Integer, default=0)  # в wei
    
    status = Column(String(50), default='PENDING')  # PENDING, CONFIRMED, FAILED
    gas_used = Column(Integer, nullable=True)
    block_number = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Transaction {self.tx_type} {self.tx_hash[:10]}... status={self.status}>"


class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized: {config.DATABASE_URL}")
    
    def create_all_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def get_session(self):
        return self.Session()
    
    def close_session(self, session):
        if session:
            session.close()


db_manager = DatabaseManager()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_manager.create_all_tables()
