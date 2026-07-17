import base64,hashlib,hmac,logging,os
from cryptography.fernet import Fernet
from app.core.config import settings
logger=logging.getLogger(__name__)
class VinProtector:
    def __init__(self):
        key=settings.vin_encryption_key.encode() if settings.vin_encryption_key else Fernet.generate_key()
        try: self.fernet=Fernet(key)
        except ValueError: self.fernet=Fernet(base64.urlsafe_b64encode(hashlib.sha256(key).digest()))
        self.secret=(settings.vin_fingerprint_secret or os.urandom(32).hex()).encode()
        self.ephemeral=not(settings.vin_encryption_key and settings.vin_fingerprint_secret)
    def encrypt(self,vin:str)->str: return self.fernet.encrypt(vin.encode()).decode()
    def decrypt(self,value:str)->str: return self.fernet.decrypt(value.encode()).decode()
    def fingerprint(self,vin:str)->str: return hmac.new(self.secret,vin.encode(),hashlib.sha256).hexdigest()
protector=VinProtector()
