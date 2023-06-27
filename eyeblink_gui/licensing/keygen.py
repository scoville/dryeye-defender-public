"""Functions to generate and validate license keys"""
# TODO: we should use an automatic obfuscator to obfuscate the code and protect against software cracking
# See: https://piprogramming.org/articles/Ultimate-Introduction-to-cracking-Software-and-how-to-protect-against-it--Reverse-Engineering-0000000022.html

import logging
import traceback
import base64
from argparse import ArgumentParser

import ecdsa

LOGGER = logging.getLogger(__name__)

# Verifying key
VERIFYING_KEY_STRING = "e3c77e79b005eb55b139b3d6a09b36364bf390071e0ac2b43f897d3ec769d4a7"


def generate_license_key(user_email: str, order_num: int, signing_key: str):
    """Generate a license key from a signing key

    :param user_email: the user email
    :param order_num: the order number
    :param signing_key: the signing key
    :return: the license key

    """
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(signing_key), curve=ecdsa.Ed25519)
    data = f"{user_email}.{order_num}".encode()
    signature = sk.sign(data)

    data_encoded = base64.b64encode(data).decode()
    signature_encoded = base64.b64encode(signature).decode()

    return f"{data_encoded}.{signature_encoded}"


def validate_license_key(license_key: str, verifying_key: ecdsa.VerifyingKey=VERIFYING_KEY_STRING):
    """Validate a license key

    :param license_key: the license key
    :param verifying_key: the verifying key
    :return: True if the license key is valid, False otherwise or if an error occurred
    """
    try:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(verifying_key), curve=ecdsa.Ed25519)
        data, signature = license_key.split(".")
        data = base64.b64decode(data)
        signature = base64.b64decode(signature)
        return vk.verify(signature, data)
    except Exception:
        LOGGER.warning("Handled the following user error:\n%s", traceback.format_exc())
        return False


def generate_sk_and_vk():
    """Generate a signing key and a verifying key

    :return: a tuple containing the signing key and the verifying key
    """
    sk = ecdsa.SigningKey.generate(curve=ecdsa.Ed25519)
    vk = sk.get_verifying_key()
    return sk.hex(), vk.hex()


def parse_args_and_generate_license_key():
    """Parses arguments and generates a license key.
    """
    parser = ArgumentParser("Generate a license key")
    parser.add_argument("--user_email",
                        "-ue",
                        type=str,
                        required=True,
                        help="email of the user")
    parser.add_argument("--order_num",
                        "-on",
                        type=int,
                        required=True,
                        help="order number")
    parser.add_argument("--signing_key",
                        "-sk",
                        type=str,
                        required=True,
                        help="file path of the signing key")

    args = parser.parse_args()

    with open(args.signing_key, "r") as f:
        sk = args.signing_key = f.read()
        license_key = generate_license_key(args.user_email, args.order_num, args.signing_key)
    return license_key


if __name__ == "__main__":
    parse_args_and_generate_license_key()
