import os
from dotenv import load_dotenv
import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from botocore.signers import CloudFrontSigner


load_dotenv()  # takes enviroment variable from .env

# Getting the values from .env
load_dotenv()

# Ensure all required environment variables are present
required_env_vars = ['CF_URL', 'CF_PUBLIC_KEY_ID', 'CF_PRIVATE_KEY']
for var_name in required_env_vars:
    if not os.getenv(var_name):
        raise ValueError(f"No {var_name} found in environment variables.")

CF_PUBLIC_KEY_ID = os.getenv('CF_PUBLIC_KEY_ID')
CF_URL = os.getenv('CF_URL')
CF_PRIVATE_KEY = os.getenv('CF_PRIVATE_KEY')
EXPIRES_AT = datetime.datetime.now() + datetime.timedelta(hours=1)


def rsa_signer(message):
    CF_PRIVATE_KEY = os.getenv('CF_PRIVATE_KEY')

    if not CF_PRIVATE_KEY:
        raise ValueError("No private key found in enviroment variable.")

    private_key_byte = CF_PRIVATE_KEY.encode('utf-8')

    private_key = serialization.load_pem_private_key(
        private_key_byte,
        password=None,
        backend=default_backend()
    )

    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())


# expiry_date = datetime.datetime(2024, 5, 28)

cloudfront_signer = CloudFrontSigner(CF_PUBLIC_KEY_ID, rsa_signer)

# Construct the full URL for the specific object.
object_url = f"{CF_URL}/pika.jpeg"

signed_url = cloudfront_signer.generate_presigned_url(
    object_url, date_less_than=EXPIRES_AT
)


# signed_url = cloudfront_signer.generate_presigned_url(
#    CF_URL, date_less_than=expiry_date
# )

print(signed_url)
