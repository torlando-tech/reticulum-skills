# Link Establishment Process

Complete 7-step link establishment procedure extracted from understanding.rst lines 518-577.

---

## Overview

The link establishment process creates an abstract encrypted channel between two nodes with forward secrecy and initiator anonymity. The process uses a 3-packet handshake with ECDH key exchange.

## Seven-Step Process

### Step 1: Generate Ephemeral Keys

**Initiator action:**

When a node wants to establish a link, it randomly generates a new X25519 key pair:

- **Encryption keypair**: X25519 for ECDH (32-byte private key, 32-byte public key)
- **Signing keypair**: Ed25519 for message authentication (32-byte private key, 32-byte public key)

Note: These are two separate keypairs sent together (64 bytes total public key material). They're referred to collectively as LKi (Link Key initiator).

### Step 2: Create and Broadcast Link Request

**Initiator action:**

Create link request packet containing:
- Destination hash (16 bytes) - identifies desired destination
- LKi (64 bytes) - newly generated public keys

The packet is broadcast using LINKREQUEST packet type (0x02).

### Step 3: Forward Through Network

**Transport node action:**

The link request packet is forwarded through the network according to standard routing rules:
- Lookup destination in path table
- Forward to next hop
- Increment hop count

### Step 4: Store Link Entry

**Transport node action:**

Any node that forwards the link request stores a link table entry:
- **link_id**: Hash of entire link request packet (16 bytes)
- **hops**: Number of hops packet had when received

If the link request is not proven within establishment timeout, the entry is dropped from the link table.

Timeout calculation:
```
timeout = hops × ESTABLISHMENT_TIMEOUT_PER_HOP
timeout = hops × 6 seconds
```

### Step 5: Destination Accepts Request

**Destination action:**

When destination receives link request:

1. **Decide acceptance**: Check if link should be accepted (based on callbacks, filters, etc.)

2. **Generate ephemeral keys**: Create new X25519 encryption keypair (Lr_priv, Lr_pub)

3. **Perform ECDH**: Calculate shared secret
   ```
   shared_secret = X25519(Lr_priv, Li_pub)
   ```
   Where Li_pub is from the link request

4. **Derive link keys**: Use HKDF to derive symmetric encryption and HMAC keys from shared_secret

### Step 6: Send Link Proof

**Destination action:**

Construct link proof packet addressed to link_id containing:

1. **LKr** (32 bytes): Newly generated X25519 public key (Lr_pub)

2. **Signature** (64 bytes): Ed25519 signature of (link_id + LKr) using destination's *persistent* signing key (proves identity)

The link proof uses PROOF packet type (0x03) with context LRPROOF (0xFF).

**Verification by transport nodes:**

All nodes that forwarded the original link request can now:
- Verify the signature using destination's known public key
- Confirm the intended destination received and accepted the request
- Confirm the forwarding path was valid
- Mark the link as ACTIVE in their link table

An abstract bidirectional channel now exists. Packets can be exchanged by addressing them to the link_id.

### Step 7: Initiator Completes ECDH

**Initiator action:**

When initiator receives link proof:

1. **Verify signature**: Check Ed25519 signature matches destination's known public key
   - This proves the response came from the correct destination
   - No impersonation possible

2. **Extract Lr_pub**: Get destination's ephemeral public key from link proof

3. **Perform ECDH**: Calculate shared secret
   ```
   shared_secret = X25519(Li_priv, Lr_pub)
   ```

4. **Derive link keys**: Use HKDF to derive same symmetric keys that destination derived

5. **Send RTT measurement**: Optionally send packet with LRRTT context to measure round-trip time

Both ends now have:
- Identical shared symmetric keys
- Ability to encrypt/decrypt link traffic
- Forward secrecy (keys exist only for this link)

---

## Initiator Anonymity

Key property: **The link initiator remains completely anonymous**.

How anonymity is preserved:
- No source address in link request packet
- Ephemeral keys not tied to initiator's identity
- Link proof routes back via reverse table (transport nodes remember ingress interface)
- Initiator identity never revealed until explicitly shared over the established link

This enables:
- Private communication initiation
- Protection from network surveillance
- Anonymous service access

---

## Packet Flow Diagram

```
Initiator                Transport Nodes              Destination
    |                           |                          |
    |-- LinkReq(LKi) --------→  |                          |
    |   [LINKREQUEST]            |                          |
    |                            |-- Store link_id, hops    |
    |                            |                          |
    |                            |-- Forward -------------→ |
    |                            |                          |
    |                            |                          |-- Accept
    |                            |                          |-- Gen Lr_priv/pub
    |                            |                          |-- ECDH
    |                            |                          |-- Derive keys
    |                            |                          |
    |                            | ←-- LinkProof(LKr,sig)---|
    |                            |     [PROOF, LRPROOF]     |
    |                            |                          |
    |                            |-- Verify signature       |
    |                            |-- Mark link active       |
    | ←-- Forward -------------  |                          |
    |                            |                          |
    |-- Verify signature         |                          |
    |-- ECDH                     |                          |
    |-- Derive keys              |                          |
    |                            |                          |
    |-- RTT packet ------------→ |-- Forward -------------→ |
    |   [DATA, LRRTT]            |                          |
    |                            |                          |
    ▼                            ▼                          ▼
 ACTIVE                      Link Active                ACTIVE
```

---

## Link ID as Destination

After link establishment, the link_id functions as a destination hash:

- All packets addressed to link_id are routed to the link
- Transport nodes know which interface leads toward both link endpoints
- Bidirectional communication using single identifier
- No additional routing announcements needed

---

## Security Properties

1. **Mutual Authentication**:
   - Destination proves identity via signature
   - Initiator can choose to remain anonymous or identify later

2. **Forward Secrecy**:
   - Ephemeral keys deleted after link closes
   - Compromise of long-term keys doesn't expose link traffic

3. **Integrity**:
   - All link traffic authenticated via HMAC
   - Tampering detected immediately

4. **Confidentiality**:
   - All link traffic encrypted with AES-256-CBC
   - Unique keys per link

---

## Establishment Timeouts

Timeout per hop: 6 seconds

Examples:
- 1 hop (direct): 6 seconds
- 5 hops: 30 seconds
- 10 hops: 60 seconds
- 128 hops (maximum): 768 seconds (12.8 minutes)

If link proof not received within timeout:
- Link marked as failed
- Resources cleaned up
- Application notified of failure

---

## Source References

- `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` lines 518-577
- `https://github.com/markqvist/Reticulum/RNS/Link.py` (validate_request, prove methods)
