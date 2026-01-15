#!/usr/bin/env python3
"""
Reticulum Wire Format Examples

This module demonstrates low-level packet construction and parsing
at the binary wire format level. These examples show the byte-level
structure of Reticulum packets without using the high-level Packet API.

WARNING: This is for educational purposes. Production code should use
the RNS.Packet class which handles all these details correctly.
"""

import struct
import hashlib
import os


# Constants matching RNS implementation
MTU = 500
TRUNCATED_HASHLENGTH = 128  # bits
DST_LEN = TRUNCATED_HASHLENGTH // 8  # 16 bytes
HEADER_MAXSIZE = 2 + 1 + DST_LEN * 2  # 35 bytes
MDU = 465
ENCRYPTED_MDU = 383


def print_packet_analysis(raw_packet, description=""):
    """
    Print detailed analysis of a raw packet's structure.
    """
    print(f"\n{'='*70}")
    print(f"Packet Analysis: {description}")
    print(f"{'='*70}")
    print(f"Total packet size: {len(raw_packet)} bytes")
    print(f"Raw bytes (hex): {raw_packet.hex()}")
    print()

    # Parse header
    flags = raw_packet[0]
    hops = raw_packet[1]

    # Extract bit fields
    ifac_flag = (flags & 0b10000000) >> 7
    header_type = (flags & 0b01000000) >> 6
    context_flag = (flags & 0b00100000) >> 5
    transport_type = (flags & 0b00010000) >> 4
    destination_type = (flags & 0b00001100) >> 2
    packet_type = (flags & 0b00000011)

    print(f"HEADER BYTE 1 (0x{flags:02x} = 0b{flags:08b}):")
    print(f"  IFAC Flag:        {ifac_flag} ({'ENABLED' if ifac_flag else 'DISABLED'})")
    print(f"  Header Type:      {header_type} ({'HEADER_2' if header_type else 'HEADER_1'})")
    print(f"  Context Flag:     {context_flag} ({'SET' if context_flag else 'UNSET'})")
    print(f"  Propagation:      {transport_type} ({'TRANSPORT' if transport_type else 'BROADCAST'})")
    print(f"  Destination Type: {destination_type} ({['SINGLE', 'GROUP', 'PLAIN', 'LINK'][destination_type]})")
    print(f"  Packet Type:      {packet_type} ({['DATA', 'ANNOUNCE', 'LINKREQUEST', 'PROOF'][packet_type]})")
    print()

    print(f"HEADER BYTE 2:")
    print(f"  Hop count: {hops}")
    print()

    # Parse addresses based on header type
    offset = 2
    if header_type == 0:  # HEADER_1
        dest_hash = raw_packet[offset:offset+DST_LEN]
        print(f"DESTINATION HASH ({DST_LEN} bytes):")
        print(f"  {dest_hash.hex()}")
        offset += DST_LEN
    else:  # HEADER_2
        transport_id = raw_packet[offset:offset+DST_LEN]
        dest_hash = raw_packet[offset+DST_LEN:offset+2*DST_LEN]
        print(f"TRANSPORT ID ({DST_LEN} bytes):")
        print(f"  {transport_id.hex()}")
        print(f"DESTINATION HASH ({DST_LEN} bytes):")
        print(f"  {dest_hash.hex()}")
        offset += 2*DST_LEN
    print()

    # Context
    context = raw_packet[offset]
    context_names = {
        0x00: "NONE", 0x01: "RESOURCE", 0x02: "RESOURCE_ADV",
        0x03: "RESOURCE_REQ", 0x04: "RESOURCE_HMU", 0x05: "RESOURCE_PRF",
        0x06: "RESOURCE_ICL", 0x07: "RESOURCE_RCL", 0x08: "CACHE_REQUEST",
        0x09: "REQUEST", 0x0A: "RESPONSE", 0x0B: "PATH_RESPONSE",
        0x0C: "COMMAND", 0x0D: "COMMAND_STATUS", 0x0E: "CHANNEL",
        0xFA: "KEEPALIVE", 0xFB: "LINKIDENTIFY", 0xFC: "LINKCLOSE",
        0xFD: "LINKPROOF", 0xFE: "LRRTT", 0xFF: "LRPROOF"
    }
    context_name = context_names.get(context, "UNKNOWN")
    print(f"CONTEXT (1 byte):")
    print(f"  0x{context:02x} ({context_name})")
    offset += 1
    print()

    # Data
    data = raw_packet[offset:]
    print(f"DATA FIELD ({len(data)} bytes):")
    if len(data) <= 64:
        print(f"  Hex: {data.hex()}")
        # Try to decode as ASCII if printable
        if all(32 <= b < 127 or b in (9, 10, 13) for b in data):
            print(f"  ASCII: {data.decode('ascii', errors='replace')}")
    else:
        print(f"  Hex (first 64 bytes): {data[:64].hex()}...")
    print(f"{'='*70}\n")


def example_1_simple_broadcast_data():
    """
    Example 1: Simple broadcast DATA packet to SINGLE destination

    This is the most common packet type for sending data to a specific
    destination on the local network segment.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Broadcast DATA Packet (HEADER_1, SINGLE, BROADCAST)")
    print("="*70)

    # Create a destination hash (in real code, this comes from destination.hash)
    destination_hash = hashlib.sha256(b"example.destination").digest()[:16]

    # Our data payload (this would be encrypted in real use)
    data_payload = b"Hello, Reticulum!"

    # Construct header byte 1
    ifac_flag = 0        # No IFAC
    header_type = 0      # HEADER_1 (single address)
    context_flag = 0     # FLAG_UNSET
    transport_type = 0   # BROADCAST
    destination_type = 0 # SINGLE
    packet_type = 0      # DATA

    flags = (
        (ifac_flag << 7) |
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    print(f"Constructing header byte 1:")
    print(f"  flags = (ifac:{ifac_flag} << 7) | (header:{header_type} << 6) | "
          f"(context_flag:{context_flag} << 5) | (transport:{transport_type} << 4) | "
          f"(dest:{destination_type} << 2) | packet:{packet_type}")
    print(f"  flags = 0b{flags:08b} = 0x{flags:02x}")

    # Construct header byte 2 (hop count)
    hops = 0

    # Pack the packet
    packet = b""
    packet += struct.pack("!B", flags)          # Header byte 1
    packet += struct.pack("!B", hops)           # Header byte 2
    packet += destination_hash                  # Destination (16 bytes)
    packet += struct.pack("!B", 0x00)           # Context: NONE
    packet += data_payload                      # Data

    print(f"\nPacket structure:")
    print(f"  [Header 2B][Dest Hash 16B][Context 1B][Data {len(data_payload)}B]")
    print(f"  Total size: {len(packet)} bytes")

    # Analyze the constructed packet
    print_packet_analysis(packet, "Broadcast DATA packet")

    return packet


def example_2_transport_data():
    """
    Example 2: Transport DATA packet (HEADER_2)

    When a packet is being forwarded through the network, it uses HEADER_2
    which includes both the transport_id (next hop) and destination_hash.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Transport DATA Packet (HEADER_2, SINGLE, TRANSPORT)")
    print("="*70)

    # Transport ID (next hop in the route)
    transport_id = hashlib.sha256(b"next.hop.node").digest()[:16]

    # Final destination
    destination_hash = hashlib.sha256(b"final.destination").digest()[:16]

    # Data payload
    data_payload = b"Forwarded data"

    # Construct header
    ifac_flag = 0
    header_type = 1      # HEADER_2 (two addresses)
    context_flag = 0
    transport_type = 1   # TRANSPORT (can be forwarded)
    destination_type = 0 # SINGLE
    packet_type = 0      # DATA

    flags = (
        (ifac_flag << 7) |
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    hops = 4  # This packet has been forwarded 4 times

    # Pack the packet
    packet = b""
    packet += struct.pack("!B", flags)
    packet += struct.pack("!B", hops)
    packet += transport_id          # First address: next hop
    packet += destination_hash      # Second address: final destination
    packet += struct.pack("!B", 0x00)  # Context: NONE
    packet += data_payload

    print(f"Packet structure:")
    print(f"  [Header 2B][Transport ID 16B][Dest Hash 16B][Context 1B][Data {len(data_payload)}B]")
    print(f"  Total size: {len(packet)} bytes")

    print_packet_analysis(packet, "Transport DATA packet")

    return packet


def example_3_announce_packet():
    """
    Example 3: ANNOUNCE packet

    Announces contain identity information and are used for path discovery.
    They are never encrypted.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: ANNOUNCE Packet (HEADER_1, SINGLE, BROADCAST)")
    print("="*70)

    # Destination hash for the announcing identity
    destination_hash = hashlib.sha256(b"announcing.identity").digest()[:16]

    # Announce data includes public key, app data, signature
    # (simplified here - real announces have specific structure)
    announce_data = b"[PUBLIC_KEY_32_BYTES][APP_DATA][SIGNATURE_64_BYTES]"

    # Construct header
    ifac_flag = 0
    header_type = 0      # HEADER_1
    context_flag = 0
    transport_type = 0   # BROADCAST (initially - may become TRANSPORT as it propagates)
    destination_type = 0 # SINGLE
    packet_type = 1      # ANNOUNCE

    flags = (
        (ifac_flag << 7) |
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    hops = 0  # Fresh announce

    # Pack the packet
    packet = b""
    packet += struct.pack("!B", flags)
    packet += struct.pack("!B", hops)
    packet += destination_hash
    packet += struct.pack("!B", 0x00)  # Context: NONE
    packet += announce_data

    print(f"Packet structure:")
    print(f"  [Header 2B][Dest Hash 16B][Context 1B][Announce Data {len(announce_data)}B]")
    print(f"  Total size: {len(packet)} bytes")
    print(f"  Note: ANNOUNCE packets are NEVER encrypted")

    print_packet_analysis(packet, "ANNOUNCE packet")

    return packet


def example_4_link_request():
    """
    Example 4: LINKREQUEST packet

    Used to establish a link with a destination. Contains ephemeral
    key material for link encryption.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: LINKREQUEST Packet (HEADER_1, LINK, BROADCAST)")
    print("="*70)

    # Destination we want to link with
    destination_hash = hashlib.sha256(b"link.target").digest()[:16]

    # Link request data includes ephemeral public key and random token
    # (simplified structure)
    link_request_data = os.urandom(64)  # Ephemeral key material

    # Construct header
    ifac_flag = 0
    header_type = 0
    context_flag = 0
    transport_type = 0
    destination_type = 3 # LINK (special type for link establishment)
    packet_type = 2      # LINKREQUEST

    flags = (
        (ifac_flag << 7) |
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    hops = 0

    # Pack the packet
    packet = b""
    packet += struct.pack("!B", flags)
    packet += struct.pack("!B", hops)
    packet += destination_hash
    packet += struct.pack("!B", 0xFF)  # Context: LRPROOF expected
    packet += link_request_data

    print(f"Packet structure:")
    print(f"  [Header 2B][Dest Hash 16B][Context 1B][Link Data {len(link_request_data)}B]")
    print(f"  Total size: {len(packet)} bytes")
    print(f"  Note: LINKREQUEST packets are NOT encrypted")

    print_packet_analysis(packet, "LINKREQUEST packet")

    return packet


def example_5_resource_packet():
    """
    Example 5: Resource transfer DATA packet

    Resources use a series of DATA packets with RESOURCE context
    to transfer large files.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Resource DATA Packet (HEADER_1, SINGLE, BROADCAST)")
    print("="*70)

    # Destination receiving the resource
    destination_hash = hashlib.sha256(b"resource.receiver").digest()[:16]

    # Resource data chunk (already encrypted by resource layer)
    resource_chunk = os.urandom(383)  # Max encrypted payload

    # Construct header
    ifac_flag = 0
    header_type = 0
    context_flag = 0
    transport_type = 0
    destination_type = 0
    packet_type = 0      # DATA

    flags = (
        (ifac_flag << 7) |
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    hops = 0

    # Pack the packet
    packet = b""
    packet += struct.pack("!B", flags)
    packet += struct.pack("!B", hops)
    packet += destination_hash
    packet += struct.pack("!B", 0x01)  # Context: RESOURCE
    packet += resource_chunk

    print(f"Packet structure:")
    print(f"  [Header 2B][Dest Hash 16B][Context 1B][Resource Data {len(resource_chunk)}B]")
    print(f"  Total size: {len(packet)} bytes")
    print(f"  Note: Resource handles its own encryption")

    print_packet_analysis(packet, "Resource DATA packet")

    return packet


def example_6_link_keepalive():
    """
    Example 6: Link KEEPALIVE packet

    Small packets sent periodically over links to maintain the connection.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Link KEEPALIVE Packet (HEADER_1, LINK, BROADCAST)")
    print("="*70)

    # Link destination
    link_hash = hashlib.sha256(b"established.link").digest()[:16]

    # Keepalives have no data payload

    # Construct header
    ifac_flag = 0
    header_type = 0
    context_flag = 0
    transport_type = 0
    destination_type = 3  # LINK
    packet_type = 0       # DATA

    flags = (
        (ifac_flag << 7) |
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    hops = 0

    # Pack the packet
    packet = b""
    packet += struct.pack("!B", flags)
    packet += struct.pack("!B", hops)
    packet += link_hash
    packet += struct.pack("!B", 0xFA)  # Context: KEEPALIVE
    # No data field

    print(f"Packet structure:")
    print(f"  [Header 2B][Link Hash 16B][Context 1B]")
    print(f"  Total size: {len(packet)} bytes (minimal keepalive)")
    print(f"  Note: Keepalive packets contain NO data")

    print_packet_analysis(packet, "Link KEEPALIVE packet")

    return packet


def example_7_packet_with_ifac():
    """
    Example 7: Packet with IFAC (Interface Access Code)

    Demonstrates how IFAC is inserted after the header on authenticated
    interfaces.
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: DATA Packet with IFAC (HEADER_1, SINGLE, BROADCAST)")
    print("="*70)

    destination_hash = hashlib.sha256(b"secure.destination").digest()[:16]
    data_payload = b"Data on authenticated interface"

    # IFAC - could be a token, signature, etc. (interface-specific)
    ifac_code = os.urandom(32)  # Example: 32-byte authentication code

    # Construct header WITH IFAC FLAG SET
    ifac_flag = 1        # IFAC ENABLED
    header_type = 0
    context_flag = 0
    transport_type = 0
    destination_type = 0
    packet_type = 0

    flags = (
        (ifac_flag << 7) |  # THIS BIT MAKES THE DIFFERENCE
        (header_type << 6) |
        (context_flag << 5) |
        (transport_type << 4) |
        (destination_type << 2) |
        packet_type
    )

    hops = 0

    # Pack the packet - NOTE IFAC POSITION
    packet = b""
    packet += struct.pack("!B", flags)
    packet += struct.pack("!B", hops)
    packet += ifac_code              # IFAC COMES BEFORE ADDRESSES
    packet += destination_hash
    packet += struct.pack("!B", 0x00)
    packet += data_payload

    print(f"Packet structure (IFAC after header, before addresses):")
    print(f"  [Header 2B][IFAC {len(ifac_code)}B][Dest Hash 16B][Context 1B][Data {len(data_payload)}B]")
    print(f"  Total size: {len(packet)} bytes")
    print(f"  Note: IFAC length is interface-specific (1-64 bytes)")

    print(f"\nWARNING: This packet cannot be analyzed by print_packet_analysis()")
    print(f"because that function doesn't handle variable-length IFAC fields.")
    print(f"In real code, the interface layer handles IFAC extraction.")

    # We can't use print_packet_analysis here because it assumes no IFAC
    # Instead, manually show the structure:
    print(f"\nManual analysis:")
    print(f"  Header Byte 1: 0x{flags:02x} (IFAC flag = 1)")
    print(f"  Header Byte 2: 0x{hops:02x} (hops = {hops})")
    print(f"  IFAC: {ifac_code.hex()} ({len(ifac_code)} bytes)")
    print(f"  Destination: {destination_hash.hex()}")
    print(f"  Context: 0x00 (NONE)")
    print(f"  Data: {data_payload} ({len(data_payload)} bytes)")

    return packet


def example_8_parsing_received_packet():
    """
    Example 8: Parsing a received packet

    Demonstrates how to unpack and extract fields from a raw received packet.
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: Parsing a Received Packet")
    print("="*70)

    # Simulate a received packet (using example 1's output)
    print("Step 1: Receive raw bytes from interface")
    raw_packet = example_1_simple_broadcast_data()

    print("\nStep 2: Extract header byte 1 and decode flags")
    flags = raw_packet[0]
    ifac_flag = (flags & 0b10000000) >> 7
    header_type = (flags & 0b01000000) >> 6
    context_flag = (flags & 0b00100000) >> 5
    transport_type = (flags & 0b00010000) >> 4
    destination_type = (flags & 0b00001100) >> 2
    packet_type = (flags & 0b00000011)

    print(f"  flags = 0x{flags:02x} = 0b{flags:08b}")
    print(f"  Decoded: ifac={ifac_flag}, header_type={header_type}, "
          f"context_flag={context_flag}, transport={transport_type}, "
          f"dest_type={destination_type}, pkt_type={packet_type}")

    print("\nStep 3: Extract hop count")
    hops = raw_packet[1]
    print(f"  hops = {hops}")

    print("\nStep 4: Parse addresses based on header type")
    if header_type == 0:  # HEADER_1
        print("  Header type is HEADER_1 (single address)")
        destination_hash = raw_packet[2:2+DST_LEN]
        context_offset = 2 + DST_LEN
        print(f"  destination_hash = {destination_hash.hex()}")
    else:  # HEADER_2
        print("  Header type is HEADER_2 (two addresses)")
        transport_id = raw_packet[2:2+DST_LEN]
        destination_hash = raw_packet[2+DST_LEN:2+2*DST_LEN]
        context_offset = 2 + 2*DST_LEN
        print(f"  transport_id = {transport_id.hex()}")
        print(f"  destination_hash = {destination_hash.hex()}")

    print("\nStep 5: Extract context")
    context = raw_packet[context_offset]
    print(f"  context = 0x{context:02x}")

    print("\nStep 6: Extract data payload")
    data = raw_packet[context_offset+1:]
    print(f"  data length = {len(data)} bytes")
    print(f"  data = {data}")

    print("\nStep 7: Process based on packet type")
    if packet_type == 0:  # DATA
        print("  This is a DATA packet")
        if destination_type == 0:  # SINGLE
            print("  Destination type is SINGLE - data should be decrypted")
        elif destination_type == 3:  # LINK
            print("  Destination type is LINK - use link decryption")
        print("  Check context to determine specific handling")
    elif packet_type == 1:  # ANNOUNCE
        print("  This is an ANNOUNCE packet")
        print("  Parse public key and signature from data")
    elif packet_type == 2:  # LINKREQUEST
        print("  This is a LINKREQUEST packet")
        print("  Extract ephemeral key material from data")
    elif packet_type == 3:  # PROOF
        print("  This is a PROOF packet")
        print("  Validate proof signature")

    return raw_packet


def demonstrate_size_limits():
    """
    Demonstrate MTU/MDU calculations and size limits
    """
    print("\n" + "="*70)
    print("MTU/MDU Size Calculations and Limits")
    print("="*70)

    print(f"\nGlobal Constants:")
    print(f"  MTU (Maximum Transmission Unit):     {MTU} bytes")
    print(f"  MDU (Maximum Data Unit):             {MDU} bytes")
    print(f"  ENCRYPTED_MDU:                       {ENCRYPTED_MDU} bytes")
    print(f"  Truncated hash length:               {DST_LEN} bytes")

    print(f"\nHeader Sizes:")
    print(f"  HEADER_1 (2B header + 16B dest + 1B context):  19 bytes")
    print(f"  HEADER_2 (2B header + 32B dests + 1B context): 35 bytes")

    print(f"\nMaximum payload sizes:")
    print(f"  Unencrypted, HEADER_1:  {MTU - 19} bytes")
    print(f"  Unencrypted, HEADER_2:  {MTU - 35} bytes")
    print(f"  Encrypted to SINGLE:    {ENCRYPTED_MDU} bytes")
    print(f"  Over established link:  ~431 bytes")

    print(f"\nEncryption overhead:")
    print(f"  Token:                  16 bytes")
    print(f"  Public key reference:   16 bytes (KEYSIZE//16)")
    print(f"  AES padding:            Up to 16 bytes")
    print(f"  Total overhead:         ~{MDU - ENCRYPTED_MDU} bytes")

    print(f"\nTypical packet sizes:")
    print(f"  Keepalive:              20 bytes")
    print(f"  Path request:           51 bytes")
    print(f"  Link request:           83 bytes")
    print(f"  Link RTT:               99 bytes")
    print(f"  Link proof:             115 bytes")
    print(f"  Announce:               167 bytes")
    print(f"  Max single packet:      {MTU} bytes")


def main():
    """
    Run all examples
    """
    print("\n" + "="*70)
    print("Reticulum Wire Format Examples")
    print("="*70)
    print("\nThese examples demonstrate the binary structure of Reticulum packets")
    print("at the wire level. Production code should use the RNS.Packet API.")

    # Run all examples
    example_1_simple_broadcast_data()
    example_2_transport_data()
    example_3_announce_packet()
    example_4_link_request()
    example_5_resource_packet()
    example_6_link_keepalive()
    example_7_packet_with_ifac()
    example_8_parsing_received_packet()

    # Show size calculations
    demonstrate_size_limits()

    print("\n" + "="*70)
    print("Examples Complete")
    print("="*70)
    print("\nFor production use, always use the RNS.Packet class which handles")
    print("all these details correctly, including encryption, signing, and")
    print("proper MTU enforcement.")


if __name__ == "__main__":
    main()
