#!/usr/bin/env python3
"""
IFAC (Interface Access Code) Implementation Example

This example demonstrates how Reticulum calculates IFAC signatures for
named virtual networks. IFAC enables creating isolated networks on shared
physical media by signing all packets with a network-specific Ed25519 key.

Only interfaces configured with matching network name and/or passphrase
can communicate - others see invalid signatures and drop packets.
"""

import RNS
import hashlib

# IFAC configuration
IFAC_NETNAME = "private_mesh"           # Virtual network name
IFAC_NETKEY = "correct_horse_battery"   # Network passphrase
IFAC_SIZE = 16                          # Signature size in bytes (1-64)

# Reticulum IFAC salt (fixed constant from RNS.Reticulum)
IFAC_SALT = bytes.fromhex("adf54d882c9a9b80771eb4995d702d4a3e733391b2a0f53f416d9f907e55cff8")

print("=" * 70)
print("IFAC (Interface Access Code) Calculation Example")
print("=" * 70)
print()

# Step 1: Hash network name and passphrase
print("Step 1: Hash network name and passphrase")
print("-" * 70)

netname_hash = RNS.Identity.full_hash(IFAC_NETNAME.encode("utf-8"))
netkey_hash = RNS.Identity.full_hash(IFAC_NETKEY.encode("utf-8"))

print(f"Network name:  {IFAC_NETNAME}")
print(f"  SHA-256:     {netname_hash.hex()}")
print()
print(f"Passphrase:    {IFAC_NETKEY}")
print(f"  SHA-256:     {netkey_hash.hex()}")
print()

# Step 2: Combine hashes to create IFAC origin
print("Step 2: Combine hashes to create IFAC origin")
print("-" * 70)

ifac_origin = netname_hash + netkey_hash
print(f"IFAC origin (netname_hash + netkey_hash):")
print(f"  {ifac_origin.hex()}")
print()

# Step 3: Hash the IFAC origin
print("Step 3: Hash IFAC origin")
print("-" * 70)

ifac_origin_hash = RNS.Identity.full_hash(ifac_origin)
print(f"SHA-256(ifac_origin):")
print(f"  {ifac_origin_hash.hex()}")
print()

# Step 4: Derive 64-byte IFAC key via HKDF
print("Step 4: Derive IFAC key via HKDF")
print("-" * 70)

ifac_key = RNS.Cryptography.hkdf(
    length=64,
    derive_from=ifac_origin_hash,
    salt=IFAC_SALT,
    context=None
)

print(f"HKDF parameters:")
print(f"  Input:       ifac_origin_hash (32 bytes)")
print(f"  Salt:        IFAC_SALT (32 bytes, fixed Reticulum constant)")
print(f"  Length:      64 bytes")
print(f"  Context:     None")
print()
print(f"Derived IFAC key (64 bytes):")
print(f"  {ifac_key.hex()}")
print()

# Step 5: Generate Ed25519 identity from IFAC key
print("Step 5: Generate Ed25519 identity from IFAC key")
print("-" * 70)

ifac_identity = RNS.Identity.from_bytes(ifac_key)

print(f"Ed25519 identity created from IFAC key")
print(f"  Public key:  {ifac_identity.get_public_key().hex()}")
print()

# Step 6: Sign the IFAC key itself (self-signature for verification)
print("Step 6: Create IFAC self-signature")
print("-" * 70)

ifac_signature = ifac_identity.sign(RNS.Identity.full_hash(ifac_key))

print(f"Ed25519 signature of SHA-256(ifac_key):")
print(f"  Full (64 bytes): {ifac_signature.hex()}")
print()
print(f"Truncated to configured IFAC size ({IFAC_SIZE} bytes):")
print(f"  {ifac_signature[-IFAC_SIZE:].hex()}")
print()

# Step 7: Demonstrate packet signing
print("Step 7: Per-packet IFAC calculation")
print("-" * 70)

# Simulate a packet (in reality this would be a full Reticulum packet)
example_packet = b"\x00\x01\x23\x45\x67\x89\xab\xcd\xef"  # Dummy packet data

print(f"Example packet (hex): {example_packet.hex()}")
print()

# Sign the packet
packet_ifac = ifac_identity.sign(example_packet)
packet_ifac_truncated = packet_ifac[-IFAC_SIZE:]

print(f"Ed25519 signature of packet:")
print(f"  Full (64 bytes): {packet_ifac.hex()}")
print()
print(f"Truncated IFAC ({IFAC_SIZE} bytes):")
print(f"  {packet_ifac_truncated.hex()}")
print()

# Step 8: Generate packet mask from IFAC
print("Step 8: Generate packet mask from IFAC")
print("-" * 70)

# In real implementation, IFAC is inserted into packet and entire packet is masked
packet_with_ifac_length = len(example_packet) + IFAC_SIZE

mask = RNS.Cryptography.hkdf(
    length=packet_with_ifac_length,
    derive_from=packet_ifac_truncated,  # Mask derived from IFAC itself
    salt=ifac_key,                      # Using IFAC key as salt
    context=None
)

print(f"Packet + IFAC length: {packet_with_ifac_length} bytes")
print(f"Mask (HKDF derived from IFAC, length={packet_with_ifac_length}):")
print(f"  {mask.hex()}")
print()

# Step 9: Demonstrate masking
print("Step 9: Mask packet with IFAC")
print("-" * 70)

# Construct packet: header(2 bytes) + IFAC + payload
# In real implementation: new_raw = header_with_ifac_flag + ifac + original_packet[2:]
# Here we'll just show XOR masking principle

example_masked = bytes([b ^ mask[i] for i, b in enumerate(example_packet)])

print(f"Original packet:  {example_packet.hex()}")
print(f"Masked packet:    {example_masked.hex()}")
print(f"(XOR with first {len(example_packet)} bytes of mask)")
print()

# Verification
print("=" * 70)
print("IFAC Verification Process")
print("=" * 70)
print()
print("Receiving interface performs these steps:")
print("  1. Check IFAC flag in packet header (bit 7 of first byte)")
print("  2. Extract IFAC (bytes after header, length = ifac_size)")
print("  3. Generate mask from IFAC using HKDF")
print("  4. Unmask packet by XOR with mask")
print("  5. Verify Ed25519 signature matches interface's IFAC identity")
print("  6. Drop packet if invalid, accept if valid")
print()

print("Security properties:")
print(f"  - IFAC size: {IFAC_SIZE} bytes = {IFAC_SIZE * 8} bits")
print(f"  - Collision probability: ~1 in 2^{IFAC_SIZE * 8}")
print("  - Cryptographic strength: Ed25519 (curve25519)")
print("  - Network isolation: Only interfaces with matching netname+netkey")
print("    can generate valid signatures")
print()

print("Configuration for this virtual network:")
print("-" * 70)
print(f"""
[[Private LoRa Network]]
  type = RNodeInterface
  port = /dev/ttyUSB0
  frequency = 867200000
  bandwidth = 125000
  txpower = 7
  spreadingfactor = 8
  codingrate = 5

  # Virtual network configuration
  ifac_netname = {IFAC_NETNAME}
  ifac_netkey = {IFAC_NETKEY}
  ifac_size = {IFAC_SIZE * 8}  # Size in bits ({IFAC_SIZE} bytes)
""")

print("=" * 70)
print()

# Additional implementation notes
print("Implementation Notes:")
print("-" * 70)
print()
print("IFAC overhead per packet:")
print(f"  - Signature: {IFAC_SIZE} bytes")
print("  - Processing: Ed25519 sign/verify per packet")
print("  - Masking: XOR operation over entire packet")
print()
print("IFAC size guidelines:")
print("  - 1 byte (8 bits):    Minimal overhead, testing only")
print("  - 8 bytes (64 bits):  LoRa/low-bandwidth (default for RNode)")
print("  - 16 bytes (128 bits): Good balance (default for TCP/UDP/I2P)")
print("  - 32 bytes (256 bits): High security")
print("  - 64 bytes (512 bits): Full Ed25519 signature")
print()
print("Smaller IFAC = less bandwidth, higher collision probability")
print("Larger IFAC = more bandwidth, stronger authentication")
print()
print("Common use cases:")
print("  - Private mesh networks (isolated from public networks)")
print("  - Multi-tenant shared infrastructure")
print("  - Passphrase-protected interfaces")
print("  - Testing network segregation")
print()
