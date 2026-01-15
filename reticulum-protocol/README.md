# Reticulum Protocol Plugin

Comprehensive knowledge base for implementing the Reticulum protocol with byte-perfect interoperability.

## Overview

This plugin provides protocol-level knowledge for implementing Reticulum in any programming language while achieving 1:1 byte-perfect compatibility with the Python reference implementation.

**Focus:** Wire format, cryptography, transport mechanics - not Python API usage.

## Components

### Skills (9 auto-triggering)

1. **Transport & Routing** - Multi-hop routing, path finding, announce propagation
2. **Links** - Encrypted channels, ECDH key exchange, forward secrecy
3. **Resources** - Large data transfers, windowing, hashmap coordination
4. **Destinations** - Addressing system, destination types, hash calculation
5. **Packets & Wire Format** - Binary packet structure, headers, MTU/MDU
6. **Cryptography & Identity** - Authoritative primitives, token format, HKDF
7. **Interfaces** - Interface types, modes, IFAC, propagation rules
8. **Announce Mechanism** - Path discovery, propagation algorithm, bandwidth allocation
9. **Reticulum Utilities** - Command-line tools (rnpath, rnprobe, rnir, rnid)

### Agent (1 proactive)

**Protocol Implementation Assistant** - Helps developers implement Reticulum in other languages with byte-level guidance.

## Installation

1. Copy this plugin to your Claude Code plugins directory:
   ```bash
   cp -r reticulum-protocol ~/.claude/plugins/
   ```

2. Restart Claude Code to load the plugin

3. Or run Claude Code with plugin directory flag:
   ```bash
   cc --plugin-dir ~/.claude/plugins/reticulum-protocol
   ```

## Usage

### Skills Auto-Trigger

Skills automatically activate when you ask protocol-related questions:

- "How does the transport layer work?" → **transport-routing** skill
- "Show me packet structure" → **packets-wire-format** skill
- "What are the cryptographic primitives?" → **cryptography-identity** skill
- "How do I calculate destination hash?" → **destinations** skill

### Agent Activation

The Protocol Implementation Assistant agent activates when you:

- Say "I want to implement Reticulum in [language]"
- Ask "How do I port Reticulum to [language]"
- Mention "reticulum wire format", "byte-level implementation"
- Debug protocol interop issues

## Content Structure

Each skill follows progressive disclosure:

- **SKILL.md** (1,500-2,000 words): Core concepts, constants, formulas
- **references/** directory: Deep technical details, verbatim RST extractions
- **wire-examples.py**: Byte-level Python code demonstrating protocol structures

## Key Protocol Constants

- **MTU**: 500 bytes (sacred, do not change)
- **MDU**: 465 bytes (MTU - headers)
- **ENCRYPTED_MDU**: 383 bytes
- **PATHFINDER_M**: 128 hops maximum
- **TRUNCATED_HASHLENGTH**: 128 bits (16 bytes)

## Reference Implementation

This plugin is based on the Python reference implementation:
- **Location**: `https://github.com/markqvist/Reticulum`
- **Author**: Mark Qvist (2016-2025)
- **License**: MIT-like with restrictions
- **Wire format**: Stable and authoritative

## Protocol Philosophy

1. **Byte-perfect interoperability** - All implementations must match wire format exactly
2. **MTU=500 is sacred** - Changing MTU breaks compatibility
3. **Cryptographic primitives are authoritative** - No substitutions allowed
4. **Protocol over implementation** - Focus on wire format, not Python API

## Verification

To verify your implementation:

1. Use `rnpath` to test path discovery
2. Use `rnprobe` to measure RTT and connectivity
3. Test packet interop with Python implementation
4. Capture packets and verify byte structure

## License Note

Reticulum is under MIT-like license with restrictions:
- Software shall not be used to purposefully harm human beings
- Software shall not be used for AI/ML training datasets
- See Python reference implementation for full license text

## Contributing

This plugin extracts knowledge from the official Reticulum documentation and source code. To improve:

1. Ensure accuracy with Python reference implementation
2. Keep wire-examples.py byte-accurate
3. Extract verbatim where specified
4. Focus on protocol, not implementation details

## Support

- **Reticulum Documentation**: https://markqvist.github.io/Reticulum/manual/
- **GitHub**: https://github.com/markqvist/Reticulum
- **Reference Implementation**: `https://github.com/markqvist/Reticulum`

---

**Created**: 2026-01-15
**Version**: 0.1.0
