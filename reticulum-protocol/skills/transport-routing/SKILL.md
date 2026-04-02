---
name: transport-routing
description: Reticulum's transport layer and multi-hop routing system. Use when working with transport nodes, routing, multi-hop forwarding, path resolution, hop counts, PATHFINDER constants, or path requests.
---

# Transport & Routing

This skill provides knowledge about Reticulum's transport layer and multi-hop routing system. Invoke when the user mentions transport layer, routing, multi-hop, path resolution, hop count, PATHFINDER constants, transport nodes, or path requests.

## Transport System Overview

The Reticulum transport layer implements trustless,decentralized routing without requiring global path knowledge or centralized coordination. Each node makes independent per-hop forwarding decisions based on locally stored path information derived from announce propagation.

### Node Types

**Reticulum Instance**: Standard node that can send and receive packets but does not forward traffic for others. Created by default when instantiating `RNS.Reticulum`.

**Transport Node**: Node with `enable_transport=True` that forwards packets and announces for other nodes. Acts as a router in the network. Maintains path table and performs multi-hop routing.

Key distinction: Enable transport functionality via configuration or programmatically to transform an instance into a transport node.

## Transport Types

Reticulum defines four transport types:

```python
BROADCAST  = 0x00  # Single hop, no routing
TRANSPORT  = 0x01  # Multi-hop routed
RELAY      = 0x02  # Acting as relay node
TUNNEL     = 0x03  # Tunneled connection
```

**BROADCAST** (`0x00`): Packets are not forwarded beyond directly connected interfaces. Used for local-only communication.

**TRANSPORT** (`0x01`): Packets are forwarded multi-hop through the network based on path table entries.

**RELAY** (`0x02`): Node is explicitly relaying packets (less commonly used).

**TUNNEL** (`0x03`): Traffic is being tunneled through another protocol or connection (advanced use case).

## Key Constants

### Pathfinder Constants

```python
PATHFINDER_M  = 128            # Maximum hops
PATHFINDER_R  = 1              # Retransmit retries
PATHFINDER_G  = 5              # Retry grace period (seconds)
PATHFINDER_RW = 0.5            # Random window for announce rebroadcast (seconds)
PATHFINDER_E  = 60*60*24*7     # Path expiration: 7 days (604800 seconds)
AP_PATH_TIME  = 60*60*24       # Access Point path expiration: 1 day
ROAMING_PATH_TIME = 60*60*6    # Roaming path expiration: 6 hours
```

**PATHFINDER_M** (`128`): Absolute maximum number of hops a packet can traverse. Packets exceeding this are dropped. This limit prevents infinite routing loops and bounds network convergence time.

**PATHFINDER_R** (`1`): Number of retransmit attempts if an announce is not heard being rebroadcast by other nodes.

**PATHFINDER_G** (`5` seconds): Grace period to wait after hearing an announce rebroadcast before retrying.

**PATHFINDER_E** (`604800` seconds): Time after which path table entries expire if not refreshed. Paths to destinations that haven't announced recently are removed.

### Path Request Constants

```python
PATH_REQUEST_TIMEOUT = 15      # Timeout for path requests (seconds)
PATH_REQUEST_GRACE   = 0.4     # Grace before announcing (seconds)
PATH_REQUEST_RG      = 1.5     # Extra grace for roaming interfaces
PATH_REQUEST_MI      = 20      # Minimum interval between requests (seconds)
```

**PATH_REQUEST_TIMEOUT** (`15` seconds): Maximum time to wait for a path response before giving up.

**PATH_REQUEST_GRACE** (`0.4` seconds): Time to wait before announcing a path, allowing directly reachable peers to respond first. Prevents unnecessary announces.

**PATH_REQUEST_MI** (`20` seconds): Minimum interval between automated path requests for the same destination to prevent request flooding.

## Path Table Structure

The path table is a dictionary mapping destination hashes to routing information:

```python
path_table = {}  # destination_hash -> (timestamp, received_from, hops, expires, random_blobs, interface, announce_packet)
```

**destination_hash** (16 bytes): Truncated SHA-256 hash identifying the destination.

**timestamp**: When the path entry was learned.

**received_from**: Next-hop hash (where to forward packets for this destination).

**hops**: Number of hops to reach destination from this node.

**expires**: Absolute time when this entry expires.

**random_blobs**: Random values from announce for proof generation.

**interface**: Interface on which announce was received.

**announce_packet**: Cached announce packet for re-verification.

## Routing Algorithm

### Per-Hop Forwarding Decision

When a transport node receives a packet:

1. Check if destination hash is in path_table
2. If yes, lookup next-hop from `received_from` field
3. Forward packet to that next-hop via the recorded interface
4. Increment hop count in packet header
5. If hop count exceeds PATHFINDER_M (128), drop packet

### Path Table Lookup

```python
# Simplified path lookup logic
if destination_hash in Transport.path_table:
    next_hop, interface, hops = Transport.path_table[destination_hash]
    if time.time() < expires:
        # Forward to next_hop via interface
        packet.hops += 1
        if packet.hops <= PATHFINDER_M:
            interface.send(packet)
```

No source routing is used - each node independently decides the next hop based on its local path table built from announce propagation.

## Header Types for Transport

Packets use two header formats:

**HEADER_1** (`0x00`): Single 16-byte destination address. Used for broadcast packets.

```
[FLAGS 1B][HOPS 1B][DEST_HASH 16B][CONTEXT 1B][DATA]
```

**HEADER_2** (`0x01`): Two 16-byte addresses. Used when packet is in transport (being routed).

```
[FLAGS 1B][HOPS 1B][TRANSPORT_ID 16B][DEST_HASH 16B][CONTEXT 1B][DATA]
```

**TRANSPORT_ID**: Hash of the transport node currently routing the packet. Used for proof return path.

When a packet enters the transport layer (multi-hop routing), it switches from HEADER_1 to HEADER_2 format to include the transport node's ID.

## Announce Propagation

See detailed announce mechanism in the `announce-mechanism` skill and `references/announce-mechanism.md`.

Key points for transport layer:

1. Announces build path table entries automatically
2. Each transport node stores announce and rebroadcasts according to bandwidth allocation
3. Announces propagate with increasing hop count
4. Path table maps destination → next hop for packet forwarding
5. Bandwidth allocation default: 2% per interface

## Path Resolution

When a node wants to reach a destination not in its path table:

1. **Send path request**: Broadcast path request packet to `rnstransport.path.request` destination
2. **Wait for grace period** (PATH_REQUEST_GRACE): Allows directly reachable peers to respond first
3. **Transport nodes respond**: Nodes with path knowledge respond with path announcement
4. **Path table updated**: Requestor receives announce and updates path table
5. **Packet forwarding begins**: Subsequent packets use newly learned path

Path requests prevent waiting for natural announce convergence when immediate connectivity is needed.

## Table Maintenance

### Path Expiration

Path entries expire after PATHFINDER_E (7 days) by default. Exceptions:

- **Access Point paths**: Expire after 1 day (86400 seconds)
- **Roaming paths**: Expire after 6 hours (21600 seconds)

Expired entries are removed during periodic table culling (every 5 seconds).

### Reverse Table

```python
reverse_table = {}  # packet_hash -> received_from
REVERSE_TIMEOUT = 8*60  # 8 minutes
```

Stores packet hashes with the interface they arrived on. Used to route proof packets back to the sender. Entries expire after 8 minutes.

### Link Table

```python
link_table = {}  # link_id -> hops
LINK_TIMEOUT = RNS.Link.STALE_TIME * 1.25
```

Stores hop count for active links. Used for link establishment timeout calculation.

## Reachability States

Destinations have three reachability states:

```python
REACHABILITY_UNREACHABLE = 0x00  # No known path
REACHABILITY_DIRECT      = 0x01  # Directly reachable (same segment)
REACHABILITY_TRANSPORT   = 0x02  # Reachable via transport nodes
```

State is determined by path table presence and hop count:
- No path entry: UNREACHABLE
- Hops = 1: DIRECT
- Hops > 1: TRANSPORT

## Network Convergence

Full network convergence (all nodes know paths to all destinations) depends on:

1. **Network size**: Number of destinations announcing
2. **Hop depth**: Maximum number of hops between nodes
3. **Bandwidth**: Available capacity for processing announces
4. **Announce rate**: How often destinations announce (default: on demand)

**Typical convergence time**: ~1 minute for 128-hop networks with sufficient bandwidth.

**Slow networks**: May never reach full convergence but can still route via recursive path resolution. Transport nodes prioritize announces for destinations that are actually requested by local nodes.

## Bandwidth Management

Each interface allocates bandwidth for announce processing (default 2%):

- High-priority announces: Low hop count (local)
- Low-priority announces: High hop count (distant)
- Queuing: Announces wait in priority queue if bandwidth unavailable
- Rate limiting: Prevents any single destination from flooding the network

## Duplicate Detection

```python
packet_hashlist = set()       # Current period hashes
packet_hashlist_prev = set()  # Previous period hashes
hashlist_maxsize = 1000000    # ~1 million packets
```

Packets are hashed and checked against recent packet history to prevent duplicate processing. Duplicate detection uses rolling window with two sets.

## Transport Identity

Each transport node has a persistent identity stored at `storagepath/transport_identity`. This identity:

- Is separate from user identities
- Used for transport-level operations
- Persists across restarts
- Enables optional remote management destination

## Control Destinations

Transport layer creates control destinations:

1. **`rnstransport.path.request`**: Handles path request packets
2. **`rnstransport.tunnel.synthesize`**: Handles tunnel synthesis
3. **`rnstransport.remote.management`**: Optional remote management (if enabled)

These destinations are automatically registered and internal to the transport system.

## Implementation Notes

### Header Type Switching

When implementing transport:
- Receive packet with HEADER_1 (broadcast)
- Lookup destination in path_table
- If forwarding, repack with HEADER_2 including transport node ID
- Forward to next hop with incremented hop count

### Path Table Serialization

Transport nodes persist path table to disk at `storagepath/destination_table` for recovery across restarts. Table includes:
- Destination hash
- Timestamp
- Next hop
- Hop count
- Expiry time
- Random blobs
- Interface hash
- Cached announce packet hash

### Announce Handling

When announce received:
- Increment hop count
- Check if hop count ≤ PATHFINDER_M
- Add to announce_table for retransmission
- Update path_table with next-hop information
- Queue for rebroadcast based on interface bandwidth

### Shared Instance Routing

When a Reticulum instance acts as a **shared instance server** (via `LocalServerInterface`), it routes traffic between external network interfaces and locally connected client applications. This architecture enables multiple applications on the same machine to share a single Reticulum instance.

**Key Architecture**: Shared instances maintain two packet flow paths:

**1. PLAIN+BROADCAST Packet Flow** (Path requests, etc.):
```python
# Handled in main inbound processing (Transport.inbound():1300-1308)
if packet.destination_type == RNS.Destination.PLAIN and packet.transport_type == Transport.BROADCAST:
    if from_local_client:
        # Forward to all interfaces EXCEPT originator
        for interface in Transport.interfaces:
            if interface != packet.receiving_interface:
                Transport.transmit(interface, packet.raw)
    else:
        # Forward to all local clients
        for interface in Transport.local_client_interfaces:
            Transport.transmit(interface, packet.raw)
```

**2. ANNOUNCE Packet Flow** (Critical for network discovery):
```python
# Handled in announce processing (Transport.py:1697-1742)
if len(Transport.local_client_interfaces):
    for local_interface in Transport.local_client_interfaces:
        if packet.receiving_interface != local_interface:
            new_announce = RNS.Packet(
                announce_destination,
                announce_data,
                RNS.Packet.ANNOUNCE,
                transport_type = Transport.TRANSPORT,
                transport_id = Transport.identity.hash,
                attached_interface = local_interface
            )
            new_announce.hops = packet.hops
            new_announce.send()  # Immediate transmission
```

**Critical Difference**: ANNOUNCE packets are **immediately retransmitted** to all local client interfaces when received, bypassing the normal announce queue and rate limiting. This ensures clients get instant network visibility without queue processing delays.

**Why Two Mechanisms?**
- **PLAIN+BROADCAST**: Simple forwarding for single-hop packets (path requests)
- **ANNOUNCE**: Must handle multi-hop propagation with proper transport_id stamping and immediate delivery for network discovery

**Implementation Note**: When implementing shared instance support, announces MUST be handled specially in `processAnnounce()` with immediate retransmission to `local_client_interfaces`, not queued like normal announce propagation.

**Interface Identification**:
```python
# Mark server interface
is_local_shared_instance = True  # On LocalServerInterface

# Track spawned client interfaces
Transport.local_client_interfaces = []  # List of interfaces spawned by server
```

**Common Bug**: Forgetting immediate announce retransmission causes clients to see no network announces even though the server receives them. Announces get stuck in rate-limited queues instead of flowing immediately to clients.

## Further Reading

For detailed protocol specifications and wire-level examples, see:

- `references/announce-mechanism.md` - Full announce propagation algorithm
- `references/path-resolution.md` - Path request/response flows
- `references/routing-tables.md` - Table structures and management
- `references/wire-examples.py` - Byte-level packet construction

For related protocol concepts:

- `packets-wire-format` skill - Packet header structures
- `announce-mechanism` skill - Detailed announce propagation
- `interfaces` skill - Interface modes and propagation rules
- `destinations` skill - Destination addressing and hashing

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Transport.py` (lines 43-250)
- `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` (lines 367-430)
- `https://github.com/markqvist/Reticulum/RNS/Transport.py` (lines 1697-1742) - Shared instance announce forwarding
- `https://github.com/torlando-tech/reticulum-kt/rns-core/src/main/kotlin/network/reticulum/transport/Transport.kt` (lines 2319-2338) - Kotlin implementation
