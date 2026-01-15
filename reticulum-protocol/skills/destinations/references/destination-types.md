# Destination Types Comparison

Complete comparison of the four destination types in Reticulum.

## Type Overview Table

| Property | SINGLE (0x00) | GROUP (0x01) | PLAIN (0x02) | LINK (0x03) |
|----------|---------------|--------------|--------------|-------------|
| **Encryption** | Asymmetric (per-packet ephemeral) | Symmetric (pre-shared key) | None | Asymmetric (per-link ephemeral) |
| **Multi-hop** | Yes | Yes | No (broadcast only) | Yes |
| **Recipients** | One | Multiple with shared key | Anyone | Two (endpoints) |
| **Announce** | Yes | Yes | Yes | No (uses SINGLE) |
| **Identity Required** | Yes | No | No | Yes (built on SINGLE) |
| **Forward Secrecy** | Per-packet | No | N/A | Yes (per-link) |
| **Overhead** | Higher (ephemeral key per packet) | Lower (symmetric) | Lowest (no encryption) | Medium (link setup + symmetric) |

## Encryption Behavior

### SINGLE
- Each packet encrypted with unique ephemeral X25519 key
- Recipient derives decryption key via ECDH with their private key
- Only intended recipient can decrypt
- No key distribution needed (uses public key from announce)

### GROUP
- All packets encrypted with same AES-256 key
- Key must be distributed out-of-band (not via protocol)
- All group members can decrypt all traffic
- Efficient for multicast scenarios

### PLAIN
- No encryption applied
- Data transmitted in cleartext
- Suitable only for public information
- Lowest overhead

### LINK
- Built on top of SINGLE destination
- Establishes encrypted channel with ECDH
- Forward secrecy via ephemeral keys
- Symmetric encryption after establishment

## Use Case Matrix

| Use Case | Recommended Type |
|----------|------------------|
| Private message to one peer | SINGLE |
| RPC call to service | SINGLE |
| File transfer to specific node | SINGLE (or LINK for large files) |
| Group chat (small group) | GROUP |
| Sensor broadcast (public) | PLAIN |
| Local service discovery | PLAIN |
| Interactive session | LINK |
| Large data stream | LINK with Resources |
| Multicast notification | GROUP |

## Performance Characteristics

**SINGLE**:
- ✓ No pre-shared secrets needed
- ✓ Perfect forward secrecy per packet
- ✗ Higher per-packet overhead (~80 bytes encryption)
- ✗ Slower (ECDH per packet)

**GROUP**:
- ✓ Fast symmetric encryption
- ✓ Lower overhead (~48 bytes)
- ✗ Requires key distribution
- ✗ No forward secrecy

**PLAIN**:
- ✓ No encryption overhead
- ✓ Fastest transmission
- ✗ No confidentiality
- ✗ Single-hop only

**LINK**:
- ✓ Forward secrecy
- ✓ Fast symmetric after establishment
- ✓ Reliable delivery
- ✗ 3-packet setup overhead
- ✗ Requires active maintenance (keepalive)

---

**Source**: `https://github.com/markqvist/Reticulum/RNS/Destination.py`
