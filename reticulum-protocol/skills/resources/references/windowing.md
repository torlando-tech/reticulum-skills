# Resource Windowing Algorithm

Dynamic window adjustment for optimal transfer rate across varying link speeds.

## Window Size Limits

```python
WINDOW_MIN = 2           # Minimum window size
WINDOW = 4               # Initial window size
WINDOW_SLOW = 4          # Window for slow links
WINDOW_MEDIUM = 8        # Window for medium links
WINDOW_FAST = 16         # Window for fast links
WINDOW_MAX_SLOW = 10     # Maximum for very slow links
WINDOW_MAX = WINDOW_MAX_FAST = 75  # Maximum window size
```

## Rate Categories

```python
RATE_VERY_SLOW = 2 * 1000      # 2 Kbps
RATE_SLOW = 20 * 1000          # 20 Kbps
RATE_MEDIUM = 100 * 1000       # 100 Kbps
RATE_FAST = 1000 * 1000        # 1 Mbps
```

## Window Adjustment Algorithm

**On successful part delivery**:
```python
if current_window < max_window:
    current_window += 1
```

**On timeout**:
```python
current_window = max(WINDOW_MIN, current_window // 2)
```

**Rate-based limits**:
```python
if link_rate < RATE_VERY_SLOW:
    max_window = WINDOW_MAX_SLOW  # 10
elif link_rate < RATE_SLOW:
    max_window = WINDOW_SLOW  # 4
elif link_rate < RATE_MEDIUM:
    max_window = WINDOW_MEDIUM  # 8
elif link_rate < RATE_FAST:
    max_window = WINDOW_FAST  # 16
else:
    max_window = WINDOW_MAX_FAST  # 75
```

This adaptive approach ensures efficient transfer across dramatically different link speeds (from 2 Kbps LoRa to 1+ Mbps TCP).

---

**Source**: `https://github.com/markqvist/Reticulum/RNS/Resource.py`
