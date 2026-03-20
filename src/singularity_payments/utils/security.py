import base64
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import re


def encrypt_initiator_password(
        initiator_password: str,
        certificate_path: str,
        private_key_path: str
) -> str:
    try:
        with open(certificate_path, "rb") as f:
            cert_data = f.file.read()
            cert = x509.load_pem_x509_certificate(cert_data)
            public_key = cert.public_key()
            encrypted_bytes = public_key.encrypt(
                initiator_password.encode('utf-8'),
                padding.PKCS11v15()
            )

            return base64.b64encode(encrypted_bytes).decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to encrypt initiator password: {str(e)}")



def validate_security_credential(credential:str)->bool:
    """
    Helper to validate security credential format
    Args:
        credential(str): security credential to validate

    Returns
        is_base64(bool): True if the credential is a valid base64 string and length of credentials is greater than 100, False otherwise
    
    """
    base64_regex = r"^[A-Za-z0-9+/]+={0,2}$"
    is_base64 = bool(re.match(base64_regex, credential))
    return is_base64 and len(credential)>100