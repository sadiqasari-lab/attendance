"""AES-256 encryption utilities for biometric embeddings."""
import base64
import os

import numpy as np
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from django.conf import settings


def _get_key() -> bytes:
    """Derive 32-byte AES key from the configured BIOMETRIC_ENCRYPTION_KEY."""
    key_b64 = settings.BIOMETRIC_ENCRYPTION_KEY
    raw = base64.b64decode(key_b64)
    if len(raw) < 32:
        raw = raw.ljust(32, b"\x00")
    return raw[:32]


def encrypt_embedding(embedding: np.ndarray) -> tuple[bytes, bytes]:
    """
    Encrypt a face embedding vector with AES-256-CBC.

    Returns:
        (encrypted_data, iv) tuple of bytes.
    """
    key = _get_key()
    iv = os.urandom(16)
    data = embedding.tobytes()

    padder = PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()

    return encrypted, iv


def decrypt_embedding(encrypted_data: bytes, iv: bytes) -> np.ndarray:
    """
    Decrypt AES-256-CBC encrypted face embedding.

    Returns:
        numpy array of float64 embedding values.
    """
    key = _get_key()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    unpadder = PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    return np.frombuffer(data, dtype=np.float64)
