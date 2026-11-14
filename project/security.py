import os
import time
import hashlib
import base64
import re
import logging
import uuid
import hmac
from functools import wraps
from flask import request, jsonify, session, g
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash

# ─── SECURITY LOGGER ──────────────────────────────────────────────────────────
security_logger = logging.getLogger("echoaction.security")
security_logger.setLevel(logging.INFO)
_sh = logging.StreamHandler()
_sh.setFormatter(logging.Formatter("[SECURITY] %(asctime)s %(levelname)s %(message)s"))
security_logger.addHandler(_sh)

LOG_SECURITY_EVENTS = True

def _audit(event, detail="", level="info"):
    if not LOG_SECURITY_EVENTS:
        return
    try:
        ip = request.remote_addr if request else "unknown"
    except Exception:
        ip = "unknown"
    log = {"event": event, "detail": detail, "ip": ip, "time": time.time()}
    msg = f"{event} | {detail} | {log['ip']}"
    if level == "warn":
        security_logger.warning(msg)
    elif level == "error":
        security_logger.error(msg)
    else:
        security_logger.info(msg)

# ─── CONFIGURATION (toggle each independently) ─────────────────────────────────

SECURITY_HEADERS_ENABLED      = True
RATE_LIMIT_ENABLED            = True
RATE_LIMIT_REQUESTS           = 60
RATE_LIMIT_WINDOW             = 60
PROFILE_ENCRYPTION_ENABLED    = True
PASSWORD_HASHING_ENABLED      = True
INPUT_SANITIZATION_ENABLED    = True
CSRF_PROTECTION_ENABLED       = True
LOGIN_RATE_LIMIT_ENABLED      = True
REQUEST_SIZE_LIMIT_ENABLED    = True
REQUEST_SIZE_MAX_BYTES        = 10 * 1024 * 1024   # 10 MB
FIREWALL_ENABLED              = True
BOT_BLOCKING_ENABLED          = True
SQL_INJECTION_DETECTION       = True
XSS_DETECTION                 = True
PATH_TRAVERSAL_DETECTION      = True
IP_BLACKLIST_ENABLED          = True

ENCRYPTED_PROFILE_FIELDS = ['phone', 'bio', 'linkedin', 'company']

# ─── IP BLACKLIST ──────────────────────────────────────────────────────────────
# Permanently banned IPs. Add malicious IPs here at runtime via block_ip().
_ip_blacklist = set()

def block_ip(ip):
    """Permanently blacklist an IP address."""
    _ip_blacklist.add(ip)
    _audit("ip_blacklisted", f"IP {ip} added to blacklist", "warn")

def unblock_ip(ip):
    """Remove an IP from the blacklist."""
    _ip_blacklist.discard(ip)

def get_blacklisted_ips():
    return list(_ip_blacklist)

def is_ip_blacklisted(ip):
    return ip in _ip_blacklist

# ─── FIREWALL PATTERNS ─────────────────────────────────────────────────────────

# SQL Injection patterns
_SQL_INJECTION_PATTERNS = re.compile(
    r"(\b(union|select|insert|update|delete|drop|create|alter|truncate|exec|execute|cast|convert|declare)\b"
    r"|\bor\s+1\s*=\s*1\b|\band\s+1\s*=\s*1\b"
    r"|'--|\";--|\b(sleep|benchmark|waitfor|delay)\s*\("
    r"|\bxp_cmdshell\b|\bsysobjects\b|\binformation_schema\b"
    r"|\/\*.*?\*\/|0x[0-9a-f]{4,}"
    r"|\bload_file\s*\(|\binto\s+outfile\b|\binto\s+dumpfile\b)",
    re.IGNORECASE
)

# XSS patterns
_XSS_PATTERNS = re.compile(
    r"<\s*script[\s>]|<\s*/\s*script\s*>"
    r"|javascript\s*:"
    r"|on(error|load|click|mouseover|focus|blur|change|submit|keydown|keyup|keypress)\s*="
    r"|<\s*iframe[\s>]|<\s*object[\s>]|<\s*embed[\s>]"
    r"|<\s*svg[\s>].*?on\w+=|expression\s*\("
    r"|vbscript\s*:|data\s*:\s*text/html",
    re.IGNORECASE
)

# Path traversal patterns
_PATH_TRAVERSAL_PATTERNS = re.compile(
    r"\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.\.%2f"
    r"|%252e%252e|/etc/passwd|/etc/shadow|/proc/self"
    r"|\\windows\\system32|cmd\.exe|powershell\.exe",
    re.IGNORECASE
)

# Malicious bot User-Agents
_MALICIOUS_UA_PATTERNS = re.compile(
    r"sqlmap|nikto|nmap|masscan|dirbuster|gobuster|wfuzz|hydra"
    r"|metasploit|acunetix|nessus|openvas|burpsuite|w3af"
    r"|havij|pangolin|jbrofuzz|webscarab|paros|skipfish"
    r"|zgrab|nuclei|subfinder|ffuf|feroxbuster",
    re.IGNORECASE
)

def detect_sql_injection(text):
    """Return True if text contains SQL injection patterns."""
    if not text or not SQL_INJECTION_DETECTION:
        return False
    return bool(_SQL_INJECTION_PATTERNS.search(str(text)))

def detect_xss(text):
    """Return True if text contains XSS patterns."""
    if not text or not XSS_DETECTION:
        return False
    return bool(_XSS_PATTERNS.search(str(text)))

def detect_path_traversal(text):
    """Return True if text contains path traversal patterns."""
    if not text or not PATH_TRAVERSAL_DETECTION:
        return False
    return bool(_PATH_TRAVERSAL_PATTERNS.search(str(text)))

def is_malicious_bot(user_agent):
    """Return True if User-Agent matches known malicious scanner."""
    if not user_agent or not BOT_BLOCKING_ENABLED:
        return False
    return bool(_MALICIOUS_UA_PATTERNS.search(user_agent))

def _scan_value(value):
    """Scan a single string value for any attack pattern."""
    s = str(value)
    if detect_sql_injection(s):
        return "sql_injection"
    if detect_xss(s):
        return "xss"
    if detect_path_traversal(s):
        return "path_traversal"
    return None

def _scan_dict(data, depth=0):
    """Recursively scan a dict/list for attack patterns. Returns threat type or None."""
    if depth > 5:
        return None
    if isinstance(data, dict):
        for v in data.values():
            threat = _scan_dict(v, depth + 1)
            if threat:
                return threat
    elif isinstance(data, (list, tuple)):
        for item in data:
            threat = _scan_dict(item, depth + 1)
            if threat:
                return threat
    elif isinstance(data, str):
        return _scan_value(data)
    return None

def run_firewall(app_instance):
    """
    Register the software firewall as a before_request hook on the Flask app.
    Checks every incoming request for: IP blacklist, bot UA, SQL injection,
    XSS, and path traversal. Logs blocked events to the security DB.
    """
    @app_instance.before_request
    def firewall_check():
        if not FIREWALL_ENABLED:
            return None

        ip = request.remote_addr or "unknown"
        ua = request.headers.get("User-Agent", "")
        url = request.path or ""
        method = request.method or ""

        def _block(event_type, detail, severity="warn"):
            """Block this request, log it, and return 403."""
            _audit(event_type, detail, severity)
            try:
                from db import db_log_security_event
                db_log_security_event(
                    event_type=event_type, detail=detail,
                    ip_address=ip, url=url, method=method,
                    user_agent=ua[:512], severity=severity, blocked=True
                )
            except Exception:
                pass
            return jsonify({"success": False, "error": "Request blocked by security firewall."}), 403

        # 1. IP Blacklist
        if IP_BLACKLIST_ENABLED and is_ip_blacklisted(ip):
            return _block("ip_blocked", f"Blacklisted IP: {ip}", "error")

        # 2. Malicious Bot Detection
        if is_malicious_bot(ua):
            return _block("bot_blocked", f"Malicious bot UA: {ua[:120]}", "warn")

        # 3. Path traversal in URL
        if detect_path_traversal(url):
            return _block("path_traversal", f"Path traversal in URL: {url[:200]}", "error")

        # 4. Scan query parameters
        for key, val in request.args.items():
            threat = _scan_value(key) or _scan_value(val)
            if threat:
                return _block(threat, f"Threat in query param '{key}': {val[:100]}", "error")

        # 5. Scan JSON body (POST/PUT/PATCH only, don't touch file uploads)
        if method in ("POST", "PUT", "PATCH"):
            ct = request.content_type or ""
            if "application/json" in ct:
                try:
                    body = request.get_json(silent=True, force=False)
                    if body:
                        threat = _scan_dict(body)
                        if threat:
                            return _block(threat, f"Threat in JSON body ({method} {url})", "error")
                except Exception:
                    pass
            elif "application/x-www-form-urlencoded" in ct or "multipart/form-data" in ct:
                for key, val in request.form.items():
                    threat = _scan_value(key) or _scan_value(val)
                    if threat:
                        return _block(threat, f"Threat in form field '{key}'", "error")

        # 6. Store request IP in flask g for use in routes
        g.request_ip = ip
        return None  # All clear


# ─── ENCRYPTION ENGINE ─────────────────────────────────────────────────────────

def _derive_encryption_key():
    secret = os.environ.get("SECRET_KEY", "echoaction_secret_key_change_in_prod")
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())

_encryption_key = None

def _get_fernet():
    global _encryption_key
    if _encryption_key is None:
        _encryption_key = _derive_encryption_key()
    return Fernet(_encryption_key)

def encrypt_value(value):
    if not value or not PROFILE_ENCRYPTION_ENABLED:
        return value
    try:
        return _get_fernet().encrypt(value.encode()).decode()
    except Exception:
        return value

def decrypt_value(value):
    if not value or not PROFILE_ENCRYPTION_ENABLED:
        return value
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        return value

def encrypt_profile(data):
    for field in ENCRYPTED_PROFILE_FIELDS:
        if field in data and data[field]:
            data[field] = encrypt_value(data[field])
    return data

def decrypt_profile(data):
    for field in ENCRYPTED_PROFILE_FIELDS:
        if field in data and data[field]:
            data[field] = decrypt_value(data[field])
    return data

# ─── PASSWORD HASHING ──────────────────────────────────────────────────────────

def hash_password(password):
    if not PASSWORD_HASHING_ENABLED:
        return password
    return generate_password_hash(password)

def verify_password(password, hashed):
    if not PASSWORD_HASHING_ENABLED:
        return password == hashed
    if hashed and (hashed.startswith('pbkdf2:') or hashed.startswith('scrypt:') or
                   hashed.startswith('bcrypt:') or hashed.startswith('argon2')):
        return check_password_hash(hashed, password)
    return password == hashed

def validate_password_strength(password):
    """
    Validate password strength server-side.
    Returns (is_valid: bool, error_message: str)
    """
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least one symbol (e.g. @, #, !)."
    return True, ""

def validate_email_format(email):
    """Validate email address format server-side."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# ─── INPUT SANITIZATION ────────────────────────────────────────────────────────

def sanitize_string(value, max_length=500):
    if not value or not INPUT_SANITIZATION_ENABLED:
        return value
    s = str(value).strip()
    s = re.sub(r'<[^>]*>', '', s)
    # Remove null bytes
    s = s.replace('\x00', '')
    s = s[:max_length]
    return s

def sanitize_data(data, fields=None):
    if not INPUT_SANITIZATION_ENABLED:
        return data
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            # Skip length truncation for avatar (Base64 data URL can be large)
            if k == "avatar":
                s = str(v).strip()
                s = re.sub(r'<[^>]*>', '', s)
                s = s.replace('\x00', '')
                result[k] = s
            else:
                result[k] = sanitize_string(v, 2000)
        elif isinstance(v, dict):
            result[k] = sanitize_data(v)
        elif isinstance(v, list):
            result[k] = [sanitize_string(i, 2000) if isinstance(i, str) else i for i in v]
        else:
            result[k] = v
    return result

# ─── RATE LIMITER ──────────────────────────────────────────────────────────────

_rate_store = {}

def rate_limit(requests=None, window=None):
    max_req = requests if requests is not None else RATE_LIMIT_REQUESTS
    win = window if window is not None else RATE_LIMIT_WINDOW
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not RATE_LIMIT_ENABLED:
                return f(*args, **kwargs)
            ip = request.remote_addr or 'unknown'
            now = time.time()
            cutoff = now - win
            if ip not in _rate_store:
                _rate_store[ip] = []
            _rate_store[ip] = [t for t in _rate_store[ip] if t > cutoff]
            if len(_rate_store[ip]) >= max_req:
                try:
                    from db import db_log_security_event
                    db_log_security_event(
                        "rate_limit_exceeded", f"Rate limit hit on {request.path}",
                        ip_address=ip, url=request.path, method=request.method,
                        severity="warn", blocked=True
                    )
                except Exception:
                    pass
                return jsonify({"success": False, "error": "Rate limit exceeded. Try again later."}), 429
            _rate_store[ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ─── SECURITY HEADERS ──────────────────────────────────────────────────────────

def add_security_headers(response):
    try:
        if not SECURITY_HEADERS_ENABLED:
            return response
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request and request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # Relaxed CSP for development — tighten for production
        response.headers['Content-Security-Policy'] = (
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "script-src * 'unsafe-inline' 'unsafe-eval'; "
            "style-src * 'unsafe-inline'; "
            "img-src * data: blob:; "
            "connect-src *;"
            "media-src * blob:;"
            "font-src * data:;"
        )
    except Exception:
        pass  # Never let security headers crash the response
    return response

# ─── CSRF PROTECTION ───────────────────────────────────────────────────────────

_csrf_tokens = {}

def generate_csrf_token():
    if not CSRF_PROTECTION_ENABLED:
        return ""
    tok = uuid.uuid4().hex + uuid.uuid4().hex
    try:
        ip = request.remote_addr or "unknown"
    except Exception:
        ip = "unknown"
    expiry = time.time() + 3600  # 1 hour
    _csrf_tokens[tok] = {"ip": ip, "expires": expiry}
    return tok

def validate_csrf_token(token=None):
    if not CSRF_PROTECTION_ENABLED:
        return True
    t = token or request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not t:
        _audit("csrf_missing", "No CSRF token provided", "warn")
        return False
    data = _csrf_tokens.get(t)
    if not data:
        _audit("csrf_invalid", "Invalid CSRF token", "warn")
        return False
    if time.time() > data["expires"]:
        _csrf_tokens.pop(t, None)
        _audit("csrf_expired", "CSRF token expired", "warn")
        return False
    # Don't pop on validation — allow multiple use within expiry window
    return True

def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and CSRF_PROTECTION_ENABLED:
            if not validate_csrf_token():
                try:
                    from db import db_log_security_event
                    db_log_security_event(
                        "csrf_failed", f"CSRF validation failed on {request.path}",
                        ip_address=request.remote_addr or "",
                        url=request.path, method=request.method,
                        severity="warn", blocked=True
                    )
                except Exception:
                    pass
                return jsonify({"success": False, "error": "CSRF validation failed. Please refresh the page."}), 403
        return f(*args, **kwargs)
    return wrapper

def cleanup_csrf_tokens():
    now = time.time()
    expired = [k for k, v in _csrf_tokens.items() if v["expires"] < now]
    for k in expired:
        del _csrf_tokens[k]

# ─── LOGIN RATE LIMITING (per-user exponential backoff) ─────────────────────────

_login_attempts = {}

def check_login_rate_limit(email=None, ip=None):
    if not LOGIN_RATE_LIMIT_ENABLED:
        return True
    now = time.time()
    key = email or ip or request.remote_addr or "unknown"
    entry = _login_attempts.get(key, {"count": 0, "first": now, "blocked_until": 0})
    if now < entry["blocked_until"]:
        remaining = int(entry["blocked_until"] - now)
        _audit("login_blocked", f"Login blocked for {key}, retry in {remaining}s", "warn")
        return False
    if now - entry["first"] > 300:
        entry["count"] = 0
        entry["first"] = now
    entry["count"] += 1
    entry["last"] = now
    if entry["count"] >= 10:
        backoff = min(60 * (2 ** (entry["count"] - 10)), 3600)
        entry["blocked_until"] = now + backoff
        _audit("login_backoff", f"Login rate limit for {key}: {entry['count']} attempts, backoff {backoff}s", "warn")
    _login_attempts[key] = entry
    return entry["count"] <= 10

def reset_login_attempts(email=None, ip=None):
    key = email or ip or request.remote_addr or "unknown"
    _login_attempts.pop(key, None)

# ─── REQUEST SIZE VALIDATION ───────────────────────────────────────────────────

def validate_request_size():
    if not REQUEST_SIZE_LIMIT_ENABLED:
        return True
    if request.content_length and request.content_length > REQUEST_SIZE_MAX_BYTES:
        _audit("request_too_large", f"Content-Length: {request.content_length}", "warn")
        return False
    return True

def check_request_size(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH") and REQUEST_SIZE_LIMIT_ENABLED:
            if not validate_request_size():
                return jsonify({"success": False, "error": "Request body too large."}), 413
        return f(*args, **kwargs)
    return wrapper

# ─── FILE UPLOAD SECURITY ──────────────────────────────────────────────────────

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'mpeg', 'mpg', 'webm'}
ALLOWED_UPLOAD_EXTENSIONS = {'txt'} | ALLOWED_AUDIO_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

# Magic bytes for MIME verification (first bytes of file)
_MAGIC_BYTES = {
    b'\xff\xfb': 'audio/mp3', b'\xff\xf3': 'audio/mp3', b'\xff\xf2': 'audio/mp3',
    b'ID3': 'audio/mp3',
    b'RIFF': 'audio/wav',   # WAV starts with RIFF
    b'\x1aE\xdf\xa3': 'video/mkv',
    b'\x00\x00\x00': 'video/mp4',  # mp4/mov approximate
    b'OggS': 'audio/ogg',
    b'fLaC': 'audio/flac',
}

def validate_filename_security(filename):
    """
    Check filename for security issues.
    Returns (is_safe: bool, error: str)
    """
    if not filename:
        return False, "Empty filename."
    # Null byte injection
    if '\x00' in filename:
        return False, "Null byte in filename."
    # Path traversal in filename
    if detect_path_traversal(filename):
        return False, "Path traversal detected in filename."
    # Extension check
    if '.' not in filename:
        return False, "File has no extension."
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return False, f"File type '.{ext}' is not allowed."
    return True, ""

def validate_upload_mime(file_stream, filename):
    """
    Validate uploaded file by reading magic bytes.
    Returns (is_valid: bool, detected_type: str)
    """
    try:
        header = file_stream.read(16)
        file_stream.seek(0)
        for magic, mime_type in _MAGIC_BYTES.items():
            if header[:len(magic)] == magic:
                return True, mime_type
        # For text files, just check extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext == 'txt':
            return True, 'text/plain'
        # For video files that don't match magic bytes, allow by extension
        if ext in ALLOWED_VIDEO_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS:
            return True, f"media/{ext}"
        return False, "unknown"
    except Exception:
        return False, "unknown"

# ─── SENSITIVE DATA MASKING ────────────────────────────────────────────────────

SENSITIVE_FIELDS = ["password", "token", "secret", "authorization", "key", "credential"]

def mask_sensitive(data, mask="****"):
    if isinstance(data, dict):
        return {k: (mask if any(s in k.lower() for s in SENSITIVE_FIELDS) else mask_sensitive(v, mask)) for k, v in data.items()}
    if isinstance(data, list):
        return [mask_sensitive(i, mask) for i in data]
    return data

# ─── SECURITY STATUS REPORT ────────────────────────────────────────────────────

def get_security_status():
    """Return the current on/off status of all security features."""
    return {
        "firewall":            {"enabled": FIREWALL_ENABLED,           "label": "Software Firewall"},
        "sqlInjection":        {"enabled": SQL_INJECTION_DETECTION,    "label": "SQL Injection Detection"},
        "xss":                 {"enabled": XSS_DETECTION,              "label": "XSS Protection"},
        "pathTraversal":       {"enabled": PATH_TRAVERSAL_DETECTION,   "label": "Path Traversal Detection"},
        "botBlocking":         {"enabled": BOT_BLOCKING_ENABLED,       "label": "Bot/Scanner Blocking"},
        "ipBlacklist":         {"enabled": IP_BLACKLIST_ENABLED,       "label": "IP Blacklist"},
        "csrf":                {"enabled": CSRF_PROTECTION_ENABLED,    "label": "CSRF Protection"},
        "rateLimiting":        {"enabled": RATE_LIMIT_ENABLED,         "label": "Rate Limiting"},
        "loginRateLimit":      {"enabled": LOGIN_RATE_LIMIT_ENABLED,   "label": "Login Attempt Backoff"},
        "passwordHashing":     {"enabled": PASSWORD_HASHING_ENABLED,   "label": "Password Hashing (scrypt)"},
        "profileEncryption":   {"enabled": PROFILE_ENCRYPTION_ENABLED, "label": "Profile Encryption (Fernet)"},
        "inputSanitization":   {"enabled": INPUT_SANITIZATION_ENABLED, "label": "Input Sanitization"},
        "securityHeaders":     {"enabled": SECURITY_HEADERS_ENABLED,   "label": "Security Headers (CSP/XSS)"},
        "requestSizeLimit":    {"enabled": REQUEST_SIZE_LIMIT_ENABLED, "label": "Request Size Limit (10MB)"},
    }
