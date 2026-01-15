# Reticulum Skills

Claude Code plugins for [Reticulum Network Stack](https://reticulum.network/) and related protocol development.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| **[reticulum-protocol](./reticulum-protocol)** | Comprehensive protocol knowledge for implementing Reticulum with byte-perfect interoperability |
| **[lxmf-toolkit](./lxmf-toolkit)** | Development toolkit for LXMF (Lightweight Extensible Message Format) protocol |

## Installation

### From GitHub (recommended)

```bash
# Add the marketplace
claude plugin marketplace add https://github.com/torlando-tech/reticulum-skills

# Install the plugin
claude plugin install lxmf-toolkit@reticulum-skills
```

### Local Development

```bash
claude --plugin-dir /path/to/reticulum-skills/lxmf-toolkit
```

## Plugins

### reticulum-protocol

Comprehensive protocol knowledge base for implementing Reticulum in any programming language with byte-perfect interoperability.

**Components:**
- **9 Skills** (auto-triggering on protocol concepts):
  - `transport-routing` - Packet routing, path tables, multi-hop forwarding
  - `links` - Link establishment, ECDH key exchange, keepalives
  - `resources` - Large data transfer, windowing, compression
  - `destinations` - Address types, hash calculation, naming
  - `packets-wire-format` - Binary packet structure, MTU/MDU, headers
  - `cryptography-identity` - Ed25519, X25519, HKDF, token format
  - `interfaces` - Interface types, IFAC, announce propagation modes
  - `announce-mechanism` - Path discovery, announce format, bandwidth management
  - `reticulum-utilities` - rnpath, rnprobe, rnid, rnstatus utilities
- **Agent**: `protocol-implementation-assistant` - Proactive assistance for implementing Reticulum protocol in any language

### lxmf-toolkit

Development toolkit for the LXMF messaging protocol built on Reticulum.

**Components:**
- **Skill**: `lxmf-protocol` - Protocol knowledge, patterns, and debugging
- **Commands**:
  - `/lxmf-debug` - Debug routing and delivery issues
  - `/lxmf-analyze` - Inspect message structure
  - `/lxmf-sender` - Run example sender script
  - `/lxmf-receiver` - Run example receiver script
  - `/lxmf-docs` - Protocol documentation lookup
- **Agent**: `lxmf-developer` - Proactive assistance when editing LXMF code

## Related Projects

- [Reticulum](https://github.com/markqvist/Reticulum) - Cryptography-based networking stack
- [LXMF](https://github.com/markqvist/LXMF) - Lightweight Extensible Message Format
- [Sideband](https://github.com/markqvist/Sideband) - LXMF client application
- [Nomad Network](https://github.com/markqvist/NomadNetwork) - Terminal-based mesh communication
