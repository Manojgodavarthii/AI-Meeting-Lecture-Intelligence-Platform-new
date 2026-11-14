import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r'c:\Users\godav\Downloads\project\static\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print(f'Total lines: {len(lines)}')

# Find ALL instances of onclick="switchScreen('screen-..." that are inside single-quoted JS strings
# A single-quoted JS string context means: BEFORE this onclick, there's an ODD number of unescaped '
# 
# We look for: onclick="switchScreen('screen-
# (NOT onclick="switchScreen(\' which would be properly escaped)

bad_lines = []
for i, line in enumerate(lines, 1):
    # Check for the specific broken pattern
    pattern = "onclick=\"switchScreen('"
    idx = 0
    while True:
        pos = line.find(pattern, idx)
        if pos < 0:
            break
        # Count unescaped ' before this position
        before = line[:pos]
        sq = 0
        j = 0
        while j < len(before):
            if j+1 < len(before) and before[j] == '\\':
                j += 2; continue
            if before[j] == "'":
                sq += 1
            j += 1
        if sq % 2 == 1:  # Odd = inside single-quoted string = BROKEN
            snippet = line[pos:pos+80]
            bad_lines.append((i, pos+1, snippet, line[:250]))
        idx = pos + 1

print(f"\nActually broken onclick patterns (inside single-quoted strings): {len(bad_lines)}")
for ln, col, snippet, ctx in bad_lines[:20]:
    print(f"\n  Line {ln}, col {col}:")
    print(f"  Snippet: {repr(snippet)}")
    print(f"  Context: {ctx[:200]}")
