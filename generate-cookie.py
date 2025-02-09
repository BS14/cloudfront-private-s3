import functools
import requests
import rsa
import datetime
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os
from dotenv import load_dotenv

# openssl genrsa -out private_key.pem 2048
# openssl rsa -pubout -in private_key.pem -out public_key.pem

# Getting the values from .env
load_dotenv()

# Ensure all required environment variables are present
required_env_vars = ['CF_URL', 'CF_PUBLIC_KEY_ID', 'CF_PRIVATE_KEY']
for var_name in required_env_vars:
    if not os.getenv(var_name):
        raise ValueError(f"No {var_name} found in environment variables.")


CLOUDFRONT_RESOURCE = os.getenv('CF_URL')
CLOUDFRONT_PUBLIC_KEY_ID = os.getenv('CF_PUBLIC_KEY_ID')
CLOUDFRONT_PRIVATE_KEY = os.getenv('CF_PRIVATE_KEY')
EXPIRES_AT = datetime.datetime.now() + datetime.timedelta(hours=1)

# Handling multiline private key correctly.
CLOUDFRONT_PRIVATE_KEY = CLOUDFRONT_PRIVATE_KEY.replace(
    '\\n', '\n').encode('utf-8')

# Load the private key using cryptography
private_key = serialization.load_pem_private_key(
    CLOUDFRONT_PRIVATE_KEY,
    password=None,
    backend=default_backend()
)

# Convert the private key to PCKS#1 format
private_key_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)


# load the private key using rsa
key = rsa.PrivateKey.load_pkcs1(private_key_pem)

# create a signer function that can sign message with the private key
rsa_signer = functools.partial(rsa.sign, priv_key=key, hash_method="SHA-1")


signer = CloudFrontSigner(CLOUDFRONT_PUBLIC_KEY_ID, rsa_signer)

resource_url = f"{CLOUDFRONT_RESOURCE}/pika.jpeg"

# generating policy
policy = signer.build_policy(resource_url, EXPIRES_AT).encode("utf8")
CLOUDFRONT_POLICY = signer._url_b64encode(policy).decode("utf8")
print("CLOUDFRONT_POLICY", CLOUDFRONT_POLICY)

signature = rsa_signer(policy)
CLOUDFRONT_SIGNATURE = signer._url_b64encode(signature).decode("utf8")
print("CLOUDFRONT_SIGNATURE", CLOUDFRONT_SIGNATURE)

COOKIES = {
    "CloudFront-Policy": CLOUDFRONT_POLICY,
    "CloudFront-Signature": CLOUDFRONT_SIGNATURE,
    "CloudFront-Key-Pair-Id": CLOUDFRONT_PUBLIC_KEY_ID,
}
print(COOKIES)

response = requests.get(resource_url, cookies=COOKIES)

print(response)
