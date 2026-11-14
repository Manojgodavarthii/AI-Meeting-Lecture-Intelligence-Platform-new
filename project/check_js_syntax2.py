import re

content = open(r'C:\Users\godav\Downloads\project\static\app.js', encoding='utf-8-sig').read()
lines = content.split('\n')

# Check for buttons with switchScreen but missing onclick in backtick templates
for i, line in enumerate(lines, 1):
    if '`' not in line:
        continue
    # Find btn elements that have switchScreen but no onclick
    matches = re.findall(r'<button[^>]*switchScreen[^>]*>', line)
    for m in matches:
        if 'onclick=' not in m:
            print(f'Line {i}: Missing onclick= in button: {m[:120]}')

# Check for other stray backslash-quotes in template literals (outside ${})
issues_found = 0
for i, line in enumerate(lines, 1):
    if '`' not in line:
        continue
    in_bt = False
    in_expr = False
    depth = 0
    j = 0
    while j < len(line):
        c = line[j]
        if c == '`':
            in_bt = not in_bt
            if not in_bt:
                in_expr = False
        elif in_bt and c == '$' and j + 1 < len(line) and line[j+1] == '{':
            in_expr = True
            depth += 1
            j += 1
        elif in_bt and in_expr and c == '{':
            depth += 1
        elif in_bt and in_expr and c == '}':
            depth -= 1
            if depth <= 0:
                in_expr = False
                depth = 0
        elif in_bt and not in_expr and c == '\\' and j + 1 < len(line) and line[j+1] in ("'", '"'):
            # But NOT inside an HTML attribute value that's part of inline JS
            # Check if this is inside onclick="..." or similar
            context_start = max(0, j - 200)
            context = line[context_start:j]
            # If there's an odd number of onclick= before this, it's inside the handler
            onclick_count = context.count('onclick="')
            if onclick_count > 0:
                # We're likely inside an onclick handler - backslash-quote is OK here
                j += 1
                continue
            # Also check for onmouseenter, onmouseleave, etc
            handler_count = sum(context.count(h + '="') for h in ['onmouseenter', 'onmouseleave', 'onchange', 'onfocus', 'onblur'])
            if handler_count > 0:
                j += 1
                continue
            print(f'Line {i}: Stray backslash-quote in template text at col {j+1}: {line[j:j+4]}')
            issues_found += 1
        j += 1

if issues_found == 0:
    print('No real issues found. All clean!')
else:
    print(f'{issues_found} issue(s) remaining')
