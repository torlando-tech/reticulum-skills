# Routing Tables

Transport nodes maintain several tables for routing and packet management.

## Path Table

Primary routing table mapping destinations to next hops:

```python
path_table = {}  # destination_hash -> (timestamp, received_from, hops, expires, random_blobs, interface, announce_packet)
```

### Entry Structure

**Key**: `destination_hash` (bytes, 16 bytes)
- Truncated SHA-256 hash of destination

**Value**: Tuple with 7 elements:

1. **timestamp** (float): When path was learned (Unix timestamp)
2. **received_from** (bytes, 16 bytes): Hash of next-hop node
3. **hops** (int): Number of hops to destination from this node
4. **expires** (float): Absolute expiry time (Unix timestamp)
5. **random_blobs** (list): Random values from announce for proof generation
6. **interface** (Interface object): Interface on which announce was received
7. **announce_packet** (bytes): Cached announce packet for verification

### Expiry Times

Different path types have different expiry times:

```python
# Normal paths
expires = timestamp + PATHFINDER_E  # 7 days (604800 seconds)

# Access Point paths (from interface in MODE_ACCESS_POINT)
expires = timestamp + AP_PATH_TIME  # 1 day (86400 seconds)

# Roaming paths (from interface in MODE_ROAMING)
expires = timestamp + ROAMING_PATH_TIME  # 6 hours (21600 seconds)
```

### Lookup Operation

```python
def get_next_hop(destination_hash):
    if destination_hash in Transport.path_table:
        entry = Transport.path_table[destination_hash]
        timestamp, received_from, hops, expires, random_blobs, interface, announce_packet = entry

        # Check expiry
        if time.time() < expires:
            return received_from, interface, hops
        else:
            # Path expired, remove it
            del Transport.path_table[destination_hash]
            return None
    return None
```

### Persistence

Path table is serialized to disk at `storagepath/destination_table`:

```python
def save_path_table():
    serialised_destinations = []
    for destination_hash, entry in Transport.path_table.items():
        timestamp, received_from, hops, expires, random_blobs, interface, announce_packet = entry

        serialised_entry = [
            destination_hash,
            timestamp,
            received_from,
            hops,
            expires,
            random_blobs,
            interface.hash,  # Store interface hash, not object
            announce_packet.hash  # Store packet hash for cache lookup
        ]
        serialised_destinations.append(serialised_entry)

    # Write to disk with umsgpack
    with open(path_table_path, "wb") as file:
        file.write(umsgpack.packb(serialised_destinations))
```

---

## Reverse Table

Maps packet hashes to ingress interfaces for proof routing:

```python
reverse_table = {}  # packet_hash -> received_from
REVERSE_TIMEOUT = 8*60  # 8 minutes (480 seconds)
```

### Purpose

When a proof packet is generated in response to a data packet, the reverse table provides the return path.

### Entry Structure

**Key**: `packet_hash` (bytes, variable length)
- Hash of the original packet

**Value**: Tuple:
- **received_from** (bytes): Hash or identifier of node/interface that sent the packet
- **timestamp** (float): When entry was created

### Operation

```python
# On packet receipt
def inbound_packet(packet, interface):
    # Store in reverse table for proof routing
    packet_hash = packet.get_hash()
    Transport.reverse_table[packet_hash] = (interface, time.time())

    # Process packet...

# On proof transmission
def send_proof(proof_packet, original_packet_hash):
    if original_packet_hash in Transport.reverse_table:
        interface, timestamp = Transport.reverse_table[original_packet_hash]

        # Check not expired
        if time.time() - timestamp < REVERSE_TIMEOUT:
            # Send proof back via same interface
            interface.send(proof_packet)
```

### Expiry

Entries automatically expire after REVERSE_TIMEOUT (8 minutes). Periodic cleanup:

```python
def clean_reverse_table():
    current_time = time.time()
    expired = [
        packet_hash
        for packet_hash, (interface, timestamp) in Transport.reverse_table.items()
        if current_time - timestamp > REVERSE_TIMEOUT
    ]
    for packet_hash in expired:
        del Transport.reverse_table[packet_hash]
```

---

## Link Table

Tracks hop counts for active links:

```python
link_table = {}  # link_id -> hops
LINK_TIMEOUT = RNS.Link.STALE_TIME * 1.25  # ~900 seconds
```

### Purpose

Stores hop count information for links to calculate establishment timeouts and RTT values.

### Entry Structure

**Key**: `link_id` (bytes, 16 bytes)
- Hash identifying the link

**Value**: Integer
- **hops** (int): Number of hops to link peer

### Usage

```python
# Calculate link establishment timeout
def get_establishment_timeout(link_id):
    if link_id in Transport.link_table:
        hops = Transport.link_table[link_id]
    else:
        hops = 1  # Assume direct if unknown

    timeout = hops * RNS.Link.ESTABLISHMENT_TIMEOUT_PER_HOP
    return timeout
```

---

## Announce Table

Temporary storage for announces awaiting retransmission:

```python
announce_table = {}  # destination_hash -> announce_data
held_announces = {}  # destination_hash -> announce_data (temporarily held)
```

### Purpose

Queues announces for rebroadcast according to bandwidth availability and priority.

### Entry Structure

**Key**: `destination_hash` (bytes, 16 bytes)

**Value**: Dictionary containing:
- **packet**: Announce packet object
- **hops**: Hop count when received
- **timestamp**: When announce was received
- **retransmitted**: Boolean, has it been retransmitted
- **retries**: Number of retransmit attempts
- **next_retry**: Time of next retry

### Priority Calculation

```python
# Priority is inversely proportional to hop count
priority = 1.0 / hops

# Lower hop count (local) = higher priority
# Higher hop count (distant) = lower priority
```

Announces are processed in priority order when bandwidth becomes available on interfaces.

---

## Announce Rate Table

Tracks announce rates per destination to prevent flooding:

```python
announce_rate_table = {}  # destination_hash -> [timestamp1, timestamp2, ...]
MAX_RATE_TIMESTAMPS = 16  # Keep last 16 announce times
```

### Purpose

Prevents any single destination from flooding network with excessive announces.

### Operation

```python
def check_announce_rate(destination_hash):
    if destination_hash not in Transport.announce_rate_table:
        Transport.announce_rate_table[destination_hash] = []

    timestamps = Transport.announce_rate_table[destination_hash]

    # Add current timestamp
    timestamps.append(time.time())

    # Keep only last MAX_RATE_TIMESTAMPS
    if len(timestamps) > MAX_RATE_TIMESTAMPS:
        timestamps = timestamps[-MAX_RATE_TIMESTAMPS:]
        Transport.announce_rate_table[destination_hash] = timestamps

    # Calculate announce rate
    if len(timestamps) >= 2:
        time_span = timestamps[-1] - timestamps[0]
        rate = len(timestamps) / time_span  # announces per second
        return rate

    return 0.0
```

---

## Path States Table

Tracks state of known destinations:

```python
path_states = {}  # destination_hash -> state
```

### States

```python
STATE_UNKNOWN      = 0x00  # Never heard from this destination
STATE_UNRESPONSIVE = 0x01  # Known but not responding
STATE_RESPONSIVE   = 0x02  # Active and responding
```

Used for network monitoring and diagnostics.

---

## Discovery Tables

For managing path requests on behalf of other nodes:

```python
discovery_path_requests = {}  # request_hash -> request_data
discovery_pr_tags = []        # list of request tags
max_pr_tags = 32000          # Maximum tags to remember
```

### Purpose

Tracks path requests being forwarded/resolved recursively through the network.

---

## Table Culling

All tables are periodically cleaned to remove expired entries:

```python
tables_cull_interval = 5.0  # Every 5 seconds
tables_last_culled = 0.0

def cull_tables():
    current_time = time.time()

    if current_time - Transport.tables_last_culled > Transport.tables_cull_interval:
        # Cull path table
        expired_paths = [
            dest_hash
            for dest_hash, entry in Transport.path_table.items()
            if current_time > entry[3]  # entry[3] is expires
        ]
        for dest_hash in expired_paths:
            del Transport.path_table[dest_hash]

        # Cull reverse table
        expired_reverse = [
            packet_hash
            for packet_hash, (interface, timestamp) in Transport.reverse_table.items()
            if current_time - timestamp > REVERSE_TIMEOUT
        ]
        for packet_hash in expired_reverse:
            del Transport.reverse_table[packet_hash]

        # Update timestamp
        Transport.tables_last_culled = current_time
```

---

## Memory Considerations

From `https://github.com/markqvist/Reticulum/RNS/Transport.py` comments:

> 1 megabyte of memory can store approximately 55,100 path table entries or approximately 22,300 link table entries.

This provides guidance for embedded implementations with limited RAM.

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Transport.py` (lines 94-137, table definitions)
- `https://github.com/markqvist/Reticulum/RNS/Transport.py` (table management methods)
