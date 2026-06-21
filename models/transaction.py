from __future__ import annotations 
import json 
from datetime import datetime, timezone


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


class Transaction:
    def __init__(self, transaction_id, user_id, merchant_id, amount, currency, timestamp, country, device_id, is_online):
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.merchant_id = merchant_id
        self.amount = amount
        self.currency = currency
        self.timestamp = timestamp
        self.country = country
        self.device_id = device_id
        self.is_online = is_online

        _require(isinstance(self.transaction_id, str) and self.transaction_id, f"transaction_id must be a non-empty string, got {self.transaction_id!r}")
        _require(isinstance(self.user_id, str) and self.user_id, f"user_id must be a non-empty string, got {self.user_id!r}")
        _require(isinstance(self.amount, (int, float)) and self.amount >= 0, f"amount must be a non-negative number, got {self.amount}")
        _require(isinstance(self.currency, str) and len(self.currency) == 3, f"currency must be a 3-letter code, got {self.currency!r}")
        _require(isinstance(self.country, str) and len(self.country) == 2, f"country must be a 2-letter ISO code, got {self.country!r}")
        _require(isinstance(self.is_online, bool), f"is_online must be a bool, got {type(self.is_online).__name__}")

    
    def to_dict(self):
        return {
            "transaction_id" : self.transaction_id,
            "user_id" : self.user_id,
            "merchant_id" : self.merchant_id,
            "amount" : self.amount,
            "currency" : self.currency,
            "timestamp" : self.timestamp,
            "country" : self.country,
            "device_id" : self.device_id,
            "is_online" : self.is_online,

        }

        
    
    def is_purchase(self):
        return True

    def event_type(self):
        return "transaction"

    def __repr__(self):
        return f"Transaction(id={self.transaction_id!r}, user={self.user_id!r}, amount={self.amount} {self.currency!r})"



class LabeledTransaction(Transaction):
    def __init__(self, transaction_id, user_id, merchant_id, amount, currency, timestamp, country, device_id, is_online, is_fraud, fraud_type):
        super().__init__(transaction_id, user_id, merchant_id, amount, currency, timestamp, country, device_id, is_online)
        self.is_fraud = is_fraud
        self.fraud_type = fraud_type

        _require(self.is_fraud or self.fraud_type is None, "fraud_type must be None when is_fraud is False")

    def to_dict(self):
        d = super().to_dict()
        d["is_fraud"] = self.is_fraud
        d["fraud_type"] = self.fraud_type
        return d

    def event_type(self):
        return "fraud" if self.is_fraud else "legit"

    def __repr__(self):
        return f"LabeledTransaction(id={self.transaction_id!r}, user={self.user_id!r}, amount={self.amount} {self.currency!r}, fraud={self.is_fraud}, type={self.fraud_type!r})"
