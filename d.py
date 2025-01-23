from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom
from Crypto.Cipher import Blowfish
import pickle


def get_parts(output_file):
    all_data = []
    with open(output_file, "rb") as file:
        # Read and append each item from the file to the list
        while True:
            try:
                data = pickle.load(file)
                all_data.append(data)
            except EOFError as a:
                print(a)
                break
    return all_data


def aes_encrypt(input_file, key):
    iv = urandom(12)  # IV size for AES-GCM is 12 bytes
    cipher = AESGCM(key)
    with open(input_file, 'rb') as f_in:
        plaintext = f_in.read()
    ciphertext = cipher.encrypt(iv, plaintext, None)
    x = iv + ciphertext
    return x


def aes_decrypt(input_file, output_file, key):
    iv = input_file[:12]  # IV size for AES-GCM is 12 bytes
    ciphertext = input_file[12:]
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(iv, ciphertext, None)
    with open(output_file, 'ab') as f_out:
        f_out.write(plaintext)


def decrypt_file(input_file, output_file, key, algorithm):  # Adjust key size if necessary
    iv = input_file[:algorithm.block_size // 8]  # Extract IV from the data
    ciphertext = input_file[algorithm.block_size // 8:]  # Extract ciphertext from the data
    cipher = Cipher(algorithm(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7(algorithm.block_size).unpadder()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    with open(output_file, 'ab') as f_out:
        f_out.write(plaintext)


def encrypt_file(input_file, key, algorithm):  # Adjust key size if necessary
    iv = urandom(algorithm.block_size // 8)  # Generate IV based on block size
    cipher = Cipher(algorithm(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithm.block_size).padder()
    with open(input_file, 'rb') as f_in:
        plaintext = f_in.read()
    padded_plaintext = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
    x = iv + ciphertext
    return x


def blowfish_pad(data):
    length = 8 - (len(data) % 8)
    return data + bytes([length] * length)


def blowfish_encrypt(input_file, key):
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    plaintext = blowfish_pad(plaintext)
    ciphertext = cipher.encrypt(plaintext)
    return ciphertext


def blowfish_unpad(data):
    return data[:-data[-1]]


def blowfish_decrypt(input_file, output_file, key):
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    plaintext = cipher.decrypt(input_file)
    plaintext = blowfish_unpad(plaintext)
    with open(output_file, 'ab') as f:
        f.write(plaintext)


def arc4_encrypt(input_file, key):
    cipher = Cipher(algorithms.ARC4(key), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    with open(input_file, 'rb') as f_in:
        plaintext = f_in.read()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext


def arc4_decrypt(input_file, output_file, key):
    cipher = Cipher(algorithms.ARC4(key), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(input_file) + decryptor.finalize()
    with open(output_file, 'ab') as f_out:
        f_out.write(plaintext)
