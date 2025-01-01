from dataclasses import dataclass
from typing import Optional
from eth_account import Account
from web3 import Web3


@dataclass
class Transaction:
    """Data class for transaction signing requests"""

    to: str
    value: int = 0
    data: str = "0x"
    nonce: Optional[int] = None
    gas_price: Optional[int] = None
    gas: Optional[int] = None


@dataclass
class SignTransactionRequest:
    """Data class for transaction signing requests"""

    rpc_url: str
    transaction: dict

    def __post_init__(self):
        # Convert the transaction dict to Transaction object after initialization
        if isinstance(self.transaction, dict):
            self.transaction = Transaction(**self.transaction)


def sign_and_broadcast_eth_transaction(
    tx: Transaction, private_key: str, rpc_url: str
) -> dict:
    """Signs and broadcasts an Ethereum transaction using the TEE's private key"""
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    account = Account.from_key(private_key)

    balance = web3.eth.get_balance(account.address)
    print(f"Account balance: {web3.from_wei(balance, 'ether')} ETH")
    print(f"Account address: {account.address}")
    print(f"RPC: {rpc_url}")

    # Get chain ID from RPC
    chain_id = web3.eth.chain_id

    tx_dict = {
        "to": tx.to,
        "value": tx.value,
        "data": tx.data,
        "chainId": chain_id,
        "nonce": (
            tx.nonce
            if tx.nonce is not None
            else web3.eth.get_transaction_count(account.address)
        ),
        "gasPrice": (tx.gas_price if tx.gas_price is not None else web3.eth.gas_price),
        "gas": (tx.gas if tx.gas is not None else 21000),  # Default gas limit
    }

    signed_tx = web3.eth.account.sign_transaction(tx_dict, account.key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    return {
        "signed_transaction": Web3.to_hex(signed_tx.raw_transaction),
        "transaction_hash": Web3.to_hex(tx_hash),
    }
