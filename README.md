# Reticulum Skills

Claude Code plugins for [Reticulum Network Stack](https://reticulum.network/) and related protocol development.

## Available Plugins

| Plugin | Description |
|--------|-------------|
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
