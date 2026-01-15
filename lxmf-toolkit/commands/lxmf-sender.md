---
name: lxmf-sender
description: Run the LXMF example sender script for testing
argument-hint: "[storage_path]"
allowed-tools:
  - Bash
  - Read
---

# LXMF Sender Command

Run the example sender script from the LXMF repository for testing message transmission.

## Usage

- No arguments: Run with default storage path (`./tmp_sender`)
- With path: Run with specified storage path

## Implementation

1. **Locate the script**: The example sender is at `docs/example_sender.py` relative to the repository root.

2. **Run the script**: Navigate to the LXMF repository and run:
   ```bash
   python3 docs/example_sender.py
   ```

3. **Interactive prompts**: The script will prompt for:
   - Recipient LXMF address (destination hash)
   - Message content

4. **Monitor output**: Show the script output including:
   - Local LXMF address generated
   - Path discovery status
   - Message state progression
   - Delivery confirmation or failure

## Script Overview

The example sender (`docs/example_sender.py`):
- Initializes Reticulum and LXMF router
- Creates a local identity and delivery destination
- Prompts for recipient hash
- Attempts to recall recipient identity
- Sends a message with random test data
- Reports delivery status via callbacks

## Tips

- First run the receiver in another terminal to get a destination hash
- The sender will wait for path discovery if needed
- Use Ctrl+C to exit after sending
- Check `~/.reticulum/` for RNS configuration if network issues occur

## Example Session

```
$ /lxmf-sender

Running LXMF example sender...

LXMF Router initialised
Local LXMF address: <abc123def456...>

Enter recipient LXMF address: c5e3842981456a23fc3332edc6056474
Requesting path to destination...
Path found, establishing link...
Message sent!
Delivery confirmed.
```

## Troubleshooting

- **No path to destination**: Ensure receiver has announced and is reachable
- **Identity not found**: The recipient hasn't announced or announce hasn't propagated
- **Link failed**: Network connectivity issue between nodes
