import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)
from pyrogram import Client, filters 

# Replace with your own API ID, API Hash, Bot Token, and Owner's Username
API_ID = "24436545"
API_HASH = "afa5558d3561cb2241ed836088b56098"
BOT_TOKEN = "7837969823:AAG3Iwsls_LYKvBiv7tGd6mDP2kxnWhF6Kw"
OWNER_USERNAME = "Jon00897"  # Replace with your username (without @)

app = Client("encryption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# AES Encryption/Decryption
def aes_encrypt(key, plaintext):
    try:
        key = key.ljust(32)[:32].encode()  # Ensure key is 32 bytes
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext).decode()
    except Exception as e:
        return f"Encryption error: {e}"

def aes_decrypt(key, ciphertext):
    try:
        key = key.ljust(32)[:32].encode()
        ciphertext = base64.b64decode(ciphertext)
        iv, actual_ciphertext = ciphertext[:16], ciphertext[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext.decode()
    except Exception as e:
        return f"Decryption error: {e}"

# RSA Key Generation
def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode(), public_pem.decode()

# RSA Encryption/Decryption
def rsa_encrypt(public_key_pem, plaintext):
    try:
        public_key = load_pem_public_key(public_key_pem.encode(), backend=default_backend())
        ciphertext = public_key.encrypt(plaintext.encode(), PKCS1v15())
        return base64.b64encode(ciphertext).decode()
    except Exception as e:
        return f"RSA encryption error: {e}"

def rsa_decrypt(private_key_pem, ciphertext):
    try:
        private_key = load_pem_private_key(private_key_pem.encode(), password=None, backend=default_backend())
        ciphertext = base64.b64decode(ciphertext)
        plaintext = private_key.decrypt(ciphertext, PKCS1v15())
        return plaintext.decode()
    except Exception as e:
        return f"RSA decryption error: {e}"

# Base64 Encoding/Decoding
def base64_encode(data):
    return base64.b64encode(data.encode()).decode()

def base64_decode(data):
    try:
        return base64.b64decode(data).decode()
    except Exception as e:
        return f"Base64 decoding error: {e}"

# Bot Handlers
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply(f"""Hello! I'm your encryption bot. Here are my commands:

/aes_encrypt [key] [message] - Encrypt a message with AES
/aes_decrypt [key] [encrypted_message] - Decrypt an AES-encrypted message
/rsa_keys - Generate RSA public and private keys
/rsa_encrypt [public_key] [message] - Encrypt a message with RSA
/rsa_decrypt [private_key] [encrypted_message] - Decrypt an RSA-encrypted message
/base64_encode [message] - Encode a message with Base64
/base64_decode [encoded_message] - Decode a Base64-encoded message

For assistance, contact the owner: @{OWNER_USERNAME}.
""")

@app.on_message(filters.new_chat_members)
def welcome(client, message):
    for member in message.new_chat_members:
        message.reply(f"Welcome {member.mention}! I'm here to assist with encryption and decryption tasks.\n\nFor more details, contact my owner: @{OWNER_USERNAME}.")

@app.on_message(filters.command("aes_encrypt"))
def aes_encrypt_command(client, message):
    try:
        _, key, plaintext = message.text.split(maxsplit=2)
        encrypted_message = aes_encrypt(key, plaintext)
        message.reply(f"Encrypted message: {encrypted_message}")
    except Exception as e:
        message.reply(f"Error: {e}")

@app.on_message(filters.command("aes_decrypt"))
def aes_decrypt_command(client, message):
    try:
        _, key, ciphertext = message.text.split(maxsplit=2)
        decrypted_message = aes_decrypt(key, ciphertext)
        message.reply(f"Decrypted message: {decrypted_message}")
    except Exception as e:
        message.reply(f"Error: {e}")

@app.on_message(filters.command("rsa_keys"))
def rsa_keys_command(client, message):
    private_key, public_key = generate_rsa_keys()
    message.reply(f"Private Key:\n{private_key}\n\nPublic Key:\n{public_key}")

@app.on_message(filters.command("rsa_encrypt"))
def rsa_encrypt_command(client, message):
    try:
        _, public_key, plaintext = message.text.split(maxsplit=2)
        encrypted_message = rsa_encrypt(public_key, plaintext)
        message.reply(f"Encrypted message: {encrypted_message}")
    except Exception as e:
        message.reply(f"Error: {e}")

@app.on_message(filters.command("rsa_decrypt"))
def rsa_decrypt_command(client, message):
    try:
        _, private_key, ciphertext = message.text.split(maxsplit=2)
        decrypted_message = rsa_decrypt(private_key, ciphertext)
        message.reply(f"Decrypted message: {decrypted_message}")
    except Exception as e:
        message.reply(f"Error: {e}")

@app.on_message(filters.command("base64_encode"))
def base64_encode_command(client, message):
    try:
        _, data = message.text.split(maxsplit=1)
        encoded_message = base64_encode(data)
        message.reply(f"Encoded message: {encoded_message}")
    except Exception as e:
        message.reply(f"Error: {e}")

@app.on_message(filters.command("base64_decode"))
def base64_decode_command(client, message):
    try:
        _, data = message.text.split(maxsplit=1)
        decoded_message = base64_decode(data)
        message.reply(f"Decoded message: {decoded_message}")
    except Exception as e:
        message.reply(f"Error: {e}")

if __name__ == "__main__":
    app.run()
    