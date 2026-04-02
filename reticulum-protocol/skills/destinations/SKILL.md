---
name: destinations
description: Reticulum's addressing system and destination types. Use when working with destination types (SINGLE, GROUP, PLAIN, LINK), destination hashes, aspect naming, or addressing.
---

# Destinations

This skill provides knowledge about Reticulum's addressing system and destination types. Invoke when the user mentions destination types, single destination, group destination, destination hash, aspect naming, or addressing.

## Addressing Overview

Destinations are Reticulum's addressing system, replacing IP addresses and ports. Each destination is identified by a 16-byte (128-bit) hash derived from cryptographic identity and naming information.

**Key property**: Destinations are location-independent. The same destination hash works regardless of network topology or physical location.

## Four Destination Types

```python
SINGLE = 0x00  # Encrypted with recipient's public key (asymmetric)
GROUP  = 0x01  # Encrypted with shared key (symmetric)
PLAIN  = 0x02  # Unencrypted, broadcast only
LINK   = 0x03  # Abstract encrypted channel
```

### SINGLE (0x00)

**Purpose**: Encrypted communication to one specific recipient

**Properties**:
- Uses recipient's public key for encryption (asymmetric)
- Multi-hop capable (can traverse network)
- Each packet has unique ephemeral key
- Identified by public key + name hash

**Use cases**: Private messages, RPC calls, file transfers

### GROUP (0x01)

**Purpose**: Encrypted communication to multiple recipients sharing a key

**Properties**:
- Uses pre-shared symmetric key (AES-256)
- All group members can decrypt
- Multi-hop capable
- Key must be distributed out-of-band

**Use cases**: Private group chat, multicast notifications

### PLAIN (0x02)

**Purpose**: Unencrypted broadcast information

**Properties**:
- No encryption
- Broadcast only (single hop, not forwarded)
- Anyone can receive
- Lowest overhead

**Use cases**: Local service discovery, beacons, public announcements

### LINK (0x03)

**Purpose**: Established encrypted channel between two nodes

**Properties**:
- Forward secrecy via ephemeral keys
- Bidirectional communication
- Reliable delivery
- Built on top of SINGLE destination

**Use cases**: Interactive sessions, streaming data, reliable messaging

## Destination Hash Calculation

Destination hash is **16 bytes** (128-bit truncated SHA-256).

### For SINGLE Destinations

```python
# Step 1: Create full name without identity
app_name = "myapp"
aspects = ["service", "function"]
full_name = app_name + "." + ".".join(aspects)
# Result: "myapp.service.function"

# Step 2: Calculate name hash (first 10 bytes of SHA-256)
name_hash = SHA256(full_name)[:10]  # 80 bits

# Step 3: Calculate identity hash (first 16 bytes of SHA-256 of public key)
identity_hash = SHA256(public_key)[:16]  # 128 bits

# Step 4: Combine and hash to get destination hash
combined = name_hash + identity_hash  # 26 bytes
destination_hash = SHA256(combined)[:16]  # Final 128-bit address
```

### For GROUP Destinations

```python
# GROUP destinations hash ONLY the name - same algorithm as PLAIN
# The group key is used for ENCRYPTION, not address calculation

# Step 1: Create full name
full_name = "myapp.group.channel"

# Step 2: Calculate name hash (first 10 bytes)
name_hash = SHA256(full_name.encode('utf-8'))[:10]

# Step 3: Hash the name_hash to get destination hash
destination_hash = SHA256(name_hash)[:16]

# Note: Group key is set separately via set_group_key()
# and encrypts/decrypts packets, not part of address
```

### For PLAIN Destinations

```python
# PLAIN uses the same algorithm as GROUP
full_name = "myapp.broadcast.beacon"
name_hash = SHA256(full_name.encode('utf-8'))[:10]
destination_hash = SHA256(name_hash)[:16]
```

## Destination Naming Convention

Destinations use hierarchical dotted notation:

```
app_name.aspect1.aspect2.aspect3...
```

**Rules**:
- App name is required (no dots in app name)
- Aspects are optional (0 or more)
- Aspects can contain any characters except dots
- Case sensitive
- UTF-8 encoded

**Examples**:
- `"fileserver.files"`
- `"chat.group.engineering"`
- `"sensor.temperature.outdoor"`
- `"lxmf.delivery"`

## Name Hash vs Destination Hash

**Name hash** (10 bytes): Hash of name string only, without identity
- Used as input to destination hash calculation
- Not unique (same name used by different identities)

**Destination hash** (16 bytes): Final unique address
- Includes identity for SINGLE destinations
- Globally unique
- Used for packet addressing

## Address Format

Addresses displayed as hex enclosed in angle brackets:

```
<13425ec15b621c1d928589718000d814>
<a5f72aefc8e8679e9f4a5a0a1b2c3d4e>
```

This is the destination_hash in hexadecimal.

## Proof Strategies

Destinations can require proof of delivery:

```python
PROVE_NONE = 0x21  # No proofs required
PROVE_APP  = 0x22  # Application decides per-packet
PROVE_ALL  = 0x23  # Proof required for every packet
```

**PROVE_NONE**: Fast, no delivery confirmation. Use for non-critical data.

**PROVE_APP**: Application sets proof requirement per packet. Flexible approach.

**PROVE_ALL**: Every packet must be proven. Reliable but higher overhead. Default for most destinations.

## Collision Probability

With 128-bit hashes:
- **Birthday bound**: 2^64 hashes before 50% collision probability
- **Practical**: Negligible collision risk for realistic network sizes
- Even 1 billion destinations: < 10^-19 collision probability

## Public Key in SINGLE Destinations

SINGLE destinations embed public key in destination hash calculation:

**Purpose**:
- Ensures global uniqueness (same name, different identities → different hashes)
- Binds destination to cryptographic identity
- Prevents impersonation

**Process**:
1. Node generates Identity (512-bit keypair)
2. Public key (64 bytes) hashed → identity_hash (16 bytes)
3. identity_hash combined with name_hash → destination_hash

**Result**: Only the holder of the private key can decrypt packets to that destination.

## Ratchets (Optional)

Destinations can use ratchets for forward secrecy on announces:

```python
RATCHET_COUNT = 512        # Number of ratchet keys to retain
RATCHET_EXPIRY = 2592000   # 30 days
RATCHET_INTERVAL = 1800    # 30 minutes between rotations
```

When ratchet enabled:
- Destination periodically rotates ratchet key
- Ratchet hash included in announce
- Provides forward secrecy for SINGLE destination announces

## Destination Direction

```python
IN  = 0x11  # Destination receives packets (server)
OUT = 0x12  # Destination sends packets (client)
```

**IN**: Accepts inbound packets. Creates receiver. Used for services.

**OUT**: Sends outbound packets. No receiver. Used for clients.

## Callbacks

IN destinations can register callbacks:

```python
destination.set_packet_callback(handler_function)
destination.set_proof_strategy(PROVE_ALL)
```

**packet_callback**: Function called when packet received
**link_established_callback**: Called when link established to this destination

## Announce Mechanism

SINGLE and GROUP destinations can announce their presence:

```python
destination.announce()
```

**Announce packet contains**:
- Destination hash (16 bytes)
- Public key (64 bytes for SINGLE)
- Name hash (10 bytes)
- Random hash (10 bytes) for uniqueness
- Optional: Ratchet (32 bytes)
- Signature (64 bytes)
- Optional: Application data

See `announce-mechanism` skill for details.

## Implementation Notes

### Creating Destinations

```python
# SINGLE destination (IN)
destination = RNS.Destination(
    identity,                    # Identity object
    RNS.Destination.IN,         # Direction
    RNS.Destination.SINGLE,     # Type
    "app_name", "aspect1"       # Name components
)

# GROUP destination
destination = RNS.Destination(
    None,                        # No identity for GROUP
    RNS.Destination.IN,
    RNS.Destination.GROUP,
    "app_name", "group_name"
)
destination.set_group_key(group_key)  # 32-byte key

# PLAIN destination
destination = RNS.Destination(
    None,                        # No identity for PLAIN
    RNS.Destination.IN,
    RNS.Destination.PLAIN,
    "app_name", "broadcast"
)
```

### Destination Registry

Transport layer maintains destination registry:
- All active destinations registered automatically
- Incoming packets routed to correct destination
- Link requests matched to destinations

## Further Reading

For detailed specifications:
- `references/destination-types.md` - Type comparison table
- `references/naming.md` - Naming rules and restrictions
- `references/addressing.md` - Hash calculation algorithm details
- `references/wire-examples.py` - Complete hash calculation examples

Related skills:
- `packets-wire-format` - How destination hash appears in packets
- `announce-mechanism` - How destinations announce themselves
- `cryptography-identity` - Identity and key generation
- `links` - LINK destination type details

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Destination.py`
