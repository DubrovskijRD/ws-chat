import hashlib


def hash_password(password: str, salt: str = None):
    """ Хеширует пароль с солью """

    enc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return enc.hex()
