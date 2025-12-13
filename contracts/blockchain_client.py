import json
import os
import time
import logging
from web3 import Web3
from typing import Optional

logger = logging.getLogger(__name__)


class BlockchainClient:
    def __init__(self):
        self.rpc_url = os.getenv("RPC_URL", "http://localhost:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        self._wait_for_connection()

        self.contract_data_path = os.getenv("CONTRACT_DATA_PATH", "./contract_data/contract_info.json")
        self.raffle_contract = self._load_dynamic_contract()

    def _wait_for_connection(self):
        while not self.w3.is_connected():
            logger.warning(f"Waiting for blockchain at {self.rpc_url}...")
            time.sleep(2)
        logger.info(f"✅ Connected to blockchain at {self.rpc_url}")

    def _load_dynamic_contract(self):
        while not os.path.exists(self.contract_data_path):
            logger.warning(f"Waiting for contract file at {self.contract_data_path}...")
            time.sleep(2)

        try:
            with open(self.contract_data_path, 'r') as f:
                data = json.load(f)
            self.contract_data = data

            address = Web3.to_checksum_address(data['address'])
            abi = data['abi']

            logger.info(f"✅ Loaded Raffle contract at {address}")
            return self.w3.eth.contract(address=address, abi=abi)
        except Exception as e:
            logger.error(f"Failed to load contract data: {e}")
            raise e

    def get_contract_by_address(self, address: str, abi: list):
        return self.w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
