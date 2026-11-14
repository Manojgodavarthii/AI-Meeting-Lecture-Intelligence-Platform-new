import sys
sys.stdout.reconfigure(encoding='latin-1')

with open(r'C:\Users\godav\Downloads\project\static\app.js', 'r', encoding='latin-1') as f:
    lines = f.readlines()

line = lines[15079]

# Second renderEmployee
idx = line.find("renderEmployee", 1600)
print(f"Second at {idx}")
ctx = line[max(0,idx-50):min(len(line),idx+80)]
print(f"Context: {ctx}")

print()

# Count onclick occurrences
count = 0
start = 0
while True:
    pos = line.find("onclick", start)
    if pos < 0:
        break
    count += 1
    ctx = line[pos:min(len(line),pos+40)]
    print(f"onclick #{count} at {pos}: {repr(ctx)}")
    start = pos + 1

print(f"\nTotal onclick: {count}")

# Also count onmouse
count2 = 0
start2 = 0
while True:
    pos = line.find("onmouse", start2)
    if pos < 0:
        break
    count2 += 1
    ctx = line[pos:min(len(line),pos+40)]
    print(f"onmouse #{count2} at {pos}: {repr(ctx)}")
    start2 = pos + 1

print(f"\nTotal onmouse: {count2}")
