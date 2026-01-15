"""
Wire Format Examples - Transport & Routing

Byte-level examples for transport layer packet structures and operations.
These examples demonstrate protocol bytes, not high-level API usage.
"""

import struct
import hashlib
import time

# ============================================================================
# HEADER TYPE 2 - Transport Packet
# ============================================================================

def build_header_type2_packet():
    """
    Build a packet in transport (HEADER_2 format) with transport node ID.

    HEADER_2 structure:
    [FLAGS 1B][HOPS 1B][TRANSPORT_ID 16B][DEST_HASH 16B][CONTEXT 1B][DATA]
    """

    # FLAGS byte construction
    ifac_flag = 0 << 7        # No IFAC
    header_type = 1 << 6      # HEADER_2 (transport)
    context_flag = 0 << 5     # Context flag unset
    propagation = 1 << 4      # TRANSPORT (not broadcast)
    dest_type = 0 << 2        # SINGLE destination
    packet_type = 0           # DATA packet

    flags = ifac_flag | header_type | context_flag | propagation | dest_type | packet_type
    # flags = 0b01010000 = 0x50

    # Hop count (incremented by each transport node)
    hops = 4

    # Transport node ID (hash of transport node currently routing)
    transport_id = hashlib.sha256(b"transport_node_identity").digest()[:16]

    # Destination hash
    dest_hash = hashlib.sha256(b"destination_identity").digest()[:16]

    # Context
    context = 0x00  # NONE

    # Encrypted data payload
    encrypted_data = b"<encrypted packet payload>"

    # Construct packet
    packet = struct.pack("BB", flags, hops)  # 2 bytes header
    packet += transport_id                    # 16 bytes
    packet += dest_hash                       # 16 bytes
    packet += bytes([context])                # 1 byte
    packet += encrypted_data                  # Variable

    print("HEADER_2 Packet (in transport):")
    print(f"  Flags: 0x{flags:02x} (HEADER_2, TRANSPORT, SINGLE, DATA)")
    print(f"  Hops: {hops}")
    print(f"  Transport ID: {transport_id.hex()}")
    print(f"  Dest Hash: {dest_hash.hex()}")
    print(f"  Context: 0x{context:02x}")
    print(f"  Total size: {len(packet)} bytes")
    print(f"  Hex: {packet[:35].hex()}...")
    print()

    return packet


# ============================================================================
# PATH TABLE ENTRY
# ============================================================================

def path_table_entry_structure():
    """
    Demonstrate path table entry structure.

    path_table = {
        destination_hash: (timestamp, received_from, hops, expires, random_blobs, interface, announce_packet)
    }
    """

    # Example destination hash
    destination_hash = hashlib.sha256(b"example.destination").digest()[:16]

    # Path entry values
    timestamp = time.time()  # When path was learned
    received_from = hashlib.sha256(b"next_hop_node").digest()[:16]  # Next hop hash
    hops = 3  # Number of hops to destination
    expires = timestamp + (60*60*24*7)  # Expires in 7 days (PATHFINDER_E)
    random_blobs = [
        hashlib.sha256(b"random1").digest()[:10],
        hashlib.sha256(b"random2").digest()[:10]
    ]
    interface_hash = hashlib.sha256(b"interface_identifier").digest()[:16]
    announce_packet_hash = hashlib.sha256(b"cached_announce").digest()

    # Path table entry
    path_entry = (
        timestamp,
        received_from,
        hops,
        expires,
        random_blobs,
        interface_hash,  # In practice, this is an Interface object
        announce_packet_hash  # In practice, this is a Packet object
    )

    print("Path Table Entry:")
    print(f"  Destination: {destination_hash.hex()}")
    print(f"  Timestamp: {timestamp} ({time.ctime(timestamp)})")
    print(f"  Next Hop: {received_from.hex()}")
    print(f"  Hops: {hops}")
    print(f"  Expires: {expires} ({time.ctime(expires)})")
    print(f"  Random Blobs: {len(random_blobs)} blobs")
    print(f"  Interface: {interface_hash.hex()}")
    print()

    return destination_hash, path_entry


# ============================================================================
# PACKET ROUTING LOGIC
# ============================================================================

def route_packet_example(packet_bytes, path_table):
    """
    Demonstrate routing logic for a received packet.

    Steps:
    1. Extract destination hash from packet
    2. Lookup in path table
    3. Get next hop and interface
    4. Increment hop count
    5. Forward to next hop (if hops <= PATHFINDER_M)
    """

    # Parse packet header
    flags = packet_bytes[0]
    hops = packet_bytes[1]

    # Determine header type
    header_type = (flags >> 6) & 0x01

    if header_type == 0:  # HEADER_1
        dest_hash = packet_bytes[2:18]  # Bytes 2-17 (16 bytes)
        offset = 18
    else:  # HEADER_2
        transport_id = packet_bytes[2:18]
        dest_hash = packet_bytes[18:34]  # Bytes 18-33 (16 bytes)
        offset = 34

    print("Routing Decision:")
    print(f"  Packet hops: {hops}")
    print(f"  Destination: {dest_hash.hex()}")

    # Lookup in path table
    if dest_hash in path_table:
        entry = path_table[dest_hash]
        timestamp, next_hop, entry_hops, expires, *rest = entry

        # Check expiry
        if time.time() < expires:
            print(f"  Path found: next_hop={next_hop.hex()}, entry_hops={entry_hops}")

            # Increment hop count
            new_hops = hops + 1

            PATHFINDER_M = 128
            if new_hops <= PATHFINDER_M:
                print(f"  Forwarding with hops={new_hops}")

                # Modify packet (increment hops)
                routed_packet = bytearray(packet_bytes)
                routed_packet[1] = new_hops

                return bytes(routed_packet), next_hop
            else:
                print(f"  Hop limit exceeded ({new_hops} > {PATHFINDER_M}), dropping")
                return None, None
        else:
            print(f"  Path expired, dropping packet")
            return None, None
    else:
        print(f"  No path to destination, dropping packet")
        return None, None


# ============================================================================
# HOP COUNT INCREMENT
# ============================================================================

def increment_hops(packet_bytes):
    """
    Increment hop count in packet header.

    Hop count is always at byte index 1 (second byte).
    """

    # Read current hops
    current_hops = packet_bytes[1]

    # Increment
    new_hops = current_hops + 1

    # Modify packet
    modified_packet = bytearray(packet_bytes)
    modified_packet[1] = new_hops

    print(f"Hop Increment: {current_hops} -> {new_hops}")

    return bytes(modified_packet)


# ============================================================================
# PATH EXPIRY CALCULATION
# ============================================================================

def calculate_path_expiry(interface_mode):
    """
    Calculate path expiry time based on interface mode.

    Different modes have different expiry times:
    - Normal: 7 days
    - Access Point: 1 day
    - Roaming: 6 hours
    """

    MODE_FULL = 0x00
    MODE_ACCESS_POINT = 0x01
    MODE_ROAMING = 0x02

    PATHFINDER_E = 60*60*24*7  # 7 days (604800 seconds)
    AP_PATH_TIME = 60*60*24    # 1 day (86400 seconds)
    ROAMING_PATH_TIME = 60*60*6  # 6 hours (21600 seconds)

    current_time = time.time()

    if interface_mode == MODE_ACCESS_POINT:
        expires = current_time + AP_PATH_TIME
        expiry_label = "1 day (Access Point)"
    elif interface_mode == MODE_ROAMING:
        expires = current_time + ROAMING_PATH_TIME
        expiry_label = "6 hours (Roaming)"
    else:
        expires = current_time + PATHFINDER_E
        expiry_label = "7 days (Normal)"

    print(f"Path Expiry Calculation:")
    print(f"  Interface Mode: 0x{interface_mode:02x}")
    print(f"  Current Time: {time.ctime(current_time)}")
    print(f"  Expires: {time.ctime(expires)}")
    print(f"  Duration: {expiry_label}")
    print()

    return expires


# ============================================================================
# REVERSE TABLE ENTRY
# ============================================================================

def reverse_table_entry_example():
    """
    Demonstrate reverse table for proof routing.

    reverse_table = {
        packet_hash: (interface, timestamp)
    }
    """

    # Original packet
    packet_data = b"example packet data"
    packet_hash = hashlib.sha256(packet_data).digest()

    # Store in reverse table
    interface_id = hashlib.sha256(b"ingress_interface").digest()[:16]
    timestamp = time.time()

    reverse_entry = (interface_id, timestamp)

    REVERSE_TIMEOUT = 8 * 60  # 8 minutes

    print("Reverse Table Entry:")
    print(f"  Packet Hash: {packet_hash.hex()}")
    print(f"  Interface: {interface_id.hex()}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Expires: {timestamp + REVERSE_TIMEOUT} (in 8 minutes)")
    print()

    # Later, when proof arrives
    print("Routing Proof:")
    if packet_hash in {packet_hash: reverse_entry}:  # Simulated lookup
        interface, stored_timestamp = reverse_entry
        if time.time() - stored_timestamp < REVERSE_TIMEOUT:
            print(f"  Route proof back via interface: {interface.hex()}")
        else:
            print(f"  Reverse entry expired, cannot route proof")

    print()


# ============================================================================
# MAIN - Run Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TRANSPORT & ROUTING - WIRE FORMAT EXAMPLES")
    print("=" * 70)
    print()

    # Example 1: HEADER_2 packet in transport
    packet = build_header_type2_packet()

    # Example 2: Path table entry
    dest_hash, path_entry = path_table_entry_structure()

    # Example 3: Routing logic
    # Create mock path table
    path_table = {dest_hash: path_entry}
    routed_packet, next_hop = route_packet_example(packet, path_table)

    # Example 4: Hop increment
    if routed_packet:
        final_packet = increment_hops(routed_packet)

    # Example 5: Path expiry
    calculate_path_expiry(0x00)  # Normal mode
    calculate_path_expiry(0x01)  # Access Point mode

    # Example 6: Reverse table
    reverse_table_entry_example()

    print("=" * 70)
    print("Examples demonstrate byte-level transport operations")
    print("=" * 70)
