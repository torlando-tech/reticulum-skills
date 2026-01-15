# Cryptography & Identity

This skill provides knowledge about Reticulum's cryptographic primitives, identity structure, encryption tokens, and key derivation. Invoke when the user mentions cryptographic primitives, Ed25519, X25519, identity, HKDF, token format, encryption, signatures, or key derivation.

## Authoritative Cryptographic Primitives

The primitives listed here **are authoritative**. Anything claiming to be Reticulum, but not using these exact primitives **is not** Reticulum, and possibly an intentionally compromised or weakened clone.

Reticulum uses a simple suite of efficient, strong and well-tested cryptographic primitives, with widely available implementations that can be used both on general-purpose CPUs and on microcontrollers.

One of the primary considerations for choosing this particular set of primitives is that they can be implemented *safely* with relatively few pitfalls, on practically all current computing platforms.

### Core Primitives

**Signatures**:
- **Ed25519** for all digital signatures
- 64-byte signatures
- Used for announce validation, link proofs, packet proofs

**ECDH Key Exchanges**:
- **X25519** on Curve25519 for all ECDH operations
- 32-byte public keys, 32-byte private keys
- Used for encryption, link establishment, ratchets

**Key Derivation**:
- **HKDF** (HMAC-based Key Derivation Function) per RFC 5869
- Uses SHA-256 as hash function
- Derives encryption and MAC keys from shared secrets

**Encryption**:
- **AES-256** in CBC mode with PKCS7 padding
- 32-byte keys
- 16-byte initialization vectors (IVs)
- IVs must be generated through `os.urandom()` or better

**Message Authentication**:
- **HMAC** using SHA-256
- 32-byte keys
- 32-byte tags

**Hashing**:
- **SHA-256** for general-purpose hashing
- **SHA-512** for specific applications
- Truncated hashes (128-bit) for addressing

### Token Format (Fernet-based)

Encrypted tokens are based on the Fernet spec with modifications:

- Ephemeral keys derived from an ECDH key exchange on Curve25519
- AES-256 in CBC mode with PKCS7 padding
- HMAC using SHA256 for message authentication
- IVs must be generated through `os.urandom()` or better
- **No Fernet version and timestamp metadata fields** (removed for efficiency and privacy)

**Token Structure**:
```
[IV 16B][CIPHERTEXT variable][HMAC 32B]
Total overhead: 48 bytes (TOKEN_OVERHEAD)
```

**Full Encryption Token** (as sent in packets):
```
[EPHEMERAL_PUBLIC_KEY 32B][IV 16B][CIPHERTEXT variable][HMAC 32B]
Total overhead: 80 bytes (32B ephemeral + 48B token)
```

### Implementation Sources

In the default installation configuration, the `X25519`, `Ed25519` and `AES-256-CBC` primitives are provided by OpenSSL (via the PyCA/cryptography package). The hashing functions `SHA-256` and `SHA-512` are provided by the standard Python hashlib. The `HKDF`, `HMAC`, `Token` primitives, and the `PKCS7` padding function are always provided by the following internal implementations:

- `RNS/Cryptography/HKDF.py`
- `RNS/Cryptography/HMAC.py`
- `RNS/Cryptography/Token.py`
- `RNS/Cryptography/PKCS7.py`

## Identity Structure

Reticulum identities are the foundation of all encrypted communication. An identity is a 512-bit keypair consisting of two 256-bit keys.

### Identity Components

**Private Keys** (64 bytes total):
- Encryption private key (X25519): 32 bytes
- Signing private key (Ed25519): 32 bytes

**Public Keys** (64 bytes total):
- Encryption public key (X25519): 32 bytes
- Signing public key (Ed25519): 32 bytes

**Identity Hash** (16 bytes):
- Truncated SHA-256 hash of public key bytes
- Used in destination hash calculation
- Format: `SHA256(pub_bytes)[:16]`

### Key Generation

```python
# Encryption keypair (X25519)
prv = X25519PrivateKey.generate()
prv_bytes = prv.private_bytes()  # 32 bytes

pub = prv.public_key()
pub_bytes = pub.public_bytes()   # 32 bytes

# Signing keypair (Ed25519)
sig_prv = Ed25519PrivateKey.generate()
sig_prv_bytes = sig_prv.private_bytes()  # 32 bytes

sig_pub = sig_prv.public_key()
sig_pub_bytes = sig_pub.public_bytes()   # 32 bytes

# Combined keys
private_key = prv_bytes + sig_prv_bytes   # 64 bytes
public_key = pub_bytes + sig_pub_bytes    # 64 bytes

# Identity hash
identity_hash = SHA256(public_key)[:16]   # 16 bytes
```

### Identity Properties

**KEYSIZE**: 512 bits (64 bytes)
- Complete key is concatenation of 256-bit encryption key and 256-bit signing key

**HASHLENGTH**: 256 bits
- Full SHA-256 hash length

**TRUNCATED_HASHLENGTH**: 128 bits (16 bytes)
- Used for destination hashes and identity hashes

**SIGLENGTH**: 512 bits (64 bytes)
- Ed25519 signature length

## Encryption Process

Reticulum uses ECDH combined with HKDF and AES-256-CBC for encryption.

### Encryption Steps

1. **Generate ephemeral keypair**:
   ```python
   ephemeral_key = X25519PrivateKey.generate()
   ephemeral_pub = ephemeral_key.public_key()
   ephemeral_pub_bytes = ephemeral_pub.public_bytes()  # 32 bytes
   ```

2. **Perform ECDH key exchange**:
   ```python
   # Use recipient's public key (or ratchet if available)
   target_public_key = recipient.pub  # X25519PublicKey
   shared_key = ephemeral_key.exchange(target_public_key)  # 32 bytes
   ```

3. **Derive encryption keys with HKDF**:
   ```python
   derived_key = HKDF(
       length=64,              # 64 bytes (512 bits)
       derive_from=shared_key, # ECDH shared secret
       salt=recipient.hash,    # Identity hash as salt
       context=None            # Optional context
   )

   signing_key = derived_key[:32]      # HMAC key
   encryption_key = derived_key[32:]   # AES key
   ```

4. **Create Token and encrypt**:
   ```python
   token = Token(derived_key)  # Creates token with both keys

   # Generate random IV
   iv = os.urandom(16)

   # Pad plaintext with PKCS7
   padded_plaintext = PKCS7.pad(plaintext)

   # Encrypt with AES-256-CBC
   ciphertext = AES_256_CBC.encrypt(
       plaintext=padded_plaintext,
       key=encryption_key,
       iv=iv
   )

   # Calculate HMAC over IV + ciphertext
   signed_parts = iv + ciphertext
   hmac_tag = HMAC.new(signing_key, signed_parts).digest()  # 32 bytes

   # Assemble token
   token_bytes = iv + ciphertext + hmac_tag
   ```

5. **Prepend ephemeral public key**:
   ```python
   final_token = ephemeral_pub_bytes + token_bytes
   # [32B ephemeral pub][16B IV][variable ciphertext][32B HMAC]
   ```

### Decryption Steps

1. **Extract ephemeral public key**:
   ```python
   peer_pub_bytes = ciphertext_token[:32]
   peer_pub = X25519PublicKey.from_public_bytes(peer_pub_bytes)
   token_data = ciphertext_token[32:]
   ```

2. **Perform ECDH with private key**:
   ```python
   # Try with ratchets first (if available)
   # Otherwise use identity private key
   shared_key = recipient.prv.exchange(peer_pub)  # 32 bytes
   ```

3. **Derive keys with HKDF** (same as encryption):
   ```python
   derived_key = HKDF(
       length=64,
       derive_from=shared_key,
       salt=recipient.hash,
       context=None
   )
   ```

4. **Verify HMAC and decrypt**:
   ```python
   token = Token(derived_key)

   # Extract components
   iv = token_data[:16]
   ciphertext = token_data[16:-32]
   received_hmac = token_data[-32:]

   # Verify HMAC
   expected_hmac = HMAC.new(signing_key, iv + ciphertext).digest()
   if received_hmac != expected_hmac:
       raise ValueError("Token HMAC was invalid")

   # Decrypt
   padded_plaintext = AES_256_CBC.decrypt(
       ciphertext=ciphertext,
       key=encryption_key,
       iv=iv
   )

   # Unpad
   plaintext = PKCS7.unpad(padded_plaintext)
   ```

## HKDF Key Derivation

HKDF (HMAC-based Key Derivation Function) is used to derive strong encryption keys from ECDH shared secrets.

### HKDF Parameters

**Function signature**:
```python
def hkdf(length=None, derive_from=None, salt=None, context=None)
```

**Parameters**:
- `length`: Output key length in bytes (typically 64 for AES-256)
- `derive_from`: Input key material (ECDH shared secret)
- `salt`: Salt value (typically identity hash, 16 bytes)
- `context`: Optional context information (typically None or empty bytes)

### HKDF Process (RFC 5869)

1. **Extract phase** (create pseudorandom key):
   ```python
   pseudorandom_key = HMAC_SHA256(salt, derive_from)
   ```

2. **Expand phase** (generate output key material):
   ```python
   block = b""
   derived = b""

   for i in range(ceil(length / 32)):  # 32 = SHA-256 output length
       block = HMAC_SHA256(pseudorandom_key, block + context + bytes([i + 1]))
       derived += block

   return derived[:length]
   ```

### HKDF Usage in Reticulum

**For Identity encryption**:
- `length=64` (512 bits)
- `derive_from=shared_key` (from ECDH)
- `salt=identity_hash` (16 bytes)
- `context=None`

**For Link encryption**:
- `length=64` (512 bits)
- `derive_from=shared_key` (from ECDH)
- `salt=None` (defaults to 32 zero bytes)
- `context=None`

**Key splitting**:
```python
derived_key = HKDF(length=64, ...)
signing_key = derived_key[:32]      # First 32 bytes for HMAC
encryption_key = derived_key[32:]   # Last 32 bytes for AES-256
```

### Why HKDF?

- **Cryptographically strong**: Extracts maximum entropy from input
- **Standard**: RFC 5869, well-analyzed
- **Flexible**: Can derive multiple independent keys
- **Salt support**: Binds derived keys to specific context (identity)
- **Domain separation**: Context parameter prevents key reuse across protocols

## Ratchets (Forward Secrecy)

Ratchets provide forward secrecy for SINGLE destinations by periodically rotating encryption keys.

### Ratchet Constants

**RATCHET_INTERVAL**: 1800 seconds (30 minutes)
- Time between automatic ratchet rotations
- Configurable per destination

**RATCHET_COUNT**: 512
- Number of historical ratchet keys to retain
- Used for decrypting late-arriving packets

**RATCHET_EXPIRY**: 2592000 seconds (30 days)
- How long to remember received ratchets
- After expiry, ratchet is discarded

**RATCHETSIZE**: 256 bits (32 bytes)
- X25519 private key size

### Ratchet Structure

A ratchet is simply an X25519 private key:

```python
ratchet_prv = X25519PrivateKey.generate()
ratchet_prv_bytes = ratchet_prv.private_bytes()  # 32 bytes
ratchet_pub = ratchet_prv.public_key()
ratchet_pub_bytes = ratchet_pub.public_bytes()   # 32 bytes
```

**Ratchet ID** (10 bytes):
```python
ratchet_id = SHA256(ratchet_pub_bytes)[:10]
```

### Ratchet Lifecycle

1. **Generation**: Destination generates new ratchet every RATCHET_INTERVAL
2. **Announcement**: Ratchet public key included in announce packet
3. **Retention**: Destination keeps RATCHET_COUNT most recent ratchets
4. **Reception**: Remote nodes remember ratchet for RATCHET_EXPIRY duration
5. **Decryption**: Try current ratchet first, then fall back to identity key

### Encryption with Ratchet

When encrypting to a destination with a known ratchet:

```python
# Use ratchet instead of identity public key
ratchet_pub = X25519PublicKey.from_public_bytes(ratchet_bytes)
shared_key = ephemeral_key.exchange(ratchet_pub)

# Rest of encryption is identical
derived_key = HKDF(
    length=64,
    derive_from=shared_key,
    salt=identity_hash,  # Still use identity hash as salt
    context=None
)
```

### Decryption with Ratchets

Destination tries ratchets before falling back to identity key:

```python
# Extract ephemeral public key from token
peer_pub = X25519PublicKey.from_public_bytes(token[:32])

# Try each retained ratchet
for ratchet_prv_bytes in retained_ratchets:
    ratchet_prv = X25519PrivateKey.from_private_bytes(ratchet_prv_bytes)
    shared_key = ratchet_prv.exchange(peer_pub)

    try:
        plaintext = decrypt_with_key(shared_key, token[32:])
        return plaintext  # Success
    except:
        continue  # Try next ratchet

# If all ratchets fail, try identity private key
shared_key = identity_prv.exchange(peer_pub)
plaintext = decrypt_with_key(shared_key, token[32:])
```

### Ratchet Benefits

**Forward secrecy**: Compromise of identity key doesn't reveal past messages encrypted with expired ratchets

**Backward secrecy**: Old ratchets eventually discarded, limiting exposure window

**Transparent**: Applications don't need to know about ratchets, handled by Identity layer

**Optional**: Destinations can choose whether to enable ratchets

### Ratchet Announce Format

When ratchet is enabled, announce packet includes:

```
[PUBLIC_KEY 64B][NAME_HASH 10B][RANDOM_HASH 10B][RATCHET_PUB 32B][SIGNATURE 64B][APP_DATA variable]
```

The signature covers: `destination_hash + public_key + name_hash + random_hash + ratchet_pub + app_data`

## Signatures

Ed25519 signatures authenticate data and prove identity ownership.

### Signing Process

```python
# Sign with identity's signing private key
signature = identity.sig_prv.sign(message)  # 64 bytes
```

**Signature length**: Always 64 bytes

**Deterministic**: Same message + key always produces same signature

**Fast**: Optimized for embedded systems

### Verification Process

```python
# Verify with identity's signing public key
try:
    identity.sig_pub.verify(signature, message)
    return True  # Valid signature
except:
    return False  # Invalid signature
```

### Signature Uses in Reticulum

**Announces**: Prove ownership of destination
- Signed data: `destination_hash + public_key + name_hash + random_hash + ratchet + app_data`

**Link proofs**: Prove destination accepted link
- Signed data: `link_id + destination_ephemeral_pub`

**Packet proofs**: Prove packet receipt
- Signed data: `packet_hash`

**Custom application data**: Any data requiring authentication

## Token Overhead Analysis

Understanding encryption overhead is critical for packet sizing.

**Minimum encryption overhead** (identity encryption):
```
Ephemeral public key: 32 bytes
IV:                   16 bytes
HMAC:                 32 bytes
PKCS7 padding:        1-16 bytes (average 8.5)
----------------------------------
Total:                80-96 bytes (average 88.5)
```

**Constants**:
- `TOKEN_OVERHEAD`: 48 bytes (IV + HMAC, not including ephemeral key)
- `AES128_BLOCKSIZE`: 16 bytes

**Padding calculation**:
```python
# PKCS7 always adds padding (1-16 bytes)
padding_length = 16 - (len(plaintext) % 16)
if padding_length == 0:
    padding_length = 16
padded_length = len(plaintext) + padding_length
```

**Ciphertext size**:
```python
ciphertext_size = len(plaintext) + padding_length
token_size = 32 + 16 + ciphertext_size + 32
# token_size = 80 + ciphertext_size
```

## Security Considerations

### Key Storage

**Private keys**: Must be stored securely
- Never transmitted over network
- Encrypted at rest recommended
- File permissions: 0600 (owner read/write only)

**Public keys**: Can be freely distributed
- Included in announce packets
- Stored in destination registry
- Used for encryption and signature verification

### Randomness Requirements

**Critical**: All IVs and ephemeral keys must use cryptographically secure randomness

**Source**: `os.urandom()` or equivalent
- **Never** use `random.random()` or predictable sources
- **Never** reuse IVs with same key

### Implementation Notes

**OpenSSL backend**: Strongly recommended for production
- Battle-tested implementations
- Hardware acceleration support
- Regular security updates

**Pure Python backend**: Only for systems without OpenSSL
- Significantly slower
- Less scrutiny and review
- Acceptable for low-throughput embedded systems

### Constant-Time Operations

**HMAC verification**: Must use constant-time comparison
- Prevents timing attacks
- Compare all bytes even if early mismatch

**Key derivation**: HKDF inherently constant-time
- No branching based on key material

## Further Reading

For detailed specifications:
- `references/token-format.md` - Token structure and encoding
- `references/hkdf-derivation.md` - HKDF detailed examples
- `references/ratchet-mechanism.md` - Ratchet rotation and management
- `references/wire-examples.py` - Complete encryption/decryption examples

Related skills:
- `destinations` - How identities relate to destinations
- `links` - Link-layer encryption
- `announce-mechanism` - Public key distribution via announces
- `packets-wire-format` - How encrypted tokens appear in packets

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Identity.py` (Identity structure, encryption)
- `https://github.com/markqvist/Reticulum/RNS/Destination.py` (RATCHET_COUNT, RATCHET_INTERVAL constants)
- `https://github.com/markqvist/Reticulum/RNS/Cryptography/Token.py`
- `https://github.com/markqvist/Reticulum/RNS/Cryptography/HKDF.py`
- `https://github.com/markqvist/Reticulum/RNS/Cryptography/HMAC.py`
- `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` (lines 869-936)
