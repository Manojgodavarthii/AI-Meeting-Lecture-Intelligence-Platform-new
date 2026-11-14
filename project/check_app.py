with open(r'c:\Users\godav\Downloads\project\templates\index.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Check auth-portal HTML tag
search = 'auth-portal-container'
idx = content.find(search)
start = max(0, idx-5)
end = idx + 120
print('Auth portal tag:')
print(repr(content[start:end]))

# Check styles.css link version
import re
css_matches = re.findall(r'href="/static/[^"]+"', content)
print('\nCSS links:', css_matches)
