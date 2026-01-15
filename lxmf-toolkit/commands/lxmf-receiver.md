---
name: lxmf-receiver
description: Run the LXMF example receiver script for testing
argument-hint: "[storage_path] [stamp_cost]"
allowed-tools:
  - Bash
  - Read
---

# LXMF Receiver Command

Run the example receiver script from the LXMF repository for testing message reception.

## Usage

- No arguments: Run with defaults (storage: `./tmp_receiver`, stamp_cost: 8)
- With path: Specify custom storage path
- With stamp_cost: Specify required stamp cost for incoming messages

## Implementation

1. **Locate the script**: The example receiver is at `docs/example_receiver.py` relative to the repository root.

2. **Run the script**: Navigate to the LXMF repository and run:
   ```bash
   python3 docs/example_receiver.py
   ```

3. **Monitor output**: Show the script output including:
   - Local LXMF address (this is what senders need)
   - Announce status
   - Incoming message details

4. **Keep running**: The receiver runs continuously until Ctrl+C

## Script Overview

The example receiver (`docs/example_receiver.py`):
- Initializes Reticulum and LXMF router
- Creates a local identity and delivery destination
- Registers a delivery callback to handle incoming messages
- Announces presence on the network
- Displays received messages with full details:
  - Source hash
  - Timestamp
  - Title and content
  - Fields dictionary
  - Signature validation status
  - Stamp information

## Tips

- Copy the displayed LXMF address to use with the sender
- Press a key to trigger re-announce
- The receiver must stay running to receive messages
- Check Reticulum interfaces in `~/.reticulum/config` for network setup

## Example Session

```
$ /lxmf-receiver

Running LXMF example receiver...

LXMF Router initialised
Your LXMF address: <c5e3842981456a23fc3332edc6056474>
Announced on network

[Waiting for messages... Press Ctrl+C to exit]

--- Incoming Message ---
From: <abc123def456...>
Time: 2025-01-14 10:30:45
Title: Test Message
Content: Hello from sender!
Signature: Valid
------------------------
```

## Message Callback Details

The receiver callback shows:
- `message.source_hash` - Sender's destination hash
- `message.timestamp` - When message was created
- `message.title` - Message title
- `message.content` - Message body
- `message.signature_validated` - True if signature verified
- `message.rssi`, `message.snr`, `message.q` - Physical layer info (if available)
- `message.receiving_interface` - Interface packet arrived on (opportunistic only)
