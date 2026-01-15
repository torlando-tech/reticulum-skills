# Resource Hashmap Structure

Hashmap provides part-level integrity verification for resource transfers.

## Purpose

Each resource is divided into parts (typically 512-1024 bytes each). The hashmap contains a 4-byte hash of each part, allowing:
- Receiver to verify each part independently
- Detection of corrupted parts
- Selective retransmission of only bad parts

## Hash Generation

For each part:
```python
part_hash = hashlib.sha256(part_data).digest()[:4]  # First 4 bytes
```

**Collision probability**: With 4-byte (32-bit) hashes and typical resource sizes:
- 100 parts: < 0.001% collision probability
- 1000 parts: < 0.1% collision probability
- Full resource hash provides final verification

## Hashmap Format

```python
hashmap = [hash1, hash2, hash3, ..., hashN]  # List of 4-byte hashes

# Serialized with umsgpack
hashmap_raw = umsgpack.packb(hashmap)
```

## Hashmap Exhaustion

For very large resources, full hashmap may not fit in single advertisement packet.

**Solution**: Partial hashmap with exhaustion flag

**Advertisement includes**:
- Initial subset of hashes (as many as fit)
- Exhaustion flag set

**Receiver behavior**:
- Requests parts using available hashes
- When needs more, sends HMU request
- Initiator responds with next batch of hashes via RESOURCE_HMU packet

## Size Calculation

```python
parts_count = (resource_size + part_size - 1) // part_size
hashmap_size = parts_count × 4 bytes

# Example: 1 MB resource, 1 KB parts
parts_count = 1024
hashmap_size = 4096 bytes (4 KB)
```

For 1 MB resource with 1 KB parts: 4 KB hashmap overhead (0.4% of data).

---

**Source**: `https://github.com/markqvist/Reticulum/RNS/Resource.py`
