---
skill_name: Reticulum Utilities
version: 1.0.0
description: Comprehensive guide to Reticulum's command-line utilities for network management, diagnostics, identity operations, file transfer, and remote execution
color: blue
triggers:
  - "rnpath"
  - "rnprobe"
  - "rnir"
  - "rnid"
  - "rncp"
  - "rnx"
  - "rnstatus"
  - "rnsd"
  - "path inspection"
  - "network probe"
  - "identity recall"
  - "file transfer"
  - "remote execution"
  - "network status"
  - "reticulum daemon"
  - "announce database"
---

# Reticulum Utilities

Reticulum provides a comprehensive suite of command-line utilities for network management, diagnostics, identity operations, file transfer, and remote execution. These utilities form the operational toolkit for managing and interacting with Reticulum networks.

## Overview of Utilities

Reticulum includes the following core utilities:

- **rnpath**: Path discovery and management
- **rnprobe**: Network probing and RTT measurement
- **rnir**: Identity Recall (announce database inspection)
- **rnid**: Identity management and cryptographic operations
- **rncp**: File transfer using the Resource API
- **rnx**: Remote command execution
- **rnstatus**: Network status and interface statistics
- **rnsd**: Reticulum daemon for running as a service

## rnpath - Path Discovery and Management

The `rnpath` utility manages path discovery and routing table inspection in Reticulum networks.

### Basic Path Request

Request and display a path to a destination:

```bash
# Request path to a destination (replace with actual hash)
rnpath c89b4da064bf66d280f0e4d8abfd9806

# Output shows:
# Path to <c89b4da064bf66d280f0e4d8abfd9806> requested
# Path found, destination <c89b4da064bf66d280f0e4d8abfd9806> is 3 hops away via <e89b4da064bf66d2> on AutoInterface[wlan0]
```

### Display Path Table

View all known paths in the routing table:

```bash
# Show all paths
rnpath --table

# Show only paths with maximum 2 hops
rnpath --table --max 2

# Filter to specific destination
rnpath --table c89b4da064bf66d280f0e4d8abfd9806
```

Example output:
```
<3e12fc71692f8ec47bc5> is 1 hop  away via <3e12fc71692f8ec47bc5> on AutoInterface[eth0] expires 2026-01-15 14:23:19
<94b08f2d39ee12cf0922> is 2 hops away via <3e12fc71692f8ec47bc5> on AutoInterface[eth0] expires 2026-01-15 14:25:41
<c89b4da064bf66d280f0> is 3 hops away via <3e12fc71692f8ec47bc5> on AutoInterface[eth0] expires 2026-01-15 14:20:08
```

### Announce Rate Information

Monitor announce rates and rate violations:

```bash
# Show announce rate info for all destinations
rnpath --rates

# Show rates for specific destination
rnpath --rates c89b4da064bf66d280f0e4d8abfd9806
```

Example output:
```
<c89b4da064bf66d280f0> last heard 2 minutes ago, 4.5 announces/hour in the last 3 hours
<3e12fc71692f8ec47bc5> last heard 30 seconds ago, 12.0 announces/hour in the last 2 hours, 2 active rate violations, new announces allowed in 45 minutes
```

### Drop Paths

Remove paths from the routing table:

```bash
# Drop specific path
rnpath --drop c89b4da064bf66d280f0e4d8abfd9806

# Drop all paths via a specific transport instance
rnpath --drop-via 3e12fc71692f8ec47bc5

# Drop all queued announces on all interfaces
rnpath --drop-announces
```

### Remote Management

Query path tables on remote Reticulum instances:

```bash
# Get path table from remote instance
# -R: remote transport instance identity hash
# -i: path to management identity file
# -W: timeout for remote queries
rnpath --table -R 9fb6d773498fb3feda407ed8ef2c3229 -i ~/.reticulum/identities/mgmt_id -W 15

# Get announce rates from remote instance
rnpath --rates -R 9fb6d773498fb3feda407ed8ef2c3229 -i ~/.reticulum/identities/mgmt_id
```

### JSON Output

Export path information in JSON format for scripting:

```bash
# Export path table as JSON
rnpath --table --json

# Export announce rates as JSON
rnpath --rates --json
```

### Common Options

```bash
--config PATH    # Use alternative config directory
-w SECONDS       # Timeout before giving up (default: 15s)
-v, --verbose    # Increase verbosity
```

## rnprobe - Network Probing and RTT Measurement

The `rnprobe` utility sends probe packets to measure round-trip time (RTT) and verify connectivity.

### Basic Probe

Send a probe to a destination:

```bash
# Probe a destination with full destination name
# Format: app.aspect1.aspect2... destination_hash
rnprobe lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# Output shows:
# Sent probe 1 (16 bytes) to <c89b4da064bf66d280f0e4d8abfd9806> via <3e12fc71692f8ec4> on AutoInterface[wlan0]
# Valid reply from <c89b4da064bf66d280f0e4d8abfd9806>
# Round-trip time is 245.3 milliseconds over 3 hops
```

### Probe with Options

Configure probe parameters:

```bash
# Send multiple probes
rnprobe -n 5 lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# Send larger probe packet
rnprobe -s 128 lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# Wait between probes
rnprobe -n 10 -w 2 lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# Set custom timeout
rnprobe -t 30 lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806
```

### Verbose Output

Show detailed path information:

```bash
# Verbose output shows next hop and interface details
rnprobe -v lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# Example output:
# Sent probe 1 (16 bytes) to <c89b4da064bf66d280f0e4d8abfd9806> via <3e12fc71692f8ec4> on AutoInterface[wlan0]
# Valid reply from <c89b4da064bf66d280f0e4d8abfd9806>
# Round-trip time is 245.3 milliseconds over 3 hops [RSSI -67 dBm] [SNR 18.5 dB] [Link Quality 94%]
```

### Probe Statistics

When sending multiple probes, statistics are shown:

```bash
rnprobe -n 10 lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# Output shows:
# ... (individual probe results) ...
# Sent 10, received 9, packet loss 10.0%
```

### Exit Codes

`rnprobe` returns meaningful exit codes for scripting:
- **0**: All probes successful
- **1**: Path request timed out
- **2**: Some packets lost
- **3**: Probe packet exceeds MTU

### Common Options

```bash
-s SIZE          # Probe packet size in bytes (default: 16)
-n COUNT         # Number of probes to send (default: 1)
-t SECONDS       # Timeout before giving up (default: 12s + hop latency)
-w SECONDS       # Time between each probe (default: 0)
-v, --verbose    # Show detailed output
--config PATH    # Use alternative config directory
```

## rnir - Identity Recall (Announce Database)

The `rnir` utility runs a simple Identity Recall service, making the announce database available for inspection. This is primarily used for diagnostic purposes.

### Start Identity Recall Service

```bash
# Run Identity Recall service with default config
rnir

# Use alternative config directory
rnir --config /path/to/config

# Verbose output
rnir -v

# Quiet mode
rnir -q
```

The Identity Recall service maintains the announce database, allowing other utilities and applications to query received announces and recalled identities. This is automatically handled by the Reticulum daemon in most deployments.

### Purpose

The `rnir` utility serves these functions:
- Maintains the announce database
- Makes identity information available for recall
- Provides network-wide identity distribution
- Enables destination lookups by identity hash

In practice, `rnir` functionality is usually provided by `rnsd` (the Reticulum daemon), and this utility is mainly used for testing and debugging announce propagation.

## rnid - Identity Management

The `rnid` utility provides comprehensive identity management, including key generation, import/export, signing, encryption, and destination operations.

### Generate New Identity

```bash
# Create new identity file
rnid --generate ~/.reticulum/identities/my_identity

# Force overwrite if file exists
rnid --generate ~/.reticulum/identities/my_identity --force
```

### Import and Export

```bash
# Import identity from hex string
rnid --import 7a2b9c... --write ~/.reticulum/identities/imported_id

# Import from base64
rnid --import ARF3t4w... --base64 --write ~/.reticulum/identities/imported_id

# Import from base32
rnid --import K4HGL... --base32 --write ~/.reticulum/identities/imported_id

# Export identity (private key) in hex
rnid -i ~/.reticulum/identities/my_identity --export

# Export in base64
rnid -i ~/.reticulum/identities/my_identity --export --base64

# Export in base32
rnid -i ~/.reticulum/identities/my_identity --export --base32
```

### Display Identity Information

```bash
# Show public key (private key hidden by default)
rnid -i ~/.reticulum/identities/my_identity --print-identity

# Show both public and private keys
rnid -i ~/.reticulum/identities/my_identity --print-identity --print-private

# Output shows:
# Public Key  : 2c0461f1c6f3a6aef3971f38e2dbd663b783c8f5ad5f2eb0e9772da88d4d1ce5
# Private Key : Hidden
```

### Calculate Destination Hashes

```bash
# Calculate destination hash for specific aspects
rnid -i ~/.reticulum/identities/my_identity --hash lxmf.delivery

# Output shows:
# The lxmf.delivery destination for this Identity is <c89b4da064bf66d2>
# The full destination specifier is <lxmf.delivery/c89b4da064bf66d280f0e4d8abfd9806>
```

### Announce Destination

```bash
# Announce a destination based on identity
rnid -i ~/.reticulum/identities/my_identity --announce lxmf.delivery

# Output shows:
# Created destination <lxmf.delivery/c89b4da064bf66d280f0e4d8abfd9806>
# Announcing destination <c89b4da064bf66d280f0e4d8abfd9806>
```

### File Signing and Verification

```bash
# Sign a file
rnid -i ~/.reticulum/identities/my_identity --sign document.pdf

# Creates document.pdf.rsg (signature file)

# Verify signature
rnid -i ~/.reticulum/identities/my_identity --validate document.pdf.rsg

# Output shows:
# Signature document.pdf.rsg for file document.pdf made by Identity <2c0461f1c6f3a6ae> is valid

# Sign with custom output path
rnid -i ~/.reticulum/identities/my_identity --sign document.pdf --write signature.rsg

# Verify with explicit paths
rnid -i ~/.reticulum/identities/my_identity --validate signature.rsg --read document.pdf
```

### File Encryption and Decryption

```bash
# Encrypt file for an identity (requires public key)
rnid -i c89b4da064bf66d280f0e4d8abfd9806 --encrypt sensitive.txt

# Creates sensitive.txt.rfe (encrypted file)

# Decrypt file (requires private key)
rnid -i ~/.reticulum/identities/my_identity --decrypt sensitive.txt.rfe

# Encrypt with custom output
rnid -i c89b4da064bf66d280f0e4d8abfd9806 --encrypt sensitive.txt --write encrypted.rfe

# Decrypt with custom output
rnid -i ~/.reticulum/identities/my_identity --decrypt encrypted.rfe --write decrypted.txt

# Force overwrite
rnid -i ~/.reticulum/identities/my_identity --decrypt encrypted.rfe --force
```

### Identity Recall from Network

```bash
# Request identity from network if not locally known
rnid -i c89b4da064bf66d280f0e4d8abfd9806 --request --print-identity

# Set custom timeout for request
rnid -i c89b4da064bf66d280f0e4d8abfd9806 --request -t 30 --print-identity

# Output shows:
# Path to <c89b4da064bf66d280f0e4d8abfd9806> requested
# Received Identity <2c0461f1c6f3a6ae> for destination <c89b4da064bf66d280f0e4d8abfd9806> from the network
# Public Key  : 2c0461f1c6f3a6aef3971f38e2dbd663b783c8f5ad5f2eb0e9772da88d4d1ce5
```

### Common Options

```bash
-i, --identity PATH    # Path to identity file or identity/destination hash
-g, --generate PATH    # Generate new identity
-m, --import DATA      # Import identity from hex/base32/base64
-x, --export           # Export identity
-p, --print-identity   # Display identity information
-P, --print-private    # Show private key (use with caution)
-H, --hash ASPECTS     # Calculate destination hash
-a, --announce ASPECTS # Announce destination
-e, --encrypt FILE     # Encrypt file
-d, --decrypt FILE     # Decrypt file
-s, --sign FILE        # Sign file
-V, --validate FILE    # Validate signature
-R, --request          # Request unknown identity from network
-t SECONDS             # Identity request timeout
-f, --force            # Force overwrite of existing files
-r, --read FILE        # Input file path
-w, --write FILE       # Output file path
-b, --base64           # Use base64 encoding
-B, --base32           # Use base32 encoding
-v, --verbose          # Increase verbosity
-q, --quiet            # Decrease verbosity
--config PATH          # Use alternative config directory
```

## rncp - File Transfer

The `rncp` utility provides secure file transfer capabilities using Reticulum's Resource API.

### Send File

```bash
# Send file to destination
rncp document.pdf c89b4da064bf66d280f0e4d8abfd9806

# Silent mode (no progress animation)
rncp --silent document.pdf c89b4da064bf66d280f0e4d8abfd9806

# Show physical layer transfer rates
rncp --phy-rates document.pdf c89b4da064bf66d280f0e4d8abfd9806

# Disable automatic compression
rncp --no-compress large.zip c89b4da064bf66d280f0e4d8abfd9806

# Set custom timeout
rncp -w 60 large_file.dat c89b4da064bf66d280f0e4d8abfd9806
```

Example output:
```
Path to <c89b4da064bf66d280f0e4d8abfd9806> requested
Establishing link with <c89b4da064bf66d280f0e4d8abfd9806>
Advertising file resource
Transferring file ⢁ 45.2% - 1.81 MB of 4.00 MB - 125.30 KBps
```

### Receive Files (Listener Mode)

```bash
# Start listener to receive files
rncp --listen

# Listen with authentication (only accept from specific identities)
rncp --listen -a c89b4da064bf66d280f0e4d8abfd9806 -a 3e12fc71692f8ec47bc5

# Listen without authentication (accept from anyone - use with caution!)
rncp --listen --no-auth

# Save received files to specific directory
rncp --listen --save ~/downloads

# Allow overwriting existing files
rncp --listen --save ~/downloads --overwrite

# Periodic announce (announce every 300 seconds)
rncp --listen -b 300

# Announce only at startup
rncp --listen -b 0
```

### Fetch File from Listener

```bash
# Fetch file from remote listener
rncp --fetch /path/to/remote/file c89b4da064bf66d280f0e4d8abfd9806

# Fetch with custom save location
rncp --fetch /path/to/remote/file c89b4da064bf66d280f0e4d8abfd9806 --save ~/downloads

# Fetch and overwrite local file if it exists
rncp --fetch /path/to/remote/file c89b4da064bf66d280f0e4d8abfd9806 --overwrite
```

### Listener with Fetch Permission

Allow authenticated clients to fetch files:

```bash
# Allow fetch from specific directory (jail)
rncp --listen --allow-fetch --jail /shared/files -a c89b4da064bf66d280f0e4d8abfd9806

# The jail restricts fetch requests to files under /shared/files
# Attempts to access files outside the jail are denied
```

### Print Listener Identity

```bash
# Display listener destination hash and exit
rncp --print-identity

# Output shows:
# Identity     : <2c0461f1c6f3a6aef3971f38e2dbd663b783c8f5>
# Listening on : <c89b4da064bf66d280f0e4d8abfd9806>
```

### Authentication Configuration

Create an allowed identities file:

```bash
# Create file at ~/.config/rncp/allowed_identities
mkdir -p ~/.config/rncp
cat > ~/.config/rncp/allowed_identities << EOF
c89b4da064bf66d280f0e4d8abfd9806
3e12fc71692f8ec47bc5
94b08f2d39ee12cf0922
EOF

# Now rncp --listen will automatically load these allowed identities
```

Alternative locations (checked in order):
1. `/etc/rncp/allowed_identities`
2. `~/.config/rncp/allowed_identities`
3. `~/.rncp/allowed_identities`

### Common Options

```bash
-l, --listen          # Listen for incoming transfers
-f, --fetch           # Fetch file from remote listener
-F, --allow-fetch     # Allow authenticated clients to fetch files
-j, --jail PATH       # Restrict fetch to specific directory
-s, --save PATH       # Save received files to directory
-O, --overwrite       # Allow overwriting existing files
-C, --no-compress     # Disable automatic compression
-a HASH               # Allow identity (can be used multiple times)
-n, --no-auth         # Accept from anyone (no authentication)
-p, --print-identity  # Print identity and listening destination
-b SECONDS            # Announce interval (0 = only at startup, -1 = never)
-w SECONDS            # Connection timeout (default: 15s)
-P, --phy-rates       # Display physical layer transfer rates
-S, --silent          # Disable transfer progress output
-v, --verbose         # Increase verbosity
-q, --quiet           # Decrease verbosity
--config PATH         # Use alternative config directory
```

## rnx - Remote Execution

The `rnx` utility enables secure remote command execution over Reticulum networks.

### Execute Remote Command

```bash
# Execute command on remote system
rnx c89b4da064bf66d280f0e4d8abfd9806 "uname -a"

# Execute with detailed output
rnx --detailed c89b4da064bf66d280f0e4d8abfd9806 "ls -la /tmp"

# Mirror remote exit code (exit with same code as remote command)
rnx -m c89b4da064bf66d280f0e4d8abfd9806 "test -f /etc/passwd"
echo $?  # Shows remote command's exit code
```

Example output:
```
Establishing link with <c89b4da064bf66d280f0e4d8abfd9806>
Sending execution request
Command delivered, awaiting result
Receiving result ⢁ 45.2%
Linux raspberrypi 5.15.84-v8+ #1613 SMP PREEMPT aarch64 GNU/Linux
```

### Execute with Options

```bash
# Limit stdout size (in bytes)
rnx --stdout 1024 c89b4da064bf66d280f0e4d8abfd9806 "dmesg"

# Limit stderr size
rnx --stderr 512 c89b4da064bf66d280f0e4d8abfd9806 "make"

# Pass data to stdin
rnx --stdin "Hello World" c89b4da064bf66d280f0e4d8abfd9806 "cat"

# Set execution timeout
rnx -w 30 c89b4da064bf66d280f0e4d8abfd9806 "long_running_task"

# Set result download timeout
rnx -W 60 c89b4da064bf66d280f0e4d8abfd9806 "generate_large_output"
```

### Detailed Output

Show comprehensive execution statistics:

```bash
rnx --detailed c89b4da064bf66d280f0e4d8abfd9806 "df -h"

# Output includes:
# --- End of remote output, rnx done ---
# Remote command execution took 0.234 seconds
# Transferred 2.45 KB in 1.8 seconds, effective rate 1.36 KBps
# Remote wrote 1234 bytes to stdout
# Remote wrote 0 bytes to stderr
```

### Interactive Mode

Enter interactive shell session with remote system:

```bash
# Interactive shell
rnx --interactive c89b4da064bf66d280f0e4d8abfd9806

# Interactive with detailed output
rnx --interactive --detailed c89b4da064bf66d280f0e4d8abfd9806

# Once connected, you get a command prompt:
> ls -la
> pwd
> cat /etc/hostname
> exit
```

Commands in interactive mode:
- Any shell command executes on remote system
- `clear` - Clear the terminal
- `exit` or `quit` - Exit interactive mode

### Listen Mode (Execute Commands from Remote)

```bash
# Start listener to accept command execution requests
rnx --listen

# Listen with authentication (only accept from specific identities)
rnx --listen -a c89b4da064bf66d280f0e4d8abfd9806 -a 3e12fc71692f8ec47bc5

# Listen without authentication (dangerous - accept from anyone)
rnx --listen --noauth

# Print listener identity and exit
rnx --print-identity

# Don't announce at startup
rnx --listen --no-announce
```

### Authentication Configuration

Create an allowed identities file:

```bash
# Create file at ~/.config/rnx/allowed_identities
mkdir -p ~/.config/rnx
cat > ~/.config/rnx/allowed_identities << EOF
c89b4da064bf66d280f0e4d8abfd9806
3e12fc71692f8ec47bc5
EOF

# Now rnx --listen will automatically load these allowed identities
```

Alternative locations (checked in order):
1. `/etc/rnx/allowed_identities`
2. `~/.config/rnx/allowed_identities`
3. `~/.rnx/allowed_identities`

### Don't Identify to Remote

Execute commands without identifying:

```bash
# Don't send local identity to remote (anonymous execution)
rnx --noid c89b4da064bf66d280f0e4d8abfd9806 "hostname"
```

### Custom Identity

Use specific identity for authentication:

```bash
# Use custom identity file
rnx -i ~/.reticulum/identities/work_id c89b4da064bf66d280f0e4d8abfd9806 "whoami"

# Listener with custom identity
rnx --listen -i ~/.reticulum/identities/server_id
```

### Common Options

```bash
-l, --listen          # Listen for incoming execution requests
-x, --interactive     # Enter interactive mode
-i PATH               # Path to identity file
-a HASH               # Accept from this identity (listener mode)
-n, --noauth          # Accept from anyone (listener mode)
-N, --noid            # Don't identify to remote
-d, --detailed        # Show detailed execution statistics
-m                    # Mirror remote command exit code
-w SECONDS            # Connection and request timeout (default: 15s)
-W SECONDS            # Maximum result download time
--stdin DATA          # Pass data to remote command's stdin
--stdout BYTES        # Maximum stdout size to return
--stderr BYTES        # Maximum stderr size to return
-p, --print-identity  # Print identity and listening destination
-b, --no-announce     # Don't announce at startup (listener mode)
-v, --verbose         # Increase verbosity
-q, --quiet           # Decrease verbosity
--config PATH         # Use alternative config directory
```

### Security Considerations

**Important:** Remote execution is a powerful capability that should be used with caution:

1. **Always use authentication**: Never use `--noauth` in production
2. **Limit allowed identities**: Maintain a strict whitelist
3. **Monitor execution logs**: Keep track of who executes what
4. **Set resource limits**: Use `--stdout` and `--stderr` limits
5. **Use timeouts**: Prevent runaway processes with `-w` and `-W`
6. **Consider command jailing**: The executed commands run with the listener's user permissions

## rnstatus - Network Status

The `rnstatus` utility displays comprehensive network status, interface statistics, and system information.

### Basic Status

```bash
# Show status of active interfaces
rnstatus

# Show all interfaces (including client connections and peers)
rnstatus --all

# Filter interfaces by name
rnstatus wlan
```

Example output:
```
 AutoInterface[wlan0]
    Status    : Up
    Mode      : Full
    Rate      : 54.0 Mbps
    Noise Fl. : -92 dBm
    Traffic   : ↑2.45 MB  125.30 KBps
                ↓5.67 MB  287.91 KBps

 TCPServerInterface[eth0:4242]
    Status    : Up
    Clients   : 3
    Mode      : Gateway
    Traffic   : ↑15.23 MB  512.45 KBps
                ↓8.91 MB  301.22 KBps

 Transport Instance <3e12fc71692f8ec47bc5> running
 Probe responder at <94b08f2d39ee12cf0922> active
 Uptime is 3 hours 24 minutes, 2 entries in link table
```

### Detailed Statistics

```bash
# Show announce statistics
rnstatus --announce-stats

# Show link table statistics
rnstatus --link-stats

# Show traffic totals
rnstatus --totals

# Combine multiple options
rnstatus --all --announce-stats --link-stats --totals
```

Example with announce stats:
```
 AutoInterface[wlan0]
    Status    : Up
    Queued    : 2 announces
    Held      : 5 announces
    Announces : 8.5/hour↑
                12.3/hour↓
    Traffic   : ↑2.45 MB  125.30 KBps
                ↓5.67 MB  287.91 KBps
```

### Sort Interfaces

```bash
# Sort by bitrate
rnstatus --sort rate

# Sort by total traffic
rnstatus --sort traffic

# Sort by received bytes
rnstatus --sort rx

# Sort by transmitted bytes
rnstatus --sort tx

# Sort by announce rate
rnstatus --sort announces

# Reverse sort order
rnstatus --sort traffic --reverse
```

Available sort keys:
- `rate` or `bitrate` - Interface bandwidth
- `traffic` - Total traffic (rx + tx)
- `rx` - Received bytes
- `tx` - Transmitted bytes
- `rxs` - Receive speed
- `txs` - Transmit speed
- `announces` or `announce` - Total announce frequency
- `arx` - Incoming announce frequency
- `atx` - Outgoing announce frequency
- `held` - Number of held announces

### Remote Status

Query status from remote Reticulum instance:

```bash
# Get status from remote instance
# -R: remote transport instance identity hash
# -i: path to management identity file
rnstatus -R 9fb6d773498fb3feda407ed8ef2c3229 -i ~/.reticulum/identities/mgmt_id

# Include link statistics
rnstatus -R 9fb6d773498fb3feda407ed8ef2c3229 -i ~/.reticulum/identities/mgmt_id --link-stats

# Set custom timeout
rnstatus -R 9fb6d773498fb3feda407ed8ef2c3229 -i ~/.reticulum/identities/mgmt_id -w 30
```

### JSON Output

Export status information in JSON format:

```bash
# Export as JSON for scripting
rnstatus --json

# Example JSON output structure:
{
  "interfaces": [
    {
      "name": "AutoInterface[wlan0]",
      "status": true,
      "mode": 0,
      "bitrate": 54000000,
      "rxb": 5945344,
      "txb": 2568192,
      "rxs": 294563,
      "txs": 128410,
      "noise_floor": -92,
      ...
    }
  ],
  "transport_id": "3e12fc71692f8ec47bc5",
  "transport_uptime": 12240.5,
  ...
}
```

### Interface Information

The status display shows various information depending on interface type:

**Physical Interfaces:**
- Status (Up/Down)
- Mode (Access Point, Point-to-Point, Roaming, Boundary, Gateway, Full)
- Rate (bandwidth)
- Noise Floor (dBm)
- Interference levels
- Airtime percentages
- Channel load

**RNode Interfaces:**
- CPU load and temperature
- Memory usage
- Battery status
- Signal quality metrics

**I2P Interfaces:**
- Tunnel state
- Connected peers
- B32 address

**Server Interfaces:**
- Connected clients
- IFAC (Interface Access Control) information

**All Interfaces:**
- Traffic statistics (bytes transferred, current speed)
- Announce queue status
- Held announces

### Common Options

```bash
-a, --all             # Show all interfaces
-A, --announce-stats  # Show announce statistics
-l, --link-stats      # Show link table statistics
-t, --totals          # Display traffic totals
-s, --sort KEY        # Sort interfaces by key
-r, --reverse         # Reverse sort order
-j, --json            # Output in JSON format
-R HASH               # Query remote transport instance
-i PATH               # Management identity for remote queries
-w SECONDS            # Timeout for remote queries (default: 15s)
-v, --verbose         # Increase verbosity
--config PATH         # Use alternative config directory
FILTER                # Only show interfaces matching filter
```

## rnsd - Reticulum Daemon

The `rnsd` utility runs Reticulum as a daemon/service, providing persistent network connectivity.

### Start Daemon

```bash
# Start daemon in foreground
rnsd

# Start as service (log to file)
rnsd --service

# Start with custom config
rnsd --config /etc/reticulum

# Verbose logging
rnsd -v

# Very verbose (debug) logging
rnsd -vv

# Quiet mode
rnsd -q
```

### Interactive Mode

Drop into Python REPL with Reticulum instance:

```bash
# Start daemon in interactive mode
rnsd --interactive

# Python REPL with access to Reticulum instance:
>>> RNS
<module 'RNS' from '/usr/lib/python3/dist-packages/RNS/__init__.py'>
>>> reticulum
<RNS.Reticulum object at 0x7f8b4c1a2e50>
>>> reticulum.get_interface_stats()
{'interfaces': [...], ...}
```

### Generate Example Configuration

```bash
# Print example configuration
rnsd --exampleconfig

# Save to file
rnsd --exampleconfig > /etc/reticulum/config.example

# Use as starting point for your config
rnsd --exampleconfig > ~/.reticulum/config
# Edit ~/.reticulum/config with your settings
```

### Systemd Service

Run `rnsd` as a systemd service:

```bash
# Create service file: /etc/systemd/system/rnsd.service
[Unit]
Description=Reticulum Network Stack Daemon
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=10
User=reticulum
ExecStart=/usr/local/bin/rnsd --service

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable rnsd
sudo systemctl start rnsd

# Check status
sudo systemctl status rnsd

# View logs
sudo journalctl -u rnsd -f
```

### Configuration Directory

By default, `rnsd` looks for configuration in:
- Linux/macOS: `~/.reticulum/`
- Windows: `%USERPROFILE%\.reticulum\`

Override with `--config`:
```bash
rnsd --config /etc/reticulum
```

### Common Options

```bash
-s, --service         # Run as service (log to file)
-i, --interactive     # Drop into interactive Python shell
-v, --verbose         # Increase verbosity (can be used multiple times)
-q, --quiet           # Decrease verbosity (can be used multiple times)
--config PATH         # Path to alternative config directory
--exampleconfig       # Print example configuration and exit
--version             # Show version and exit
```

### Logging

When run as a service, logs are written to:
- Linux/macOS: `~/.reticulum/logfile`
- Windows: `%USERPROFILE%\.reticulum\logfile`

Log levels (0-7):
- 0: Critical only
- 1: Errors
- 2: Warnings
- 3: Notices
- 4: Info (default)
- 5: Verbose
- 6: Debug
- 7: Extreme debug

Configure in `config` file:
```ini
[logging]
loglevel = 4
```

## Common Patterns and Examples

### Network Diagnostics Workflow

```bash
# 1. Check network status
rnstatus --all --announce-stats

# 2. Inspect routing table
rnpath --table

# 3. Test connectivity to destination
rnprobe -n 5 lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806

# 4. Check announce rates
rnpath --rates c89b4da064bf66d280f0e4d8abfd9806

# 5. Request path if needed
rnpath c89b4da064bf66d280f0e4d8abfd9806
```

### Secure File Transfer Setup

```bash
# Server: Start listener with authentication
rncp --listen --save ~/incoming -a c89b4da064bf66d280f0e4d8abfd9806 -b 300

# Client: Send file
rncp important.pdf c89b4da064bf66d280f0e4d8abfd9806

# Client: Fetch file from server
rncp --fetch /shared/document.pdf c89b4da064bf66d280f0e4d8abfd9806
```

### Remote System Management

```bash
# Server: Start rnx listener
rnx --listen -a c89b4da064bf66d280f0e4d8abfd9806

# Client: Execute commands
rnx c89b4da064bf66d280f0e4d8abfd9806 "df -h"
rnx c89b4da064bf66d280f0e4d8abfd9806 "systemctl status rnsd"
rnx --detailed c89b4da064bf66d280f0e4d8abfd9806 "dmesg | tail -50"

# Client: Interactive session
rnx --interactive c89b4da064bf66d280f0e4d8abfd9806
```

### Identity and Encryption Workflow

```bash
# 1. Generate identity
rnid --generate ~/.reticulum/identities/my_id

# 2. Display public key
rnid -i ~/.reticulum/identities/my_id --print-identity

# 3. Calculate destination hash
rnid -i ~/.reticulum/identities/my_id --hash myapp.service

# 4. Announce destination
rnid -i ~/.reticulum/identities/my_id --announce myapp.service

# 5. Sign a document
rnid -i ~/.reticulum/identities/my_id --sign contract.pdf

# 6. Encrypt file for recipient
rnid -i c89b4da064bf66d280f0e4d8abfd9806 --encrypt sensitive.txt

# 7. Decrypt received file
rnid -i ~/.reticulum/identities/my_id --decrypt sensitive.txt.rfe
```

### Monitoring Script

```bash
#!/bin/bash
# monitor_reticulum.sh - Monitor Reticulum network health

while true; do
    echo "=== Reticulum Status at $(date) ==="

    # Get JSON status
    STATUS=$(rnstatus --json)

    # Extract uptime
    UPTIME=$(echo $STATUS | jq -r '.transport_uptime')
    echo "Uptime: $UPTIME seconds"

    # Count active interfaces
    ACTIVE=$(echo $STATUS | jq '[.interfaces[] | select(.status == true)] | length')
    echo "Active interfaces: $ACTIVE"

    # Show traffic totals
    rnstatus --totals

    # Check paths
    echo -e "\nKnown paths:"
    rnpath --table --json | jq -r '.[] | "\(.hash) - \(.hops) hops"'

    sleep 300  # Check every 5 minutes
done
```

## Best Practices

1. **Use Authentication**: Always authenticate connections in production (rncp, rnx)
2. **Monitor Announces**: Keep track of announce rates to detect issues
3. **Regular Probing**: Use rnprobe to verify critical paths
4. **Manage Identities Securely**: Protect private keys, use separate identities for different purposes
5. **Log Analysis**: Review rnsd logs regularly for anomalies
6. **Remote Management**: Set up remote management identities for distributed networks
7. **Resource Limits**: Use timeouts and size limits in rncp and rnx
8. **Configuration Backups**: Keep backups of identities and configurations

## Integration with Applications

All utilities can be integrated into scripts and applications:

```python
import subprocess
import json

# Get network status
result = subprocess.run(['rnstatus', '--json'], capture_output=True, text=True)
status = json.loads(result.stdout)

# Check if specific interface is up
for iface in status['interfaces']:
    if 'wlan0' in iface['name']:
        if iface['status']:
            print(f"wlan0 is up, {iface['rxb']} bytes received")
        else:
            print("wlan0 is down")

# Probe destination
result = subprocess.run([
    'rnprobe', '-n', '1',
    'lxmf.delivery',
    'c89b4da064bf66d280f0e4d8abfd9806'
], capture_output=True, text=True)

if result.returncode == 0:
    print("Destination is reachable")
else:
    print("Destination is unreachable")
```

## Troubleshooting

### Connection Issues

```bash
# Check if rnsd is running
ps aux | grep rnsd

# Verify interfaces are up
rnstatus --all

# Test path discovery
rnpath --table

# Request new path
rnpath c89b4da064bf66d280f0e4d8abfd9806

# Probe with verbose output
rnprobe -v lxmf.delivery c89b4da064bf66d280f0e4d8abfd9806
```

### Authentication Failures

```bash
# Verify identity
rnid -i ~/.reticulum/identities/my_id --print-identity

# Check allowed identities list
cat ~/.config/rncp/allowed_identities

# Test without authentication (diagnostic only)
rncp --listen --no-auth  # Not for production!
```

### Performance Issues

```bash
# Check interface statistics
rnstatus --all --announce-stats

# Look for high announce rates
rnpath --rates

# Check for held announces
rnstatus --announce-stats | grep "Held"

# Drop stuck announces
rnpath --drop-announces
```

## Conclusion

Reticulum's utilities provide comprehensive network management capabilities. Master these tools to effectively operate, monitor, and troubleshoot Reticulum networks. Each utility serves a specific purpose, and together they form a complete operational toolkit for Reticulum network administration.
