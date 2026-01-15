---
name: micron-preview
description: Analyze Micron markup and describe how it will render - shows structure, formatting, links, fields, and potential issues
argument-hint: "<micron_text|file_path.mu>"
allowed-tools:
  - Read
  - Glob
---

# Micron Preview Command

Analyze Micron markup content and provide a detailed breakdown of how it will render.

## Input Handling

Accept either:
1. **File path**: Read and analyze a `.mu` file
2. **Inline markup**: Analyze Micron text provided directly

If no argument provided, ask the user to specify the Micron content to analyze.

## Analysis Output

Provide a structured analysis including:

### 1. Overview Statistics

```
Lines: [count]
Sections: [count] ([list of heading names])
Links: [count internal], [count external]
Fields: [breakdown by type]
```

### 2. Structure Breakdown

Walk through the document section by section:

```
Structure:
  L1: Page header (cache=3600, bg=#222)
  L3: Heading "Welcome" (level 1)
  L4-6: Body text (centered)
  L8: Divider
  L10: Heading "Navigation" (level 2)
  L11-14: Links (4 internal)
  ...
```

### 3. Formatting Analysis

List all formatting used:
- Colors (foreground and background hex values)
- Text styles (bold, italic, underline)
- Alignment changes

### 4. Interactive Elements

For pages with forms:
- List all field names and types
- Identify form submission links
- Note any pre-filled values

### 5. Potential Issues

Flag common problems:
- Unclosed formatting tags (`!` without closing `!`)
- Missing color resets (`F` without `f`)
- Invalid hex color values
- Fields without submission links
- Empty sections

## Example Output

```
Micron Preview Analysis
=======================

File: login.mu
Lines: 24
Cache: 0 (no caching)
Page colors: fg=#ddd, bg=#222

Sections:
  1. "Login" (level 1)
  2. (unnamed, level 2)

Links: 2
  - "Sign In" → :/page/auth.mu (submits: *)
  - "Register" → :/page/register.mu

Fields: 3
  - username: text, width=16
  - password: masked, width=16
  - remember: checkbox

Colors used:
  Foreground: #ddd (default), #888
  Background: #222 (default), #444 (field highlights)

Formatting:
  Bold: lines 3, 15
  Italic: line 20

Potential issues:
  ⚠ Line 12: Background color not reset (missing `b)
  ✓ All fields have submission link
  ✓ No unclosed formatting tags
```

## Validation Checks

Perform these checks and report results:

1. **Tag balance**: All formatting toggles closed
2. **Color resets**: Background/foreground colors properly reset
3. **Link validity**: Link syntax is correct
4. **Field completeness**: Fields have names and valid syntax
5. **Header format**: Cache and color headers in correct order
6. **Section depth**: Sections don't skip levels unexpectedly
