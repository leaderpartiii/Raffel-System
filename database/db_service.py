import logging
from database.models import db_manager, User, Raffle, Transaction
from sqlalchemy import func

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def create_user(tg_id: str, evm_address: str, encrypted_key: str) -> User:
        """Создать нового пользователя"""
        session = db_manager.get_session()
        try:
            user = User(
                tg_id=tg_id,
                evm_address=evm_address,
                encrypted_private_key=encrypted_key
            )
            session.add(user)
            session.commit()
            logger.info(f"Created user: {tg_id}")
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def get_user_by_tg_id(tg_id: str) -> User:
        """Получить пользователя по Telegram ID"""
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.tg_id == str(tg_id)).first()
            return user
        finally:
            session.close()
    
    @staticmethod
    def get_user_by_address(evm_address: str) -> User:
        """Получить пользователя по EVM адресу"""
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.evm_address == evm_address).first()
            return user
        finally:
            session.close()
    
    @staticmethod
    def update_user_deposit(tg_id: str, amount: int, tx_hash: str = None):
        """Обновить статус депозита"""
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.tg_id == str(tg_id)).first()
            if user:
                user.deposit_amount = amount
                user.deposit_tx_hash = tx_hash
                session.commit()
                logger.info(f"Updated deposit for {tg_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user deposit: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def mark_in_raffle(tg_id: str):
        """Отметить пользователя как участника текущей лотереи"""
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.tg_id == str(tg_id)).first()
            if user:
                user.is_in_current_raffle = True
                user.total_entries += 1
                session.commit()
                logger.info(f"Marked {tg_id} as in raffle")
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking user in raffle: {e}")
            raise
        finally:
            session.close()


class RaffleService:
    @staticmethod
    def create_raffle(raffle_id: int) -> Raffle:
        """Создать новую лотерею"""
        session = db_manager.get_session()
        try:
            raffle = Raffle(raffle_id=raffle_id, status='OPEN')
            session.add(raffle)
            session.commit()
            logger.info(f"Created raffle: {raffle_id}")
            return raffle
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating raffle: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def get_current_raffle() -> Raffle:
        """Получить текущую (открытую) лотерею"""
        session = db_manager.get_session()
        try:
            raffle = session.query(Raffle).filter(Raffle.status.in_(['OPEN', 'CALCULATING'])).order_by(Raffle.id.desc()).first()
            return raffle
        finally:
            session.close()
    
    @staticmethod
    def update_raffle_participant_count(raffle_id: int, count: int):
        """Обновить количество участников"""
        session = db_manager.get_session()
        try:
            raffle = session.query(Raffle).filter(Raffle.raffle_id == raffle_id).first()
            if raffle:
                raffle.total_participants = count
                session.commit()
                logger.info(f"Updated raffle {raffle_id} participants: {count}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating raffle: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def mark_raffle_calculating(raffle_id: int, vrf_request_id: str = None):
        """Отметить лотерею как рассчитываемую"""
        session = db_manager.get_session()
        try:
            raffle = session.query(Raffle).filter(Raffle.raffle_id == raffle_id).first()
            if raffle:
                raffle.status = 'CALCULATING'
                if vrf_request_id:
                    raffle.vrf_request_id = vrf_request_id
                session.commit()
                logger.info(f"Raffle {raffle_id} marked as CALCULATING")
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking raffle calculating: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def finalize_raffle(raffle_id: int, winner_address: str, prize_amount: int):
        """Завершить лотерею с победителем"""
        session = db_manager.get_session()
        try:
            raffle = session.query(Raffle).filter(Raffle.raffle_id == raffle_id).first()
            if raffle:
                raffle.status = 'CLOSED'
                raffle.winner_address = winner_address
                raffle.prize_amount = prize_amount
                raffle.ended_at = db_manager.Session.query(func.now()).scalar()
                
                # Обновляем статистику пользователя
                user = session.query(User).filter(User.evm_address == winner_address).first()
                if user:
                    user.total_winnings += prize_amount
                    user.is_in_current_raffle = False
                
                session.commit()
                logger.info(f"Raffle {raffle_id} finalized. Winner: {winner_address}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error finalizing raffle: {e}")
            raise
        finally:
            session.close()


class TransactionService:
    @staticmethod
    def create_transaction(tg_id: str, tx_hash: str, tx_type: str, from_addr: str, to_addr: str, amount: int = 0) -> Transaction:
        """Создать запись о транзакции"""
        session = db_manager.get_session()
        try:
            tx = Transaction(
                tg_id=str(tg_id),
                tx_hash=tx_hash,
                tx_type=tx_type,
                from_address=from_addr,
                to_address=to_addr,
                amount=amount,
                status='PENDING'
            )
            session.add(tx)
            session.commit()
            logger.info(f"Created transaction record: {tx_hash}")
            return tx
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating transaction: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def mark_transaction_confirmed(tx_hash: str, gas_used: int = None, block_number: int = None):
        """Отметить транзакцию как подтвержденную"""
        session = db_manager.get_session()
        try:
            tx = session.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
            if tx:
                tx.status = 'CONFIRMED'
                tx.gas_used = gas_used
                tx.block_number = block_number
                tx.confirmed_at = db_manager.Session.query(func.now()).scalar()
                session.commit()
                logger.info(f"Transaction confirmed: {tx_hash}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error confirming transaction: {e}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Инициализируем БД
    db_manager.create_all_tables()
    
    # Пример использования
    user = UserService.create_user("123456789", "0x1234567890123456789012345678901234567890", "encrypted_key_here")
    print(f"Created user: {user}")
