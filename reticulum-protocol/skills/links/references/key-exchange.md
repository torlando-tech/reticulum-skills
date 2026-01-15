# Key Exchange and Derivation

Complete ECDH process and key derivation for link encryption.

## X25519 ECDH Overview

Links use X25519 Elliptic Curve Diffie-Hellman on Curve25519 for key agreement:

**Properties:**
- 128-bit security level
- Fast computation
- Small key size (32 bytes)
- Resistant to timing attacks
- Industry standard (used in TLS 1.3, Signal, WireGuard)

## Key Generation

### Initiator

```python
# Generate ephemeral X25519 private key
Li_priv = X25519PrivateKey.generate()  # 32 bytes random

# Derive public key
Li_pub = Li_priv.public_key()  # 32 bytes

# Also generate Ed25519 signing keypair
Li_sign_priv = Ed25519PrivateKey.generate()
Li_sign_pub = Li_sign_priv.public_key()

# LKi = Li_pub + Li_sign_pub (64 bytes total)
LKi = Li_pub.public_bytes() + Li_sign_pub.public_bytes()
```

### Destination

```python
# Generate ephemeral X25519 private key
Lr_priv = X25519PrivateKey.generate()  # 32 bytes random

# Derive public key
Lr_pub = Lr_priv.public_key()  # 32 bytes

# LKr = Lr_pub
LKr = Lr_pub.public_bytes()
```

## Shared Secret Calculation

Both parties perform ECDH independently to arrive at identical shared secret.

### Destination (first)

```python
# Extract Li_pub from link request
Li_pub = X25519PublicKey.from_public_bytes(link_request_data[:32])

# Perform ECDH
shared_secret = Lr_priv.exchange(Li_pub)  # 32 bytes
```

### Initiator (after receiving link proof)

```python
# Extract Lr_pub from link proof
Lr_pub = X25519PublicKey.from_public_bytes(link_proof_data[:32])

# Perform ECDH
shared_secret = Li_priv.exchange(Lr_pub)  # 32 bytes
```

**Critical property:** Both sides compute identical `shared_secret` without ever transmitting it over the network.

Mathematical basis:
```
Initiator: shared_secret = Li_priv × Lr_pub
Destination: shared_secret = Lr_priv × Li_pub

Due to ECDH math: Li_priv × Lr_pub = Lr_priv × Li_pub
```

## Key Derivation with HKDF

The raw shared_secret is expanded into multiple keys using HKDF (HMAC-based Key Derivation Function, RFC 5869).

### HKDF Process

```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# Derive 64 bytes of key material
hkdf = HKDF(
    algorithm=hashes.SHA256(),
    length=64,  # 32 bytes encryption + 32 bytes HMAC
    salt=None,
    info=None
)

key_material = hkdf.derive(shared_secret)

# Split into separate keys
encryption_key = key_material[:32]  # AES-256 key
hmac_key = key_material[32:64]      # HMAC-SHA256 key
```

### Derived Keys

**encryption_key** (32 bytes): Used for AES-256-CBC encryption of all link traffic

**hmac_key** (32 bytes): Used for HMAC-SHA256 authentication of all link traffic

## Link Key Structure

After ECDH and HKDF, both link ends have:

```python
link_keys = {
    'shared_secret': bytes(32),      # ECDH output (never transmitted)
    'encryption_key': bytes(32),     # AES-256 key
    'hmac_key': bytes(32),           # HMAC key
    'Li_pub': bytes(32),             # Initiator public key (for reference)
    'Lr_pub': bytes(32),             # Destination public key (for reference)
    'Li_sign_pub': bytes(32),        # Initiator signing key
    'Lr_sign_pub': bytes(32),        # Destination signing key (from identity)
}
```

## Encryption Mode

Currently only AES-256-CBC supported:

```python
MODE_AES256_CBC = 0x01
```

### Packet Encryption

Each link packet encrypted with:
- **Algorithm**: AES-256 in CBC mode
- **Key**: `encryption_key` (32 bytes)
- **IV**: Random 16 bytes per packet (included in ciphertext)
- **Padding**: PKCS7 padding to 16-byte blocks
- **MAC**: HMAC-SHA256 with `hmac_key` over (IV + ciphertext)

Structure:
```
[IV 16B][Ciphertext variable][HMAC 32B]
```

See `cryptography-identity` skill for detailed token format.

## Forward Secrecy Mechanism

Forward secrecy achieved through:

1. **Ephemeral keys**: Li_priv and Lr_priv generated fresh for each link
2. **No key storage**: Private keys kept only in memory during link lifetime
3. **Key destruction**: Private keys zeroed and garbage collected when link closes
4. **Independence from identity**: Link keys completely separate from node's persistent identity keys

Result: Even if node's identity private key is compromised later, past link traffic remains secure.

## Key Rotation

Reticulum does not perform automatic key rotation within an established link. Instead:

- Links are expected to be ephemeral (closed and reopened when needed)
- Each new link establishment generates fresh keys
- Long-lived links protected by physical security of endpoints

For applications requiring key rotation, recommended approach:
- Close existing link
- Establish new link (generates new keys automatically)
- Resume communication

## Signature Verification in Link Proof

The link proof includes Ed25519 signature to prove destination identity:

```python
# Destination creates signature
signature = destination_identity.sign(link_id + Lr_pub)  # 64 bytes

# Initiator verifies
destination_identity.verify(signature, link_id + Lr_pub)
```

This binds:
- The link (via link_id)
- The ephemeral key (Lr_pub)
- The destination's persistent identity (via signature key)

Prevents man-in-the-middle: Attacker cannot substitute their own Lr_pub because they can't create valid signature with destination's private key.

## ECDH Security Properties

X25519 provides:

1. **Computational Diffie-Hellman (CDH) hardness**: Infeasible to compute shared secret from public keys alone

2. **Decisional Diffie-Hellman (DDH) hardness**: Cannot distinguish real shared secret from random value

3. **Passive security**: Eavesdropper seeing Li_pub and Lr_pub cannot derive shared secret

4. **Active security** (with authentication): Combined with Ed25519 signatures, prevents active attacks

## Implementation Example

Complete ECDH and key derivation:

```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from RNS.Cryptography import X25519PrivateKey, X25519PublicKey

# Initiator side
def initiator_derive_keys(link_proof_data):
    # Extract Lr_pub from link proof
    Lr_pub_bytes = link_proof_data[:32]
    Lr_pub = X25519PublicKey.from_public_bytes(Lr_pub_bytes)

    # Perform ECDH with saved Li_priv
    shared_secret = Li_priv.exchange(Lr_pub)  # 32 bytes

    # Derive keys with HKDF
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=None,
        info=None
    )
    key_material = hkdf.derive(shared_secret)

    encryption_key = key_material[:32]
    hmac_key = key_material[32:64]

    return encryption_key, hmac_key

# Destination side
def destination_derive_keys(link_request_data):
    # Extract Li_pub from link request
    Li_pub_bytes = link_request_data[:32]
    Li_pub = X25519PublicKey.from_public_bytes(Li_pub_bytes)

    # Generate ephemeral key
    Lr_priv = X25519PrivateKey.generate()
    Lr_pub = Lr_priv.public_key()

    # Perform ECDH
    shared_secret = Lr_priv.exchange(Li_pub)  # 32 bytes

    # Derive keys with HKDF (same as initiator)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=None,
        info=None
    )
    key_material = hkdf.derive(shared_secret)

    encryption_key = key_material[:32]
    hmac_key = key_material[32:64]

    return encryption_key, hmac_key, Lr_pub
```

Both sides now have identical `encryption_key` and `hmac_key` for secure communication.

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Link.py` (key exchange implementation)
- `https://github.com/markqvist/Reticulum/RNS/Cryptography/HKDF.py`
- RFC 5869 (HKDF specification)
- RFC 7748 (X25519 specification)
