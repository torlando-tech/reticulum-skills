# Path Resolution

Path resolution is the process by which a node discovers a route to a destination that is not in its local path table.

## Path Request Flow

### 1. Initiate Path Request

When a node needs to send a packet to a destination but has no path table entry:

```python
# Node checks path_table
if destination_hash not in Transport.path_table:
    # Check if we've recently requested this path
    if destination_hash not in Transport.path_requests:
        # Send path request
        Transport.request_path(destination_hash)
```

### 2. Path Request Packet

Path request is sent to control destination `rnstransport.path.request`:

- **Packet type**: DATA
- **Destination**: `rnstransport.path.request` (PLAIN destination)
- **Payload**: Requested destination hash (16 bytes)
- **Propagation**: BROADCAST initially, then TRANSPORT

### 3. Grace Period

After sending path request, wait PATH_REQUEST_GRACE (0.4 seconds):

- Allows directly reachable peers to respond first
- Prevents unnecessary announce propagation
- Roaming interfaces get extra grace time (PATH_REQUEST_RG = 1.5s)

### 4. Transport Node Response

Transport nodes with path knowledge respond:

1. Check if requested destination_hash is in path_table
2. If yes, retrieve cached announce packet
3. Resend announce packet toward requestor
4. Announce propagates back to requestor with path information

### 5. Path Table Update

Requestor receives announce response:

```python
# Announce received
announce_packet.unpack()
destination_hash = announce_packet.destination_hash
hops = announce_packet.hops
received_from = announce_packet.receiving_interface

# Update path_table
Transport.path_table[destination_hash] = (
    time.time(),           # timestamp
    received_from,         # next hop
    hops,                  # hop count
    time.time() + PATHFINDER_E,  # expiry
    announce_packet.random_blobs,
    announce_packet.receiving_interface,
    announce_packet
)
```

### 6. Packet Transmission

Now that path exists, original packet can be sent:

```python
if destination_hash in Transport.path_table:
    # Packet can now be routed
    send_packet(packet)
```

## Path Request Timeout

If no response received within PATH_REQUEST_TIMEOUT (15 seconds):

- Request is considered failed
- Destination marked as unreachable
- Application layer notified (if packet has receipt)

```python
timeout = PATH_REQUEST_TIMEOUT  # 15 seconds
start_time = time.time()

while destination_hash not in Transport.path_table:
    if time.time() - start_time > timeout:
        # Path request timed out
        destination_unreachable()
        break
    sleep(0.1)
```

## Minimum Request Interval

To prevent request flooding, minimum interval between requests:

```python
PATH_REQUEST_MI = 20  # 20 seconds

if destination_hash in Transport.path_requests:
    last_request = Transport.path_requests[destination_hash]
    if time.time() - last_request < PATH_REQUEST_MI:
        # Too soon to request again
        return
```

## Path Response Optimization

Transport nodes optimize responses:

### Hop Count Comparison

- Only respond if your path is shorter than requestor's current best path
- Prevents suboptimal path information

### Interface Awareness

- Don't respond back on same interface request arrived on
- Prevents routing loops
- Use reverse_table to determine ingress interface

### Bandwidth Allocation

- Path responses (announces) subject to same 2% bandwidth limit
- Queued with priority based on hop count

## Recursive Resolution

If intermediate transport node doesn't have path:

1. Intermediate node also sends path request
2. Recursively resolved through network
3. Once any transport node responds, path propagates back to original requestor
4. This allows slow segments to reach distant segments without full knowledge

## Discovery Path Requests

Transport nodes can request paths on behalf of other nodes:

```python
discovery_path_requests = {}  # Track path requests we've forwarded
discovery_pr_tags = []        # Track request tags to prevent loops
max_pr_tags = 32000           # Maximum tags to remember
```

This enables:
- Nodes without transport capability to reach any destination
- Recursive path resolution across network segments
- Efficient bandwidth usage on slow links

## Path Request Destination

Control destination for path requests:

```python
# Created automatically by Transport.start()
path_request_destination = RNS.Destination(
    None,
    RNS.Destination.IN,
    RNS.Destination.PLAIN,
    "rnstransport",
    "path",
    "request"
)
```

- **Type**: PLAIN (unencrypted, broadcast-friendly)
- **Direction**: IN (receives path requests)
- **Name**: `rnstransport.path.request`
- **Handler**: `Transport.path_request_handler()`

All transport nodes register this destination automatically.

## Implementation Example

Complete path request/response cycle:

```python
def send_packet_with_path_resolution(packet):
    destination_hash = packet.destination_hash

    # Check if path exists
    if destination_hash not in Transport.path_table:
        # No path, request it
        request_path(destination_hash)

        # Wait for path with timeout
        timeout = PATH_REQUEST_TIMEOUT
        start_time = time.time()

        while destination_hash not in Transport.path_table:
            if time.time() - start_time > timeout:
                raise DestinationUnreachable(destination_hash)
            sleep(0.1)

    # Path now available, send packet
    path_info = Transport.path_table[destination_hash]
    next_hop, interface, hops = path_info[1], path_info[5], path_info[2]

    # Set packet transport type
    packet.transport_type = Transport.TRANSPORT
    packet.transport_id = Transport.identity.hash
    packet.hops += 1

    # Send via interface to next hop
    interface.send(packet)
```

## Path Response Context

Path responses use PATH_RESPONSE context (0x0B):

- Distinguishes path response announces from spontaneous announces
- Helps with priority and bandwidth management
- Context flag set in packet header

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Transport.py` (path_request_handler, request_path methods)
- `https://github.com/markqvist/Reticulum/RNS/Packet.py` (PATH_RESPONSE = 0x0B context)
