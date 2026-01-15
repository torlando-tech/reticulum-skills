---
name: lxmf-docs
description: Quick reference for LXMF protocol documentation
argument-hint: "[constants|states|methods|fields|stamps|tickets|router|peer|examples]"
allowed-tools:
  - Read
  - Grep
---

# LXMF Docs Command

Quickly look up LXMF protocol documentation by topic.

## Usage

- No arguments: Show overview and available topics
- With topic: Show specific documentation section

## Available Topics

| Topic | Description |
|-------|-------------|
| `constants` | All LXMF constants (fields, states, methods) |
| `states` | Message state machine and transitions |
| `methods` | Delivery methods (DIRECT, OPPORTUNISTIC, etc.) |
| `fields` | FIELD_* constants for message fields |
| `stamps` | Proof-of-work stamp system |
| `tickets` | Ticket authentication system |
| `router` | LXMRouter configuration and API |
| `peer` | LXMPeer states and sync protocol |
| `examples` | Code examples for common operations |

## Implementation

### No argument - Overview

Show a brief overview of LXMF with links to topics:
- What LXMF is (Lightweight Extensible Message Format)
- Quick summary of key concepts
- List of available topics

### Topic: constants

Read and display: `the plugin's skill references directory/references/constants.md`

### Topic: states

Extract message states from `the plugin's skill references directory/LXMF/LXMessage.py`:
```
GENERATING (0x00) - Stamp/content being generated
OUTBOUND (0x01)   - Queued for delivery
SENDING (0x02)    - Currently transmitting
SENT (0x04)       - Transmitted successfully
DELIVERED (0x08)  - Confirmed delivered
REJECTED (0xFD)   - Rejected by propagation node
CANCELLED (0xFE)  - Cancelled by user
FAILED (0xFF)     - Failed after retries
```

### Topic: methods

Show delivery methods:
```
OPPORTUNISTIC (0x01) - Single packet, no link, max ~295 bytes
DIRECT (0x02)        - Establish link first (default)
PROPAGATED (0x03)    - Via propagation node
PAPER (0x05)         - QR/URI encoding
```

### Topic: fields

Extract FIELD_* constants from `the plugin's skill references directory/LXMF/LXMF.py`

### Topic: stamps

Show stamp system documentation:
- Purpose (proof-of-work for spam prevention)
- Cost range (1-254)
- Generation and validation
- External generator support

### Topic: tickets

Show ticket documentation:
- Purpose (pre-authorized stamp bypass)
- Expiry (21 days)
- Grace period (5 days)
- Auto-renewal (14 days threshold)

### Topic: router

Show LXMRouter configuration:
- Constructor parameters
- Default values
- Key methods (handle_outbound, register_delivery_callback, etc.)

### Topic: peer

Show LXMPeer information:
- Peer states (IDLE, LINK_ESTABLISHING, SYNCING, etc.)
- Sync strategies (LAZY, PERSISTENT)
- Error states and backoff

### Topic: examples

Read and display: `the plugin's skill references directory/references/examples.md`

## Example Output

```
$ /lxmf-docs methods

LXMF Delivery Methods
=====================

OPPORTUNISTIC (0x01)
  - Single RNS packet, no link established
  - Maximum content: ~295 bytes
  - Fast but less reliable
  - Requires announced destination

DIRECT (0x02) [DEFAULT]
  - Establishes RNS link first
  - Supports unlimited size via Resource transfer
  - Most reliable delivery method
  - Confirms delivery

PROPAGATED (0x03)
  - Routes through propagation node
  - For offline recipients
  - Size limited by propagation node settings
  - Higher latency

PAPER (0x05)
  - Encodes message as QR code or URI
  - For offline/physical transmission
  - Maximum: ~2.9 KB
  - No network required
```
