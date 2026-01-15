"""
Wire Format Examples - Links

Byte-level examples for link establishment and encryption.
These examples demonstrate protocol bytes, not high-level API usage.
"""

import struct
import hashlib
import os
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# Mock X25519 for demonstration (would use real crypto in practice)
class MockX25519PrivateKey:
    def __init__(self, private_bytes):
        self.private_bytes = private_bytes

    def public_key(self):
        # In reality, this derives public from private via curve math
        return MockX25519PublicKey(hashlib.sha256(self.private_bytes).digest()[:32])

    def exchange(self, peer_public_key):
        # In reality, this performs ECDH
        # Mock: XOR private with peer public
        result = bytes(a ^ b for a, b in zip(self.private_bytes, peer_public_key.public_bytes))
        return result

class MockX25519PublicKey:
    def __init__(self, public_bytes):
        self._public_bytes = public_bytes

    def public_bytes(self):
        return self._public_bytes

# ============================================================================
# LINK REQUEST PACKET
# ============================================================================

def build_link_request_packet():
    """
    Build a link request packet with ephemeral keys.

    Structure:
    [HEADER 19B][LKi 64B][MTU_SIGNALLING 3B]
    Total: 86 bytes (83 without MTU signalling)

    LKi = encryption_public_key (32B) + signing_public_key (32B)
    """

    # Generate ephemeral keys
    Li_enc_priv = os.urandom(32)
    Li_sign_priv = os.urandom(32)

    # Derive public keys (mocked)
    Li_enc_pub = hashlib.sha256(Li_enc_priv + b"enc").digest()[:32]
    Li_sign_pub = hashlib.sha256(Li_sign_priv + b"sign").digest()[:32]

    # Construct LKi
    LKi = Li_enc_pub + Li_sign_pub  # 64 bytes

    # Destination hash
    dest_hash = hashlib.sha256(b"target_destination").digest()[:16]

    # FLAGS byte
    ifac_flag = 0 << 7
    header_type = 0 << 6       # HEADER_1
    context_flag = 0 << 5
    propagation = 0 << 4       # BROADCAST
    dest_type = 0 << 2         # SINGLE
    packet_type = 2            # LINKREQUEST

    flags = ifac_flag | header_type | context_flag | propagation | dest_type | packet_type
    # flags = 0b00000010 = 0x02

    # Header
    hops = 0
    context = 0x00  # NONE

    header = struct.pack("BB", flags, hops) + dest_hash + bytes([context])

    # MTU signalling (optional)
    mtu = 512
    mode = 0x01  # MODE_AES256_CBC

    # Encode: 21 bits MTU + 3 bits mode (shifted)
    MTU_BYTEMASK = 0x1FFFFF
    MODE_BYTEMASK = 0xE0
    signalling_value = (mtu & MTU_BYTEMASK) + (((mode << 5) & MODE_BYTEMASK) << 16)
    mtu_bytes = struct.pack(">I", signalling_value)[1:]  # Last 3 bytes

    # Complete packet
    packet = header + LKi + mtu_bytes

    print("Link Request Packet:")
    print(f"  Flags: 0x{flags:02x} (LINKREQUEST)")
    print(f"  Destination: {dest_hash.hex()}")
    print(f"  LKi (encryption pub): {Li_enc_pub.hex()}")
    print(f"  LKi (signing pub): {Li_sign_pub.hex()}")
    print(f"  MTU Signalling: {mtu} bytes, mode 0x{mode:02x}")
    print(f"  Total size: {len(packet)} bytes")
    print()

    return packet, Li_enc_priv, dest_hash

# ============================================================================
# LINK ID CALCULATION
# ============================================================================

def calculate_link_id(link_request_packet):
    """
    Link ID is SHA-256 hash of entire link request packet, truncated to 16 bytes.
    """

    link_id = hashlib.sha256(link_request_packet).digest()[:16]

    print("Link ID Calculation:")
    print(f"  Link Request Hash: {hashlib.sha256(link_request_packet).digest().hex()}")
    print(f"  Link ID (truncated): {link_id.hex()}")
    print()

    return link_id

# ============================================================================
# LINK PROOF PACKET
# ============================================================================

def build_link_proof_packet(link_id):
    """
    Build link proof packet from destination.

    Structure:
    [HEADER 19B][LKr 32B][SIGNATURE 64B][MTU_SIGNALLING 3B]
    Total: 118 bytes (115 without MTU signalling)
    """

    # Generate destination's ephemeral key
    Lr_enc_priv = os.urandom(32)
    Lr_enc_pub = hashlib.sha256(Lr_enc_priv + b"enc").digest()[:32]

    # Create signature (mocked - would use Ed25519)
    # Signature over: link_id + Lr_enc_pub
    signature_data = link_id + Lr_enc_pub
    signature = hashlib.sha256(signature_data + b"destination_private_key").digest()
    signature = signature + hashlib.sha256(signature).digest()  # 64 bytes total

    # FLAGS byte for PROOF packet
    flags = 0b00000011  # HEADER_1, BROADCAST, SINGLE, PROOF

    # Header addressed to link_id
    hops = 0
    context = 0xFF  # LRPROOF

    header = struct.pack("BB", flags, hops) + link_id + bytes([context])

    # MTU signalling (optional)
    mtu = 512
    mode = 0x01
    signalling_value = (mtu & 0x1FFFFF) + (((mode << 5) & 0xE0) << 16)
    mtu_bytes = struct.pack(">I", signalling_value)[1:]

    # Complete packet
    packet = header + Lr_enc_pub + signature + mtu_bytes

    print("Link Proof Packet:")
    print(f"  Addressed to Link ID: {link_id.hex()}")
    print(f"  LKr (encryption pub): {Lr_enc_pub.hex()}")
    print(f"  Signature: {signature.hex()}")
    print(f"  Total size: {len(packet)} bytes")
    print()

    return packet, Lr_enc_priv

# ============================================================================
# ECDH KEY EXCHANGE
# ============================================================================

def perform_ecdh_exchange(Li_priv, Lr_pub, Lr_priv, Li_pub):
    """
    Both sides perform ECDH to derive shared secret.
    """

    # Initiator side: shared_secret = X25519(Li_priv, Lr_pub)
    mock_Li_priv = MockX25519PrivateKey(Li_priv)
    mock_Lr_pub = MockX25519PublicKey(Lr_pub)
    initiator_shared_secret = mock_Li_priv.exchange(mock_Lr_pub)

    # Destination side: shared_secret = X25519(Lr_priv, Li_pub)
    mock_Lr_priv = MockX25519PrivateKey(Lr_priv)
    mock_Li_pub = MockX25519PublicKey(Li_pub)
    destination_shared_secret = mock_Lr_priv.exchange(mock_Li_pub)

    print("ECDH Key Exchange:")
    print(f"  Initiator shared secret: {initiator_shared_secret.hex()}")
    print(f"  Destination shared secret: {destination_shared_secret.hex()}")
    print(f"  Secrets match: {initiator_shared_secret == destination_shared_secret}")
    print()

    return initiator_shared_secret

# ============================================================================
# KEY DERIVATION WITH HKDF
# ============================================================================

def derive_link_keys(shared_secret):
    """
    Derive encryption and HMAC keys from shared secret using HKDF.
    """

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,  # 32 bytes encryption + 32 bytes HMAC
        salt=None,
        info=None
    )

    key_material = hkdf.derive(shared_secret)

    encryption_key = key_material[:32]
    hmac_key = key_material[32:64]

    print("HKDF Key Derivation:")
    print(f"  Shared Secret: {shared_secret.hex()}")
    print(f"  Encryption Key (AES-256): {encryption_key.hex()}")
    print(f"  HMAC Key (SHA-256): {hmac_key.hex()}")
    print()

    return encryption_key, hmac_key

# ============================================================================
# KEEP-ALIVE PACKET
# ============================================================================

def build_keepalive_packet(link_id):
    """
    Build keep-alive packet for active link.

    Structure:
    [HEADER 19B][ENCRYPTED_DATA ~16B]
    Total: ~35 bytes
    """

    # FLAGS for DATA packet to link
    flags = 0b00001100  # HEADER_1, BROADCAST, LINK dest, DATA

    hops = 0
    context = 0xFA  # KEEPALIVE

    header = struct.pack("BB", flags, hops) + link_id + bytes([context])

    # Minimal encrypted data
    encrypted_data = os.urandom(16)  # Just enough for valid packet

    packet = header + encrypted_data

    print("Keep-Alive Packet:")
    print(f"  Link ID: {link_id.hex()}")
    print(f"  Context: 0xFA (KEEPALIVE)")
    print(f"  Size: {len(packet)} bytes")
    print(f"  Bandwidth: {(len(packet) * 8) / 360:.2f} bits/second @ 360s interval")
    print()

    return packet

# ============================================================================
# LINK TIMEOUT CALCULATION
# ============================================================================

def calculate_link_timeout(rtt_seconds):
    """
    Calculate link timeout based on RTT.

    timeout = (RTT × KEEPALIVE_TIMEOUT_FACTOR) + STALE_GRACE
    """

    KEEPALIVE_TIMEOUT_FACTOR = 4
    STALE_GRACE = 5

    timeout = (rtt_seconds * KEEPALIVE_TIMEOUT_FACTOR) + STALE_GRACE

    print("Link Timeout Calculation:")
    print(f"  RTT: {rtt_seconds} seconds")
    print(f"  Timeout Factor: {KEEPALIVE_TIMEOUT_FACTOR}")
    print(f"  Stale Grace: {STALE_GRACE} seconds")
    print(f"  Total Timeout: {timeout} seconds")
    print()

    return timeout

# ============================================================================
# MAIN - Run Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LINKS - WIRE FORMAT EXAMPLES")
    print("=" * 70)
    print()

    # Example 1: Link request
    link_req, Li_priv, dest_hash = build_link_request_packet()

    # Example 2: Link ID calculation
    link_id = calculate_link_id(link_req)

    # Example 3: Link proof
    link_proof, Lr_priv = build_link_proof_packet(link_id)

    # Extract public keys for ECDH
    Li_pub = hashlib.sha256(Li_priv + b"enc").digest()[:32]
    Lr_pub = hashlib.sha256(Lr_priv + b"enc").digest()[:32]

    # Example 4: ECDH exchange
    shared_secret = perform_ecdh_exchange(Li_priv, Lr_pub, Lr_priv, Li_pub)

    # Example 5: Key derivation
    enc_key, hmac_key = derive_link_keys(shared_secret)

    # Example 6: Keep-alive
    keepalive = build_keepalive_packet(link_id)

    # Example 7: Timeout calculation
    for rtt in [0.01, 1.0, 5.0, 30.0]:
        calculate_link_timeout(rtt)

    print("=" * 70)
    print("Examples demonstrate byte-level link operations")
    print("=" * 70)
