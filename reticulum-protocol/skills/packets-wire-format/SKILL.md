---
name: packets-wire-format
description: Reticulum's packet structure and wire format. Use when working with packet headers, MTU/MDU, packet types, header types (HEADER_1/HEADER_2), packet context flags, IFAC, or binary packet encoding.
  - destination hash
  - transport ID
description: Deep technical knowledge about Reticulum packet structure, binary wire format, header encoding, packet types, MTU/MDU calculations, and IFAC handling. Use when analyzing packet construction, parsing binary protocol data, or debugging wire-level communication.
---

# Packets & Wire Format

This skill provides detailed technical knowledge about Reticulum's binary packet structure and wire format, essential for understanding how data flows across the network at the byte level.

## Binary Packet Structure

Every Reticulum packet follows a strict binary format:

```
[HEADER 2 bytes] [IFAC 0-64 bytes] [ADDRESSES 16/32 bytes] [CONTEXT 1 byte] [DATA 0-464 bytes]
```

### Field Details

**HEADER (2 bytes)**
- Byte 1: Packed flags (see Header Byte 1 structure below)
- Byte 2: Hop count (0-255)

**IFAC Field (0-64 bytes, optional)**
- Only present if IFAC flag is set in header
- Length varies by interface configuration (1-64 bytes)
- Used for interface authentication/access control
- Public interfaces don't use IFAC (length = 0)

**ADDRESSES Field (16 or 32 bytes)**
- HEADER_1: Single 16-byte destination hash
- HEADER_2: Two 16-byte hashes (transport_id + destination_hash)
- Addresses are SHA-256 hashes truncated to 128 bits (16 bytes)

**CONTEXT Field (1 byte)**
- Indicates packet context/purpose
- See Context Types section below

**DATA Field (0-464 bytes)**
- Payload data (encrypted or plaintext depending on packet type)
- Maximum size depends on MTU/MDU calculations

## Header Byte 1 Structure

The first header byte encodes six pieces of information using bit fields:

```
Bit Layout: [IFAC][Header Type][Context Flag][Propagation][Dest Type 2 bits][Packet Type 2 bits]

Bit 7:     IFAC Flag (1 bit)
Bit 6:     Header Type (1 bit)
Bit 5:     Context Flag (1 bit)
Bit 4:     Propagation Type (1 bit)
Bits 3-2:  Destination Type (2 bits)
Bits 1-0:  Packet Type (2 bits)
```

### Extracting Header Fields

From a raw packet's first byte:

```python
flags = raw_packet[0]

ifac_flag        = (flags & 0b10000000) >> 7
header_type      = (flags & 0b01000000) >> 6
context_flag     = (flags & 0b00100000) >> 5
propagation_type = (flags & 0b00010000) >> 4
destination_type = (flags & 0b00001100) >> 2
packet_type      = (flags & 0b00000011)
```

### Packing Header Fields

When constructing a packet:

```python
packed_flags = (
    (header_type << 6) |
    (context_flag << 5) |
    (transport_type << 4) |
    (destination_type << 2) |
    packet_type
)
```

Note: IFAC flag is typically set by the interface layer, not in application code.

## Packet Types

Four fundamental packet types (2 bits, values 0-3):

| Type | Value | Purpose | Encrypted |
|------|-------|---------|-----------|
| **DATA** | 0x00 | Application data | Usually yes |
| **ANNOUNCE** | 0x01 | Identity/service announcement | No |
| **LINKREQUEST** | 0x02 | Establish link | No |
| **PROOF** | 0x03 | Delivery confirmation | Depends on context |

### Packet Type Usage

**DATA (0x00)**
- Standard application payload delivery
- Encrypted to SINGLE/GROUP destinations
- Can be sent over links (using link encryption)
- Context field indicates specific data purpose

**ANNOUNCE (0x01)**
- Broadcasts identity and public key
- Contains signed identity proof
- Never encrypted (must be readable by all)
- Propagates through network based on hop count
- Used for path discovery

**LINKREQUEST (0x02)**
- Initiates link establishment with a destination
- Contains ephemeral key for link encryption
- Not encrypted (but contains cryptographic material)
- Requires PROOF response to complete handshake

**PROOF (0x03)**
- Confirms successful packet delivery
- Can be explicit (with packet hash) or implicit
- Link proofs are encrypted; resource proofs are not
- Size: ~115 bytes for explicit proofs

## Header Types

Two header formats control address field structure:

**HEADER_1 (0x00)**
- Two byte header + one 16-byte address field
- Total header size: 2 bytes + 16 bytes = 18 bytes (+ 1 context = 19)
- Used for:
  - Broadcast packets
  - Direct destination communication
  - Most application-level packets

**HEADER_2 (0x01)**
- Two byte header + two 16-byte address fields
- Total header size: 2 bytes + 32 bytes = 34 bytes (+ 1 context = 35)
- Used for:
  - Packets in transport (being forwarded)
  - First address: transport_id (next hop)
  - Second address: destination_hash (final destination)

## Destination Types

Four destination types (2 bits):

| Type | Value | Bits | Purpose |
|------|-------|------|---------|
| **SINGLE** | 0 | 00 | One-to-one, ephemeral encryption |
| **GROUP** | 1 | 01 | One-to-many, shared key |
| **PLAIN** | 2 | 10 | Unencrypted broadcast |
| **LINK** | 3 | 11 | Over established link |

## Propagation Types

Two propagation modes (1 bit):

**BROADCAST (0)**
- Packet travels on local interfaces only
- Not forwarded by transport nodes
- Hop count typically low (0-3)

**TRANSPORT (1)**
- Packet can be forwarded across multiple hops
- Routed through transport nodes
- Uses path tables for routing
- Header may be rewritten to HEADER_2 for forwarding

## Context Types

The context byte indicates packet purpose within higher-level protocols:

### Core Context Values

```python
NONE           = 0x00  # Generic data packet
RESOURCE       = 0x01  # Resource transfer data chunk
RESOURCE_ADV   = 0x02  # Resource advertisement
RESOURCE_REQ   = 0x03  # Resource part request
RESOURCE_HMU   = 0x04  # Resource hashmap update
RESOURCE_PRF   = 0x05  # Resource proof (not encrypted)
RESOURCE_ICL   = 0x06  # Resource initiator cancel
RESOURCE_RCL   = 0x07  # Resource receiver cancel
CACHE_REQUEST  = 0x08  # Path/announce cache request
REQUEST        = 0x09  # Request packet (request/response pattern)
RESPONSE       = 0x0A  # Response to request
PATH_RESPONSE  = 0x0B  # Path request response
COMMAND        = 0x0C  # Command packet
COMMAND_STATUS = 0x0D  # Command execution status
CHANNEL        = 0x0E  # Link channel data
```

### Link-Specific Context Values

```python
KEEPALIVE      = 0xFA  # Link keepalive (no data)
LINKIDENTIFY   = 0xFB  # Link peer identification proof
LINKCLOSE      = 0xFC  # Link close notification
LINKPROOF      = 0xFD  # Link packet proof
LRRTT          = 0xFE  # Link request RTT measurement
LRPROOF        = 0xFF  # Link request proof
```

### Context Flag

The context flag (bit 5 in header byte 1) provides additional signaling:

- **FLAG_UNSET (0)**: Standard behavior
- **FLAG_SET (1)**: Context-dependent signaling

Usage varies by packet context. For example, in resource transfers it may indicate last packet, or in links it may signal specific protocol states.

## MTU, MDU, and Size Calculations

Understanding packet size limits is critical for protocol implementation:

### Constants

```python
MTU = 500               # Maximum Transmission Unit (bytes)
TRUNCATED_HASHLENGTH = 128  # Hash length in bits (16 bytes)
HEADER_MAXSIZE = 2 + 1 + (128//8)*2  # 35 bytes
IFAC_MIN_SIZE = 1       # Minimum IFAC overhead
```

### MDU (Maximum Data Unit)

The maximum payload size in a packet:

```python
MDU = MTU - HEADER_MAXSIZE - IFAC_MIN_SIZE
    = 500 - 35 - 1
    = 464 bytes
```

The MDU is **464 bytes** as calculated above.

### ENCRYPTED_MDU

When encryption is applied, overhead reduces available payload:

```python
TOKEN_OVERHEAD = 48    # IV (16 bytes) + HMAC (32 bytes)
KEYSIZE = 512          # Identity keypair size in bits (64 bytes = KEYSIZE//8)
AES128_BLOCKSIZE = 16  # AES block size

# The calculation from Packet.py (KEYSIZE//16 = 32 bytes for ephemeral public key):
ENCRYPTED_MDU = floor((MDU - TOKEN_OVERHEAD - KEYSIZE//16) / AES128_BLOCKSIZE) * AES128_BLOCKSIZE - 1
              = floor((464 - 48 - 32) / 16) * 16 - 1
              = floor(384 / 16) * 16 - 1
              = 24 * 16 - 1
              = 384 - 1
              = 383 bytes
```

The **ENCRYPTED_MDU is 383 bytes**. The `KEYSIZE//16` term (32 bytes) accounts for the ephemeral X25519 public key prepended to encrypted tokens.

### Practical Size Limits

| Packet Type | Typical Size | Max Size |
|-------------|--------------|----------|
| Path Request | 51 bytes | - |
| Announce | 167 bytes | - |
| Link Request | 83 bytes | - |
| Link Proof | 115 bytes | - |
| Link RTT | 99 bytes | - |
| Link Keepalive | 20 bytes | - |
| Data (encrypted to SINGLE) | Variable | 383 bytes payload |
| Data (unencrypted/GROUP) | Variable | 464 bytes payload |
| Data (over Link) | Variable | ~431 bytes payload |

## IFAC (Interface Access Code)

IFAC provides interface-level authentication and access control:

### Purpose

- Restricts access to specific interfaces
- Prevents unauthorized nodes from using sensitive interfaces
- Adds 0-64 bytes to packet size
- Validated before packet processing

### IFAC Flag

Bit 7 of header byte 1:

- **0**: Public interface, no IFAC
- **1**: IFAC included after header, before addresses

### IFAC Structure

When present, IFAC appears immediately after the 2-byte header:

```
[Header Byte 1][Header Byte 2][IFAC N bytes][Addresses...][Context][Data]
```

The IFAC content is interface-specific and opaque to higher protocol layers. Length is negotiated during interface configuration.

### IFAC in Packet Parsing

When unpacking a packet with IFAC set:

1. Read 2-byte header
2. Determine IFAC length (interface-specific)
3. Extract and validate IFAC
4. Parse remaining fields starting after IFAC

Most application code doesn't handle IFAC directly—it's managed by the interface layer.

## Packet Construction Example

Building a simple DATA packet to a SINGLE destination (broadcast):

```python
import struct

# Parameters
destination_hash = b'\x01\x02\x03...'  # 16 bytes
data_payload = b"Hello, Reticulum!"
hops = 0

# Header byte 1
header_type = 0      # HEADER_1
context_flag = 0     # FLAG_UNSET
transport_type = 0   # BROADCAST
destination_type = 0 # SINGLE
packet_type = 0      # DATA

flags = (
    (header_type << 6) |
    (context_flag << 5) |
    (transport_type << 4) |
    (destination_type << 2) |
    packet_type
)  # Result: 0b00000000 = 0x00

# Pack header
header = struct.pack("!B", flags)      # Byte 1: 0x00
header += struct.pack("!B", hops)      # Byte 2: 0x00

# Add destination
header += destination_hash             # 16 bytes

# Add context
context = 0x00  # NONE
header += struct.pack("!B", context)   # 1 byte

# Encrypt data (simplified, actual encryption is complex)
ciphertext = encrypt_for_destination(data_payload, destination_hash)

# Assemble packet
raw_packet = header + ciphertext

# Verify size
if len(raw_packet) > 500:
    raise ValueError("Packet exceeds MTU")
```

## Packet Parsing Example

Unpacking a received packet:

```python
# Assume raw_packet is received bytes
flags = raw_packet[0]
hops = raw_packet[1]

# Extract header fields
ifac_flag = (flags & 0b10000000) >> 7
header_type = (flags & 0b01000000) >> 6
context_flag = (flags & 0b00100000) >> 5
transport_type = (flags & 0b00010000) >> 4
destination_type = (flags & 0b00001100) >> 2
packet_type = (flags & 0b00000011)

# Determine hash length
DST_LEN = 16  # TRUNCATED_HASHLENGTH // 8

# Parse based on header type
if header_type == 1:  # HEADER_2
    transport_id = raw_packet[2:DST_LEN+2]
    destination_hash = raw_packet[DST_LEN+2:2*DST_LEN+2]
    context = raw_packet[2*DST_LEN+2]
    data = raw_packet[2*DST_LEN+3:]
else:  # HEADER_1
    transport_id = None
    destination_hash = raw_packet[2:DST_LEN+2]
    context = raw_packet[DST_LEN+2]
    data = raw_packet[DST_LEN+3:]

# Process based on packet type
if packet_type == 0:  # DATA
    if destination_type == 0:  # SINGLE
        plaintext = decrypt_data(data, destination_hash)
    # ... handle data
elif packet_type == 1:  # ANNOUNCE
    # ... process announce
```

## Wire Format Diagram Examples

### Example 1: Broadcast DATA Packet (HEADER_1)

```
   HEADER FIELD   DESTINATION FIELD   CONTEXT FIELD  DATA FIELD
 _______|_______   _______|_______   ________|______   __|_
|               | |               | |               | |    |
00000000 00000111 [HASH1, 16 bytes] [CONTEXT, 1 byte] [DATA]
|| | | |    |
|| | | |    +-- Hops             = 7
|| | | +------- Packet Type      = DATA (00)
|| | +--------- Destination Type = SINGLE (00)
|| +----------- Propagation Type = BROADCAST (0)
|+------------- Header Type      = HEADER_1 (0)
+-------------- Access Codes     = DISABLED (0)
```

### Example 2: Transport DATA Packet (HEADER_2)

```
   HEADER FIELD           DESTINATION FIELDS            CONTEXT FIELD  DATA FIELD
 _______|_______   ________________|________________   ________|______   __|_
|               | |                                 | |               | |    |
01010000 00000100 [HASH1, 16 bytes] [HASH2, 16 bytes] [CONTEXT, 1 byte] [DATA]
|| | | |    |
|| | | |    +-- Hops             = 4
|| | | +------- Packet Type      = DATA (00)
|| | +--------- Destination Type = SINGLE (00)
|| +----------- Propagation Type = TRANSPORT (1)
|+------------- Header Type      = HEADER_2 (1)
+-------------- Access Codes     = DISABLED (0)
```

### Example 3: Packet with IFAC

```
   HEADER FIELD     IFAC FIELD    DESTINATION FIELD   CONTEXT FIELD  DATA FIELD
 _______|_______   ______|______   _______|_______   ________|______   __|_
|               | |             | |               | |               | |    |
10000000 00000111 [IFAC, N bytes] [HASH1, 16 bytes] [CONTEXT, 1 byte] [DATA]
|| | | |    |
|| | | |    +-- Hops             = 7
|| | | +------- Packet Type      = DATA (00)
|| | +--------- Destination Type = SINGLE (00)
|| +----------- Propagation Type = BROADCAST (0)
|+------------- Header Type      = HEADER_1 (0)
+-------------- Access Codes     = ENABLED (1)
```

## Key Implementation Notes

1. **Byte Order**: All multi-byte integers use network byte order (big-endian, ``!`` format in struct)

2. **Hash Truncation**: Full SHA-256 hashes (256 bits) are truncated to 128 bits (16 bytes) for addresses

3. **Hop Count**: Starts at 0, incremented by each forwarding node, max 255

4. **MTU Enforcement**: Packets exceeding 500 bytes are rejected before transmission

5. **Context Field Placement**: Always the last byte before payload data, regardless of header type

6. **Encryption Overhead**: When encrypting to SINGLE destinations, expect ~81 bytes overhead (464 - 383)

7. **Link Packets**: Special handling with different encryption scheme, identified by destination_type = LINK

8. **Proof Packets**: Size varies; explicit proofs include full packet hash + signature

9. **Announce Propagation**: Controlled by hop count; decremented at each hop until reaching 0

10. **Header Rewriting**: Transport nodes may rewrite HEADER_1 to HEADER_2 when forwarding

## Common Pitfalls

- **Forgetting Context Byte**: Even if context is NONE (0x00), the byte must be included
- **MTU Calculation Errors**: Always account for header, addresses, context, and IFAC when sizing payload
- **Bit Shift Mistakes**: Destination type is 2 bits, shifted left by 2; packet type is 2 bits, not shifted
- **Encryption Assumptions**: Not all packets are encrypted (ANNOUNCE, LINKREQUEST, some PROOFs are plaintext)
- **Hash Length**: Using full 32-byte SHA-256 instead of truncated 16-byte hash
- **IFAC Handling**: Attempting to parse addresses before accounting for variable-length IFAC field

## Debugging Wire Format

When debugging packet issues:

1. **Examine First Byte**: Extract and decode all flag bits
2. **Check Hop Count**: Verify reasonable value (usually 0-30)
3. **Validate Packet Length**: Ensure within MTU and correct for header type
4. **Verify Hash Positions**: Confirm 16-byte boundaries align correctly
5. **Inspect Context Byte**: Ensure valid context value (0x00-0x0E, 0xFA-0xFF)
6. **Check Payload Size**: Verify data doesn't exceed MDU/ENCRYPTED_MDU
7. **Trace Encryption**: Determine if packet should be encrypted based on type and context

## Reference Code

See `wire-examples.py` for complete working examples of packet construction and parsing at the byte level.

## Related Skills

- **Cryptography & Identity**: Understanding encryption/decryption applied to packet data
- **Transport & Routing**: How packets are forwarded and header types are used
- **Links**: Link-specific packet types and context values
- **Resources**: Resource transfer packet contexts and sequencing
- **Announce Mechanism**: Structure and propagation of ANNOUNCE packets
