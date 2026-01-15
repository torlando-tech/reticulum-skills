---
name: nomadnet-page-create
description: Scaffold a new NomadNet page with the appropriate template based on page type
argument-hint: "<type> <name> [--path <path>]"
allowed-tools:
  - Read
  - Write
  - Bash
---

# NomadNet Page Create Command

Create a new NomadNet page (.mu file) with appropriate scaffolding based on the page type.

## Arguments

- **type**: Page template type (static, form, menu, dynamic, status)
- **name**: Page filename (without .mu extension)
- **--path**: Optional output directory (default: current directory)

If arguments not provided, ask the user interactively.

## Page Types

### static

Basic informational page with navigation structure:

```micron
#!c=3600
#!fg=ddd
#!bg=222

>Page Title

`cPage description or subtitle
`a

-

>>Section 1

Content for section 1.

>>Section 2

Content for section 2.

-

`[Back to Home`:/page/index.mu]
```

### form

Page with input fields and submission:

```micron
#!c=0

>Form Title

`cForm description
`a

-

Field 1: `B444`<16|field1`>`b

Field 2: `B444`<16|field2`>`b

Password: `B444`<!16|password`>`b

-

`[Submit`:/page/handler.mu`*]

`[Cancel`:/page/index.mu]
```

### menu

Navigation menu page:

```micron
#!c=1800

>Navigation

`cSelect a destination
`a

-

>>Main

`F0af`_`[Home`:/page/index.mu]`_`f
`F0af`_`[About`:/page/about.mu]`_`f
`F0af`_`[Contact`:/page/contact.mu]`_`f

>>Resources

`F0af`_`[Files`:/page/files.mu]`_`f
`F0af`_`[Documentation`:/page/docs/index.mu]`_`f

-

`c`F888Node Name`f
```

### dynamic

Executable Python page template:

```python
#!/usr/bin/env python3
import os
import time

# Page configuration
print("#!c=0")  # No caching for dynamic content

# Page content
print(">Dynamic Page")
print("")
print(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("")

# Access form data from environment variables
# field_<name> for form fields
# var_<name> for request link variables
field_value = os.environ.get('field_example', '')
var_value = os.environ.get('var_action', 'default')

if field_value:
    print(f"Received: {field_value}")
else:
    print(">>Input")
    print("Enter value: `B444`<example`>`b")
    print("")
    print("`[Submit`:/page/PAGE_NAME.mu`*]")
```

### status

System status page (dynamic):

```python
#!/usr/bin/env python3
import os
import time
import subprocess

print("#!c=0")
print(">System Status")
print("")
print(f"`cLast updated: {time.strftime('%H:%M:%S')}`a")
print("")

print(">>Node Information")
try:
    hostname = subprocess.check_output(['hostname']).decode().strip()
    print(f"Hostname: `!{hostname}`!")
except:
    print("Hostname: Unknown")

try:
    uptime = subprocess.check_output(['uptime', '-p']).decode().strip()
    print(f"Uptime: {uptime}")
except:
    pass

print("")
print(">>Quick Actions")
print("`[Refresh`:/page/PAGE_NAME.mu]")
print("`[Home`:/page/index.mu]")
```

## Creation Process

1. **Validate type**: Ensure type is one of: static, form, menu, dynamic, status
2. **Generate filename**: Use provided name with `.mu` extension
3. **Apply template**: Use appropriate template for the type
4. **Replace placeholders**: Substitute PAGE_NAME with actual name
5. **Write file**: Create the .mu file at specified path
6. **Set permissions**: For dynamic/status, make executable (`chmod +x`)
7. **Report success**: Show created file path and next steps

## Output

After creating the page, provide:

```
Created: <path>/name.mu
Type: <type>
Cache: <cache setting>

Next steps:
1. Copy to ~/.nomadnetwork/storage/pages/
2. Edit content as needed
3. [For dynamic] Ensure execute permissions: chmod +x name.mu
4. Test by browsing to :/page/name.mu
```

## Interactive Mode

If arguments are missing, prompt the user:

1. "What type of page? (static, form, menu, dynamic, status)"
2. "Page name (without .mu extension)?"
3. "Output directory? (default: current)"

## Customization Options

After creating the basic template, offer to customize:

- Page title
- Cache duration
- Color scheme
- Number of fields (for form)
- Menu items (for menu)
