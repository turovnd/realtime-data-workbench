import hashlib


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
