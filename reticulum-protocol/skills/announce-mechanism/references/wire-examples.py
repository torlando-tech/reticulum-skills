"""Wire Format Examples - Announce Mechanism"""
import hashlib
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

def create_announce_packet():
    """
    Construct a complete announce packet showing all components.

    An announce packet consists of:
    [DEST_HASH 16B][PUB_KEY 64B][NAME_HASH 10B][RANDOM_HASH 10B][RATCHET? 32B][SIGNATURE 64B][APP_DATA?]

    The signature is computed over:
    destination_hash + public_key + name_hash + random_hash + ratchet + app_data
    """

    # Step 1: Generate identity (encryption + signing keys)
    print("=" * 70)
    print("ANNOUNCE PACKET CONSTRUCTION")
    print("=" * 70)

    # X25519 encryption key (32 bytes)
    encryption_key = X25519PrivateKey.generate()
    encryption_pub = encryption_key.public_key().public_bytes_raw()

    # Ed25519 signing key (32 bytes)
    signing_key = Ed25519PrivateKey.generate()
    signing_pub = signing_key.public_key().public_bytes_raw()

    # Combined public key (64 bytes)
    public_key = encryption_pub + signing_pub
    print(f"\n1. Public Key (64 bytes):")
    print(f"   Encryption: {encryption_pub.hex()}")
    print(f"   Signing:    {signing_pub.hex()}")
    print(f"   Combined:   {public_key.hex()}")

    # Step 2: Calculate identity hash
    identity_hash = hashlib.sha256(public_key).digest()[:16]
    print(f"\n2. Identity Hash (16 bytes):")
    print(f"   {identity_hash.hex()}")

    # Step 3: Calculate name hash
    app_name = "exampledestination"
    aspects = ["app", "service"]
    full_name = app_name + "." + ".".join(aspects)
    name_hash = hashlib.sha256(full_name.encode()).digest()[:10]
    print(f"\n3. Name Hash (10 bytes):")
    print(f"   Full Name: {full_name}")
    print(f"   Hash:      {name_hash.hex()}")

    # Step 4: Calculate destination hash
    addr_hash_material = name_hash + identity_hash
    destination_hash = hashlib.sha256(addr_hash_material).digest()[:16]
    print(f"\n4. Destination Hash (16 bytes):")
    print(f"   {destination_hash.hex()}")

    # Step 5: Generate random hash (5 random bytes + 5 byte timestamp)
    import os
    random_bytes = os.urandom(5)
    timestamp_bytes = int(time.time()).to_bytes(5, "big")
    random_hash = random_bytes + timestamp_bytes
    print(f"\n5. Random Hash (10 bytes):")
    print(f"   Random:    {random_bytes.hex()}")
    print(f"   Timestamp: {timestamp_bytes.hex()} ({int.from_bytes(timestamp_bytes, 'big')})")
    print(f"   Combined:  {random_hash.hex()}")

    # Step 6: Generate ratchet (optional)
    ratchet_key = X25519PrivateKey.generate()
    ratchet_pub = ratchet_key.public_key().public_bytes_raw()
    print(f"\n6. Ratchet Public Key (32 bytes, optional):")
    print(f"   {ratchet_pub.hex()}")

    # Step 7: Add application data (optional)
    app_data = b"user@hostname|Online"
    print(f"\n7. Application Data ({len(app_data)} bytes, optional):")
    print(f"   {app_data.decode('utf-8')}")
    print(f"   Hex: {app_data.hex()}")

    # Step 8: Create signed data
    # CRITICAL: Destination hash is included in signature even though it's in the header
    signed_data = destination_hash + public_key + name_hash + random_hash + ratchet_pub + app_data
    print(f"\n8. Signed Data ({len(signed_data)} bytes):")
    print(f"   Components: dest_hash + pub_key + name_hash + random_hash + ratchet + app_data")
    print(f"   {signed_data.hex()}")

    # Step 9: Generate signature
    signature = signing_key.sign(signed_data)
    print(f"\n9. Signature (64 bytes):")
    print(f"   {signature.hex()}")

    # Step 10: Construct announce data (what goes in the packet payload)
    # Note: destination_hash is NOT in the announce data, it's in the packet header
    announce_data = public_key + name_hash + random_hash + ratchet_pub + signature + app_data
    print(f"\n10. Announce Data ({len(announce_data)} bytes):")
    print(f"    Components: pub_key + name_hash + random_hash + ratchet + signature + app_data")
    print(f"    {announce_data.hex()}")

    # Summary
    print("\n" + "=" * 70)
    print("ANNOUNCE PACKET SUMMARY")
    print("=" * 70)
    print(f"Destination Hash:  {destination_hash.hex()}")
    print(f"Public Key:        {public_key.hex()}")
    print(f"Name Hash:         {name_hash.hex()}")
    print(f"Random Hash:       {random_hash.hex()}")
    print(f"Ratchet:           {ratchet_pub.hex()}")
    print(f"Signature:         {signature.hex()}")
    print(f"App Data:          {app_data.hex()}")
    print(f"\nTotal Announce Data Size: {len(announce_data)} bytes")
    print(f"  Base (no ratchet, no app_data): 167 bytes")
    print(f"  With ratchet (no app_data):     199 bytes")
    print(f"  This announce (with both):      {len(announce_data)} bytes")

    # Step 11: Verify signature
    print("\n" + "=" * 70)
    print("SIGNATURE VERIFICATION")
    print("=" * 70)
    try:
        signing_key.public_key().verify(signature, signed_data)
        print("✓ Signature verification PASSED")
    except Exception as e:
        print(f"✗ Signature verification FAILED: {e}")

    return {
        "destination_hash": destination_hash,
        "announce_data": announce_data,
        "public_key": public_key,
        "signature": signature
    }


def create_announce_without_ratchet():
    """
    Create a minimal announce without ratchet for comparison.
    Total size: 167 bytes (64 + 10 + 10 + 64 = 148 bytes + app overhead)
    """
    print("\n\n" + "=" * 70)
    print("MINIMAL ANNOUNCE (NO RATCHET, NO APP DATA)")
    print("=" * 70)

    # Generate keys
    encryption_key = X25519PrivateKey.generate()
    encryption_pub = encryption_key.public_key().public_bytes_raw()
    signing_key = Ed25519PrivateKey.generate()
    signing_pub = signing_key.public_key().public_bytes_raw()
    public_key = encryption_pub + signing_pub

    # Calculate hashes
    identity_hash = hashlib.sha256(public_key).digest()[:16]
    app_name = "minimaldest"
    aspects = ["basic"]
    full_name = app_name + "." + ".".join(aspects)
    name_hash = hashlib.sha256(full_name.encode()).digest()[:10]
    addr_hash_material = name_hash + identity_hash
    destination_hash = hashlib.sha256(addr_hash_material).digest()[:16]

    # Random hash
    import os
    random_hash = os.urandom(5) + int(time.time()).to_bytes(5, "big")

    # Signed data WITHOUT ratchet
    signed_data = destination_hash + public_key + name_hash + random_hash
    signature = signing_key.sign(signed_data)

    # Announce data WITHOUT ratchet
    announce_data = public_key + name_hash + random_hash + signature

    print(f"Destination Hash: {destination_hash.hex()}")
    print(f"Public Key:       {public_key.hex()}")
    print(f"Name Hash:        {name_hash.hex()}")
    print(f"Random Hash:      {random_hash.hex()}")
    print(f"Signature:        {signature.hex()}")
    print(f"\nAnnounce Data Size: {len(announce_data)} bytes")
    print(f"  Public Key:    64 bytes")
    print(f"  Name Hash:     10 bytes")
    print(f"  Random Hash:   10 bytes")
    print(f"  Signature:     64 bytes")
    print(f"  Total:         {64 + 10 + 10 + 64} bytes")


def simulate_announce_propagation():
    """
    Simulate how an announce propagates through the network.
    """
    print("\n\n" + "=" * 70)
    print("ANNOUNCE PROPAGATION SIMULATION")
    print("=" * 70)

    # Constants
    PATHFINDER_M = 128
    PATHFINDER_R = 1
    PATHFINDER_G = 5
    PATHFINDER_RW = 0.5

    print(f"\nPathfinder Constants:")
    print(f"  PATHFINDER_M:  {PATHFINDER_M} (max hops)")
    print(f"  PATHFINDER_R:  {PATHFINDER_R} (retransmit retries)")
    print(f"  PATHFINDER_G:  {PATHFINDER_G} (retry grace period)")
    print(f"  PATHFINDER_RW: {PATHFINDER_RW} (random window)")

    print(f"\nAnnounce Propagation Steps:")
    print(f"1. Node A announces destination")
    print(f"2. Transport Node B receives (hops=0)")
    print(f"   - Check duplicate: NO (first time)")
    print(f"   - Check hop limit: 0 < {PATHFINDER_M+1} ✓")
    print(f"   - Store in path table")
    print(f"   - Wait random delay (0-{PATHFINDER_RW}s)")
    print(f"   - Retransmit with hops=1")
    print(f"3. Transport Node C receives (hops=1)")
    print(f"   - Check duplicate: NO")
    print(f"   - Check hop limit: 1 < {PATHFINDER_M+1} ✓")
    print(f"   - Store in path table")
    print(f"   - Priority = 1/1 = 1.0 (high)")
    print(f"   - Retransmit with hops=2")
    print(f"4. Process continues until:")
    print(f"   - Hops reach {PATHFINDER_M+1}, OR")
    print(f"   - All reachable nodes have received it")

    print(f"\nBandwidth Management:")
    print(f"  - Each interface: 2% bandwidth for announces")
    print(f"  - If over capacity: queue by priority (1/hops)")
    print(f"  - Closer destinations process first")

    print(f"\nConvergence Time:")
    print(f"  - Small network (10 hops):  ~5 seconds")
    print(f"  - Medium network (50 hops): ~30 seconds")
    print(f"  - Large network (128 hops): ~60 seconds")


if __name__ == "__main__":
    # Create full announce with ratchet
    announce_result = create_announce_packet()

    # Create minimal announce
    create_announce_without_ratchet()

    # Simulate propagation
    simulate_announce_propagation()

    print("\n" + "=" * 70)
    print("NOTES:")
    print("=" * 70)
    print("1. Destination hash is signed but NOT in announce_data")
    print("   (it's in the packet header)")
    print("2. Signature covers ALL components including optional ratchet and app_data")
    print("3. Random hash ensures each announce is unique (prevents duplicate filtering)")
    print("4. Ratchet enables forward secrecy (rotates with each announce)")
    print("5. App_data should be minimal to conserve bandwidth")
    print("=" * 70)
