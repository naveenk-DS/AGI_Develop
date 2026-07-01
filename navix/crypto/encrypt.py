import os, json, subprocess
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

def get_machine_id() -> str:
    try:
        import uuid
        return str(uuid.getnode())
    except:
        return "default-machine-id-fallback"

def derive_key(machine_id: str) -> bytes:
    kdf = Scrypt(
        salt=b"myaiproduct-salt-v1",
        length=32, n=2**14, r=8, p=1,
        backend=default_backend()
    )
    return kdf.derive(machine_id.encode())

_KEY = derive_key(get_machine_id())

def encrypt(data: dict) -> bytes:
    aesgcm = AESGCM(_KEY)
    iv = os.urandom(12)
    ct = aesgcm.encrypt(iv, json.dumps(data).encode(), None)
    return iv + ct

def decrypt(payload: bytes) -> dict:
    aesgcm = AESGCM(_KEY)
    iv, ct = payload[:12], payload[12:]
    plain = aesgcm.decrypt(iv, ct, None)
    return json.loads(plain.decode())