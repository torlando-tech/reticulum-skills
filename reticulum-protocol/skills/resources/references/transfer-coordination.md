# Resource Transfer Coordination

Complete coordination protocol for reliable large data transfer over Reticulum links.

## Advertisement Phase

When initiator has data to transfer:

1. **Create resource**: Data segmented into parts (default size varies by link speed)
2. **Generate hashmap**: 4-byte hash of each part
3. **Pack advertisement**: Use umsgpack with resource metadata
4. **Send RESOURCE_ADV packet**: Contains size, compression flag, hashmap

Advertisement structure:
```python
{
    'h': resource_hash,      # SHA-256 of complete resource
    't': total_size,         # Bytes after compression
    'd': uncompressed_size,  # Original bytes
    'f': flags,              # bit 0: encrypted, bit 1: compressed
    'm': hashmap_raw,        # List of 4-byte part hashes
    'o': original_hash,      # SHA-256 of original data
    'r': random_hash,        # 4 bytes for uniqueness
    'i': segment_index,      # Which segment (for >1MB files)
    'l': total_segments      # Total number of segments
}
```

## Request/Response Cycle

Receiver drives transfer by requesting parts:

1. **Parse advertisement**: Extract hashmap and metadata
2. **Initialize window**: Start with WINDOW_MIN (2 parts)
3. **Request parts**: Send RESOURCE_REQ with part numbers
4. **Receive parts**: Validate hash of each part
5. **Adjust window**: Increase on success, decrease on timeout
6. **Repeat**: Until all parts received

Part request packet (RESOURCE_REQ context):
```python
request_data = umsgpack.packb([part_num1, part_num2, ...])
```

## Hashmap Update (HMU)

For large resources where hashmap doesn't fit in single advertisement:

**Hashmap exhaustion flag**: Set in advertisement when partial hashmap

**HMU packet** (RESOURCE_HMU context):
```python
hmu_data = umsgpack.packb({
    'h': resource_hash,
    'm': additional_hashes,  # Next batch of 4-byte hashes
    'i': segment_index
})
```

Receiver requests HMU when it needs more part hashes.

## Completion and Proof

After all parts received:

1. **Assemble resource**: Combine parts in order
2. **Verify hash**: Check assembled data hash matches resource_hash
3. **Decompress** (if compressed)
4. **Send proof**: RESOURCE_PRF packet with resource hash

Proof packet confirms successful transfer to initiator.

## Cancellation

Either side can cancel:

**Initiator cancel** (RESOURCE_ICL): Sender aborts transfer
**Receiver cancel** (RESOURCE_RCL): Receiver rejects or fails

Cancellation immediately terminates resource and cleans up state.

---

**Source**: `https://github.com/markqvist/Reticulum/RNS/Resource.py`
