"""
encryption.py — DBファイルの暗号化・復号
使用ライブラリ: cryptography (pip install cryptography)

仕組み:
  - パスワードから PBKDF2 で鍵を生成し、Fernet（AES-128-CBC）で暗号化
  - 暗号化ファイル: ~/.cashflow_app/.data.enc
  - ソルトファイル:  ~/.cashflow_app/.salt
  - アプリ起動時に復号 → 終了時に再暗号化
"""
import os
import base64
from pathlib import Path

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

BASE      = Path.home() / "cashflow_app"
SALT_FILE = BASE / ".salt"
ENC_FILE  = BASE / ".data.enc"


def is_available() -> bool:
    """cryptographyライブラリが使えるか"""
    return CRYPTO_AVAILABLE


def is_enabled() -> bool:
    """暗号化が有効か"""
    return ENC_FILE.exists() and SALT_FILE.exists()


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _encrypt_to_file(db_path: Path, password: str, salt: bytes):
    key  = _derive_key(password, salt)
    data = db_path.read_bytes()
    ENC_FILE.write_bytes(Fernet(key).encrypt(data))


def setup(db_path: Path, password: str):
    """暗号化を初めて有効にする（既存DBを暗号化）"""
    BASE.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    SALT_FILE.write_bytes(salt)
    _encrypt_to_file(db_path, password, salt)


def unlock(db_path: Path, password: str) -> bool:
    """起動時: 暗号化DBを復号して db_path に書き出す。失敗したら False"""
    if not is_enabled():
        return True
    try:
        salt = SALT_FILE.read_bytes()
        key  = _derive_key(password, salt)
        data = Fernet(key).decrypt(ENC_FILE.read_bytes())
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_bytes(data)
        return True
    except (InvalidToken, Exception):
        return False


def lock(db_path: Path, password: str):
    """終了時: db_path を再暗号化"""
    if not is_enabled() or not db_path.exists():
        return
    salt = SALT_FILE.read_bytes()
    _encrypt_to_file(db_path, password, salt)


def change_password(db_path: Path, old_pw: str, new_pw: str) -> bool:
    """パスワード変更"""
    if not unlock(db_path, old_pw):
        return False
    salt = os.urandom(16)
    SALT_FILE.write_bytes(salt)
    _encrypt_to_file(db_path, new_pw, salt)
    return True


def disable(db_path: Path, password: str) -> bool:
    """暗号化を無効化（復号してファイルを削除）"""
    if not unlock(db_path, password):
        return False
    ENC_FILE.unlink(missing_ok=True)
    SALT_FILE.unlink(missing_ok=True)
    return True
