import re, sys

content = open(r'C:\Users\godav\Downloads\project\static\app.js', encoding='utf-8-sig').read()
lines = content.split('\n')
issues = []

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped:
        continue
    for attr in ['onclick=', 'onmouseenter=', 'onmouseleave=', 'onchange=', 'onfocus=', 'onblur=']:
        idx = 0
        while True:
            pos = stripped.find(attr, idx)
            if pos == -1:
                break
            after = stripped[pos + len(attr):]
            if after.startswith('"'):
                close = after.find('"', 1)
                if close == -1:
                    issues.append(f'Line {i}: Unmatched double quote after {attr}')
            elif after.startswith("'"):
                close = after.find("'", 1)
                if close == -1:
                    issues.append(f'Line {i}: Unmatched single quote after {attr}')
            idx = pos + 1

    # Check backtick template: stray backslash-quote (backslash before ' or " in template text)
    if '`' in stripped:
        in_bt = False
        in_expr = False
        depth = 0
        j = 0
        while j < len(stripped):
            c = stripped[j]
            if c == '`':
                in_bt = not in_bt
                if not in_bt:
                    in_expr = False
            elif in_bt and c == '$' and j + 1 < len(stripped) and stripped[j+1] == '{':
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
            elif in_bt and not in_expr and c == '\\' and j + 1 < len(stripped) and stripped[j+1] in ("'", '"'):
                issues.append(f'Line {i}: Stray backslash-quote in template text at col {j+1}: {stripped[j:j+4]}')
            j += 1

    # Check single-quoted JS string with unescaped content ' chars
    # Look for cells+='<div...' patterns
    if "cells+='" in stripped or "cells +='" in stripped:
        sq_count = stripped.count("'")
        if sq_count % 2 != 0:
            issues.append(f'Line {i}: ODD single quote count ({sq_count}) in cells+= pattern')

if issues:
    for issue in issues:
        print(issue)
    print(f'\n{len(issues)} issue(s) found')
else:
    print('No obvious syntax issues found')
