import typing
from datetime import datetime

class Action:
    def __init__(self, timestamp: datetime, tx_hash: str, block_number: str, swap_fee: str, denorms: typing.Dict, action_type: str, action: typing.Dict):
        self.timestamp = timestamp
        self.tx_hash = tx_hash
        self.block_number = block_number
        self.swap_fee = swap_fee
        self.denorms = denorms
        self.action_type = action_type
        self.action = action
