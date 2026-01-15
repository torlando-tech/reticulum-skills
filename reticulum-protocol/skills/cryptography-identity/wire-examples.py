"""
Wire Format Examples - Cryptography & Identity

Byte-level examples for identity creation, token encryption, and key derivation.
These examples demonstrate the exact cryptographic operations and wire format.
"""

import hashlib
import os
import hmac as std_hmac
import struct
from math import ceil

# Use real cryptography library for X25519/Ed25519
try:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives import serialization
    USE_REAL_CRYPTO = True
except ImportError:
    USE_REAL_CRYPTO = False
    print("Warning: cryptography library not available, using mock implementation")
    print("Install with: pip install cryptography")

# ============================================================================
# MOCK CRYPTOGRAPHIC PRIMITIVES (for demonstration)
# ============================================================================

class MockX25519PrivateKey:
    """Mock X25519 private key for demonstration."""
    def __init__(self, private_bytes):
        if len(private_bytes) != 32:
            raise ValueError("X25519 private key must be 32 bytes")
        self.private_bytes = private_bytes
        # Store a scalar representation (just use first 32 bits as simple scalar)
        self.scalar = int.from_bytes(private_bytes[:4], 'big')

    def public_key(self):
        # In reality, this derives public from private via curve25519 scalar multiplication: P = s*G
        # Mock: Multiply scalar by a fixed "generator" and hash
        # This creates a deterministic public key from the private key
        generator = b"X25519_GENERATOR_POINT_MOCK"
        # Simulate scalar multiplication: pub = scalar * G
        pub_bytes = hashlib.sha256(
            self.private_bytes + generator + str(self.scalar).encode()
        ).digest()[:32]
        return MockX25519PublicKey(pub_bytes, generator)

    def exchange(self, peer_public_key):
        # In reality, this performs ECDH: shared = scalar_mult(my_private, peer_public)
        # Real ECDH property: my_scalar * (peer_scalar * G) = peer_scalar * (my_scalar * G)
        # Both operations yield: (my_scalar * peer_scalar) * G

        # Mock: Simulate this by combining private with peer's public deterministically
        # The trick is to extract something from peer_public that, when combined with
        # our private, produces the same result as peer's private combined with our public

        # Use the peer's public key bytes directly (which encodes peer_scalar * G)
        # and "multiply" by our scalar
        peer_pub_bytes = peer_public_key.public_bytes()

        # Simulate scalar multiplication: our_scalar * peer_public_point
        # In the mock, we hash (our_private || peer_public) to create shared secret
        shared = hashlib.sha256(
            self.private_bytes + peer_pub_bytes + b"ecdh_exchange"
        ).digest()[:32]
        return shared

class MockX25519PublicKey:
    """Mock X25519 public key for demonstration."""
    def __init__(self, public_bytes, generator=None):
        if len(public_bytes) != 32:
            raise ValueError("X25519 public key must be 32 bytes")
        self._public_bytes = public_bytes
        self.generator = generator or b"X25519_GENERATOR_POINT_MOCK"

    def public_bytes(self):
        return self._public_bytes

class MockEd25519PrivateKey:
    """Mock Ed25519 private key for demonstration."""
    def __init__(self, private_bytes):
        if len(private_bytes) != 32:
            raise ValueError("Ed25519 private key must be 32 bytes")
        self.private_bytes = private_bytes

    def public_key(self):
        # Mock: Use hash to simulate public key derivation
        pub_bytes = hashlib.sha256(self.private_bytes + b"ed25519_pub").digest()[:32]
        return MockEd25519PublicKey(pub_bytes)

    def sign(self, message):
        # In reality, this performs Ed25519 signature
        # Mock: Create 64-byte signature using HMAC
        sig_part1 = std_hmac.new(self.private_bytes, message, hashlib.sha256).digest()
        sig_part2 = std_hmac.new(self.private_bytes, sig_part1, hashlib.sha256).digest()
        return sig_part1 + sig_part2  # 64 bytes

class MockEd25519PublicKey:
    """Mock Ed25519 public key for demonstration."""
    def __init__(self, public_bytes):
        if len(public_bytes) != 32:
            raise ValueError("Ed25519 public key must be 32 bytes")
        self._public_bytes = public_bytes

    def public_bytes(self):
        return self._public_bytes

    def verify(self, signature, message):
        # Mock: Would verify Ed25519 signature
        # For demo, just check signature length
        if len(signature) != 64:
            raise ValueError("Invalid signature")
        return True

# ============================================================================
# HKDF IMPLEMENTATION (RFC 5869)
# ============================================================================

def hkdf(length, derive_from, salt=None, context=None):
    """
    HKDF key derivation function (RFC 5869).

    Args:
        length: Output key length in bytes
        derive_from: Input key material (IKM)
        salt: Optional salt (defaults to 32 zero bytes)
        context: Optional context info

    Returns:
        Derived key bytes
    """
    hash_len = 32  # SHA-256 output length

    if length is None or length < 1:
        raise ValueError("Invalid output key length")

    if derive_from is None or derive_from == "":
        raise ValueError("Cannot derive key from empty input material")

    if salt is None or len(salt) == 0:
        salt = bytes([0] * hash_len)

    if context is None:
        context = b""

    # Extract phase: PRK = HMAC-SHA256(salt, IKM)
    pseudorandom_key = std_hmac.new(salt, derive_from, hashlib.sha256).digest()

    # Expand phase: Generate output key material
    block = b""
    derived = b""

    for i in range(ceil(length / hash_len)):
        # T(i) = HMAC-SHA256(PRK, T(i-1) | context | counter)
        block = std_hmac.new(
            pseudorandom_key,
            block + context + bytes([(i + 1) % (0xFF + 1)]),
            hashlib.sha256
        ).digest()
        derived += block

    return derived[:length]

# ============================================================================
# PKCS7 PADDING
# ============================================================================

def pkcs7_pad(data, block_size=16):
    """
    Apply PKCS7 padding to data.

    Args:
        data: Data to pad
        block_size: Block size (16 for AES)

    Returns:
        Padded data
    """
    padding_length = block_size - (len(data) % block_size)
    if padding_length == 0:
        padding_length = block_size
    padding = bytes([padding_length] * padding_length)
    return data + padding

def pkcs7_unpad(data):
    """
    Remove PKCS7 padding from data.

    Args:
        data: Padded data

    Returns:
        Unpadded data
    """
    if len(data) == 0:
        raise ValueError("Cannot unpad empty data")
    padding_length = data[-1]
    if padding_length > len(data) or padding_length > 16:
        raise ValueError("Invalid padding")
    # Verify all padding bytes are correct
    for i in range(padding_length):
        if data[-(i + 1)] != padding_length:
            raise ValueError("Invalid padding")
    return data[:-padding_length]

# ============================================================================
# AES-256-CBC MOCK
# ============================================================================

def aes_256_cbc_encrypt(plaintext, key, iv):
    """
    Mock AES-256-CBC encryption.
    Real implementation would use cryptography.hazmat.primitives.ciphers
    """
    # Mock: XOR plaintext with key material for demonstration
    # Real AES-256-CBC would use proper block cipher
    key_material = key + iv  # 48 bytes
    ciphertext = bytearray()
    for i, byte in enumerate(plaintext):
        ciphertext.append(byte ^ key_material[i % len(key_material)])
    return bytes(ciphertext)

def aes_256_cbc_decrypt(ciphertext, key, iv):
    """
    Mock AES-256-CBC decryption.
    Real implementation would use cryptography.hazmat.primitives.ciphers
    """
    # Mock: XOR ciphertext with key material (same as encrypt for demo)
    return aes_256_cbc_encrypt(ciphertext, key, iv)

# ============================================================================
# IDENTITY CREATION
# ============================================================================

def create_identity():
    """
    Create a new Reticulum identity with 512-bit keypair.

    Returns:
        Dictionary with identity components
    """
    print("=" * 70)
    print("CREATING IDENTITY")
    print("=" * 70)

    # Generate encryption keypair (X25519)
    if USE_REAL_CRYPTO:
        enc_prv = X25519PrivateKey.generate()
        enc_prv_bytes = enc_prv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        enc_pub = enc_prv.public_key()
        enc_pub_bytes = enc_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    else:
        enc_prv_bytes = os.urandom(32)
        enc_prv = MockX25519PrivateKey(enc_prv_bytes)
        enc_pub = enc_prv.public_key()
        enc_pub_bytes = enc_pub.public_bytes()

    print(f"\nEncryption Private Key (X25519): {enc_prv_bytes.hex()}")
    print(f"Encryption Public Key (X25519):  {enc_pub_bytes.hex()}")

    # Generate signing keypair (Ed25519)
    if USE_REAL_CRYPTO:
        sig_prv = Ed25519PrivateKey.generate()
        sig_prv_bytes = sig_prv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        sig_pub = sig_prv.public_key()
        sig_pub_bytes = sig_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    else:
        sig_prv_bytes = os.urandom(32)
        sig_prv = MockEd25519PrivateKey(sig_prv_bytes)
        sig_pub = sig_prv.public_key()
        sig_pub_bytes = sig_pub.public_bytes()

    print(f"\nSigning Private Key (Ed25519): {sig_prv_bytes.hex()}")
    print(f"Signing Public Key (Ed25519):  {sig_pub_bytes.hex()}")

    # Combine keys
    private_key = enc_prv_bytes + sig_prv_bytes  # 64 bytes
    public_key = enc_pub_bytes + sig_pub_bytes   # 64 bytes

    print(f"\nCombined Private Key (512 bits): {private_key.hex()}")
    print(f"Combined Public Key (512 bits):  {public_key.hex()}")

    # Calculate identity hash (truncated SHA-256 of public key)
    full_hash = hashlib.sha256(public_key).digest()
    identity_hash = full_hash[:16]  # 128 bits

    print(f"\nFull SHA-256 Hash:    {full_hash.hex()}")
    print(f"Identity Hash (128b): {identity_hash.hex()}")
    print(f"Identity Hash Hex:    <{identity_hash.hex()}>")

    print("\nIdentity Properties:")
    print(f"  KEYSIZE: 512 bits (64 bytes)")
    print(f"  HASHLENGTH: 256 bits (32 bytes)")
    print(f"  TRUNCATED_HASHLENGTH: 128 bits (16 bytes)")
    print(f"  SIGLENGTH: 512 bits (64 bytes)")
    print()

    return {
        'enc_prv': enc_prv,
        'enc_pub': enc_pub,
        'enc_prv_bytes': enc_prv_bytes,
        'enc_pub_bytes': enc_pub_bytes,
        'sig_prv': sig_prv,
        'sig_pub': sig_pub,
        'sig_prv_bytes': sig_prv_bytes,
        'sig_pub_bytes': sig_pub_bytes,
        'private_key': private_key,
        'public_key': public_key,
        'identity_hash': identity_hash
    }

# ============================================================================
# TOKEN ENCRYPTION
# ============================================================================

def encrypt_token(plaintext, recipient_identity):
    """
    Encrypt data using identity encryption (ECDH + HKDF + AES-256-CBC).

    Args:
        plaintext: Data to encrypt (bytes)
        recipient_identity: Recipient's identity dict

    Returns:
        Encrypted token bytes
    """
    print("=" * 70)
    print("TOKEN ENCRYPTION")
    print("=" * 70)

    print(f"\nPlaintext ({len(plaintext)} bytes): {plaintext}")
    print(f"Plaintext hex: {plaintext.hex()}")

    # Step 1: Generate ephemeral keypair
    print("\n--- Step 1: Generate Ephemeral Keypair ---")
    if USE_REAL_CRYPTO:
        ephemeral_prv = X25519PrivateKey.generate()
        ephemeral_prv_bytes = ephemeral_prv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        ephemeral_pub = ephemeral_prv.public_key()
        ephemeral_pub_bytes = ephemeral_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    else:
        ephemeral_prv_bytes = os.urandom(32)
        ephemeral_prv = MockX25519PrivateKey(ephemeral_prv_bytes)
        ephemeral_pub = ephemeral_prv.public_key()
        ephemeral_pub_bytes = ephemeral_pub.public_bytes()

    print(f"Ephemeral Private Key: {ephemeral_prv_bytes.hex()}")
    print(f"Ephemeral Public Key:  {ephemeral_pub_bytes.hex()}")

    # Step 2: Perform ECDH key exchange
    print("\n--- Step 2: ECDH Key Exchange ---")
    recipient_pub = recipient_identity['enc_pub']
    if USE_REAL_CRYPTO:
        recipient_pub_bytes = recipient_identity['enc_pub_bytes']
        print(f"Recipient Public Key: {recipient_pub_bytes.hex()}")
        shared_secret = ephemeral_prv.exchange(recipient_pub)
    else:
        shared_secret = ephemeral_prv.exchange(recipient_pub)
        print(f"Recipient Public Key: {recipient_pub.public_bytes().hex()}")

    print(f"Shared Secret (32B):  {shared_secret.hex()}")

    # Step 3: Derive keys with HKDF
    print("\n--- Step 3: HKDF Key Derivation ---")
    salt = recipient_identity['identity_hash']
    print(f"Salt (identity hash): {salt.hex()}")
    print(f"Context: None")
    print(f"Derive length: 64 bytes")

    derived_key = hkdf(
        length=64,
        derive_from=shared_secret,
        salt=salt,
        context=None
    )

    signing_key = derived_key[:32]
    encryption_key = derived_key[32:]

    print(f"\nDerived Key (64B):  {derived_key.hex()}")
    print(f"Signing Key (32B):  {signing_key.hex()}")
    print(f"Encryption Key (32B): {encryption_key.hex()}")

    # Step 4: Pad plaintext with PKCS7
    print("\n--- Step 4: PKCS7 Padding ---")
    padded_plaintext = pkcs7_pad(plaintext, block_size=16)
    padding_length = len(padded_plaintext) - len(plaintext)

    print(f"Original length: {len(plaintext)} bytes")
    print(f"Padding length: {padding_length} bytes")
    print(f"Padded length: {len(padded_plaintext)} bytes")
    print(f"Padded plaintext: {padded_plaintext.hex()}")

    # Step 5: Generate IV and encrypt with AES-256-CBC
    print("\n--- Step 5: AES-256-CBC Encryption ---")
    iv = os.urandom(16)
    print(f"IV (16B): {iv.hex()}")

    ciphertext = aes_256_cbc_encrypt(padded_plaintext, encryption_key, iv)
    print(f"Ciphertext ({len(ciphertext)}B): {ciphertext.hex()}")

    # Step 6: Calculate HMAC
    print("\n--- Step 6: HMAC Calculation ---")
    signed_parts = iv + ciphertext
    print(f"Signed parts ({len(signed_parts)}B): IV || Ciphertext")

    hmac_tag = std_hmac.new(signing_key, signed_parts, hashlib.sha256).digest()
    print(f"HMAC Tag (32B): {hmac_tag.hex()}")

    # Step 7: Assemble complete token
    print("\n--- Step 7: Assemble Token ---")
    token_without_ephemeral = iv + ciphertext + hmac_tag
    complete_token = ephemeral_pub_bytes + token_without_ephemeral

    print(f"\nToken Structure:")
    print(f"  [Ephemeral Pub: {len(ephemeral_pub_bytes)}B]")
    print(f"  [IV: {len(iv)}B]")
    print(f"  [Ciphertext: {len(ciphertext)}B]")
    print(f"  [HMAC: {len(hmac_tag)}B]")
    print(f"  Total: {len(complete_token)} bytes")

    print(f"\nComplete Token: {complete_token.hex()}")
    print(f"\nOverhead Analysis:")
    print(f"  Ephemeral pub: 32 bytes")
    print(f"  IV: 16 bytes")
    print(f"  HMAC: 32 bytes")
    print(f"  Padding: {padding_length} bytes")
    print(f"  Total overhead: {32 + 16 + 32 + padding_length} bytes")
    print(f"  TOKEN_OVERHEAD constant: 48 bytes (IV + HMAC)")
    print()

    return {
        'token': complete_token,
        'ephemeral_pub': ephemeral_pub_bytes,
        'iv': iv,
        'ciphertext': ciphertext,
        'hmac_tag': hmac_tag,
        'shared_secret': shared_secret,
        'signing_key': signing_key,
        'encryption_key': encryption_key
    }

# ============================================================================
# TOKEN DECRYPTION
# ============================================================================

def decrypt_token(token_bytes, recipient_identity):
    """
    Decrypt token using identity private key.

    Args:
        token_bytes: Complete encrypted token
        recipient_identity: Recipient's identity dict (with private keys)

    Returns:
        Decrypted plaintext
    """
    print("=" * 70)
    print("TOKEN DECRYPTION")
    print("=" * 70)

    print(f"\nReceived Token ({len(token_bytes)}B): {token_bytes.hex()}")

    # Step 1: Extract ephemeral public key
    print("\n--- Step 1: Extract Ephemeral Public Key ---")
    if len(token_bytes) < 32:
        raise ValueError("Token too short")

    peer_pub_bytes = token_bytes[:32]
    token_data = token_bytes[32:]

    print(f"Ephemeral Public Key: {peer_pub_bytes.hex()}")
    print(f"Token data length: {len(token_data)} bytes")

    if USE_REAL_CRYPTO:
        peer_pub = X25519PublicKey.from_public_bytes(peer_pub_bytes)
    else:
        peer_pub = MockX25519PublicKey(peer_pub_bytes)

    # Step 2: Perform ECDH with recipient's private key
    print("\n--- Step 2: ECDH Key Exchange ---")
    recipient_prv = recipient_identity['enc_prv']
    recipient_prv_bytes = recipient_identity['enc_prv_bytes']
    shared_secret = recipient_prv.exchange(peer_pub)

    print(f"Recipient Private Key: {recipient_prv_bytes.hex()}")
    print(f"Shared Secret: {shared_secret.hex()}")

    # Step 3: Derive keys with HKDF (same as encryption)
    print("\n--- Step 3: HKDF Key Derivation ---")
    salt = recipient_identity['identity_hash']

    derived_key = hkdf(
        length=64,
        derive_from=shared_secret,
        salt=salt,
        context=None
    )

    signing_key = derived_key[:32]
    encryption_key = derived_key[32:]

    print(f"Derived Key: {derived_key.hex()}")
    print(f"Signing Key: {signing_key.hex()}")
    print(f"Encryption Key: {encryption_key.hex()}")

    # Step 4: Extract token components
    print("\n--- Step 4: Extract Token Components ---")
    if len(token_data) < 48:  # Minimum: 16B IV + 32B HMAC
        raise ValueError("Token data too short")

    iv = token_data[:16]
    ciphertext = token_data[16:-32]
    received_hmac = token_data[-32:]

    print(f"IV: {iv.hex()}")
    print(f"Ciphertext ({len(ciphertext)}B): {ciphertext.hex()}")
    print(f"HMAC: {received_hmac.hex()}")

    # Step 5: Verify HMAC
    print("\n--- Step 5: Verify HMAC ---")
    signed_parts = iv + ciphertext
    expected_hmac = std_hmac.new(signing_key, signed_parts, hashlib.sha256).digest()

    print(f"Expected HMAC: {expected_hmac.hex()}")
    print(f"Received HMAC: {received_hmac.hex()}")
    print(f"HMAC Valid: {expected_hmac == received_hmac}")

    if expected_hmac != received_hmac:
        raise ValueError("Token HMAC was invalid")

    # Step 6: Decrypt with AES-256-CBC
    print("\n--- Step 6: AES-256-CBC Decryption ---")
    padded_plaintext = aes_256_cbc_decrypt(ciphertext, encryption_key, iv)
    print(f"Padded plaintext: {padded_plaintext.hex()}")

    # Step 7: Remove PKCS7 padding
    print("\n--- Step 7: Remove PKCS7 Padding ---")
    plaintext = pkcs7_unpad(padded_plaintext)

    print(f"Padding length: {len(padded_plaintext) - len(plaintext)} bytes")
    print(f"Plaintext ({len(plaintext)}B): {plaintext.hex()}")
    print(f"Plaintext (UTF-8): {plaintext}")
    print()

    return plaintext

# ============================================================================
# RATCHET EXAMPLE
# ============================================================================

def create_ratchet():
    """
    Create a ratchet key for forward secrecy.

    Returns:
        Dictionary with ratchet components
    """
    print("=" * 70)
    print("RATCHET CREATION")
    print("=" * 70)

    # Generate ratchet private key
    if USE_REAL_CRYPTO:
        ratchet_prv = X25519PrivateKey.generate()
        ratchet_prv_bytes = ratchet_prv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        ratchet_pub = ratchet_prv.public_key()
        ratchet_pub_bytes = ratchet_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    else:
        ratchet_prv_bytes = os.urandom(32)
        ratchet_prv = MockX25519PrivateKey(ratchet_prv_bytes)
        ratchet_pub = ratchet_prv.public_key()
        ratchet_pub_bytes = ratchet_pub.public_bytes()

    print(f"\nRatchet Private Key (32B): {ratchet_prv_bytes.hex()}")
    print(f"Ratchet Public Key (32B):  {ratchet_pub_bytes.hex()}")

    # Calculate ratchet ID (first 10 bytes of SHA-256 hash)
    ratchet_id = hashlib.sha256(ratchet_pub_bytes).digest()[:10]
    print(f"Ratchet ID (10B): {ratchet_id.hex()}")

    print("\nRatchet Constants:")
    print(f"  RATCHET_INTERVAL: 1800 seconds (30 minutes)")
    print(f"  RATCHET_COUNT: 512 (retained ratchets)")
    print(f"  RATCHET_EXPIRY: 2592000 seconds (30 days)")
    print(f"  RATCHETSIZE: 256 bits (32 bytes)")
    print()

    return {
        'prv': ratchet_prv,
        'pub': ratchet_pub,
        'prv_bytes': ratchet_prv_bytes,
        'pub_bytes': ratchet_pub_bytes,
        'ratchet_id': ratchet_id
    }

# ============================================================================
# SIGNATURE EXAMPLE
# ============================================================================

def sign_and_verify(identity, message):
    """
    Demonstrate Ed25519 signing and verification.

    Args:
        identity: Identity dict with signing keys
        message: Message to sign (bytes)
    """
    print("=" * 70)
    print("SIGNATURE CREATION & VERIFICATION")
    print("=" * 70)

    print(f"\nMessage: {message}")
    print(f"Message hex: {message.hex()}")

    # Sign with private key
    print("\n--- Signing ---")
    sig_prv = identity['sig_prv']
    sig_prv_bytes = identity['sig_prv_bytes']
    signature = sig_prv.sign(message)

    print(f"Signing Private Key: {sig_prv_bytes.hex()}")
    print(f"Signature (64B): {signature.hex()}")

    # Verify with public key
    print("\n--- Verification ---")
    sig_pub = identity['sig_pub']
    sig_pub_bytes = identity['sig_pub_bytes']
    print(f"Signing Public Key: {sig_pub_bytes.hex()}")

    try:
        if USE_REAL_CRYPTO:
            sig_pub.verify(signature, message)
        else:
            sig_pub.verify(signature, message)
        print("Signature Valid: True")
    except:
        print("Signature Valid: False")

    print()

# ============================================================================
# MAIN - Run Examples
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print("RETICULUM CRYPTOGRAPHY & IDENTITY - WIRE FORMAT EXAMPLES")
    print("=" * 70)
    print()

    # Example 1: Create identity
    alice_identity = create_identity()

    # Example 2: Create another identity (recipient)
    print("\n")
    bob_identity = create_identity()

    # Example 3: Encrypt message from Alice to Bob
    print("\n")
    message = b"Hello Bob, this is Alice!"
    encrypted = encrypt_token(message, bob_identity)

    # Example 4: Bob decrypts message
    print("\n")
    decrypted = decrypt_token(encrypted['token'], bob_identity)

    # Verify decryption succeeded
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print(f"\nOriginal:  {message}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {message == decrypted}")
    print()

    # Example 5: Create ratchet
    print("\n")
    ratchet = create_ratchet()

    # Example 6: Sign and verify
    print("\n")
    announce_data = b"This is an announce"
    sign_and_verify(alice_identity, announce_data)

    # Example 7: Token overhead analysis
    print("=" * 70)
    print("TOKEN OVERHEAD ANALYSIS")
    print("=" * 70)
    print("\nFor different plaintext sizes:")

    for plaintext_size in [1, 16, 32, 64, 128, 256]:
        test_plaintext = b"X" * plaintext_size
        padding = 16 - (plaintext_size % 16)
        if padding == 0:
            padding = 16
        ciphertext_size = plaintext_size + padding
        total_token_size = 32 + 16 + ciphertext_size + 32

        print(f"\n  Plaintext: {plaintext_size}B")
        print(f"  Padding: {padding}B")
        print(f"  Ciphertext: {ciphertext_size}B")
        print(f"  Total token: {total_token_size}B")
        print(f"  Overhead: {total_token_size - plaintext_size}B ({100 * (total_token_size - plaintext_size) / plaintext_size:.1f}%)")

    print("\n" + "=" * 70)
    print("Examples demonstrate byte-level cryptographic operations")
    print("=" * 70)
    print()
