content = open(r'C:\Users\godav\Downloads\project\static\app.js', encoding='utf-8-sig').read()
checks = [
    ('Confirm Password', 'Confirm Password label'),
    ('sec-match', 'Match verification div'),
    ('sec-confirm', 'Confirm password input'),
    ('btn-upd-pass', 'Update Password button'),
    ('Min 6 characters', 'Min 6 chars validation'),
]
for needle, desc in checks:
    count = content.count(needle)
    status = 'OK' if count > 0 else 'MISSING'
    print(f'  [{status}] {desc}: found {count} time(s)')

if 'Verify New Password' in content:
    print('  [BAD] Verify New Password still present!')
else:
    print('  [OK] Verify New Password removed')

# Check onclick on toggleSw
toggle_idx = content.find('function toggleSw')
toggle_chunk = content[toggle_idx:toggle_idx+500]
if 'onclick="var p=this.parentElement' in toggle_chunk:
    print('  [OK] toggleSw has proper onclick handler')
else:
    print('  [BAD] toggleSw missing onclick handler')

# Check eye toggles in genSecurity
sec_idx = content.find('function genSecurity()')
sec_chunk = content[sec_idx:sec_idx+3000]
if 'onclick="var e=document.getElementById' in sec_chunk:
    print('  [OK] Security eye toggles have onclick')
else:
    print('  [BAD] Security eye toggles broken')
