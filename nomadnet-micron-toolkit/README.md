# NomadNet Micron Toolkit

Development toolkit for NomadNet pages and Micron markup language. Provides syntax reference, page creation commands, and development assistance for the Reticulum network ecosystem.

## Features

### Skills

- **micron-syntax**: Complete Micron markup language specification including formatting, colors, links, fields, and parser implementation guidance
- **nomadnet-pages**: NomadNet page development patterns including static pages, dynamic pages, file hosting, and authentication

### Commands

- `/nomadnet-micron-toolkit:micron-preview` - Analyze Micron markup and describe rendering
- `/nomadnet-micron-toolkit:nomadnet-page-create` - Scaffold new NomadNet pages from templates

### Agent

- **nomadnet-developer** - Proactive development assistant that triggers when editing `.mu` files, working on Micron parsers, or asking about NomadNet page development

## Installation

### As Claude Code Plugin

```bash
# Clone and use directly
claude --plugin-dir /path/to/nomadnet-micron-toolkit
```

Or copy to your project's `.claude-plugin/` directory.

### From reticulum-skills Repository

This plugin is part of the public reticulum-skills collection at:
```
public/reticulum-skills/nomadnet-micron-toolkit/
```

## Usage

### Ask About Micron Syntax

```
How do I format bold text in Micron?
What's the syntax for colored backgrounds?
How do form fields work in NomadNet pages?
```

### Create Pages

```
/nomadnet-micron-toolkit:nomadnet-page-create form login
/nomadnet-micron-toolkit:nomadnet-page-create dynamic status
```

### Analyze Markup

```
/nomadnet-micron-toolkit:micron-preview mypage.mu
```

### Get Help Implementing Parsers

```
I'm porting the Micron parser to Kotlin
How does color expansion work in MicronParser.py?
```

## Micron Quick Reference

| Category | Syntax | Description |
|----------|--------|-------------|
| Bold | `` `! `` | Toggle bold |
| Italic | `` `* `` | Toggle italic |
| Underline | `` `_ `` | Toggle underline |
| Center | `` `c `` | Center alignment |
| Color | `` `FXXX `` | Foreground (3-digit hex) |
| Background | `` `BXXX `` | Background (3-digit hex) |
| Heading | `>` | Section heading |
| Link | `` `[label`dest] `` | Hyperlink |
| Field | `` `<name`value> `` | Input field |

See `skills/micron-syntax/references/syntax-spec.md` for complete specification.

## Reference Implementations

This toolkit references these Micron parser implementations:

- **Python (NomadNetwork)**: `nomadnet/ui/textui/MicronParser.py`
- **JavaScript (meshchat)**: `src/frontend/js/MicronParser.js`
- **JavaScript (rBrowser)**: `script/micron-parser_original.js`

## License

MIT License - See repository root for details.
