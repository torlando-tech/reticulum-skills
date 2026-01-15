# Destination Naming Rules

Hierarchical dotted naming convention for Reticulum destinations.

## Format

```
app_name.aspect1.aspect2.aspect3...
```

## Rules

1. **App name required**: First component, no dots allowed within it
2. **Aspects optional**: Zero or more additional components
3. **Dot separator**: Components separated by single dots
4. **Case sensitive**: "MyApp.Service" ≠ "myapp.service"
5. **UTF-8 encoding**: Unicode characters allowed
6. **No trailing dots**: "app.service." is invalid

## Valid Examples

```
"fileserver"
"fileserver.files"
"chat.group.engineering"
"sensor.temperature.outdoor.deck"
"lxmf.delivery"
"nomadnetwork.node.page"
```

## Invalid Examples

```
"my.app.service"      # Dot in app name
".service"            # No app name
"app..service"        # Double dot
"app.service."        # Trailing dot
""                    # Empty string
```

## Name Uniqueness

For SINGLE destinations, uniqueness guaranteed by combining:
- Name hash (from full name string)
- Identity hash (from public key)

Two nodes can use same name but will have different destination hashes due to different identities.

## Hierarchical Organization

Naming encourages logical organization:

```
myapp.api.v1
myapp.api.v2
myapp.admin
myapp.metrics
```

While hierarchy implied by naming, protocol treats full name as atomic - no automatic routing by prefix.

---

**Source**: `https://github.com/markqvist/Reticulum/RNS/Destination.py`
