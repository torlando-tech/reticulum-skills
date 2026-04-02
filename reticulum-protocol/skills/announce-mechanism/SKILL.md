---
name: announce-mechanism
description: Detailed knowledge of Reticulum's announce mechanism for automatic path discovery. Use when working with announce propagation, path discovery, announce bandwidth, announce forwarding, path requests, or announce structure.
---

# Announce Mechanism

This skill provides detailed knowledge about Reticulum's announce mechanism for automatic path discovery. Invoke when the user mentions announce, announce propagation, path discovery, announce bandwidth, announce forwarding, path request, or announce structure.

## Overview

The announce mechanism is Reticulum's core method for automatic path discovery and establishing end-to-end connectivity. When a destination announces itself, the announcement propagates through the network, allowing any node to discover and reach that destination without manual configuration or centralized coordination.

Announces serve two critical functions:
1. **Public Key Distribution**: Share the destination's public key for encrypted communication
2. **Path Establishment**: Create routing entries at transport nodes for multi-hop forwarding

## Announce Packet Structure

An announce packet consists of a standard packet header plus the announce payload:

**Packet Header** (separate from payload):
- DEST_HASH (16 bytes) is in the packet address field, NOT the announce payload

**Announce Payload** (the data portion):
```
[PUB_KEY 64B][NAME_HASH 10B][RANDOM_HASH 10B][RATCHET? 32B][SIGNATURE 64B][APP_DATA?]
```

### Component Breakdown

**DEST_HASH** (16 bytes, in packet header): Truncated SHA-256 hash of the destination being announced. Located in the packet's address field, not the payload. Used for routing.

**PUB_KEY** (64 bytes): Full X25519/Ed25519 public key (32 bytes encryption + 32 bytes signing). Used by receivers to reconstruct the destination and encrypt traffic.

**NAME_HASH** (10 bytes): Truncated SHA-256 hash of the destination's full name (app_name + aspects). Helps receivers identify the destination type without transmitting the full name.

**RANDOM_HASH** (10 bytes): Unique blob making each announce distinct. Composed of 5 random bytes + 5 bytes timestamp (big-endian). Prevents duplicate detection from blocking refreshed announces.

**RATCHET** (32 bytes, optional): Current X25519 ratchet public key for forward secrecy. Present only if destination uses ratchets. Indicated by packet context flag.

**SIGNATURE** (64 bytes): Ed25519 signature over all preceding fields (including destination hash, which is signed but not transmitted in the data portion). Ensures authenticity and prevents spoofing.

**APP_DATA** (variable, optional): Application-specific data such as user nickname, status, version, capabilities, etc. Can be any length but should be minimized to conserve bandwidth.

### Announce Payload Sizes

**Without ratchet**: 64 + 10 + 10 + 64 = **148 bytes** (plus optional app data)

**With ratchet**: 64 + 10 + 10 + 32 + 64 = **180 bytes** (plus optional app data)

These are minimum sizes for the announce **payload only**. The packet header (including DEST_HASH) adds 19 bytes (HEADER_1 format), for total packet sizes of approximately 167 and 199 bytes respectively.

## Signature Verification

The signature is computed over the following signed data:

```python
signed_data = destination_hash + public_key + name_hash + random_hash + ratchet + app_data
```

**Critical**: The destination hash is included in the signed data even though it's already in the packet header. This binds the public key cryptographically to the destination hash, preventing relay attacks where an attacker might try to substitute a different destination hash.

The signature can be verified by any node that receives the announce using the public key contained in the announce itself. This creates a self-authenticating packet.

## Announce Propagation Rules

When a transport node receives an announce, it applies the following forwarding algorithm:

### 1. Duplicate Detection
- Check if this exact announce (identified by destination hash + random hash) has been seen before
- If yes, discard immediately to prevent routing loops
- If no, proceed to next step

### 2. Hop Limit Check
- Increment hop count
- If hops > PATHFINDER_M + 1 (129 hops), discard the announce
- Otherwise, record the announce in the path table

### 3. Path Table Update
```python
path_table[destination_hash] = {
    "timestamp": time.time(),
    "received_from": announcing_interface_hash,
    "hops": announce_hops,
    "expires": time.time() + PATHFINDER_E,
    "random_blobs": random_hash,
    "interface": receiving_interface,
    "announce_packet": announce_packet
}
```

### 4. Retransmission Decision
- Apply randomized delay (0 to PATHFINDER_RW seconds)
- Check bandwidth allocation on each interface
- If bandwidth available, retransmit immediately
- If bandwidth exhausted, queue with priority = 1 / hops

### 5. Priority Queuing
Announces closer to their origin (fewer hops) have higher priority:

```python
priority = 1.0 / hop_count
```

This ensures local connectivity converges quickly even on slow networks, while announces for distant destinations wait in queue until bandwidth becomes available.

### 6. Retransmit Confirmation
- After retransmitting, listen for other nodes rebroadcasting the same announce
- If no rebroadcast heard within PATHFINDER_G seconds, retry up to PATHFINDER_R times
- This ensures announces propagate even in sparse networks

## Propagation Constants

```python
PATHFINDER_M  = 128      # Max hops before discarding
PATHFINDER_R  = 1        # Retransmit retries
PATHFINDER_G  = 5        # Retry grace period (seconds)
PATHFINDER_RW = 0.5      # Random window for announce rebroadcast (seconds)
PATHFINDER_E  = 604800   # Path entry expiration (7 days)
```

**PATHFINDER_M** (`128`): Absolute maximum network diameter. Announces exceeding this hop count are dropped. This bounds convergence time and prevents infinite propagation.

**PATHFINDER_R** (`1`): Number of retransmission attempts if rebroadcast is not heard from neighbors. Ensures reliability in lossy networks.

**PATHFINDER_G** (`5` seconds): Grace period to wait for neighbor rebroadcast before retrying. Prevents redundant transmissions.

**PATHFINDER_RW** (`0.5` seconds): Randomization window for retransmit timing. Spreads announce traffic over time to avoid burst congestion.

**PATHFINDER_E** (`604800` seconds): Path table entry lifetime. Paths are removed after 7 days without a refresh announce.

## Bandwidth Management

Interfaces allocate a maximum of **2% bandwidth** for processing announces by default. This percentage is configurable per-interface.

```python
announce_bandwidth_allocation = 0.02  # 2% of interface bandwidth
```

### Bandwidth Allocation Strategy

1. **Immediate Transmission**: If current announce traffic < 2% of interface capacity, transmit immediately after random delay
2. **Priority Queue**: If over capacity, insert into priority queue sorted by hop count (lower hops = higher priority)
3. **Backpressure**: Queue grows during high network activity, drains during quiet periods
4. **Local Priority**: Nearby destinations (few hops) always get priority over distant ones

This ensures local network segments maintain connectivity even when connected to much larger, faster networks that generate many announces.

## Path Requests

When a node needs to send a packet to an unknown destination, it can issue a **path request**:

```python
PATH_REQUEST_TIMEOUT = 15    # Timeout for path requests (seconds)
PATH_REQUEST_GRACE   = 0.4   # Grace before announcing (seconds)
PATH_REQUEST_MI      = 20    # Minimum interval between requests (seconds)
```

### Path Request Process

1. **Initiation**: Send a path request packet addressed to the unknown destination hash
2. **Propagation**: The path request propagates through the network like a normal packet (transport nodes forward it)
3. **Response**: If the destination or a transport node with a cached path receives it, they respond with a path response (which is an announce)
4. **Timeout**: Wait up to PATH_REQUEST_TIMEOUT (15 seconds) for a response
5. **Rate Limiting**: Don't send another path request for the same destination within PATH_REQUEST_MI (20 seconds)

### Path Response Structure

A path response is an announce packet with:
- **Context**: `RNS.Packet.PATH_RESPONSE` instead of `RNS.Packet.NONE`
- **Content**: Full announce data (public key, signature, app data)
- **Destination**: Sent back toward the requesting node using the reverse path

The path response follows the return path established by the path request, allowing bidirectional communication.

## Network Convergence

Network convergence refers to the time required for all nodes to learn paths to all destinations after an announce is sent.

### Convergence Time Factors

1. **Network Diameter**: Number of hops in the longest path
2. **Interface Bandwidth**: Available capacity for announce processing
3. **Announce Rate**: How many destinations are announcing simultaneously
4. **Retransmission Delays**: Random windows and retry grace periods

### Typical Convergence Times

**Fast Networks** (high bandwidth, low latency):
- Small network (< 10 hops): ~1-5 seconds
- Medium network (< 50 hops): ~10-30 seconds
- Large network (< 128 hops): ~30-60 seconds

**Slow Networks** (low bandwidth, high latency):
- May take several minutes to reach full convergence
- Local segments converge quickly (priority queuing)
- Distant destinations appear gradually as bandwidth permits

### Worst-Case Convergence

For a maximum-diameter network (128 hops) with adequate bandwidth:
- **~1 minute** to achieve full end-to-end connectivity
- Priority system ensures local connectivity much faster (~seconds)

Even networks that never reach full convergence can still communicate via recursive path resolution: slow segments query faster segments for paths on-demand.

## Announce Types

### 1. Regular Announce
Broadcast periodically or on network join. Used for:
- Initial presence announcement
- Path refresh (before expiry)
- Topology changes (moved to new network segment)

### 2. Path Response Announce
Sent in response to a path request. Characteristics:
- Targeted to requesting node (follows reverse path)
- May use cached announce data for efficiency
- Establishes bidirectional path

### 3. Ratcheted Announce
Includes current ratchet public key for forward secrecy:
- Rotates ratchet on each announce
- Old ratchets expire after RATCHET_EXPIRY (30 days)
- Receiving nodes remember and use latest ratchet

## Application Data in Announces

The optional app_data field allows destinations to include contextual information:

### Common Use Cases
- **User Status**: Online, away, busy, offline
- **Display Name**: Human-readable nickname
- **Service Capabilities**: Supported features, protocol version
- **Resource Advertising**: Available services, file shares
- **Ephemeral Keys**: Additional cryptographic material

### Best Practices
- Keep app_data minimal (< 100 bytes recommended)
- Consider bandwidth impact (app_data included in every announce retransmission)
- Use compact encoding (msgpack, custom binary)
- Don't include frequently-changing data (use regular packets instead)

## Announce Frequency

There is no strict requirement for announce frequency, but typical patterns:

**Periodic Announces**:
- Every few hours to refresh path before expiry
- Recommended: Every 2-4 hours for active destinations

**Event-Driven Announces**:
- On network join or reconnection
- When app_data changes (status update, name change)
- Before extended period of activity (e.g., starting long file transfer)

**Conservative Strategy**:
- Announce once on startup
- Re-announce only when necessary (IP change, long downtime)
- Rely on path requests for discovery

## Security Considerations

### Announce Authenticity
- Every announce is cryptographically signed
- Signature covers destination hash, preventing substitution attacks
- Receiving nodes verify signature before accepting

### Announce Flooding Prevention
- Duplicate detection prevents reprocessing
- Hop limit prevents infinite propagation
- Bandwidth limits prevent announce storms
- Rate limiting on path requests

### Privacy Implications
- Announces are cleartext (not encrypted)
- Public key and name hash are visible to all nodes
- App_data should not contain sensitive information
- Destination hash is pseudonymous but trackable

### Ratchet Forward Secrecy
- Including ratchets in announces enables forward secrecy
- Even if long-term identity key is compromised, past messages remain secure
- Ratchets rotate periodically (each announce)

## Wire Format Example

See `references/wire-examples.py` for a complete implementation of announce packet construction including signature generation.

## Common Questions

**Q: Can announces be encrypted?**
A: No. Announces must be cleartext so any node can learn the public key and establish paths. However, the signature ensures authenticity.

**Q: What happens if two nodes have the same destination hash?**
A: Collisions are astronomically unlikely (2^-128 probability). If it occurred, both destinations would be reachable, but packets might be routed incorrectly.

**Q: Do announces consume a lot of bandwidth?**
A: In sparse networks, no. In dense networks with thousands of destinations, announce traffic can be significant. The 2% bandwidth limit prevents congestion.

**Q: How do mobile destinations re-announce after moving?**
A: Simply send a new announce from the new location. The updated path entry will propagate through the network with the new routing information.

**Q: Can I suppress announces for private destinations?**
A: Yes. Don't call `announce()`. Instead, share the public key out-of-band (QR code, file, manual exchange). Packets can still be sent if both ends know each other's keys.

**Q: What's the difference between an announce and a path request?**
A: An announce is a broadcast from a destination advertising its presence. A path request is a query asking "who knows how to reach this destination?"

## Related Skills

- **Transport & Routing**: How announces populate the path table and enable multi-hop forwarding
- **Destinations**: Destination types and how announce() is called
- **Packets & Wire Format**: Complete packet structure including headers
- **Cryptography & Identity**: Key generation, signature verification, ratchets
