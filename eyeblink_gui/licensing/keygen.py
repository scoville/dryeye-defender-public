"""Functions to generate and validate license keys"""
# TODO: we should use an automatic obfuscator to obfuscate the code and protect against software
# cracking
# See: https://piprogramming.org/articles/Ultimate-Introduction-to-cracking-Software-and-how-to-
#      protect-against-it--Reverse-Engineering-0000000022.html

import logging
import traceback
import base64
from argparse import ArgumentParser
from typing import Tuple

import ecdsa    # type: ignore[import]

LOGGER = logging.getLogger(__name__)

VERIFYING_KEY_STRING = "e3c77e79b005eb55b139b3d6a09b36364bf390071e0ac2b43f897d3ec769d4a7"


def generate_license_key(user_email: str, order_num: int, signing_key_string: str) -> str:
    """Generate a license key from a signing key

    :param user_email: the user email
    :param order_num: the order number
    :param signing_key_string: the signing key
    :return: the license key

    """
    signing_key = ecdsa.SigningKey.from_string(
        bytes.fromhex(signing_key_string),
        curve=ecdsa.Ed25519
    )
    data = f"{user_email}.{order_num}".encode()
    signature = signing_key.sign(data)

    data_encoded = base64.b64encode(data).decode()
    signature_encoded = base64.b64encode(signature).decode()

    return f"{data_encoded}.{signature_encoded}"


def validate_license_key(
        license_key: str,
        verifying_key_string: ecdsa.VerifyingKey = VERIFYING_KEY_STRING
) -> bool:
    """Validate a license key

    :param license_key: the license key
    :param verifying_key_string: the verifying key
    :return: True if the license key is valid, False otherwise or if an error occurred
    """
    try:
        verifying_key = ecdsa.VerifyingKey.from_string(
            bytes.fromhex(verifying_key_string),
            curve=ecdsa.Ed25519  # pylint: disable=no-member
        )
        data, signature = license_key.split(".")
        data_bytes = base64.b64decode(data)
        signature_bytes = base64.b64decode(signature)
        return bool(verifying_key.verify(signature_bytes, data_bytes))
    except Exception:
        LOGGER.warning("Handled the following user error:\n%s", traceback.format_exc())
        return False


def generate_sk_and_vk() -> Tuple[str, str]:
    """Generate a signing key and a verifying key

    :return: a tuple containing the signing key and the verifying key
    """
    signing_key = ecdsa.SigningKey.generate(curve=ecdsa.Ed25519)
    verifying_key = signing_key.get_verifying_key()
    return signing_key.hex(), verifying_key.hex()  # pylint: disable=no-member


def parse_args_and_generate_license_key() -> None:
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

    with open(args.signing_key, "r", encoding="utf-8") as signing_key_file:
        signing_key = args.signing_key = signing_key_file.read()
        license_key = generate_license_key(args.user_email, int(args.order_num), signing_key)
    print(license_key)


if __name__ == "__main__":
    parse_args_and_generate_license_key()
