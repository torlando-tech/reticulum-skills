---
name: lxmf-analyze
description: Inspect LXMF message structure and content (for debugging already-decrypted messages)
argument-hint: "<message_object_info|destination_hash>"
allowed-tools:
  - Bash
  - Read
---

# LXMF Analyze Command

Analyze LXMF message structure during debugging.

## Important: LXMF Messages Are Encrypted

All LXMF messages (OPPORTUNISTIC, DIRECT, PROPAGATED, and PAPER) encrypt the payload using the recipient's public key. The only unencrypted portion is the **destination hash** (first 16 bytes).

To decrypt a message, you need:
- The recipient's `RNS.Identity` with private key
- Call `LXMessage.unpack_from_bytes(data, identity)`

This command helps analyze messages **after** decryption, typically during debugging.

## Use Cases

### 1. Analyze a Received Message Object

In a delivery callback, inspect the message:

```python
def delivery_callback(message):
    print(f"Hash: {RNS.prettyhexrep(message.hash)}")
    print(f"Source: {RNS.prettyhexrep(message.source_hash)}")
    print(f"Destination: {RNS.prettyhexrep(message.destination_hash)}")
    print(f"Timestamp: {message.timestamp}")
    print(f"Title: {message.title}")
    print(f"Content: {message.content}")
    print(f"Method: {message.method}")  # OPPORTUNISTIC=1, DIRECT=2, PROPAGATED=3
    print(f"Fields: {message.fields}")
    print(f"Signature valid: {message.signature_validated}")

    # Physical layer info (if available)
    print(f"RSSI: {message.rssi}, SNR: {message.snr}, Q: {message.q}")

    # Opportunistic-only attributes
    if hasattr(message, 'receiving_interface'):
        print(f"Interface: {message.receiving_interface}")
        print(f"Hops: {message.receiving_hops}")
```

### 2. Extract Destination from Encrypted Bytes

The only thing you can extract from encrypted bytes without the key:

```python
encrypted_bytes = bytes.fromhex("c5e3842981456a23...")
destination_hash = encrypted_bytes[:16]
print(f"Destination: {RNS.prettyhexrep(destination_hash)}")
# Everything after byte 16 is encrypted
```

### 3. Decrypt and Analyze Raw Bytes

If you have the recipient's identity:

```python
import RNS, LXMF

# Load identity with private key
identity = RNS.Identity.from_file("~/.myapp/identity")

# Decrypt and unpack
message = LXMF.LXMessage.unpack_from_bytes(encrypted_bytes, identity)

if message:
    print(f"Title: {message.title}")
    print(f"Content: {message.content}")
    print(f"From: {RNS.prettyhexrep(message.source_hash)}")
else:
    print("Failed to decrypt - wrong identity or corrupted data")
```

## Message Structure Reference

### Wire Format
```
[0:16]   Destination hash (UNENCRYPTED)
[16:]    Encrypted payload (requires recipient's private key)
```

### Decrypted Payload (msgpack list)
```python
[
    timestamp,    # float: seconds since Unix epoch
    title,        # bytes: message title
    content,      # bytes: message body
    fields,       # dict: extensible fields (FIELD_* constants)
    stamp         # optional: proof-of-work stamp bytes
]
```

### Common Fields
| Constant | Value | Purpose |
|----------|-------|---------|
| FIELD_FILE_ATTACHMENTS | 0x05 | List of (filename, data) tuples |
| FIELD_IMAGE | 0x06 | Image data |
| FIELD_AUDIO | 0x07 | Audio data |
| FIELD_TICKET | 0x0C | Authentication ticket |
| FIELD_RENDERER | 0x0F | Content renderer type |

## Debugging Tips

Enable verbose logging to see message flow:
```python
import RNS
RNS.loglevel = RNS.LOG_VERBOSE
```

Check message state progression:
```python
# States: GENERATING=0, OUTBOUND=1, SENDING=2, SENT=4,
#         DELIVERED=8, REJECTED=253, CANCELLED=254, FAILED=255
print(f"State: {message.state}")
```
