path = r'C:\Users\godav\Downloads\project\static\app.js'
content = open(path, encoding='utf-8-sig').read()

old_start = content.find('function genSecurity(){return _proCard("lock","#ef4444","Security","Password and authentication"')
if old_start == -1:
    print("ERROR: Could not find genSecurity function start")
    exit(1)

next_func = content.find('\n  function genSkills()', old_start)
if next_func == -1:
    next_func = content.find('function genSkills()', old_start)
if next_func == -1:
    print("ERROR: Could not find genSkills after genSecurity")
    exit(1)

old_func = content[old_start:next_func].rstrip()
print(f"Found genSecurity: length={len(old_func)}")

new_func = (
'function genSecurity(){return _proCard("lock","#ef4444","Security","Password and authentication",'
"'<div style=\"display:flex;flex-direction:column;gap:10px;\">'+"
"    '<div><label style=\"color:#6b7a8a;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.4px;display:block;margin-bottom:4px;\">Current Password</label><div style=\"position:relative;\"><input type=\"password\" id=\"sec-old\" placeholder=\"Enter current password\" style=\"width:100%;background:#0f172a;border:1px solid rgba(129,140,248,0.35);color:#f3f4f6;padding:8px 12px;border-radius:6px;font-size:0.8rem;outline:none;padding-right:35px;\" onfocus=\"this.style.borderColor=\\\\'#818cf8\\\\';this.style.boxShadow=\\\\'0 0 0 3px rgba(99,102,241,0.2)\\\\'\" onblur=\"this.style.borderColor=\\\\'rgba(129,140,248,0.35)\\\\';this.style.boxShadow=\\\\'none\\\\'\"><button type=\"button\" style=\"position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:#6b7a8a;cursor:pointer;font-size:0.85rem;\" onclick=\"var e=document.getElementById(\\\\'sec-old\\\\');e.type=e.type===\\\\'password\\\\'?\\\\'text\\\\':\\\\'password\\\\';this.querySelector(\\\\'i\\\\').className=\\\\'fa-solid fa-\\\\'+(e.type===\\\\'password\\\\'?\\\\'eye\\\\':\\\\'eye-slash\\\\')\"><i class=\"fa-solid fa-eye\"></i></button></div></div>'+"
)

# This is getting complex with escaping. Let me use a simpler approach.
# Read the working copy's genSecurity and modify it.

path2 = r'C:\Users\godav\Downloads\project - Copy\static\app.js'
content2 = open(path2, encoding='utf-8-sig').read()

# Find genSecurity in the copy
copy_start = content2.find('function genSecurity()')
copy_end = content2.find('\n  function genSkills()', copy_start)
if copy_end == -1:
    copy_end = content2.find('function genSkills()', copy_start)

copy_func = content2[copy_start:copy_end].rstrip()
print(f"Copy genSecurity: length={len(copy_func)}")

# Replace "Verify New Password" with "Confirm Password" and update placeholder
copy_func = copy_func.replace("Verify New Password", "Confirm Password")
copy_func = copy_func.replace('placeholder="Re-enter new password"', 'placeholder="Re-enter new password"')

# Replace the card() wrapper with _proCard() wrapper
# Copy uses: card("lock","#ef4444","Security","Password and authentication", ... + card("fa-shield-halved",...))
# We need: _proCard("lock","#ef4444","Security","Password and authentication", ... + _proField("Enable 2FA",...))
# The copy has: return card(...)+card("fa-shield-halved","#10b981","Two-Factor Authentication","Extra security",fieldRow("Enable 2FA",toggleSw(0,"sec-2fa")));
# We need: return _proCard(...)+ _proField("Enable 2FA",toggleSw(0,"sec-2fa"));

new_func = copy_func

# Replace card( with _proCard(
new_func = new_func.replace('return card("lock","#ef4444","Security","Password and authentication",', 'return _proCard("lock","#ef4444","Security","Password and authentication",')

# Replace the second card + fieldRow with _proField
old_2fa = 'card("fa-shield-halved","#10b981","Two-Factor Authentication","Extra security",fieldRow("Enable 2FA",toggleSw(0,"sec-2fa")))'
new_2fa = '_proField("Enable 2FA",toggleSw(0,"sec-2fa"))'
new_func = new_func.replace(old_2fa, new_2fa)

print(f"New genSecurity: length={len(new_func)}")
print(f"First 100: {new_func[:100]}")
print(f"Last 100: {new_func[-100:]}")

# Replace in main content
new_content = content[:old_start] + new_func + content[next_func:]
open(path, 'w', encoding='utf-8').write(new_content)
print("SUCCESS: genSecurity replaced")
