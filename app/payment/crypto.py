import binascii, os
from flask import current_app
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _get_aesgcm():
    key_hex = current_app.config['PAYMENT_ENC_KEY']
    key = binascii.unhexlify(key_hex)
    return AESGCM(key)

def encrypt_pan(pan: str) -> dict:
    aesgcm = _get_aesgcm()
    nonce  = os.urandom(12)
    ct     = aesgcm.encrypt(nonce, pan.encode(), None)
    return {
        'nonce': nonce,
        'ciphertext': ct,
        'key_version': None  
    }


def decrypt_pan(nonce: bytes, ciphertext: bytes) -> str:
    aesgcm = _get_aesgcm()
    return aesgcm.decrypt(nonce, ciphertext, None).decode()

def luhn_checksum(card_number: str) -> bool:
    """Return True if card_number passes the Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0
