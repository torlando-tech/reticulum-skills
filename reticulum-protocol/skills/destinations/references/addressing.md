# Destination Addressing

Complete address calculation algorithm for all destination types.

## Hash Sizes

- **Name hash**: 10 bytes (80 bits)
- **Identity hash**: 16 bytes (128 bits)
- **Destination hash**: 16 bytes (128 bits)

## SINGLE Destination Algorithm

```python
# Step 1: Create full name string
app_name = "myapp"
aspects = ["service", "function"]
full_name = app_name + "." + ".".join(aspects)
# Result: "myapp.service.function"

# Step 2: Calculate name hash
name_hash = SHA256(full_name.encode('utf-8'))[:10]  # First 10 bytes

# Step 3: Get identity hash from public key
public_key = identity.get_public_key()  # 64 bytes
identity_hash = SHA256(public_key)[:16]  # First 16 bytes

# Step 4: Combine and hash for final destination
combined = name_hash + identity_hash  # 26 bytes total
destination_hash = SHA256(combined)[:16]  # Final 16-byte address
```

## GROUP Destination Algorithm

GROUP destinations use the same hash algorithm as PLAIN. The group key is used for **encryption**, not for address calculation.

```python
# GROUP and PLAIN use identical address calculation
full_name = "myapp.group.channel"
name_hash = SHA256(full_name.encode('utf-8'))[:10]  # First 10 bytes
destination_hash = SHA256(name_hash)[:16]  # Final 16-byte address

# The group key is set separately and used only for packet encryption:
# destination.set_group_key(group_key)  # 32-byte AES-256 key
```

## PLAIN Destination Algorithm

```python
# PLAIN uses identical algorithm to GROUP
full_name = "myapp.broadcast.beacon"
name_hash = SHA256(full_name.encode('utf-8'))[:10]
destination_hash = SHA256(name_hash)[:16]
```

## LINK Destination Algorithm

LINK addresses are calculated differently - they use the hash of the link request packet itself:

```python
link_id = SHA256(link_request_packet)[:16]
```

This link_id then serves as the destination hash for all link traffic.

## Collision Analysis

With 128-bit destination hashes:
- **Address space**: 2^128 = 3.4 × 10^38 addresses
- **Birthday bound**: 2^64 hashes for 50% collision probability
- **Practical safety**: Up to 10^18 destinations with negligible risk

For realistic networks (millions of destinations), collision probability is astronomically low.

---

**Source**: `https://github.com/markqvist/Reticulum/RNS/Destination.py`
