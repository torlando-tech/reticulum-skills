"""Wire Format Examples - Destinations"""
import hashlib

def calculate_single_destination_hash():
    """Calculate destination hash for SINGLE destination."""
    app_name = "environmentlogger"
    aspects = ["remotesensor", "temperature"]
    
    # Step 1: Full name without identity
    full_name_without_identity = app_name + "." + ".".join(aspects)
    print(f"Full name: {full_name_without_identity}")
    
    # Step 2: Name hash (80 bits = 10 bytes)
    name_hash = hashlib.sha256(full_name_without_identity.encode()).digest()[:10]
    print(f"Name hash: {name_hash.hex()}")
    
    # Step 3: Identity hash (from public key)
    public_key = bytes(64)  # Example 64-byte public key
    identity_hash = hashlib.sha256(public_key).digest()[:16]
    print(f"Identity hash: {identity_hash.hex()}")
    
    # Step 4: Destination hash
    addr_hash_material = name_hash + identity_hash
    destination_hash = hashlib.sha256(addr_hash_material).digest()[:16]
    print(f"Destination: <{destination_hash.hex()}>")
    return destination_hash

if __name__ == "__main__":
    calculate_single_destination_hash()
