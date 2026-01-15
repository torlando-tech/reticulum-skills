# Keep-Alive Mechanism

Link monitoring and timeout detection through keep-alive packets.

## Purpose

Keep-alive packets serve to:
1. Detect link failure (broken connection, crashed peer)
2. Prevent NAT/firewall timeout
3. Maintain routing table entries in transport nodes
4. Measure round-trip time (RTT)

## Keep-Alive Interval

```python
KEEPALIVE = 360  # seconds (6 minutes)
```

When link is idle (no data packets) for KEEPALIVE seconds, a keep-alive packet is automatically sent.

## Keep-Alive Packet Structure

```
[HEADER 19B][ENCRYPTED_DATA ~16B]
Total: ~35 bytes
```

**Context**: 0xFA (KEEPALIVE)
**Data**: Minimal encrypted payload (just enough to validate encryption)

## Bandwidth Cost Calculation

```python
packet_size = 35 bytes
interval = 360 seconds

bits_per_second = (35 × 8) / 360
                = 280 / 360
                = 0.78 bits/second
```

With protocol optimizations: **~0.44 bits/second**

This extremely low bandwidth cost allows links to remain active on even the slowest connections (Reticulum operates down to 5 bps).

## Link States and Keep-Alive

### ACTIVE State

Link is healthy and exchanging traffic:
- Data packets reset keep-alive timer
- If no packets for KEEPALIVE seconds, send keep-alive
- Receiving any packet (data or keep-alive) resets timeout

### STALE State

```python
STALE_TIME = 720  # seconds (2 × KEEPALIVE = 12 minutes)
```

If no packets received for STALE_TIME:
1. Link transitions to STALE state
2. **Final keep-alive packet sent**
3. Watchdog timer starts for timeout detection

This is the last chance to confirm link is alive.

### Timeout Detection

After sending final keep-alive in STALE state:

```python
timeout = (RTT × KEEPALIVE_TIMEOUT_FACTOR) + STALE_GRACE
timeout = (RTT × 4) + 5 seconds
```

If no response within timeout period:
- Link declared dead
- State → CLOSED
- Reason: TIMEOUT (0x01)
- Resources cleaned up
- Callbacks notified

## Watchdog Thread

Links run a watchdog thread that monitors:

```python
def watchdog():
    while link.active:
        current_time = time.time()

        # Check if we should send keep-alive
        if current_time - last_outbound > KEEPALIVE:
            send_keepalive()

        # Check if link is stale
        if current_time - last_inbound > STALE_TIME:
            if link.state == ACTIVE:
                link.state = STALE
                send_keepalive()  # Final keep-alive
                stale_timeout = (rtt × 4) + 5

        # Check if link timed out
        if link.state == STALE:
            if current_time - last_inbound > stale_timeout:
                link.close(reason=TIMEOUT)

        sleep(min(WATCHDOG_MAX_SLEEP, check_interval))
```

## RTT Measurement

Round-trip time measured during link establishment and updated periodically:

### Initial RTT Measurement

After link proof received, initiator sends RTT packet:
- Context: 0xFE (LRRTT - Link Request RTT)
- Contains: Timestamp
- Destination echoes packet back
- RTT = time_received - time_sent

### Ongoing RTT Updates

RTT updated with each acknowledged packet:
```python
# Exponential moving average
new_rtt = (old_rtt × 0.7) + (measured_rtt × 0.3)
```

Smooth RTT value used for timeout calculations.

## Timeout Calculation Examples

### Fast Local Link

```
RTT = 10ms = 0.01 seconds
timeout = (0.01 × 4) + 5 = 5.04 seconds
```

Link declared dead if no response to final keep-alive within 5.04 seconds.

### Slow Multi-Hop Link

```
RTT = 2 seconds
timeout = (2 × 4) + 5 = 13 seconds
```

Link declared dead if no response within 13 seconds.

### Very Slow Link (LoRa, HF radio)

```
RTT = 30 seconds
timeout = (30 × 4) + 5 = 125 seconds
```

Link declared dead if no response within 125 seconds (~2 minutes).

Adaptive timeout ensures reliability across vastly different link speeds.

## Grace Period

```python
STALE_GRACE = 5  # seconds
```

Extra 5 seconds added to RTT-based timeout provides margin for:
- Processing delays
- Queueing in transport nodes
- Temporary network congestion
- Clock skew

Prevents premature timeout on marginal links.

## Keep-Alive Strategy

### Outbound Logic

```python
if time.time() - link.last_outbound >= KEEPALIVE:
    if link.state == ACTIVE:
        link.send_keepalive()
        link.last_outbound = time.time()
```

Only sent when link is idle. Data packets reset timer.

### Inbound Logic

```python
def receive_packet(packet):
    link.last_inbound = time.time()

    if link.state == STALE:
        # Link was stale but is now alive again
        link.state = ACTIVE
        link.stale_timeout = None

    # Process packet...
```

Any received packet (data or keep-alive) resets inbound timer and revives stale link.

## Link Closure

Links can close for several reasons:

### Timeout (0x01)

```python
TIMEOUT = 0x01
```

No keep-alive response after entering STALE state. Indicates:
- Remote peer crashed
- Network path broken
- Remote peer overwhelmed/unresponsive

### Initiator Closed (0x02)

```python
INITIATOR_CLOSED = 0x02
```

Link initiator explicitly called `link.close()`. Clean shutdown.

### Destination Closed (0x03)

```python
DESTINATION_CLOSED = 0x03
```

Link destination explicitly closed the link. Clean shutdown.

## Close Packet

When explicitly closing link, LINKCLOSE packet sent:
- Context: 0xFC (LINKCLOSE)
- Informs peer of intentional closure
- Allows clean resource cleanup on both ends

## Traffic-Based Keep-Alive Optimization

Keep-alive only sent when needed:

```python
# If data traffic is frequent
if time.time() - last_outbound < KEEPALIVE:
    # No keep-alive needed, data packets keep link alive
    pass
else:
    # Link idle, send keep-alive
    send_keepalive()
```

Active links with continuous traffic never send keep-alive packets, minimizing overhead.

## Implementation Notes

### Minimum Keep-Alive Interval

```python
KEEPALIVE_MIN = 5  # seconds
```

Prevents excessive keep-alive on very fast links. Even if RTT is milliseconds, minimum interval is 5 seconds.

### Maximum Keep-Alive Interval

```python
KEEPALIVE_MAX = 360  # seconds (6 minutes)
```

Default and maximum interval. Cannot be extended further.

### Asymmetric Links

Keep-alive handles asymmetric links (different uplink/downlink speeds):
- Timeout based on measured RTT
- Adapts to actual observed latency
- Not dependent on bandwidth

## Watchdog Sleep Interval

```python
WATCHDOG_MAX_SLEEP = 5  # seconds
```

Watchdog thread wakes at least every 5 seconds to check timers, ensuring timely timeout detection.

## Multi-Hop Considerations

Keep-alive works across arbitrary hop counts:
- Transport nodes forward keep-alive like any packet
- RTT automatically accounts for multi-hop latency
- Timeout adapts to measured end-to-end RTT

No special handling needed for multi-hop links.

---

**Source References:**
- `https://github.com/markqvist/Reticulum/RNS/Link.py` (watchdog method, keep-alive logic)
