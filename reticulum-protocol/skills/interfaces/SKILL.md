---
name: interfaces
description: Reticulum's hardware abstraction layer and interface types. Use when working with RNode, AutoInterface, TCP, UDP, I2P, Serial, KISS, BLE interfaces, interface modes, IFAC, bandwidth allocation, or MTU.
---

# Interfaces

This skill provides knowledge about Reticulum's hardware abstraction layer and interface types. Invoke when the user mentions interface types, RNode, AutoInterface, TCP interface, UDP interface, I2P, Serial, KISS, Pipe, Local, Weave, Backbone, interface modes, IFAC (Interface Access Code), announce propagation, bandwidth allocation, or MTU.

## Hardware Abstraction Overview

Reticulum implements a flexible hardware abstraction layer that allows communication over virtually any medium. The interface system handles physical layer details while presenting a uniform API to the transport layer.

**Key principle**: Interfaces are the only part of Reticulum that need to know about physical medium characteristics. Everything above the interface layer is hardware-agnostic.

## Built-in Interface Types

Reticulum includes 15+ built-in interface types:

### RNode Interface

**RNodeInterface**: Hardware interface for RNode LoRa devices - open-source, general-purpose data radios.

**Properties**:
- Direct LoRa radio control
- Long-range, low-bandwidth communication (typical: 1-10 km)
- Configurable frequency, spreading factor, coding rate, TX power
- Hardware-level packet framing via KISS protocol
- Default IFAC size: 8 bytes

**Use cases**: Off-grid mesh networking, long-range point-to-point links, disaster communications

**RNodeMultiInterface**: Manages multiple RNode sub-interfaces for frequency diversity and channel bonding.

### AutoInterface

**AutoInterface**: Zero-configuration local network discovery and communication over Ethernet/WiFi.

**Properties**:
- Automatic peer discovery via IPv6 link-local multicast
- No routers, DHCP, or IP infrastructure required
- Works on any Ethernet-based medium (wired, WiFi, direct cable)
- Uses UDP for transport but doesn't require functional IP routing
- Creates dynamic sub-interfaces for each discovered peer
- Default IFAC size: 16 bytes (spawned peers)

**Use cases**: LAN mesh networking, automatic peer discovery, zero-config local communication

### TCP Interfaces

**TCPClientInterface**: Connects to remote TCP server, establishing persistent connection.

**TCPServerInterface**: Listens for incoming TCP connections, spawning interface per client.

**Properties**:
- Internet/WAN connectivity
- Works over IPv4, IPv6, Yggdrasil, I2P (tunneled)
- Reliable, ordered delivery (TCP semantics)
- Default IFAC size: 16 bytes
- Supports device binding, IP preference, port configuration

**Use cases**: Internet backbone connectivity, connecting to public nodes, WAN bridges

### UDP Interface

**UDPInterface**: Connectionless UDP-based interface for specific remote endpoints.

**Properties**:
- Lightweight, lower overhead than TCP
- Best-effort delivery (no reliability guarantees)
- Suitable for controlled networks with low packet loss
- Default IFAC size: 16 bytes
- Configurable forward_ip/forward_port

**Use cases**: Low-latency links, controlled network segments, testing

### I2P Interface

**I2PInterface**: Anonymous networking via the Invisible Internet Project.

**Properties**:
- End-to-end encrypted, anonymous connections
- NAT traversal without port forwarding
- High latency but strong privacy properties
- Spawns peer interfaces for each connection
- Default IFAC size: 16 bytes
- Requires I2P router (i2pd or Java I2P)

**Use cases**: Censorship resistance, privacy-critical applications, anonymous mesh networking

### Serial Interface

**SerialInterface**: Direct serial port communication (RS-232, USB serial, etc.).

**Properties**:
- Physical serial connections
- Configurable baud rate, parity, stop bits
- Point-to-point links only
- Default IFAC size: 8 bytes
- Common baud rates: 9600 to 115200

**Use cases**: Direct device connections, legacy hardware integration, physical point-to-point links

### KISS Interface

**KISSInterface**: Serial interface using KISS protocol framing for radio modems.

**AX25KISSInterface**: KISS interface with AX.25 (amateur packet radio) support.

**Properties**:
- Standard protocol for TNC (Terminal Node Controller) connections
- Works with many amateur radio modems
- Byte-stuffing for binary transparency
- Configurable preamble, tail, persistence, slot time
- Default IFAC size: 8 bytes

**Use cases**: Amateur radio packet networks, hardware TNC integration, legacy radio modems

### Pipe Interface

**PipeInterface**: Bidirectional communication through Unix pipes or external programs.

**Properties**:
- Connects to stdin/stdout of external process
- Allows integration of custom transport mechanisms
- Full-duplex communication
- Process lifecycle management
- No default IFAC (typically used without virtual networks)

**Use cases**: Custom transport scripts, integration with external tools, testing and development

### Local Interface

**LocalInterface**: Unix socket-based inter-process communication on same machine.

**Properties**:
- High-speed, zero-latency local IPC
- Multiple local clients can connect to single server socket
- No network overhead
- Useful for multi-process architectures
- No default IFAC (local-only communication)

**Use cases**: Multi-process applications, local service integration, development/testing

### Weave Interface

**WeaveInterface**: Advanced interface type for creating resilient multi-path networks.

**Properties**:
- Aggregates multiple physical interfaces into single logical interface
- Path diversity and automatic failover
- Load balancing across available paths
- Dynamic path selection based on metrics
- Default IFAC size: 16 bytes
- Spawns peer interfaces automatically

**Use cases**: High-availability links, multi-homed connectivity, resilient backbone connections

### Backbone Interface

**BackboneInterface**: High-speed backbone networking over IP networks (designed for Yggdrasil and similar).

**Properties**:
- Optimized for high-throughput, low-latency links
- Supports binding to specific network devices (e.g., Yggdrasil tun0)
- Can act as both client and server
- Compatible with TCPServerInterface remotes
- Default IFAC size: 16 bytes
- Efficient for overlay networks

**Use cases**: Yggdrasil backbone links, high-speed overlay networks, regional/global connectivity

## Interface Modes

All interfaces support optional `mode` setting that affects announce propagation, path discovery, and path expiration:

### MODE_FULL (0x01) - Default

**Behavior**: All discovery, meshing, and transport functionality active.

**Announce propagation**: Accepts announces from all modes, propagates to Full, Boundary, and Roaming interfaces.

**Path expiration**: Standard (7 days / PATHFINDER_E)

**Use case**: Default for most interfaces, general mesh participation

### MODE_GATEWAY (0x06) - Gateway

**Behavior**: Same as Full, plus actively discovers unknown paths on behalf of clients.

**Announce propagation**: Same as Full mode.

**Path discovery**: When receiving path request for unknown destination from gateway interface, attempts discovery via all other interfaces and forwards discovered path back to requestor.

**Use case**: Interface facing clients that need wide path resolution (e.g., client-facing WiFi interface while uplink is on another interface)

**Important**: Gateway mode goes on the **client-facing interface**, not the uplink.

### MODE_ACCESS_POINT (0x03) - Access Point

**Behavior**: Network access point for transient clients.

**Announce propagation**: Does NOT accept announces from other APs or Roaming interfaces. Propagates to Full, Boundary, and Roaming interfaces only.

**Path expiration**: Short (1 day / AP_PATH_TIME)

**Characteristics**:
- Quiet by default - doesn't broadcast announces until clients use them
- Handles path requests like Gateway mode
- Suitable for wide-area access points

**Use case**: Public LoRa hotspots, wide-area radio access points with transient users

### MODE_ROAMING (0x04) - Roaming

**Behavior**: Physically mobile interface from network's perspective.

**Announce propagation**: Accepts announces from Full and Boundary only. Does NOT propagate announces to any other interfaces (leaf mode).

**Path expiration**: Very short (6 hours / ROAMING_PATH_TIME)

**Use case**: Mobile vehicle external interface, while internal interfaces serve devices moving WITH the vehicle

**Example**: Vehicle with external LoRa (roaming mode) and internal WiFi (full mode). Internal devices reach each other and LoRa-side devices when in range; LoRa-side reaches internal devices when vehicle is in range.

### MODE_BOUNDARY (0x05) - Boundary

**Behavior**: Connects significantly different network segments.

**Announce propagation**: Accepts announces from Full, AP, Boundary, and Roaming. Propagates to Full and Boundary only.

**Path expiration**: Standard (7 days)

**Use case**: Interface connecting different network types (e.g., local LoRa mesh + high-speed Internet backbone)

**Example**: LoRa mesh node with Internet connection - set Internet-facing interface to Boundary mode.

## Announce Propagation Rules

The following rules govern automatic announce forwarding between interface modes:

**From Full interface** → Propagates to: Full, Boundary, Roaming (not AP)

**From Gateway interface** → Same as Full mode

**From Access Point interface** → Propagates to: Full, Boundary, Roaming (not other APs)

**From Roaming interface** → Propagates to: Full, Boundary (not AP, not other Roaming)

**From Boundary interface** → Propagates to: Full, Boundary (not AP, not Roaming)

**Receiving side**:
- Full/Gateway: Accepts from Full, AP, Boundary, Roaming
- Access Point: Accepts from Full, Boundary only (not AP, not Roaming)
- Roaming: Accepts from Full, Boundary only (not AP, not Roaming)
- Boundary: Accepts from Full, AP, Boundary, Roaming

This creates a hierarchical propagation graph that prevents announce flooding while ensuring reachability.

## Interface Access Codes (IFAC)

IFAC enables named virtual networks and passphrase-protected interfaces. Packets without valid IFAC are silently dropped.

### Purpose

- Create isolated virtual networks on shared physical medium
- Authenticate packets at interface level
- Prevent unauthorized network access

### Implementation

**IFAC generation**:
1. Interface configured with `ifac_netname` (network name) and/or `ifac_netkey` (passphrase)
2. Derive IFAC origin: `Full_Hash(network_name) + Full_Hash(passphrase)`
3. Generate 64-byte key via HKDF: `HKDF(SHA-256(ifac_origin), salt=IFAC_SALT, length=64)`
4. Create Ed25519 identity from derived key: `Identity.from_bytes(ifac_key)`
5. For each outbound packet: Sign entire packet with IFAC identity
6. Truncate signature to configured `ifac_size` (1-64 bytes)
7. Insert IFAC into packet after header, mask entire packet with IFAC-derived mask
8. Set IFAC flag in header (bit 7 of first byte)

**IFAC verification**:
1. Check IFAC flag in packet header
2. Extract IFAC from packet (after header, length = ifac_size)
3. Unmask packet using IFAC-derived mask
4. Verify signature matches expected value from interface's IFAC identity
5. Drop packet if signature invalid; accept if valid

**IFAC size**: Configurable from 8 to 512 bits in config (1 to 64 bytes). Default varies by interface type:
- RNode: 64 bits / 8 bytes (bandwidth-constrained)
- TCP/UDP/I2P/Backbone/Weave/Auto: 128 bits / 16 bytes (good balance)
- Full Ed25519: 512 bits / 64 bytes (maximum security)

Smaller IFAC = lower overhead but higher collision probability. Larger IFAC = stronger authentication but more bandwidth.

**Constants**:
```python
IFAC_MIN_SIZE = 1  # Minimum IFAC size in bytes
IFAC_SALT = bytes.fromhex("adf54d882c9a9b80...")  # Fixed salt for IFAC derivation
```

### Configuration Example

```ini
[[Private LoRa Network]]
  type = RNodeInterface
  port = /dev/ttyUSB0

  # Create isolated virtual network
  ifac_netname = private_mesh
  ifac_netkey = correct_horse_battery_staple
  ifac_size = 64  # 64 bits = 8 bytes
```

Only interfaces with matching netname+netkey can communicate. Others see encrypted garbage or invalid signatures.

## Bandwidth Allocation

### Announce Cap

The `announce_cap` option controls maximum bandwidth allocated to announce propagation and network maintenance at any given time.

**Default**: 2% (`ANNOUNCE_CAP = 2`)

**Range**: 1-100 (percentage of interface bandwidth)

**Behavior**:
- If announce would exceed cap, it's queued for later transmission
- Queue prioritizes announces with fewer hops (nearby nodes first)
- Ensures local networks aren't overwhelmed by distant high-bandwidth networks
- Stale announces eventually dropped if queued too long

**Per-interface configuration**:
```ini
[[High Speed Backbone]]
  type = TCPClientInterface
  announce_cap = 5  # Allow 5% bandwidth for announces
```

**Calculation**:
```python
tx_time = (packet_length_bytes * 8) / interface_bitrate_bps
wait_time = tx_time / (announce_cap / 100.0)
announce_allowed_at = current_time + wait_time
```

### Announce Rate Control

Fine-grained control over announce re-broadcast rate on fast interfaces:

**announce_rate_target**: Minimum seconds between re-broadcasts of announces for same destination.
- Example: `3600` = max once per hour per destination

**announce_rate_grace**: Number of times destination can announce before rate limiting applied.
- Allows initial announces through, then rate-limits

**announce_rate_penalty**: Additional delay after rate limit triggered.

These moderate the *rate at which received announces are re-broadcast to other interfaces*, independent of announce_cap.

## MTU (Maximum Transmission Unit)

MTU is the maximum packet size an interface can transmit, configurable per-interface.

**Default**: 500 bytes (`Reticulum.MTU = 500`)

**Calculation chain**:
```python
MTU = 500  # Wire MTU (configurable per-interface)
HEADER_MAXSIZE = 2 + 1 + 32 = 35 bytes  # Flags + hops + 2x truncated hash
IFAC_MIN_SIZE = 1 byte  # Minimum IFAC overhead

MDU (Maximum Data Unit) = MTU - HEADER_MAXSIZE - IFAC_MIN_SIZE
MDU = 500 - 35 - 1 = 464 bytes  # Available for payload

# For links (with encryption overhead):
Link.MDU = floor((MTU - IFAC_MIN_SIZE - HEADER_MINSIZE - TOKEN_OVERHEAD) / AES128_BLOCKSIZE) * AES128_BLOCKSIZE - 1
```

**Auto-configuration**: Some interfaces (like AutoInterface, TCPClientInterface) support automatic MTU optimization based on detected bitrate:

```python
if bitrate >= 1 Gbps:   HW_MTU = 524288
elif bitrate > 750 Mbps: HW_MTU = 262144
elif bitrate > 400 Mbps: HW_MTU = 131072
elif bitrate > 200 Mbps: HW_MTU = 65536
# ... down to ...
elif bitrate <= 62.5 kbps: HW_MTU = None (use default)
```

Larger MTU = higher throughput but requires all intermediary hops to support it. Link MTU discovery negotiates optimal MTU across multi-hop paths.

**Configuration**:
```ini
[[High Speed Link]]
  type = TCPClientInterface
  target_host = 10.0.0.1
  target_port = 4242
  mtu = 16384  # Increase MTU for high-speed link
```

## Common Interface Options

All interfaces support these common configuration options:

**enabled**: `yes` or `no` - Whether interface is active

**mode**: Interface mode (`full`, `gateway`/`gw`, `access_point`/`ap`, `roaming`, `boundary`)

**ifac_netname**: Virtual network name (string)

**ifac_netkey**: Virtual network passphrase (string)

**ifac_size**: IFAC signature size in bits (minimum 8, i.e., 1 byte)

**announce_cap**: Bandwidth percentage for announces (1-100, default 2)

**announce_rate_target**: Minimum seconds between re-broadcasts per destination

**announce_rate_grace**: Number of announces before rate limiting

**announce_rate_penalty**: Penalty delay after rate limit

**mtu**: Maximum transmission unit in bytes (default 500)

**ingress_control**: Enable/disable ingress limiting (default enabled on most interfaces)

## Interface Statistics

All interfaces track basic statistics:

**rxb**: Bytes received

**txb**: Bytes transmitted

**bitrate**: Configured/detected bitrate in bits per second

**online**: Boolean - interface operational status

**HW_MTU**: Hardware MTU (may differ from configured MTU)

Statistics accessible via `rnstatus` utility or programmatically via interface properties.

## Trigger Phrases

This skill should activate when users mention:
- "interface types", "what interfaces", "available interfaces"
- "RNode", "RNodeInterface", "LoRa interface"
- "AutoInterface", "automatic discovery", "zero-config"
- "TCP interface", "TCPClientInterface", "TCPServerInterface"
- "UDP interface", "UDPInterface"
- "I2P interface", "I2PInterface", "anonymous"
- "Serial interface", "SerialInterface", "KISS", "KISSInterface", "AX25"
- "Pipe interface", "PipeInterface"
- "Local interface", "LocalInterface", "Unix socket"
- "Weave interface", "WeaveInterface", "multi-path"
- "Backbone interface", "BackboneInterface", "Yggdrasil"
- "interface modes", "gateway mode", "access point mode", "roaming mode", "boundary mode"
- "IFAC", "Interface Access Code", "virtual network", "ifac_netname", "ifac_netkey"
- "announce propagation", "announce rules", "propagation graph"
- "announce cap", "bandwidth allocation", "announce_cap"
- "MTU", "maximum transmission unit", "HW_MTU"
- "interface configuration", "configure interface"

## Implementation Notes

### Custom Interfaces

Reticulum is fully extensible with custom interfaces. Custom interface classes inherit from `RNS.Interfaces.Interface` and implement:

**Required methods**:
- `__init__()`: Initialize interface
- `process_outgoing(data)`: Send data to physical medium
- `process_incoming(data)`: Receive data from physical medium

**Required properties**:
- `IN`: Boolean - can receive
- `OUT`: Boolean - can transmit
- `bitrate`: Interface speed in bps

**Optional**:
- `mode`: Interface mode constant
- `announce_cap`: Bandwidth allocation override
- IFAC configuration
- MTU customization

See `RNS/Interfaces/Interface.py` for base class and implementation details.

### Spawned Interfaces

Some interface types (AutoInterface, TCPServerInterface, I2PInterface, WeaveInterface, BackboneInterface) spawn child interfaces dynamically:

- Parent interface listens/discovers
- Creates child interface per peer/connection
- Child inherits IFAC settings, announce_cap, mode from parent
- Each child tracked independently for statistics

**Example**: TCPServerInterface spawns TCPClientInterface for each incoming connection. Each client connection is a separate interface in the transport layer.

## Reference Implementation

See implementation files:
- `https://github.com/markqvist/Reticulum/RNS/Interfaces/Interface.py` - Base interface class
- `https://github.com/markqvist/Reticulum/RNS/Interfaces/RNodeInterface.py` - RNode implementation
- `https://github.com/markqvist/Reticulum/RNS/Interfaces/AutoInterface.py` - AutoInterface implementation
- `https://github.com/markqvist/Reticulum/RNS/Interfaces/TCPInterface.py` - TCP client/server
- `https://github.com/markqvist/Reticulum/RNS/Interfaces/I2PInterface.py` - I2P implementation
- `https://github.com/markqvist/Reticulum/RNS/Transport.py` - IFAC calculation and verification (lines 795-830)
- `https://github.com/markqvist/Reticulum/docs/source/interfaces.rst` - Interface configuration documentation
- `https://github.com/markqvist/Reticulum/docs/source/understanding.rst` - Lines 677-694 (IFAC), 834-867 (announce propagation)
