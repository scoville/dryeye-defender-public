import logging
import traceback
import base64

import ecdsa

LOGGER = logging.getLogger(__name__)


def generate_key(data: bytes, signing_key: ecdsa.SigningKey):
    """Generate a license key from a signing key

    :param data: the data to sign
    :param signing_key: the signing key
    :return: the license key
    """
    signature = signing_key.sign(data)

    data_encoded = base64.b64encode(data).decode()
    signature_encoded = base64.b64encode(signature).decode()

    return f"{data_encoded}.{signature_encoded}"


def validate_key(license_key: str, verifying_key: ecdsa.VerifyingKey):
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


sk = ecdsa.SigningKey.generate(curve=ecdsa.Ed25519) 
vk = sk.get_verifying_key()

sk_string = sk.to_string().hex()
vk_string = vk.to_string().hex()

# TODO: export signing key and verifying key to files

# TODO: read signing key from file

sk = ecdsa.SigningKey.from_string(bytes.fromhex(sk_string), curve=ecdsa.Ed25519)
license_key = generate_key(b"hello@world.com", sk)
print(f"{license_key}")

# TODO: read verifying key from file

vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(vk_string), curve=ecdsa.Ed25519)
isSignatureValid = validate_key(license_key, vk)
print(f"{isSignatureValid=}")

# TODO: we should use an automatic obfuscator to obfuscate the code and protect against software cracking
# See: https://piprogramming.org/articles/Ultimate-Introduction-to-cracking-Software-and-how-to-protect-against-it--Reverse-Engineering-0000000022.html
