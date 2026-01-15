# Links

This skill provides knowledge about Reticulum's link system - encrypted channels with forward secrecy. Invoke when the user mentions link establishment, link request, ECDH, ephemeral keys, forward secrecy, keep-alive, or link timeouts.

## Link Overview

Links are abstract encrypted channels between two nodes providing:
- **Forward secrecy** via per-link ephemeral keys
- **Initiator anonymity** - no source addresses exposed
- **Reliable delivery** with sequencing and retransmission
- **Keep-alive** mechanism for connection monitoring
- **Multi-hop support** spanning arbitrary network paths

Unlike traditional connections, links are not tied to specific interfaces or IP addresses. They're abstract channels identified by link hash.

## Link States

```python
PENDING   = 0x00  # Link request sent, awaiting response
HANDSHAKE = 0x01  # Link proof received, deriving keys
ACTIVE    = 0x02  # Link established and operational
STALE     = 0x03  # No traffic, final keep-alive sent
CLOSED    = 0x04  # Link terminated
```

### State Transitions

```
PENDING → HANDSHAKE → ACTIVE → STALE → CLOSED
           ↓                      ↓
           └──────── CLOSED ──────┘
```

**PENDING**: Initial state after sending link request. Waiting for link proof from destination.

**HANDSHAKE**: Link proof received and validated. Performing ECDH key exchange to derive shared secret.

**ACTIVE**: Link fully established. Data can be exchanged with encryption and forward secrecy.

**STALE**: No traffic received for STALE_TIME (720s). Final keep-alive sent. Link will timeout if no response.

**CLOSED**: Link terminated. Reasons: timeout, explicit close, or error.

## Key Constants

```python
ECPUBSIZE = 64                           # Public key size (32B encryption + 32B signing)
KEYSIZE = 32                             # Symmetric key size (AES-256)

ESTABLISHMENT_TIMEOUT_PER_HOP = 6        # Seconds per hop for establishment
KEEPALIVE = 360                          # Keep-alive interval (seconds)
STALE_TIME = 720                         # Time before link considered stale (2×KEEPALIVE)
STALE_GRACE = 5                          # Grace period before timeout (seconds)
KEEPALIVE_TIMEOUT_FACTOR = 4            # Multiplier for RTT-based timeout
```

**ECPUBSIZE** (`64` bytes): Combined size of X25519 encryption public key (32B) + Ed25519 signing public key (32B). Sent together in link request.

**ESTABLISHMENT_TIMEOUT_PER_HOP** (`6` seconds): Timeout per hop. For 10-hop path: `10 × 6 = 60` seconds total timeout.

**KEEPALIVE** (`360` seconds): Interval for sending keep-alive packets when link is idle. Ensures both ends know link is alive.

**STALE_TIME** (`720` seconds): After no traffic for this duration, link enters STALE state and sends final keep-alive.

**STALE_GRACE** (`5` seconds): Additional grace period after final keep-alive before declaring timeout.

## Three-Packet Handshake

Link establishment uses exactly 3 packets totaling 297 bytes:

### Packet 1: Link Request (83 bytes)

Sent by initiator to destination:

```
[HEADER 19B][LKi 64B]
Total: 83 bytes

LKi = encryption_public_key (32B) + signing_public_key (32B)
```

**Header** (19 bytes):
- FLAGS (1B): LINKREQUEST packet type
- HOPS (1B): Initially 0
- DEST_HASH (16B): Destination hash
- CONTEXT (1B): 0x00 (NONE)

**LKi** (64 bytes): Initiator's ephemeral public keys
- X25519 encryption public key (32B)
- Ed25519 signing public key (32B)

With optional MTU signalling (+3 bytes): 86 bytes total

### Packet 2: Link Proof (115 bytes)

Sent by destination back to initiator:

```
[HEADER 19B][LKr 32B][SIGNATURE 64B]
Total: 115 bytes

LKr = responder encryption public key (32B)
SIGNATURE = Ed25519 signature (64B)
```

**Header** (19 bytes):
- FLAGS (1B): PROOF packet type
- HOPS (1B): Incremented by each hop
- LINK_ID (16B): Hash of link request packet
- CONTEXT (1B): 0xFF (LRPROOF - Link Request Proof)

**LKr** (32 bytes): Destination's ephemeral X25519 encryption public key

**SIGNATURE** (64 bytes): Ed25519 signature of (link_id + LKr) using destination's persistent signing key. Proves destination's identity.

With optional MTU signalling (+3 bytes): 118 bytes total

### Packet 3: RTT Measurement (99 bytes)

Sent by initiator to measure round-trip time:

```
[HEADER 19B][ENCRYPTED_DATA 80B]
Total: 99 bytes
```

**Header** (19 bytes):
- FLAGS (1B): DATA packet type
- HOPS (1B)
- LINK_ID (16B)
- CONTEXT (1B): 0xFE (LRRTT - Link Request RTT)

**ENCRYPTED_DATA** (80 bytes): Encrypted timestamp for RTT calculation

## X25519 ECDH Key Exchange

Links use Elliptic Curve Diffie-Hellman on Curve25519:

### Initiator Side

1. Generate ephemeral X25519 private key: `Li_priv`
2. Derive public key: `Li_pub = X25519(Li_priv, G)` where G is generator
3. Send `Li_pub` in link request as part of LKi

When link proof received:
4. Extract `Lr_pub` from link proof
5. Perform ECDH: `shared_secret = X25519(Li_priv, Lr_pub)`
6. Derive link keys via HKDF from shared_secret

### Destination Side

1. Receive link request with `Li_pub`
2. Generate ephemeral X25519 private key: `Lr_priv`
3. Derive public key: `Lr_pub = X25519(Lr_priv, G)`
4. Perform ECDH: `shared_secret = X25519(Lr_priv, Li_pub)`
5. Derive link keys via HKDF from shared_secret
6. Send `Lr_pub` in link proof

Both sides now share the same `shared_secret` without ever transmitting it.

## Link ID Calculation

Link ID is SHA-256 hash of entire link request packet:

```python
link_id = SHA256(link_request_packet)[:16]  # Truncated to 16 bytes
```

This hash serves as:
- Unique identifier for the link
- Destination address for all link packets
- Input to signature verification

## Link Encryption Mode

Currently only AES-256-CBC is enabled:

```python
MODE_AES256_CBC = 0x01
ENABLED_MODES = [MODE_AES256_CBC]
```

Reserved modes for future use:
- MODE_AES128_CBC (0x00)
- MODE_AES256_GCM (0x02)
- MODE_OTP_RESERVED (0x03)
- MODE_PQ_RESERVED_1-4 (0x04-0x07) - Post-quantum reserved

## Keep-Alive Mechanism

Links send keep-alive packets when idle to detect timeouts.

### Keep-Alive Transmission

```python
# Send keep-alive if no traffic for KEEPALIVE seconds
if time_since_last_traffic >= KEEPALIVE:
    send_keepalive()
```

Keep-alive packet:
- CONTEXT: 0xFA (KEEPALIVE)
- DATA: 1 byte payload (0xFF or 0xFE)
- Size: ~20 bytes (header 19 bytes + 1 byte payload)

### Bandwidth Cost

```python
keepalive_size = 20 bytes
keepalive_interval = 360 seconds
bits_per_second = (20 * 8) / 360 = 0.44 bits/second
```

**Total cost: ~0.44 bits/second** per active link

### Link Timeout Calculation

```python
timeout = (RTT * KEEPALIVE_TIMEOUT_FACTOR) + STALE_GRACE

# Example: RTT = 2 seconds
timeout = (2 * 4) + 5 = 13 seconds
```

After entering STALE state (no traffic for 720s):
1. Send final keep-alive
2. Wait for `(RTT × 4) + 5` seconds
3. If no response, declare link timed out and close

## Forward Secrecy

Links provide forward secrecy through:

1. **Ephemeral keys**: New key pair generated for each link
2. **No key reuse**: Keys destroyed after link closes
3. **Separate from identity**: Link keys independent of node identity
4. **ECDH per link**: Each link has unique shared secret

If link keys compromised:
- ✓ Only that link's traffic is exposed
- ✓ Other links remain secure
- ✓ Node identity remains secure
- ✓ Past and future links remain secure

## MTU Signalling

Links negotiate MTU during establishment (optional):

```python
# 3-byte MTU signalling
mtu = 512  # Example MTU
mode = 0x01  # MODE_AES256_CBC

# Encode: 21 bits MTU + 3 bits mode
signalling_value = (mtu & 0x1FFFFF) + (((mode << 5) & 0xE0) << 16)
mtu_bytes = struct.pack(">I", signalling_value)[1:]  # Last 3 bytes
```

Appended to link request (LKi + mtu_bytes) and link proof (LKr + signature + mtu_bytes).

## Link MDU

Maximum data unit for link packets:

```python
# Calculation from Link.py
MDU = floor((MTU - IFAC_MIN_SIZE - HEADER_MINSIZE - TOKEN_OVERHEAD) / AES_BLOCKSIZE) * AES_BLOCKSIZE - 1

# With MTU=500:
MDU = floor((500 - 1 - 19 - 48) / 16) * 16 - 1
MDU = floor(432 / 16) * 16 - 1
MDU = 27 * 16 - 1
MDU = 432 - 1 = 431 bytes
```

This is the maximum application data per link packet after encryption overhead.

## Link Establishment Timeline

```
Time    Initiator              Network             Destination
----    ---------              -------             -----------
t=0     Send LinkReq ─────────────────────────────→ Receive
        State: PENDING                              Validate
                                                    Generate keys
                                                    ECDH
t=RTT/2                        ←───────────────────  Send LinkProof
        Receive                                     State: ACTIVE
        Validate signature
        ECDH
        Send RTT packet ───────────────────────────→ Receive
        State: ACTIVE                               Measure RTT

t=RTT   Link fully established with measured RTT
```

Total establishment time: ~1 RTT for 3-packet handshake

## Implementation Notes

### Initiator Anonymity

Link initiator reveals no identifying information:
- No source address in packets
- Ephemeral keys used (not tied to identity)
- Proof routing via reverse table (stored by transport nodes)

### Link Table

Transport nodes store link entries:

```python
link_table = {
    link_id: hops
}
```

Entries timeout if not proven within establishment timeout period.

### Reliable Delivery

Links provide reliable delivery via:
- Sequence numbers on packets
- Receipt/proof system
- Automatic retransmission on timeout
- Out-of-order detection and reordering

## Further Reading

For detailed protocol specifications:
- `references/link-establishment.md` - Complete 7-step handshake process
- `references/key-exchange.md` - ECDH shared secret derivation and HKDF
- `references/keepalive.md` - Watchdog logic and timeout detection
- `references/wire-examples.py` - Byte-level link request packet construction

Related skills:
- `cryptography-identity` - X25519, Ed25519, HKDF details
- `packets-wire-format` - Packet structure and contexts
- `transport-routing` - Link table and multi-hop routing
- `resources` - Large data transfer over links

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Link.py` (lines 65-200)
- `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` (lines 518-577)
