---
name: resources
description: Reticulum's resource transfer system for large data over links. Use when working with resource transfers, windowing, hashmaps, segments, compression, file transfers, or resource states.
---

# Resources

This skill provides knowledge about Reticulum's resource transfer system for large data over links. Invoke when the user mentions large data transfer, resource transfer, windowing, hashmap, segments, compression, file transfer, or resource states.

## Resource Overview

Resources are Reticulum's mechanism for reliably transferring arbitrary amounts of data over a link. They automatically handle:
- **Sequencing** - Data split into numbered parts
- **Compression** - Optional bz2 compression
- **Coordination** - Dynamic window-based flow control
- **Checksumming** - Hash verification at multiple levels
- **Segmentation** - Large files split into manageable segments

Resources work exclusively over established links, never directly. They're designed to efficiently transfer data of any size - from a few kilobytes to gigabytes - while adapting to link quality.

## Resource States

```python
NONE            = 0x00  # Uninitialized
QUEUED          = 0x01  # Waiting for link readiness
ADVERTISED      = 0x02  # Advertisement sent, awaiting acceptance
TRANSFERRING    = 0x03  # Data transfer in progress
AWAITING_PROOF  = 0x04  # All parts sent, waiting for completion proof
ASSEMBLING      = 0x05  # Receiver assembling complete resource
COMPLETE        = 0x06  # Transfer successful
FAILED          = 0x07  # Transfer failed or cancelled
CORRUPT         = 0x08  # Data integrity check failed
REJECTED        = 0x00  # Receiver rejected the resource
```

### State Flow - Sender Side

```
NONE → QUEUED → ADVERTISED → TRANSFERRING → AWAITING_PROOF → COMPLETE
         ↓          ↓              ↓               ↓
         └──────────┴──────────────┴───────────────┴───────→ FAILED
```

**NONE**: Resource object created but not yet advertised.

**QUEUED**: Resource ready to advertise but link is busy with another transfer. Waiting for link availability.

**ADVERTISED**: Advertisement packet sent to receiver. Waiting for first part request.

**TRANSFERRING**: Receiver has accepted and is requesting parts. Sender transmitting data.

**AWAITING_PROOF**: All parts transmitted. Waiting for receiver's completion proof.

**COMPLETE**: Receiver sent valid proof. Transfer successful.

**FAILED**: Transfer failed due to timeout, network error, or cancellation.

### State Flow - Receiver Side

```
NONE → TRANSFERRING → ASSEMBLING → COMPLETE
         ↓                ↓
         └────────────────┴──────────────────→ FAILED/CORRUPT
```

**TRANSFERRING**: Advertisement accepted, requesting and receiving parts.

**ASSEMBLING**: All parts received. Decrypting, decompressing, and verifying integrity.

**COMPLETE**: Assembly successful, hash verified. Resource data ready.

**CORRUPT**: Hash verification failed. Data integrity compromised.

## Key Constants

```python
# Window management
WINDOW               = 4      # Initial window size
WINDOW_MIN           = 2      # Absolute minimum window
WINDOW_MAX_SLOW      = 10     # Maximum for slow links
WINDOW_MAX_VERY_SLOW = 4      # Maximum for very slow links
WINDOW_MAX_FAST      = 75     # Maximum for fast links
WINDOW_FLEXIBILITY   = 4      # Minimum window range

# Rate thresholds
RATE_FAST            = 6250   # 50 Kbps in bytes/second (50000/8)
RATE_VERY_SLOW       = 250    # 2 Kbps in bytes/second (2000/8)
FAST_RATE_THRESHOLD  = 4      # Rounds to qualify as fast
VERY_SLOW_RATE_THRESHOLD = 2  # Rounds to qualify as very slow

# Data limits
MAX_EFFICIENT_SIZE   = 1048575  # 1MB - 1 byte (0xFFFFFF)
METADATA_MAX_SIZE    = 16777215 # 16MB - 1 byte
AUTO_COMPRESS_MAX_SIZE = 67108864  # 64MB

# Timeout and retry
MAX_RETRIES          = 16     # Maximum part request retries
MAX_ADV_RETRIES      = 4      # Maximum advertisement retries
SENDER_GRACE_TIME    = 10.0   # Extra timeout allowance for sender
RETRY_GRACE_TIME     = 0.25   # Grace before retry
PER_RETRY_DELAY      = 0.5    # Delay per retry attempt

# Hash sizes
MAPHASH_LEN          = 4      # Bytes per part hash in hashmap
RANDOM_HASH_SIZE     = 4      # Random hash prefix size
```

**WINDOW_MIN** (`2`): Absolute minimum window size. Even on worst connections, at least 2 parts can be outstanding.

**WINDOW_MAX_FAST** (`75`): Maximum window for fast links (>50 Kbps sustained). Allows high throughput without overwhelming receiver.

**MAX_EFFICIENT_SIZE** (`1,048,575` bytes): Maximum size for a single resource segment. Larger resources are split into multiple segments. Limited to 3 bytes in advertisement (0xFFFFFF).

**MAPHASH_LEN** (`4` bytes): Each data part is identified by a 4-byte hash. Collision probability is negligible within a resource.

**RANDOM_HASH_SIZE** (`4` bytes): Random prefix added to resource data before hashing. Prevents hash collisions between similar resources.

## Resource Advertisement Format

Resource transfer begins with an advertisement packet using umsgpack:

```python
# Sent by initiator to receiver
context = RNS.Packet.RESOURCE_ADV

advertisement = {
    "t": transfer_size,       # Bytes after encryption (3 bytes max: 0xFFFFFF)
    "d": data_size,           # Uncompressed data size (3 bytes max)
    "n": number_of_parts,     # Total parts in this segment
    "h": resource_hash,       # 32-byte SHA-256 hash
    "r": random_hash,         # 4-byte random hash prefix
    "o": original_hash,       # Hash of first segment (for multi-segment)
    "i": segment_index,       # Current segment (1-based)
    "l": total_segments,      # Total number of segments
    "q": request_id,          # Optional request ID (for request/response)
    "f": flags,               # Bit flags (see below)
    "m": hashmap_segment      # Partial hashmap (first N hashes)
}

# Flags byte (f)
flags = (
    (has_metadata << 5) |     # Bit 5: Metadata present
    (is_response << 4) |      # Bit 4: This is a response to request
    (is_request << 3) |       # Bit 3: This is a request
    (is_split << 2) |         # Bit 2: Multi-segment resource
    (compressed << 1) |       # Bit 1: Data is bz2 compressed
    (encrypted << 0)          # Bit 0: Data is encrypted (always 1)
)
```

### Hashmap Segmentation

The full hashmap may be too large for a single advertisement. Only the first segment is sent:

```python
HASHMAP_MAX_LEN = floor((Link.MDU - 134) / MAPHASH_LEN)

# With typical MDU=431:
# HASHMAP_MAX_LEN = floor((431 - 134) / 4) = floor(297 / 4) = 74 hashes

# Advertisement includes first 74 part hashes (296 bytes)
# Remaining hashes sent via RESOURCE_HMU packets when requested
```

**Overhead calculation**: Advertisement umsgpack structure uses ~134 bytes for fields, leaving room for hashmap.

## Window-Based Transfer Flow

Resources use a sliding window protocol for efficient, adaptive transfer:

### Initial Window Setup

```python
# Receiver initializes window
window = 4                    # Start conservatively
window_min = 2                # Can't go below this
window_max = 10               # Initial limit (slow link assumption)
window_flexibility = 4        # Minimum range between min and max
```

### Request Cycle

1. **Receiver requests parts**:
   ```python
   # Request up to 'window' missing parts
   outstanding_parts = 0
   requested_hashes = b""

   for part_index in range(consecutive_completed + 1, consecutive_completed + window + 1):
       if parts[part_index] is None and hashmap[part_index] is not None:
           requested_hashes += hashmap[part_index]  # 4-byte hash
           outstanding_parts += 1

   request_packet = RNS.Packet(link, hash + requested_hashes, context=RNS.Packet.RESOURCE_REQ)
   ```

2. **Sender transmits requested parts**:
   ```python
   # Sender looks up parts by hash and sends them
   for requested_hash in requested_hashes:
       part = find_part_by_hash(requested_hash)
       part.send()  # context=RNS.Packet.RESOURCE
   ```

3. **Receiver processes parts**:
   ```python
   # Store part and update consecutive completed pointer
   parts[index] = part_data
   if index == consecutive_completed + 1:
       consecutive_completed = index
       # Advance pointer past any already-received parts
       while parts[consecutive_completed + 1] is not None:
           consecutive_completed += 1
   ```

### Dynamic Window Adjustment

Window size adapts based on performance:

```python
# Successful round - all parts received
if outstanding_parts == 0:
    if window < window_max:
        window += 1
        # Increase minimum too if flexibility allows
        if (window - window_min) > (window_flexibility - 1):
            window_min += 1

# Timeout - some parts not received
if timeout:
    if window > window_min:
        window -= 1
        if window_max > window_min:
            window_max -= 1
            # Reduce max further if window too flexible
            if (window_max - window) > (window_flexibility - 1):
                window_max -= 1
```

### Rate-Based Window Limits

The window maximum adjusts based on measured transfer rate:

```python
# Measure request-response RTT rate
rtt = response_time - request_time
req_resp_cost = response_packet_size + request_packet_size
req_resp_rtt_rate = req_resp_cost / rtt  # bytes/second

# Fast link detection (>50 Kbps sustained)
if req_resp_rtt_rate > RATE_FAST:
    fast_rate_rounds += 1
    if fast_rate_rounds >= FAST_RATE_THRESHOLD:
        window_max = WINDOW_MAX_FAST  # Upgrade to 75

# Very slow link detection (<2 Kbps sustained)
if req_resp_rtt_rate < RATE_VERY_SLOW:
    very_slow_rate_rounds += 1
    if very_slow_rate_rounds >= VERY_SLOW_RATE_THRESHOLD:
        window_max = WINDOW_MAX_VERY_SLOW  # Downgrade to 4
```

This creates an adaptive system:
- Fast links: window can grow to 75 parts in flight
- Normal links: window capped at 10 parts
- Very slow links: window capped at 4 parts
- All links: minimum of 2 parts maintained

## Hashmap Updates (HMU)

When the receiver exhausts its current hashmap segment, it requests more:

```python
# Receiver detects hashmap exhaustion
if hashmap[next_part_index] is None:
    hashmap_exhausted = 0xFF
    hmu_request = bytes([hashmap_exhausted]) + last_received_hash + resource_hash
    # Include last_received_hash to identify position

# Sender responds with next hashmap segment
segment_number = part_index // HASHMAP_MAX_LEN
hashmap_start = segment_number * HASHMAP_MAX_LEN
hashmap_end = min((segment_number + 1) * HASHMAP_MAX_LEN, total_parts)

hashmap_segment = b""
for i in range(hashmap_start, hashmap_end):
    hashmap_segment += hashmap[i]  # 4 bytes per part

hmu_packet = umsgpack.packb([segment_number, hashmap_segment])
RNS.Packet(link, resource_hash + hmu_packet, context=RNS.Packet.RESOURCE_HMU).send()
```

This keeps advertisement packets small while supporting resources with thousands of parts.

## Compression with bz2

Resources can optionally compress data before transfer:

```python
# Sender side (auto_compress=True by default)
if auto_compress and data_size <= AUTO_COMPRESS_MAX_SIZE:
    compressed_data = bz2.compress(uncompressed_data)

    if len(compressed_data) < len(uncompressed_data):
        # Compression beneficial
        resource_data = random_hash + compressed_data
        compressed_flag = True
    else:
        # Compression increased size, send uncompressed
        resource_data = random_hash + uncompressed_data
        compressed_flag = False
```

Compression is skipped for data larger than 64MB to avoid excessive CPU and memory usage.

### Decompression on Receive

```python
# Receiver side - after decryption
if compressed_flag:
    data = bz2.decompress(encrypted_data)
else:
    data = encrypted_data

# Verify hash
calculated_hash = SHA256(data + random_hash)
if calculated_hash == advertised_hash:
    # Data valid
```

Typical compression ratios for text data: 3:1 to 10:1. Binary data varies widely.

## Data Integrity Verification

Resources use multiple levels of hashing:

### Level 1: Part Hashes (4 bytes each)

```python
# Each part identified by 4-byte hash
part_data = resource_data[i * sdu : (i+1) * sdu]
part_hash = SHA256(part_data + random_hash)[:4]
hashmap.append(part_hash)
```

Prevents:
- Requesting wrong parts
- Accepting corrupted parts
- Part ordering errors

### Level 2: Resource Hash (32 bytes)

```python
# Complete encrypted resource
resource_hash = SHA256(encrypted_data + random_hash)
```

Advertised to receiver. Verified after assembly.

### Level 3: Completion Proof (32 bytes)

```python
# Receiver proves successful assembly
decrypted_data = link.decrypt(encrypted_resource)
proof = SHA256(decrypted_data + resource_hash)

# Sender verifies against expected proof
expected_proof = SHA256(original_data + resource_hash)
if proof == expected_proof:
    status = COMPLETE
```

This three-level system ensures end-to-end integrity even with encryption.

## Resource Segmentation

Resources larger than MAX_EFFICIENT_SIZE (1MB - 1) are split:

```python
total_segments = ceil(total_size / MAX_EFFICIENT_SIZE)

# Example: 3.2 MB resource
# Segment 1: 1,048,575 bytes
# Segment 2: 1,048,575 bytes
# Segment 3: 1,048,575 bytes
# Segment 4:   206,944 bytes
# Total: 4 segments

# Each segment is a complete resource transfer
# Segments sent sequentially, not in parallel
```

### Segment Coordination

```python
# First segment advertised normally
segment_1 = Resource(data, link, segment_index=1, original_hash=hash1)

# When segment 1 completes, sender advertises segment 2
# Receiver maintains state across segments

# All segments share original_hash for tracking
# Individual segments have unique resource_hash
```

The receiver assembles segments into a single file, verifying each segment before combining.

## Metadata Support

Resources can include structured metadata:

```python
# Sender includes metadata
metadata = {
    "filename": "document.pdf",
    "size": 1024000,
    "hash": "sha256:...",
    "created": 1704067200,
}

resource = Resource(data, link, metadata=metadata)

# Metadata prepended to first segment
# Format: [3-byte size][umsgpack metadata][data]
metadata_size = len(umsgpack.packb(metadata))  # Max 16MB - 1
size_bytes = struct.pack(">I", metadata_size)[1:]  # Last 3 bytes
segment_data = size_bytes + umsgpack.packb(metadata) + data
```

Only the first segment of a multi-segment resource contains metadata.

## Timeout and Retry Logic

Resources implement sophisticated timeout handling:

### Advertisement Timeout

```python
# After sending advertisement
timeout = link.rtt * link.traffic_timeout_factor + PROCESSING_GRACE

if no_request_received_within(timeout):
    if retries_left > 0:
        resend_advertisement()
        retries_left -= 1
    else:
        cancel_resource()  # MAX_ADV_RETRIES = 4
```

### Part Transfer Timeout (Receiver)

```python
# Expected time for outstanding parts
expected_inflight_rate = measured_data_rate  # bytes/second
expected_tof = (outstanding_parts * sdu * 8) / expected_inflight_rate

timeout = last_activity + (PART_TIMEOUT_FACTOR * expected_tof) + RETRY_GRACE_TIME

if time.time() > timeout:
    if retries_left > 0:
        window -= 1  # Reduce window
        request_next()  # Retry
        retries_left -= 1
    else:
        cancel_resource()  # MAX_RETRIES = 16
```

### Proof Timeout (Sender)

```python
# After sending last part
timeout = last_part_sent + (rtt * PROOF_TIMEOUT_FACTOR) + SENDER_GRACE_TIME

if time.time() > timeout:
    if retries_left > 0:
        # Query network cache for proof packet
        request_cache(expected_proof_packet_hash)
        retries_left -= 1
    else:
        cancel_resource()
```

The grace times account for processing delays, especially on resource-constrained devices.

## Transfer Efficiency

Resource overhead varies by size:

### Small Resource (10 KB, ~24 parts)

```
Advertisement:     ~230 bytes
Part requests:     ~105 bytes × ~6 requests = ~630 bytes
Parts:             ~19 bytes header × 24 = ~456 bytes
Proof:             ~115 bytes
Total overhead:    ~1,431 bytes
Payload:           ~10,240 bytes
Efficiency:        87.7%
```

### Large Resource (1 MB, ~2,400 parts)

```
Advertisement:     ~230 bytes
Hashmap updates:   ~1,200 bytes × 32 updates = ~38,400 bytes
Part requests:     ~105 bytes × ~75 requests = ~7,875 bytes
Parts:             ~19 bytes × 2,400 = ~45,600 bytes
Proof:             ~115 bytes
Total overhead:    ~92,220 bytes
Payload:           ~1,048,575 bytes
Efficiency:        91.9%
```

Efficiency improves with size due to fixed overhead amortization. Fast links with large windows achieve near-optimal throughput.

## Resource Cancellation

Either side can cancel a resource:

```python
# Initiator cancels
cancel_packet = RNS.Packet(link, resource_hash, context=RNS.Packet.RESOURCE_ICL)
# ICL = Initiator Cancel

# Receiver rejects advertisement
reject_packet = RNS.Packet(link, resource_hash, context=RNS.Packet.RESOURCE_RCL)
# RCL = Receiver Cancel/Reject

# Both trigger callback with status=FAILED or REJECTED
```

Cancellation is immediate and does not wait for acknowledgment.

## Progress Tracking

Resources support progress callbacks:

```python
def progress_callback(resource):
    progress = resource.get_progress()  # 0.0 to 1.0
    segment_progress = resource.get_segment_progress()

    print(f"Overall: {progress*100:.1f}%")
    print(f"Segment {resource.segment_index}/{resource.total_segments}: {segment_progress*100:.1f}%")

resource = Resource(data, link, progress_callback=progress_callback)
```

Progress is calculated differently for single vs. multi-segment resources to provide accurate overall progress.

## Implementation Notes

### Collision Guard

The sender maintains a collision guard to prevent hash collisions in the hashmap:

```python
COLLISION_GUARD_SIZE = 2 * WINDOW_MAX + HASHMAP_MAX_LEN

# Sender only compares hashes within collision guard range
# If collision detected during hashmap generation, regenerate with new random_hash
```

This ensures requested parts can be uniquely identified.

### Memory Management

Large resources use temporary files to avoid memory exhaustion:

```python
# Sender side
if data_size > MAX_EFFICIENT_SIZE:
    data_file = tempfile.TemporaryFile()
    data_file.write(data)
    resource = Resource(data_file, link)  # File handle instead of bytes

# Receiver side
storage_path = RNS.Reticulum.resourcepath + "/" + original_hash.hex()
# Parts assembled directly to file, not held in memory
```

This allows transferring multi-gigabyte files on memory-constrained devices.

### Watchdog Thread

Each resource runs a watchdog thread monitoring timeouts:

```python
# Runs continuously while resource active
def watchdog():
    while status < ASSEMBLING:
        calculate_next_timeout()
        sleep(min(timeout, WATCHDOG_MAX_SLEEP))

        if timeout_occurred():
            handle_timeout()

# Multiple resources can have concurrent watchdogs
```

The watchdog ensures timely timeout detection without blocking the main thread.

## Further Reading

For detailed protocol specifications:
- `references/wire-examples.py` - Advertisement packet construction and window flow

Related skills:
- `links` - Link establishment required for resource transfer
- `packets-wire-format` - Resource packet contexts (RESOURCE_ADV, RESOURCE_REQ, etc.)
- `cryptography-identity` - Hash functions and encryption used

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Resource.py` (complete implementation)
- `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` (resource overview)
