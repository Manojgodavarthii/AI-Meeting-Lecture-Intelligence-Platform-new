import sys
sys.stdout.reconfigure(encoding='latin-1')

with open(r'C:\Users\godav\Downloads\project\static\app.js', 'rb') as f:
    content = f.read()

idx = content.find(b"font-family:'Inter'")
if idx >= 0:
    print("FOUND unescaped Inter quote at byte", idx)
    print("Context:", content[idx-10:idx+40])
else:
    idx2 = content.find(b"font-family:\\'Inter\\'")
    if idx2 >= 0:
        print("FOUND escaped Inter quote at byte", idx2)
    else:
        print("Inter quote not found with those patterns")
        # Search for 'Inter' in the line
        line_start = 15106  # 0-indexed
        lines = content.split(b'\n')
        line = lines[line_start]
        pos = line.find(b"'Inter'")
        if pos >= 0:
            print("Found 'Inter' at position", pos, "context:", line[max(0,pos-20):pos+20])
        pos2 = line.find(b"\\'Inter\\'")
        if pos2 >= 0:
            print("Found \\'Inter\\' at position", pos2, "context:", line[max(0,pos2-20):pos2+20])
