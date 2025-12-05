import logging
from flask import Flask, jsonify, request
from wallet.wallet_manager import WalletManager
from database.db_service import UserService, RaffleService
from transaction.raffle_processor import RaffleProcessor
from config.settings import config

app = Flask(__name__)
logger = logging.getLogger(__name__)

wallet_manager = WalletManager()
raffle_processor = RaffleProcessor()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/wallet/generate', methods=['POST'])
def generate_wallet():
    """
    Генерирует новый кошелек для пользователя
    
    Request body:
    {
        "tg_id": "123456789"
    }
    
    Response:
    {
        "success": true,
        "address": "0x...",
        "private_key": "0x..." (НЕ ХРАНИТЬ НА КЛИЕНТЕ!)
    }
    """
    try:
        data = request.json
        tg_id = data.get('tg_id')
        
        if not tg_id:
            return jsonify({'success': False, 'error': 'Missing tg_id'}), 400
        
        # Проверяем, есть ли уже кошелек
        user = UserService.get_user_by_tg_id(tg_id)
        if user:
            return jsonify({
                'success': True,
                'address': user.evm_address,
                'message': 'User already has a wallet'
            }), 200
        
        # Генерируем новый кошелек
        wallet = wallet_manager.generate_wallet()
        
        # Создаем пользователя в БД
        user = UserService.create_user(
            tg_id=tg_id,
            evm_address=wallet['address'],
            encrypted_key=wallet['encrypted_private_key']
        )
        
        return jsonify({
            'success': True,
            'address': wallet['address'],
            'private_key': wallet['private_key'],
            'message': 'Wallet generated. Keep private key safe!'
        }), 201
    
    except Exception as e:
        logger.error(f"Error generating wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wallet/balance/<tg_id>', methods=['GET'])
def get_balance(tg_id):
    """
    Получить баланс USDT пользователя
    
    Response:
    {
        "success": true,
        "balance": 1000000 (в wei),
        "balance_usdt": 1.0 (в USDT, если 18 decimals)
    }
    """
    try:
        user = UserService.get_user_by_tg_id(tg_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        balance = raffle_processor.check_user_balance(user.evm_address)
        
        return jsonify({
            'success': True,
            'balance': balance,
            'balance_usdt': balance / 1e18  # Предполагая 18 decimals
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/raffle/status', methods=['GET'])
def get_raffle_status():
    """
    Получить статус текущей лотереи
    
    Response:
    {
        "success": true,
        "players_count": 5,
        "state": "OPEN",
        "entrance_fee": 1000000,
        "pool": 5000000
    }
    """
    try:
        status = raffle_processor.get_raffle_status()
        return jsonify({
            'success': True,
            **status
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting raffle status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/raffle/enter', methods=['POST'])
def enter_raffle():
    """
    Вход в лотерею
    
    Request body:
    {
        "tg_id": "123456789"
    }
    
    Response:
    {
        "success": true,
        "tx_hash": "0x...",
        "message": "Entry processed"
    }
    """
    try:
        data = request.json
        tg_id = data.get('tg_id')
        
        if not tg_id:
            return jsonify({'success': False, 'error': 'Missing tg_id'}), 400
        
        user = UserService.get_user_by_tg_id(tg_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        result = raffle_processor.process_user_entry(
            tg_id=tg_id,
            evm_address=user.evm_address,
            encrypted_key=user.encrypted_private_key
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'tx_hash': result['tx_hash'],
            'message': 'Entry processed'
        }), 200
    
    except Exception as e:
        logger.error(f"Error entering raffle: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/raffle/draw', methods=['POST'])
def trigger_draw():
    """
    Запустить розыгрыш (ТОЛЬКО ДЛЯ АДМИНА)
    
    Response:
    {
        "success": true,
        "tx_hash": "0x..."
    }
    """
    try:
        # Простая проверка (в продакшене нужна полноценная аутентификация)
        auth_token = request.headers.get('Authorization')
        if not auth_token or auth_token != f"Bearer {config.SECRET_KEY}":
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        result = raffle_processor.trigger_raffle_draw()
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400
        
        return jsonify({
            'success': True,
            'tx_hash': result['tx_hash']
        }), 200
    
    except Exception as e:
        logger.error(f"Error triggering draw: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/user/stats/<tg_id>', methods=['GET'])
def get_user_stats(tg_id):
    """
    Получить статистику пользователя
    
    Response:
    {
        "success": true,
        "total_entries": 5,
        "total_winnings": 50000000,
        "current_deposit": 1000000
    }
    """
    try:
        user = UserService.get_user_by_tg_id(tg_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'total_entries': user.total_entries,
            'total_winnings': user.total_winnings,
            'current_deposit': user.deposit_amount,
            'is_in_raffle': user.is_in_current_raffle
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host=config.API_HOST, port=config.API_PORT, debug=True)
