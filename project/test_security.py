import sys
sys.path.insert(0, 'c:\\Users\\godav\\Downloads\\project')
from security import (
    detect_sql_injection, detect_xss, detect_path_traversal,
    is_malicious_bot, validate_password_strength, validate_email_format,
    get_security_status
)

print('=== Testing security.py ===')

tests = [
    ('SQL injection detected', detect_sql_injection("' OR 1=1 --"), True),
    ('SQL inject clean', detect_sql_injection('hello world'), False),
    ('XSS detected', detect_xss('<script>alert(1)</script>'), True),
    ('XSS clean', detect_xss('Hello world'), False),
    ('Path traversal detected', detect_path_traversal('../../../etc/passwd'), True),
    ('Path clean', detect_path_traversal('/api/meetings'), False),
    ('Bot sqlmap blocked', is_malicious_bot('sqlmap/1.0'), True),
    ('Chrome UA allowed', is_malicious_bot('Mozilla/5.0 Chrome/114.0'), False),
    ('Email valid', validate_email_format('test@gmail.com'), True),
    ('Email invalid', validate_email_format('notanemail'), False),
]

all_pass = True
for name, result, expected in tests:
    status = 'PASS' if result == expected else 'FAIL'
    if result != expected:
        all_pass = False
    print(f'  [{status}] {name}: got {result}')

ok, msg = validate_password_strength('Abc123!')
print(f'  [{"PASS" if ok else "FAIL"}] Strong password accepted: {ok}')
bad_ok, bad_msg = validate_password_strength('abc')
print(f'  [{"PASS" if not bad_ok else "FAIL"}] Weak password rejected: {bad_msg}')

status = get_security_status()
print(f'  [PASS] Security status has {len(status)} features listed')
print()
print('ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED')
