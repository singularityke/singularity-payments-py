import base64
import re

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def encrypt_initiator_password(
    initiator_password: str,
    certificate_path: str,
) -> str:
    """
    Encrypt the initiator password using the provided certificate.

    Uses RSA PKCS#1 v1.5 padding, which is what the M-Pesa Daraja API expects
    for the ``SecurityCredential`` field. The certificate must be PEM-encoded
    (the Safaricom ``.cer`` files are).

    Args:
        initiator_password (str): The plaintext password to encrypt.
        certificate_path (str): Path to the PEM-encoded certificate file.

    Returns:
        str: The encrypted password, base64-encoded.

    Raises:
        Exception: If the certificate cannot be read/parsed or encryption fails.
    """
    try:
        with open(certificate_path, "rb") as f:
            cert_data = f.read()

        cert = x509.load_pem_x509_certificate(cert_data)
        public_key = cert.public_key()

        if not isinstance(public_key, rsa.RSAPublicKey):
            raise TypeError("Certificate does not contain an RSA public key")

        encrypted_bytes = public_key.encrypt(
            initiator_password.encode("utf-8"),
            padding.PKCS1v15(),
        )
        return base64.b64encode(encrypted_bytes).decode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to encrypt initiator password: {str(e)}") from e


def validate_security_credential(credential: str) -> bool:
    """
    Validate the format of a security credential string.

    Args:
        credential (str): The security credential to validate.

    Returns:
        bool: True if the credential is a valid base64 string and its length is
        greater than 100, False otherwise.
    """
    base64_regex = r"^[A-Za-z0-9+/]+={0,2}$"
    is_base64 = bool(re.match(base64_regex, credential))
    return is_base64 and len(credential) > 100
