"""
Wire Format Examples - Resources

Byte-level examples for resource transfer protocol.
These examples demonstrate protocol bytes for advertisements, requests,
and window-based transfer flow.
"""

import struct
import hashlib
import os
import bz2
import math

try:
    import umsgpack
except ImportError:
    print("Warning: umsgpack not available, using mock")
    # Mock umsgpack for demonstration
    class umsgpack:
        @staticmethod
        def packb(data):
            # Simplified mock - real umsgpack produces MessagePack format
            import json
            return json.dumps(data).encode()

        @staticmethod
        def unpackb(data):
            import json
            return json.loads(data.decode())

# ============================================================================
# RESOURCE CONSTANTS
# ============================================================================

# Window management
WINDOW_MIN = 2
WINDOW_MAX_FAST = 75
WINDOW_MAX_SLOW = 10

# Data limits
MAX_EFFICIENT_SIZE = 1048575  # 1MB - 1 (0xFFFFFF)
MAPHASH_LEN = 4
RANDOM_HASH_SIZE = 4

# MDU calculation (simplified)
SDU = 431  # Typical link MDU

# Advertisement overhead
ADV_OVERHEAD = 134
HASHMAP_MAX_LEN = math.floor((SDU - ADV_OVERHEAD) / MAPHASH_LEN)

print(f"HASHMAP_MAX_LEN: {HASHMAP_MAX_LEN} hashes per advertisement")
print(f"Hashmap bytes per advertisement: {HASHMAP_MAX_LEN * MAPHASH_LEN}")
print()

# ============================================================================
# RESOURCE ADVERTISEMENT PACKET
# ============================================================================

def build_resource_advertisement(data):
    """
    Build resource advertisement packet with umsgpack format.

    Structure:
    [HEADER 19B][UMSGPACK_ADVERTISEMENT]

    Advertisement dictionary:
    {
        "t": transfer_size,      # Encrypted size (3 bytes max)
        "d": data_size,          # Uncompressed size (3 bytes max)
        "n": number_of_parts,    # Total parts
        "h": resource_hash,      # 32-byte hash
        "r": random_hash,        # 4-byte random hash
        "o": original_hash,      # First segment hash
        "i": segment_index,      # Current segment (1-based)
        "l": total_segments,     # Total segments
        "q": request_id,         # Request ID (or None)
        "f": flags,              # Bit flags
        "m": hashmap             # Partial hashmap
    }
    """

    # Generate random hash prefix
    random_hash = os.urandom(RANDOM_HASH_SIZE)

    # Compress data
    compressed_data = bz2.compress(data)
    if len(compressed_data) < len(data):
        print(f"Compression: {len(data)} → {len(compressed_data)} bytes ({len(data) - len(compressed_data)} saved)")
        resource_data = random_hash + compressed_data
        compressed = True
    else:
        print(f"Compression: Not beneficial, sending uncompressed")
        resource_data = random_hash + data
        compressed = False

    # Mock encryption (add random bytes)
    encrypted_data = resource_data + os.urandom(16)  # AES padding
    encrypted = True

    transfer_size = len(encrypted_data)
    data_size = len(data)

    # Calculate parts
    total_parts = math.ceil(transfer_size / SDU)

    # Generate hashmap
    hashmap = b""
    parts = []
    for i in range(total_parts):
        part_data = encrypted_data[i * SDU : (i+1) * SDU]
        part_hash = hashlib.sha256(part_data + random_hash).digest()[:MAPHASH_LEN]
        hashmap += part_hash
        parts.append(part_data)

    # Calculate resource hash
    resource_hash = hashlib.sha256(encrypted_data + random_hash).digest()

    # First segment only
    segment_index = 1
    total_segments = 1
    original_hash = resource_hash

    # Flags byte
    has_metadata = False
    is_response = False
    is_request = False
    is_split = (total_segments > 1)

    flags = (
        (int(has_metadata) << 5) |
        (int(is_response) << 4) |
        (int(is_request) << 3) |
        (int(is_split) << 2) |
        (int(compressed) << 1) |
        (int(encrypted) << 0)
    )

    # First hashmap segment only (HASHMAP_MAX_LEN hashes)
    hashmap_segment = hashmap[:HASHMAP_MAX_LEN * MAPHASH_LEN]

    # Build advertisement dictionary
    advertisement = {
        "t": transfer_size,
        "d": data_size,
        "n": total_parts,
        "h": resource_hash,
        "r": random_hash,
        "o": original_hash,
        "i": segment_index,
        "l": total_segments,
        "q": None,  # No request ID
        "f": flags,
        "m": hashmap_segment
    }

    # Pack with umsgpack
    packed_adv = umsgpack.packb(advertisement)

    # Construct packet header
    link_id = os.urandom(16)
    flags_byte = 0b00001100  # HEADER_1, BROADCAST, LINK dest, DATA
    hops = 0
    context = 0x9A  # RESOURCE_ADV (made up value for example)

    header = struct.pack("BB", flags_byte, hops) + link_id + bytes([context])

    # Complete packet
    packet = header + packed_adv

    print("Resource Advertisement Packet:")
    print(f"  Transfer size: {transfer_size} bytes")
    print(f"  Data size: {data_size} bytes")
    print(f"  Total parts: {total_parts}")
    print(f"  Resource hash: {resource_hash.hex()[:32]}...")
    print(f"  Random hash: {random_hash.hex()}")
    print(f"  Flags: 0x{flags:02x} (compressed={compressed}, encrypted={encrypted})")
    print(f"  Hashmap segment: {len(hashmap_segment)} bytes ({len(hashmap_segment)//MAPHASH_LEN} hashes)")
    print(f"  Advertisement size: {len(packed_adv)} bytes")
    print(f"  Total packet size: {len(packet)} bytes")
    print()

    return packet, resource_hash, hashmap, parts, random_hash

# ============================================================================
# RESOURCE PART REQUEST
# ============================================================================

def build_part_request(resource_hash, hashmap, window_size, consecutive_completed):
    """
    Build part request packet from receiver.

    Structure:
    [HEADER 19B][HMU_FLAG 1B][RESOURCE_HASH 32B][REQUESTED_HASHES NxMAPHASH_LEN]

    HMU_FLAG:
    - 0x00: Hashmap not exhausted, just requesting parts
    - 0xFF: Hashmap exhausted, need more hashes (includes last_hash)
    """

    # Request next 'window_size' missing parts
    requested_hashes = b""
    parts_to_request = []

    start_index = consecutive_completed + 1
    end_index = min(start_index + window_size, len(hashmap) // MAPHASH_LEN)

    for i in range(start_index, end_index):
        part_hash = hashmap[i * MAPHASH_LEN : (i+1) * MAPHASH_LEN]
        requested_hashes += part_hash
        parts_to_request.append(i)

    # HMU flag (not exhausted in this example)
    hmu_flag = 0x00
    hmu_part = bytes([hmu_flag])

    # Request data
    request_data = hmu_part + resource_hash + requested_hashes

    # Construct packet header
    link_id = os.urandom(16)
    flags_byte = 0b00001100
    hops = 0
    context = 0x9B  # RESOURCE_REQ

    header = struct.pack("BB", flags_byte, hops) + link_id + bytes([context])

    # Complete packet
    packet = header + request_data

    print("Part Request Packet:")
    print(f"  Window size: {window_size}")
    print(f"  Consecutive completed: {consecutive_completed}")
    print(f"  Requesting parts: {parts_to_request}")
    print(f"  Requested hashes: {len(requested_hashes)} bytes ({len(requested_hashes)//MAPHASH_LEN} hashes)")
    print(f"  HMU flag: 0x{hmu_flag:02x}")
    print(f"  Total packet size: {len(packet)} bytes")
    print()

    return packet, parts_to_request

# ============================================================================
# RESOURCE PART TRANSMISSION
# ============================================================================

def transmit_resource_parts(parts, requested_indices):
    """
    Sender transmits requested parts.

    Each part is sent as a separate DATA packet with context RESOURCE.
    """

    transmitted = []

    for index in requested_indices:
        part_data = parts[index]

        # Construct packet header
        link_id = os.urandom(16)
        flags_byte = 0b00001100
        hops = 0
        context = 0x9C  # RESOURCE

        header = struct.pack("BB", flags_byte, hops) + link_id + bytes([context])

        # Complete packet
        packet = header + part_data

        transmitted.append({
            "index": index,
            "size": len(packet),
            "part_size": len(part_data)
        })

    total_bytes = sum(p["size"] for p in transmitted)

    print("Resource Parts Transmitted:")
    print(f"  Parts sent: {len(transmitted)}")
    print(f"  Total bytes: {total_bytes}")
    if len(transmitted) > 0:
        print(f"  Average part size: {total_bytes / len(transmitted):.1f} bytes")
    print()

    return transmitted

# ============================================================================
# HASHMAP UPDATE (HMU)
# ============================================================================

def build_hashmap_update(resource_hash, hashmap, segment_number):
    """
    Build hashmap update packet when receiver exhausts current segment.

    Structure:
    [HEADER 19B][RESOURCE_HASH 32B][UMSGPACK [segment, hashmap_bytes]]
    """

    hashmap_start = segment_number * HASHMAP_MAX_LEN
    hashmap_end = min((segment_number + 1) * HASHMAP_MAX_LEN, len(hashmap) // MAPHASH_LEN)

    hashmap_segment = b""
    for i in range(hashmap_start, hashmap_end):
        hashmap_segment += hashmap[i * MAPHASH_LEN : (i+1) * MAPHASH_LEN]

    # Pack with umsgpack
    hmu_data = umsgpack.packb([segment_number, hashmap_segment])

    # Request data
    packet_data = resource_hash + hmu_data

    # Construct packet header
    link_id = os.urandom(16)
    flags_byte = 0b00001100
    hops = 0
    context = 0x9D  # RESOURCE_HMU

    header = struct.pack("BB", flags_byte, hops) + link_id + bytes([context])

    # Complete packet
    packet = header + packet_data

    hashes_count = len(hashmap_segment) // MAPHASH_LEN

    print("Hashmap Update Packet:")
    print(f"  Segment: {segment_number}")
    print(f"  Hashmap range: {hashmap_start} - {hashmap_end}")
    print(f"  Hashes: {hashes_count}")
    print(f"  Hashmap bytes: {len(hashmap_segment)}")
    print(f"  Total packet size: {len(packet)} bytes")
    print()

    return packet

# ============================================================================
# RESOURCE COMPLETION PROOF
# ============================================================================

def build_completion_proof(resource_hash, assembled_data, random_hash):
    """
    Build completion proof packet from receiver after successful assembly.

    Structure:
    [HEADER 19B][RESOURCE_HASH 32B][PROOF_HASH 32B]

    Proof demonstrates successful decryption and decompression.
    """

    # Calculate proof (sender expects this)
    proof_hash = hashlib.sha256(assembled_data + resource_hash).digest()

    # Proof data
    proof_data = resource_hash + proof_hash

    # Construct packet header
    link_id = os.urandom(16)
    flags_byte = 0b00000011  # PROOF packet
    hops = 0
    context = 0x9E  # RESOURCE_PRF

    header = struct.pack("BB", flags_byte, hops) + link_id + bytes([context])

    # Complete packet
    packet = header + proof_data

    print("Completion Proof Packet:")
    print(f"  Resource hash: {resource_hash.hex()[:32]}...")
    print(f"  Proof hash: {proof_hash.hex()[:32]}...")
    print(f"  Total packet size: {len(packet)} bytes")
    print()

    return packet

# ============================================================================
# WINDOW ADJUSTMENT SIMULATION
# ============================================================================

def simulate_window_adjustment():
    """
    Demonstrate dynamic window adjustment based on performance.
    """

    window = 4
    window_min = 2
    window_max = 10
    window_flexibility = 4

    print("Window Adjustment Simulation:")
    print(f"  Initial: window={window}, min={window_min}, max={window_max}")
    print()

    # Successful rounds - window grows
    for round_num in range(1, 8):
        if window < window_max:
            window += 1
            if (window - window_min) > (window_flexibility - 1):
                window_min += 1

        print(f"  Round {round_num} SUCCESS: window={window}, min={window_min}, max={window_max}")

    print()

    # Timeout - window shrinks
    print("  TIMEOUT occurred")
    if window > window_min:
        window -= 1
        if window_max > window_min:
            window_max -= 1
            if (window_max - window) > (window_flexibility - 1):
                window_max -= 1

    print(f"  After timeout: window={window}, min={window_min}, max={window_max}")
    print()

    # Fast link upgrade
    print("  Fast link detected (>50 Kbps sustained)")
    window_max = WINDOW_MAX_FAST
    print(f"  Upgraded: window={window}, min={window_min}, max={window_max}")
    print()

# ============================================================================
# TRANSFER EFFICIENCY CALCULATION
# ============================================================================

def calculate_efficiency(data_size):
    """
    Calculate transfer efficiency for given data size.
    """

    total_parts = math.ceil(data_size / SDU)

    # Overhead calculations
    advertisement_overhead = 230  # Approximate
    part_header_overhead = 19 * total_parts

    # Number of requests (assuming window = 10)
    window = 10
    num_requests = math.ceil(total_parts / window)
    request_overhead = 105 * num_requests  # Approximate request packet size

    # Hashmap updates (if needed)
    hashmap_segments = math.ceil(total_parts / HASHMAP_MAX_LEN) - 1
    hmu_overhead = 1200 * hashmap_segments if hashmap_segments > 0 else 0

    # Proof
    proof_overhead = 115

    total_overhead = (advertisement_overhead + part_header_overhead +
                     request_overhead + hmu_overhead + proof_overhead)

    efficiency = data_size / (data_size + total_overhead) * 100

    print(f"Transfer Efficiency for {data_size:,} bytes:")
    print(f"  Total parts: {total_parts}")
    print(f"  Advertisement: {advertisement_overhead} bytes")
    print(f"  Part headers: {part_header_overhead} bytes")
    print(f"  Requests: {request_overhead} bytes ({num_requests} requests)")
    print(f"  Hashmap updates: {hmu_overhead} bytes ({hashmap_segments} updates)")
    print(f"  Proof: {proof_overhead} bytes")
    print(f"  Total overhead: {total_overhead:,} bytes")
    print(f"  Efficiency: {efficiency:.1f}%")
    print()

# ============================================================================
# MULTI-SEGMENT RESOURCE
# ============================================================================

def demonstrate_segmentation(total_size):
    """
    Demonstrate how large resources are split into segments.
    """

    total_segments = math.ceil(total_size / MAX_EFFICIENT_SIZE)

    print(f"Resource Segmentation for {total_size:,} bytes:")
    print(f"  MAX_EFFICIENT_SIZE: {MAX_EFFICIENT_SIZE:,} bytes")
    print(f"  Total segments: {total_segments}")
    print()

    for i in range(1, total_segments + 1):
        if i < total_segments:
            segment_size = MAX_EFFICIENT_SIZE
        else:
            segment_size = total_size - ((total_segments - 1) * MAX_EFFICIENT_SIZE)

        parts = math.ceil(segment_size / SDU)

        print(f"  Segment {i}:")
        print(f"    Size: {segment_size:,} bytes")
        print(f"    Parts: {parts}")

    print()
    print("  Note: Segments transferred sequentially, not in parallel")
    print()

# ============================================================================
# MAIN - Run Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("RESOURCES - WIRE FORMAT EXAMPLES")
    print("=" * 70)
    print()

    # Example 1: Small resource transfer
    print("-" * 70)
    print("EXAMPLE 1: Small Resource (500 bytes)")
    print("-" * 70)
    print()

    test_data = b"Example resource data. " * 20  # ~480 bytes
    adv_packet, res_hash, hashmap, parts, rand_hash = build_resource_advertisement(test_data)

    # Example 2: Part request with window
    print("-" * 70)
    print("EXAMPLE 2: Part Request")
    print("-" * 70)
    print()

    req_packet, requested = build_part_request(res_hash, hashmap, window_size=4, consecutive_completed=0)

    # Example 3: Transmit parts
    print("-" * 70)
    print("EXAMPLE 3: Part Transmission")
    print("-" * 70)
    print()

    transmitted = transmit_resource_parts(parts, requested)

    # Example 4: Hashmap update (if resource was larger)
    print("-" * 70)
    print("EXAMPLE 4: Hashmap Update")
    print("-" * 70)
    print()

    hmu_packet = build_hashmap_update(res_hash, hashmap, segment_number=1)

    # Example 5: Completion proof
    print("-" * 70)
    print("EXAMPLE 5: Completion Proof")
    print("-" * 70)
    print()

    proof_packet = build_completion_proof(res_hash, test_data, rand_hash)

    # Example 6: Window adjustment
    print("-" * 70)
    print("EXAMPLE 6: Window Adjustment")
    print("-" * 70)
    print()

    simulate_window_adjustment()

    # Example 7: Efficiency calculations
    print("-" * 70)
    print("EXAMPLE 7: Transfer Efficiency")
    print("-" * 70)
    print()

    calculate_efficiency(10240)    # 10 KB
    calculate_efficiency(1048575)  # 1 MB - 1

    # Example 8: Segmentation
    print("-" * 70)
    print("EXAMPLE 8: Multi-Segment Resource")
    print("-" * 70)
    print()

    demonstrate_segmentation(3355443)  # ~3.2 MB

    print("=" * 70)
    print("Examples demonstrate byte-level resource transfer protocol")
    print("=" * 70)
