import logging
import traceback
import base64

import ecdsa

LOGGER = logging.getLogger(__name__)


def generate_key(data, signing_key):
    """Generate a license key from a signing key

    :param data: the data to sign
    :param signing_key: the signing key
    :return: the license key
    """
    signature = signing_key.sign(data)

    data_encoded = base64.b64encode(data).decode()
    signature_encoded = base64.b64encode(signature).decode()

    return f"{data_encoded}.{signature_encoded}"


def validate_key(license_key, verifying_key):
    """Validate a license key

    :param license_key: the license key
    :param verifying_key: the verifying key
    :return: True if the license key is valid, False otherwise
    """
    try:
        data, signature = license_key.split(".")
        data = base64.b64decode(data)
        signature = base64.b64decode(signature)
        return verifying_key.verify(signature, data)
    except Exception:
        LOGGER.warning("Handled the following user error:\n%s", traceback.format_exc())
        return False


sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) 
vk = sk.get_verifying_key()

license_key = generate_key(b"hello world", sk)
print(f"{license_key}")

isSignatureValid = validate_key("fsdf.scdf", vk)
print(f"{isSignatureValid=}")