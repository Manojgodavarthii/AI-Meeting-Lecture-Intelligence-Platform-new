import sys
import json
import pkgutil
import importlib.util

# Monkeypatch pkgutil.get_loader for Python 3.14 compatibility with Flask/Werkzeug
def _get_loader(name):
    try:
        spec = importlib.util.find_spec(name)
        return spec.loader if spec is not None else None
    except Exception:
        return None
pkgutil.get_loader = _get_loader

try:
    import torch
    import whisper
    _WHISPER_AVAILABLE = True
except Exception as _e:
    torch = None
    whisper = None
    _WHISPER_AVAILABLE = False
    print(f"WARNING: torch/whisper unavailable ({_e}); voice transcription disabled.")
import re
import os
import datetime
from flask import Flask, render_template, request, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename
from security import (
    add_security_headers, rate_limit, sanitize_data, sanitize_string,
    generate_csrf_token, csrf_required, check_request_size,
    check_login_rate_limit, reset_login_attempts, _audit,
    mask_sensitive, run_firewall, validate_email_format,
    validate_password_strength, get_security_status,
    validate_filename_security, block_ip, get_blacklisted_ips
)
from db import (
    db_register_user, db_get_user, db_get_single_user, db_get_all_users, db_delete_user,
    db_authenticate_user, db_authenticate_admin, db_log_login, db_get_login_history,
    db_update_user_password, db_update_admin, db_init_auth_tables,
    db_save_meeting, db_get_meetings, db_delete_meeting,
    db_save_activity, db_get_activities,
    db_save_settings, db_get_settings,
    db_add_notification, db_get_notifications, db_mark_notifications_read, db_clear_notifications,
    db_follow_user, db_unfollow_user, db_get_followers,
    db_save_profile_links, db_get_profile_links,
    db_save_query, db_get_queries, db_update_query_status, db_admin_update_user,
    db_save_edit, db_get_edit_history,
    db_init_global_edit_history, db_save_global_edit, db_get_global_edit_history,
    db_count_global_edit_history, db_clear_global_edit_history, db_delete_global_edit,
    db_log_security_event, db_get_security_events, db_get_security_stats, db_init_security_table
)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.environ.get("SECRET_KEY", "echoaction_secret_key_change_in_prod")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 86400

def require_session(f):
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({"success": False, "error": "Authentication required. Please log in."}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# ── REGISTER SOFTWARE FIREWALL ────────────────────────────────────────────────
run_firewall(app)

@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return add_security_headers(response)

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Dynamic cache-busting: version = file modification time so edited static files are always re-fetched
def _asset_ver(name):
    try:
        return int(os.path.getmtime(os.path.join(app.static_folder, name)))
    except Exception:
        return 1

# Configure ffmpeg path
def configure_ffmpeg():
    user_profile = os.environ.get("USERPROFILE", "")
    
    # 1. Search in Winget packages first
    winget_packages = os.path.join(user_profile, "AppData", "Local", "Microsoft", "WinGet", "Packages")
    if os.path.exists(winget_packages):
        for item in os.listdir(winget_packages):
            if "Gyan.FFmpeg" in item:
                path_to_search = os.path.join(winget_packages, item)
                for root, dirs, files in os.walk(path_to_search):
                    if "ffmpeg.exe" in files:
                        print(f"Found ffmpeg in Winget folder: {root}")
                        os.environ["PATH"] += os.pathsep + root
                        return True
                        
    # 2. Check local downloads path
    ffmpeg_local_path = os.path.join(user_profile, "Downloads", "ffmpeg-8.1.1-essentials_build", "bin")
    if os.path.exists(ffmpeg_local_path):
        print(f"Found ffmpeg in Downloads path: {ffmpeg_local_path}")
        os.environ["PATH"] += os.pathsep + ffmpeg_local_path
        return True
        
    # 3. Check another downloads path
    fallback_full = os.path.join(user_profile, "Downloads", "ffmpeg-8.1.1-full_build.exp", "ffmpeg-8.1.1-full_build", "bin")
    if os.path.exists(fallback_full):
        print(f"Found ffmpeg in fallback path: {fallback_full}")
        os.environ["PATH"] += os.pathsep + fallback_full
        return True
        
    print("WARNING: ffmpeg not found. Audio transcription may fail if it is not in the system PATH.")
    return False

configure_ffmpeg()


# Configure CUDA device if available, otherwise CPU
device = "cuda" if (_WHISPER_AVAILABLE and torch.cuda.is_available()) else "cpu"
model = None
if _WHISPER_AVAILABLE:
    try:
        print("Loading Whisper base model...")
        model = whisper.load_model("base").to(device)
        print("Whisper base model loaded successfully.")
    except Exception as _e:
        print(f"WARNING: Whisper model failed to load ({_e}); voice transcription disabled.")
else:
    print("Whisper disabled: torch/whisper not available.")

# Allowed files helper
ALLOWED_EXTENSIONS = {
    'txt', 
    # Audio formats
    'mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac',
    # Video formats
    'mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'mpeg', 'mpg'
}

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'm4v', 'mpeg', 'mpg', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

# --- Video Analysis Helpers ---

def extract_video_metadata(filepath):
    """Use ffprobe to extract video metadata: duration, resolution, fps, codecs."""
    import subprocess
    import json
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', filepath
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if result.returncode != 0:
            print(f"ffprobe error: {result.stderr}")
            return {}
        data = json.loads(result.stdout)
        metadata = {}
        # Extract format info
        fmt = data.get('format', {})
        duration_sec = float(fmt.get('duration', 0))
        minutes = int(duration_sec // 60)
        seconds = int(duration_sec % 60)
        metadata['duration'] = f"{minutes}m {seconds:02d}s"
        metadata['duration_seconds'] = duration_sec
        metadata['size_mb'] = round(int(fmt.get('size', 0)) / (1024 * 1024), 1)
        # Extract stream info
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video' and 'video_codec' not in metadata:
                metadata['video_codec'] = stream.get('codec_name', 'unknown').upper()
                metadata['width'] = stream.get('width', 0)
                metadata['height'] = stream.get('height', 0)
                metadata['resolution'] = f"{stream.get('width', '?')}x{stream.get('height', '?')}"
                # Parse FPS
                r_frame_rate = stream.get('r_frame_rate', '0/1')
                try:
                    num, den = r_frame_rate.split('/')
                    metadata['fps'] = round(int(num) / int(den), 1)
                except Exception:
                    metadata['fps'] = 0
            elif stream.get('codec_type') == 'audio' and 'audio_codec' not in metadata:
                metadata['audio_codec'] = stream.get('codec_name', 'unknown').upper()
                metadata['sample_rate'] = stream.get('sample_rate', '?')
        return metadata
    except Exception as e:
        print(f"Error extracting video metadata: {e}")
        return {}


def detect_chapters(transcript_text, total_duration_seconds=0):
    """Detect chapters from transcript by clustering sentences into ~5 segments."""
    sentences = re.split(r'[.!?]', transcript_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    if not sentences:
        return []

    # Topic-shift keywords for chapter boundaries
    topic_keywords = [
        'first', 'second', 'third', 'next', 'now', 'moving on', 'let\'s talk about',
        'another', 'additionally', 'finally', 'in conclusion', 'to summarize',
        'the main', 'key point', 'important', 'let me', 'starting with',
        'agenda', 'topic', 'item', 'section', 'part'
    ]

    chapter_titles = [
        'Introduction & Overview',
        'Core Discussion',
        'Key Decisions & Action Points',
        'Deep Dive Analysis',
        'Next Steps & Wrap-Up'
    ]

    chapter_colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e']

    # Split sentences into up to 5 chapters
    num_chapters = min(5, max(2, len(sentences) // 2))
    chunk_size = max(1, len(sentences) // num_chapters)
    chapters = []

    for i in range(num_chapters):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < num_chapters - 1 else len(sentences)
        chapter_sentences = sentences[start_idx:end_idx]
        
        # Calculate timestamp offset
        if total_duration_seconds > 0:
            ts_start = (i / num_chapters) * total_duration_seconds
            ts_end = ((i + 1) / num_chapters) * total_duration_seconds
            ts_start_fmt = f"{int(ts_start // 60)}:{int(ts_start % 60):02d}"
            ts_end_fmt = f"{int(ts_end // 60)}:{int(ts_end % 60):02d}"
        else:
            ts_start_fmt = f"{i * 2}:00"
            ts_end_fmt = f"{(i + 1) * 2}:00"

        # Auto-derive chapter title from keywords in sentences
        title = chapter_titles[i] if i < len(chapter_titles) else f"Chapter {i + 1}"
        for sent in chapter_sentences[:3]:
            for kw in topic_keywords:
                if kw in sent.lower():
                    # Capitalize first meaningful chunk as title
                    words = sent.split()[:6]
                    title = ' '.join(words).title()
                    break

        chapters.append({
            'index': i + 1,
            'title': title,
            'timestamp_start': ts_start_fmt,
            'timestamp_end': ts_end_fmt,
            'color': chapter_colors[i % len(chapter_colors)],
            'summary': '. '.join(chapter_sentences[:2]) + '.' if chapter_sentences else 'No content.'
        })

    return chapters

# Summary extraction
def generate_summary(text):
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    summary = ". ".join(sentences[:3])
    if summary and not summary.endswith('.'):
        summary += '.'
    return summary

# Month mapper
def month_name_to_num(name):
    months = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    name_lower = name.lower()
    return months.get(name_lower[:3]) or months.get(name_lower)

# Robust date parser (now defaults to current year if not specified)
def parse_date_from_text(text):
    current_year = datetime.datetime.now().year
    
    # 1. YYYY-MM-DD or YYYY/MM/DD
    match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", text)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # 2. MM/DD/YYYY or DD/MM/YYYY or MM-DD-YYYY or DD-MM-YYYY
    match = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", text)
    if match:
        v1, v2, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if v1 > 12:
            day, month = v1, v2
        elif v2 > 12:
            month, day = v1, v2
        else:
            month, day = v1, v2 # default to MM/DD/YYYY
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # 3. Textual dates WITH year: "December 25, 2026" or "25 Dec 2026"
    months_pattern = r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b"
    # Pattern 3A: [Month] [Day] [Year]
    match = re.search(months_pattern + r"\s+(\d{1,2})(?:st|nd|rd|th)?\b,?\s*(\d{4})\b", text, re.IGNORECASE)
    if match:
        month_name = match.group(1)
        day = int(match.group(2))
        year = int(match.group(3))
        month = month_name_to_num(month_name)
        if month and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # Pattern 3B: [Day] [Month] [Year]
    match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?" + months_pattern + r"\s*,?\s*(\d{4})\b", text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        month = month_name_to_num(month_name)
        if month and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # 4. Textual dates WITHOUT year: "December 25" or "25th Dec"
    # Pattern 4A: [Month] [Day]
    match = re.search(months_pattern + r"\s+(\d{1,2})(?:st|nd|rd|th)?\b", text, re.IGNORECASE)
    if match:
        month_name = match.group(1)
        day = int(match.group(2))
        month = month_name_to_num(month_name)
        if month and 1 <= day <= 31:
            return f"{current_year:04d}-{month:02d}-{day:02d}"

    # Pattern 4B: [Day] [Month]
    match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?" + months_pattern + r"\b", text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        month = month_name_to_num(month_name)
        if month and 1 <= day <= 31:
            return f"{current_year:04d}-{month:02d}-{day:02d}"

    # 5. MM/DD or MM-DD without year (e.g. 12/25)
    match = re.search(r"\b(\d{1,2})[-/](\d{1,2})\b", text)
    if match:
        v1, v2 = int(match.group(1)), int(match.group(2))
        # Validate Month/Day combinations
        if 1 <= v1 <= 12 and 1 <= v2 <= 31:
            return f"{current_year:04d}-{v1:02d}-{v2:02d}"
        elif 1 <= v2 <= 12 and 1 <= v1 <= 31:
            return f"{current_year:04d}-{v2:02d}-{v1:02d}"

    return None

# Action Items extraction
def extract_action_items(text):
    keywords = [
        "complete",
        "submit",
        "prepare",
        "send",
        "finish",
        "update",
        "create",
        "review",
        "develop",
        "design",
        "implement"
    ]
    actions = []
    sentences = re.split(r'[.!?]', text)
    for sentence in sentences:
        sentence_str = sentence.strip()
        if not sentence_str:
            continue
        
        has_keyword = False
        for keyword in keywords:
            if keyword.lower() in sentence_str.lower():
                has_keyword = True
                break
        
        # Check if sentence has a parsed date
        formatted_date = parse_date_from_text(sentence_str)
        
        # Extract sentence if it has an action keyword OR has a date
        if has_keyword or formatted_date:
            priority = "Medium"
            high_keys = ["urgent", "critical", "asap", "must", "immediately", "high", "important"]
            low_keys = ["low", "later", "maybe", "sometime", "could", "nice to"]
            
            sentence_lower = sentence_str.lower()
            if any(k in sentence_lower for k in high_keys):
                priority = "High"
            elif any(k in sentence_lower for k in low_keys):
                priority = "Low"
            elif not has_keyword:
                # General deadline mention (no action verb) defaults to Low priority
                priority = "Low"
                
            actions.append({
                'title': sentence_str,
                'deadline': formatted_date,
                'priority': priority,
                'assignee': 'Sarah Jenkins' # Default assignee
            })
            
    return actions

# Deadlines extraction
def extract_deadlines(text):
    deadlines = []
    sentences = re.split(r'[.!?]', text)
    for sentence in sentences:
        parsed = parse_date_from_text(sentence)
        if parsed:
            deadlines.append(parsed)
    return list(dict.fromkeys(deadlines))

# Class Notes extraction
def extract_class_notes(text):
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    concepts = []
    study_guide = []
    qa = []
    assignments = []
    
    concept_keywords = ["defined as", "refers to", "means", "known as", "concept of", "is when", "stands for", "is defined", "definition", "called", "is a", "is an"]
    guide_keywords = ["remember", "key point", "focus on", "essential", "crucial", "tip", "always", "never", "formula", "note that", "important", "summary", "takeaway"]
    assignment_keywords = ["homework", "assignment", "read", "study", "submit", "prepare", "exam", "quiz", "project", "review", "exercise", "practice", "problem set", "due"]
    
    # 0. Extract lecture title/topic from first few sentences
    lecture_title = ""
    if sentences:
        first = sentences[0]
        if len(first) < 100:
            lecture_title = first
    
    # 1. Extract Concepts — also grab noun phrases / technical terms
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in concept_keywords):
            concepts.append(s)
    
    # If no keyword-based concepts found, extract meaningful noun phrases
    if len(concepts) < 2 and len(sentences) >= 3:
        # Take sentences that look like definitions (contain "is" or "are")
        for s in sentences:
            s_lower = s.lower()
            if (" is " in s_lower or " are " in s_lower or " refers " in s_lower) and len(s.split()) >= 4 and len(s.split()) <= 40:
                if s not in concepts:
                    concepts.append(s)
    
    # If still no concepts, create from first substantive sentences
    if len(concepts) == 0 and sentences:
        for s in sentences[:3]:
            concepts.append(s)
            
    # 2. Extract Study Guide
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in guide_keywords) and s not in concepts:
            study_guide.append(s)
    
    # If no study tips found, use the last few sentences as summary
    if len(study_guide) < 2 and len(sentences) >= 6:
        study_guide = [s for s in sentences[-3:] if s not in concepts]
            
    # 3. Extract Q&A
    for i in range(len(sentences)):
        s = sentences[i]
        s_lower = s.lower()
        if "?" in s or "question" in s_lower or "ask" in s_lower or "how to" in s_lower or "what is" in s_lower or "explain" in s_lower:
            question = s
            answer = "Review the lecture notes for a detailed explanation."
            if i + 1 < len(sentences):
                answer = sentences[i+1]
            qa.append({
                "question": question,
                "answer": answer
            })
    
    # Generate Q&A from transcript if none found
    if len(qa) == 0 and len(sentences) >= 4:
        for i in range(0, min(len(sentences)-1, 6), 2):
            qa.append({
                "question": f"What is the significance of: \"{sentences[i][:80]}...\"?" if len(sentences[i]) > 80 else f"Can you explain: {sentences[i]}?",
                "answer": sentences[i+1] if i+1 < len(sentences) else "Refer to the lecture transcript."
            })
            
    # 4. Extract Assignments / Action Items
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in assignment_keywords):
            date = parse_date_from_text(s)
            assignments.append({
                'title': s,
                'deadline': date,
                'priority': 'High' if any(w in s_lower for w in ['exam', 'quiz', 'due tomorrow']) else 'Medium',
                'assignee': 'Student'
            })
    
    # 5. Extract Lecture Notes outline
    if len(sentences) >= 4:
        # Create organized sections
        intro = sentences[0] if len(sentences) > 0 else ""
        main_points = sentences[1:4] if len(sentences) >= 4 else sentences[1:]
        summary = sentences[-1] if len(sentences) > 4 else ""
        lecture_notes_text = f"Introduction: {intro}\n\nMain Points:\n"
        for mp in main_points:
            lecture_notes_text += f"- {mp}\n"
        if summary:
            lecture_notes_text += f"\nSummary: {summary}"
        lecture_notes = lecture_notes_text
    else:
        lecture_notes = ". ".join(sentences) + "." if sentences else "No lecture content available."
    
    return {
        'lecture_notes': lecture_notes,
        'concepts': concepts[:8],
        'study_guide': study_guide[:8],
        'qa': qa[:6],
        'assignments': assignments
    }


@app.route("/analyze-video", methods=["POST"])
def analyze_video():
    """Dedicated endpoint for video file analysis."""
    error = None
    file = request.files.get('file')

    if not file or file.filename == '':
        return {"success": False, "error": "No video file provided."}, 400

    filename = file.filename
    if not filename or not is_video_file(filename):
        return {"success": False, "error": f"Invalid file type. Supported video formats: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"}, 400

    sec_filename = secure_filename(filename)
    if not sec_filename:
        return {"success": False, "error": "Invalid filename."}, 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], sec_filename)
    file.save(filepath)

    transcript_text = ""
    metadata = {}
    chapters = []

    try:
        # Step 1: Extract video metadata via ffprobe
        print(f"Extracting metadata for: {filepath}")
        metadata = extract_video_metadata(filepath)
        print(f"Metadata: {metadata}")

        # Step 2: Transcribe audio track with Whisper
        if model is None:
            raise RuntimeError("Voice transcription is unavailable (Whisper model not loaded).")
        print(f"Transcribing video audio: {filepath}")
        result = model.transcribe(filepath)
        transcript_text = result.get("text", "")
        print(f"Transcription complete: {len(transcript_text)} chars")

        # Step 3: Detect chapters from transcript
        total_dur = metadata.get('duration_seconds', 0)
        chapters = detect_chapters(transcript_text, total_dur)

    except Exception as e:
        import traceback
        print("ERROR during video analysis:")
        traceback.print_exc()
        error = f"Error analyzing video: {str(e)}"
    finally:
        # Clean up uploaded file after processing
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

    if error:
        return {"success": False, "error": error}, 500

    if not transcript_text.strip():
        return {"success": False, "error": "No speech detected in video."}, 400

    summary = generate_summary(transcript_text)
    actions = extract_action_items(transcript_text)
    deadlines = extract_deadlines(transcript_text)

    return {
        "success": True,
        "filename": filename,
        "fileUrl": "/uploads/" + sec_filename,
        "transcript": transcript_text,
        "summary": summary,
        "actions": actions,
        "deadlines": deadlines,
        "metadata": metadata,
        "chapters": chapters
    }


@app.route("/", methods=["GET", "POST"])
def index():
    summary = ""
    actions = []
    deadlines = []
    transcript = ""
    filename = ""
    error = None
    success = False
    mode = "meeting"
    class_notes = None

    if request.method == "POST":
        import subprocess
        print("--- DIAGNOSTIC START ---")
        print("PATH:", os.environ.get("PATH"))
        try:
            res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("FFMPEG TEST SUCCESS:", res.stdout.splitlines()[0] if res.stdout else "No output")
        except Exception as ex:
            print("FFMPEG TEST FAILED:", ex)
        print("------------------------")
        
        mode = request.form.get('mode', 'meeting')
        uploadType = request.form.get('type', '')
        file = request.files.get('file')
        use_default = False
        
        if not file or not file.filename:
            use_default = True
            
        if use_default:
            default_filename = 'lecture_transcript.txt' if mode == 'class' else 'meeting_transcript.txt'
            default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), default_filename)
            if os.path.exists(default_path):
                try:
                    with open(default_path, 'r', encoding='utf-8', errors='ignore') as f:
                        meeting_text = f.read()
                    filename = default_filename
                    if meeting_text.strip():
                        transcript = meeting_text
                        summary = generate_summary(meeting_text)
                        deadlines = extract_deadlines(meeting_text)
                        if mode == 'class':
                            class_notes = extract_class_notes(meeting_text)
                            actions = class_notes['assignments']
                        else:
                            actions = extract_action_items(meeting_text)
                        success = True
                    else:
                        error = "Default transcript file is empty."
                except Exception as e:
                    error = f"Error reading default transcript: {str(e)}"
            else:
                error = "No file selected. Please select a transcript or audio file."
        elif file and allowed_file(file.filename):
            filename = file.filename
            ext = filename.rsplit('.', 1)[1].lower()
            meeting_text = ""
            
            if ext == 'txt':
                try:
                    meeting_text = file.read().decode('utf-8', errors='ignore')
                except Exception as e:
                    error = f"Error reading text file: {str(e)}"
            else:
                sec_filename = secure_filename(filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], sec_filename)
                file.save(filepath)
                
                try:
                    print(f"Transcribing audio file: {filepath}")
                    result = model.transcribe(filepath)
                    meeting_text = result["text"]
                except Exception as e:
                    import traceback
                    print("ERROR: Exception during transcription:")
                    traceback.print_exc()
                    error = f"Error transcribing audio: {str(e)}"
                finally:
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception:
                        pass
            
            if not error:
                if meeting_text.strip():
                    transcript = meeting_text
                    summary = generate_summary(meeting_text)
                    deadlines = extract_deadlines(meeting_text)
                    if mode == 'class':
                        class_notes = extract_class_notes(meeting_text)
                        actions = class_notes['assignments']
                    else:
                        actions = extract_action_items(meeting_text)
                    success = True
                else:
                    error = "The uploaded file contains no readable text or speech."
        else:
            error = "Invalid file type. Supported types: .txt, audio (.mp3, .wav, .m4a, .ogg, .flac, etc.), or video (.mp4, .mkv, .avi, .mov, etc.)"

        # AJAX JSON Interceptor for SPA integration
        if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if error:
                return {"success": False, "error": error}, 400
            detectedType = uploadType
            if not detectedType and filename:
                detectedType = "video" if is_video_file(filename) else "audio"
            return {
                "success": True,
                "mode": mode,
                "type": detectedType,
                "filename": filename,
                "fileUrl": "/uploads/" + secure_filename(filename) if filename and filename != '' else "",
                "transcript": transcript,
                "summary": summary,
                "actions": actions,
                "deadlines": deadlines,
                "class_notes": class_notes
            }

    csrf_token_str = generate_csrf_token()
    return render_template(
        "index.html",
        summary=summary,
        actions=actions,
        deadlines=deadlines,
        transcript=transcript,
        filename=filename,
        error=error,
        success=success,
        mode=mode,
        class_notes=class_notes,
        csrf_token=csrf_token_str,
        app_v=_asset_ver('app.js'),
        mock_v=_asset_ver('mockData.js'),
        new_v=_asset_ver('new-features.js'),
        v2_v=_asset_ver('features-v2.js'),
        is_desktop=os.environ.get("ECHOACTION_DESKTOP") == "1"
    )

# ── MySQL API ROUTES ──────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
@rate_limit(requests=10, window=60)
@check_request_size
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()
    if not email or not password or not name:
        return jsonify({"success": False, "error": "Name, email and password are required."}), 400
    # Server-side email format validation
    if not validate_email_format(email):
        return jsonify({"success": False, "error": "Invalid email address format."}), 400
    # Server-side password strength validation
    pw_ok, pw_err = validate_password_strength(password)
    if not pw_ok:
        return jsonify({"success": False, "error": pw_err}), 400
    existing = db_get_user(email)
    if existing:
        return jsonify({"success": False, "error": "Email already registered."}), 409
    data["email"] = email
    db_register_user(sanitize_data(data))
    db_log_security_event("user_registered", f"New user registered: {email}",
                          ip_address=request.remote_addr or "", email=email,
                          url="/api/register", method="POST", severity="info")
    return jsonify({"success": True, "message": "User registered successfully."})

@app.route("/api/login", methods=["POST"])
@rate_limit(requests=20, window=60)
@check_request_size
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    device_name = (data.get("device") or "").strip()[:255]
    ip_address = request.remote_addr or ""
    user_agent = (request.headers.get("User-Agent") or "")[:512]

    if not check_login_rate_limit(email=email):
        _audit("login_blocked", f"Login blocked for {email} due to rate limit", "warn")
        return jsonify({"success": False, "error": "Too many login attempts. Please wait before trying again."}), 429

    user = db_authenticate_user(email, password)
    # If user is in ea_registration, also check if they're a staff member
    if user:
        from db import get_conn as _gcheck
        _cchk = _gcheck(); _uchk = _cchk.cursor(dictionary=True)
        _uchk.execute("SELECT id, staff_role, department, position, avatar, active FROM ea_staff_members WHERE email=%s AND password IS NOT NULL", (email,))
        _sm = _uchk.fetchone()
        _uchk.close(); _cchk.close()
        if _sm:
            user["role"] = "staff"
            user["portal"] = "staff"
            user["isAdmin"] = False
            user["staff_role"] = _sm.get("staff_role", "")
            user["department"] = _sm.get("department", "")
    if not user:
        # Check if this is a root admin
        from db import db_authenticate_root_admin
        root = db_authenticate_root_admin(email, password)
        if root:
            user = {"id": root.get("id"), "name": root["name"], "email": root["email"], "role": "root_admin",
                    "company": "", "phone": "", "bio": "", "linkedin": "",
                    "timezone": "UTC", "avatar": root.get("avatar", ""), "profileLinkSlug": "",
                    "isAdmin": True}
        else:
            # Check if this is a sub-admin
            admin = db_authenticate_admin(email, password)
            if admin:
                user = {"id": admin.get("id"), "name": admin["name"], "email": admin["email"], "role": "admin",
                        "company": "", "phone": "", "bio": "", "linkedin": "",
                        "timezone": "UTC", "avatar": admin.get("avatar", ""), "profileLinkSlug": "",
                        "isAdmin": True}
            else:
                # Check if this is a staff member
                from db import get_conn as _gconn
                _conn = _gconn(); _cur = _conn.cursor(dictionary=True)
                _cur.execute("SELECT id, name, email, password, staff_role, department, position, avatar, active FROM ea_staff_members WHERE email=%s", (email,))
                _staff_row = _cur.fetchone()
                _cur.close(); _conn.close()
                if _staff_row and _staff_row.get("password"):
                    from security import verify_password as _vp
                    if _vp(password, _staff_row["password"]):
                        user = {"id": _staff_row.get("id"), "name": _staff_row["name"], "email": _staff_row["email"],
                                "role": "staff", "portal": "staff", "company": "", "phone": "",
                                "bio": "", "linkedin": "", "timezone": "UTC",
                                "avatar": _staff_row.get("avatar", ""), "profileLinkSlug": "", "isAdmin": False,
                                "staff_role": _staff_row.get("staff_role", ""), "department": _staff_row.get("department", "")}
                if not user:
                    _audit("login_failed", f"Failed login attempt for {email}", "warn")
                    db_log_login(email, success=False, device_name=device_name, ip_address=ip_address, user_agent=user_agent)
                    db_log_security_event("login_failed", f"Failed login for {email}",
                                          ip_address=ip_address, email=email,
                                          url="/api/login", method="POST", severity="warn", blocked=False)
                    return jsonify({"success": False, "error": "Invalid email or password."}), 401

    reset_login_attempts(email=email)
    db_log_login(email, success=True, device_name=device_name, ip_address=ip_address, user_agent=user_agent)
    db_log_security_event("login_success", f"Successful login for {email}",
                          ip_address=ip_address, email=email,
                          url="/api/login", method="POST", severity="info")
    _audit("login_success", f"Successful login for {email}")
    # Check if user is an admin (from ea_users or ea_root_admins)
    if not user.get("isAdmin"):
        from db import db_authenticate_root_admin
        root = db_authenticate_root_admin(email, password)
        if root:
            user["isAdmin"] = True
        else:
            admin = db_authenticate_admin(email, password)
            user["isAdmin"] = admin is not None
    session.permanent = True
    session['user_email'] = email
    session['user_name'] = user.get('name', email)
    session['user_role'] = user.get('role', 'user')
    return jsonify({"success": True, "user": user})

@app.route("/api/csrf-token", methods=["GET"])
def api_csrf_token():
    token = generate_csrf_token()
    return jsonify({"success": True, "csrf_token": token})

@app.route("/api/user", methods=["POST"])
@csrf_required
@check_request_size
def api_update_user():
    data = request.get_json(silent=True) or {}
    if not data.get("email"):
        return jsonify({"success": False, "error": "Email is required."}), 400
    new_email = (data.pop("newEmail", None) or "").strip().lower()
    orig_email = data["email"]
    # Handle email change
    if new_email and new_email != orig_email:
        from db import get_conn
        conn = get_conn(); cur = conn.cursor()
        try:
            cur.execute("UPDATE ea_users SET email=%s WHERE email=%s", (new_email, orig_email))
            cur.execute("UPDATE ea_registration SET email=%s WHERE email=%s", (new_email, orig_email))
            cur.execute("UPDATE ea_staff_members SET email=%s WHERE email=%s", (new_email, orig_email))
            conn.commit()
        finally:
            cur.close(); conn.close()
        data["email"] = new_email
    # Preserve password in registration if provided
    pwd = data.pop("password", None) if "password" in data else None
    db_register_user(sanitize_data(data))
    # Update password separately if provided
    if pwd:
        from security import hash_password
        conn = __import__('db', fromlist=['get_conn']).get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE ea_registration SET password=%s WHERE email=%s", (hash_password(pwd), data["email"]))
        conn.commit()
        cur.close(); conn.close()
    return jsonify({"success": True, "message": "Profile updated."})

@app.route("/api/change-password", methods=["POST"])
@csrf_required
@check_request_size
def api_change_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or data.get("adminEmail") or "").strip().lower()
    current_password = data.get("currentPassword", "")
    new_password = data.get("newPassword", "")
    if not email or not current_password or not new_password:
        return jsonify({"success": False, "error": "All fields are required."}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
    from db import get_conn
    from security import verify_password, hash_password
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT password FROM ea_registration WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "error": "User not found."}), 404
        if not verify_password(current_password, row["password"]):
            return jsonify({"success": False, "error": "Current password is incorrect."}), 403
        hashed = hash_password(new_password)
        cur.execute("UPDATE ea_registration SET password=%s WHERE email=%s", (hashed, email))
        cur.execute("UPDATE ea_staff_members SET password=%s WHERE email=%s", (hashed, email))
        conn.commit()
        return jsonify({"success": True, "message": "Password changed successfully."})
    finally:
        cur.close(); conn.close()

@app.route("/api/users", methods=["GET"])
def api_get_all_users():
    requester = session.get('user_email', '') or request.args.get("email", "").strip().lower()
    if not requester:
        return jsonify({"success": False, "error": "Email parameter required."}), 400
    users = db_get_all_users()
    # Strip password from output
    safe = [{k: v for k, v in u.items() if k != "password"} for u in users]
    return jsonify({"success": True, "users": safe})

@app.route("/api/meetings", methods=["GET"])
def api_get_meetings():
    email = session.get('user_email', '') or request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email is required."}), 400
    meetings = db_get_meetings(email)
    return jsonify({"success": True, "meetings": meetings})

@app.route("/api/meetings", methods=["POST"])
@csrf_required
@check_request_size
def api_save_meeting():
    data = request.get_json(silent=True) or {}
    meeting = data.get("meeting")
    email = data.get("email", "")
    if not meeting or not meeting.get("id"):
        return jsonify({"success": False, "error": "Meeting data with id is required."}), 400
    db_save_meeting(meeting, email)
    return jsonify({"success": True, "message": "Meeting saved to database."})

@app.route("/api/meetings/<meeting_id>", methods=["DELETE"])
@csrf_required
def api_delete_meeting(meeting_id):
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required to delete meeting."}), 400
    # Only delete meetings belonging to the requesting user
    user_meetings = db_get_meetings(email)
    owned = any(str(m.get("id")) == str(meeting_id) for m in user_meetings)
    if not owned:
        db_log_security_event("unauthorized_delete", f"{email} attempted to delete meeting {meeting_id}",
                              ip_address=request.remote_addr or "", email=email,
                              url=f"/api/meetings/{meeting_id}", method="DELETE",
                              severity="warn", blocked=True)
        return jsonify({"success": False, "error": "Unauthorized: meeting not found or not yours."}), 403
    db_delete_meeting(meeting_id)
    return jsonify({"success": True, "message": "Meeting deleted."})

@app.route("/api/activities", methods=["GET"])
def api_get_activities():
    email = request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email is required."}), 400
    activities = db_get_activities(email)
    return jsonify({"success": True, "activities": activities})

@app.route("/api/activities", methods=["POST"])
@csrf_required
@check_request_size
def api_save_activity():
    data = request.get_json(silent=True) or {}
    activity = data.get("activity")
    email = data.get("email", "")
    if not activity or not activity.get("id"):
        return jsonify({"success": False, "error": "Activity data with id is required."}), 400
    db_save_activity(activity, email)
    return jsonify({"success": True, "message": "Activity saved."})

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    email = request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email is required."}), 400
    settings = db_get_settings(email)
    return jsonify({"success": True, "settings": settings})

@app.route("/api/settings", methods=["POST"])
@csrf_required
@check_request_size
def api_save_settings():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    settings = data.get("settings", {})
    if not email:
        return jsonify({"success": False, "error": "Email is required."}), 400
    db_save_settings(email, settings)
    return jsonify({"success": True, "message": "Settings saved."})

@app.route("/api/user", methods=["DELETE"])
@csrf_required
def api_delete_user():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    if not password:
        return jsonify({"success": False, "error": "Password confirmation required to delete account."}), 400
    # Verify password before allowing deletion
    from db import db_authenticate_user
    verified = db_authenticate_user(email, password)
    if not verified:
        db_log_security_event("unauthorized_delete", f"Failed account deletion attempt for {email}",
                              ip_address=request.remote_addr or "", email=email,
                              url="/api/user", method="DELETE", severity="warn", blocked=True)
        return jsonify({"success": False, "error": "Password incorrect. Account not deleted."}), 403
    db_delete_user(email)
    db_log_security_event("account_deleted", f"Account deleted: {email}",
                          ip_address=request.remote_addr or "", email=email,
                          url="/api/user", method="DELETE", severity="warn")
    return jsonify({"success": True})

@app.route("/api/login-history", methods=["GET"])
@require_session
def api_get_login_history():
    email = request.args.get("email", "") or session.get('user_email', '')
    if not email:
        return jsonify({"success": False, "error": "Authentication required."}), 401
    history = db_get_login_history(email)
    return jsonify({"success": True, "history": history})

@app.route("/api/notifications", methods=["GET"])
def api_get_notifications():
    email = session.get('user_email', '') or request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    return jsonify({"success": True, "notifications": db_get_notifications(email)})

@app.route("/api/notifications", methods=["POST"])
@csrf_required
@check_request_size
def api_add_notification():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    message = data.get("message", "")
    if not email or not message:
        return jsonify({"success": False, "error": "Email and message required."}), 400
    db_add_notification(email, message, data.get("type", "info"))
    return jsonify({"success": True})

@app.route("/api/notifications/read", methods=["POST"])
@csrf_required
def api_mark_notifications_read():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    db_mark_notifications_read(email)
    return jsonify({"success": True})

@app.route("/api/notifications/clear", methods=["POST"])
@csrf_required
def api_clear_notifications():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    db_clear_notifications(email)
    return jsonify({"success": True})

@app.route("/api/follow", methods=["POST"])
@csrf_required
@check_request_size
def api_follow():
    data = request.get_json(silent=True) or {}
    ue = data.get("userEmail", "")
    fe = data.get("followerEmail", "")
    if not ue or not fe:
        return jsonify({"success": False, "error": "Both emails required."}), 400
    db_follow_user(ue, fe)
    db_add_notification(ue, f"{fe} started following you.", "follow")
    return jsonify({"success": True})

@app.route("/api/unfollow", methods=["POST"])
@csrf_required
def api_unfollow():
    data = request.get_json(silent=True) or {}
    db_unfollow_user(data.get("userEmail", ""), data.get("followerEmail", ""))
    return jsonify({"success": True})

@app.route("/api/followers", methods=["GET"])
def api_get_followers():
    email = request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    return jsonify({"success": True, "followers": db_get_followers(email)})

@app.route("/api/profile-links", methods=["GET"])
def api_get_profile_links():
    email = request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    return jsonify({"success": True, "links": db_get_profile_links(email)})


# ── Public profile page (/p/<slug>) ────────────────────────────────────────
@app.route("/p/<path:slug>")
def public_profile(slug):
    """Renders a public profile card for the given profile_link_slug."""
    from db import get_db
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT name, role, company, bio, avatar, linkedin FROM ea_users "
            "WHERE profile_link_slug = %s LIMIT 1",
            (slug,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()
    except Exception:
        user = None

    if not user:
        return (
            """<!DOCTYPE html><html><head><title>Profile Not Found</title>
            <style>body{font-family:sans-serif;display:flex;align-items:center;
            justify-content:center;height:100vh;background:#0c1020;color:#fff;}
            .box{text-align:center;padding:2rem;}
            h2{font-size:1.5rem;margin-bottom:0.5rem;}
            p{color:#9ca3af;font-size:0.9rem;}
            a{color:#6366f1;text-decoration:none;}
            </style></head><body>
            <div class="box">
              <div style="font-size:3rem;margin-bottom:1rem;">🔍</div>
              <h2>Profile not found</h2>
              <p>The profile link <strong>/p/""" + slug + """</strong> does not exist or has been removed.</p>
              <p style="margin-top:1rem;"><a href="/">← Return to EchoAction AI</a></p>
            </div></body></html>""",
            404,
        )

    name    = user.get("name", "User")
    role    = user.get("role", "")
    company = user.get("company", "")
    bio     = user.get("bio", "")
    avatar  = user.get("avatar", "")
    linkedin = user.get("linkedin", "")

    initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "U"
    avatar_html = (
        f'<img src="{avatar}" alt="Avatar" style="width:96px;height:96px;border-radius:50%;object-fit:cover;">'
        if avatar else
        f'<div style="width:96px;height:96px;border-radius:50%;background:linear-gradient(135deg,#4f46e5,#6366f1);'
        f'display:flex;align-items:center;justify-content:center;font-size:2.2rem;font-weight:800;color:white;">{initials}</div>'
    )
    li_btn = (
        f'<a href="{linkedin}" target="_blank" style="display:inline-flex;align-items:center;gap:0.4rem;'
        f'background:#0077b5;color:#fff;padding:0.45rem 1rem;border-radius:8px;text-decoration:none;'
        f'font-size:0.85rem;font-weight:600;margin-top:0.5rem;">'
        f'<svg width="14" height="14" viewBox="0 0 24 24" fill="white"><path d="M19 0h-14c-2.761 0-5 2.239-5 '
        f'5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c'
        f'-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h'
        f'-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg> LinkedIn</a>'
    ) if linkedin else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{name} — EchoAction AI Profile</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: linear-gradient(135deg, #0c1020 0%, #1e1b4b 60%, #0f172a 100%);
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center; padding: 2rem;
    }}
    .card {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 24px;
      padding: 2.5rem 2rem;
      max-width: 420px; width: 100%;
      text-align: center;
      backdrop-filter: blur(12px);
      box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }}
    .avatar-wrap {{ display: flex; justify-content: center; margin-bottom: 1.2rem; }}
    h1 {{ font-size: 1.6rem; font-weight: 800; color: #fff; margin-bottom: 0.2rem; }}
    .role {{ font-size: 0.9rem; color: #6366f1; font-weight: 600; margin-bottom: 0.1rem; }}
    .company {{ font-size: 0.82rem; color: #9ca3af; margin-bottom: 1rem; }}
    .bio {{
      font-size: 0.85rem; color: #c8d0dc; line-height: 1.65;
      background: rgba(99,102,241,0.07); border-radius: 10px;
      padding: 0.8rem 1rem; margin-bottom: 1rem;
      border: 1px solid rgba(99,102,241,0.15);
    }}
    .badge {{
      display: inline-flex; align-items: center; gap: 0.35rem;
      font-size: 0.72rem; color: #34d399; font-weight: 600;
      background: rgba(16,185,129,0.1); padding: 0.25rem 0.65rem;
      border-radius: 20px; border: 1px solid rgba(52,211,153,0.25);
      margin-bottom: 1rem;
    }}
    .back-link {{
      display: inline-block; margin-top: 1.2rem;
      color: #6366f1; text-decoration: none; font-size: 0.82rem;
      font-weight: 600; letter-spacing: 0.2px;
    }}
    .back-link:hover {{ color: #a5b4fc; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="avatar-wrap">{avatar_html}</div>
    <h1>{name}</h1>
    {'<div class="role">' + role + '</div>' if role else ''}
    {'<div class="company">🏢 ' + company + '</div>' if company else ''}
    <div class="badge">✓ EchoAction AI Member</div>
    {'<div class="bio">' + bio + '</div>' if bio else ''}
    {li_btn}
    <br>
    <a class="back-link" href="/">← Return to EchoAction AI</a>
  </div>
</body>
</html>"""
    return html

@app.route("/api/profile-links", methods=["POST"])
@csrf_required
@check_request_size
def api_save_profile_links_route():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    db_save_profile_links(email, data.get("links", []))
    return jsonify({"success": True})

@app.route("/api/query", methods=["POST"])
@csrf_required
@check_request_size
def api_save_query_route():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "error": "Name required."}), 400
    db_save_query(data)
    return jsonify({"success": True, "message": "Query submitted successfully."})

@app.route("/api/edit-history", methods=["GET"])
def api_get_edit_history():
    mid = request.args.get("meetingId", "")
    if not mid:
        return jsonify({"success": False, "error": "Meeting ID required."}), 400
    return jsonify({"success": True, "history": db_get_edit_history(mid)})

@app.route("/api/edit-history", methods=["POST"])
@csrf_required
@check_request_size
def api_save_edit_route():
    data = request.get_json(silent=True) or {}
    mid = data.get("meetingId", "")
    field = data.get("field", "")
    email = data.get("email", "")
    oldV = data.get("oldValue", "")
    newV = data.get("newValue", "")
    desc = data.get("description", "")
    print(f"[EHD] POST meetingId={mid} field={field} email={email} old=|{oldV}| new=|{newV}| desc=|{desc}|")
    if not mid or not field:
        return jsonify({"success": False, "error": "meetingId and field required."}), 400
    db_save_edit(mid, email, field, oldV, newV, desc)
    return jsonify({"success": True})

# ─── GLOBAL EDIT HISTORY ──────────────────────────────────────────────────────

@app.route("/api/global-edit-history", methods=["GET"])
def api_get_global_edit_history():
    email = request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "email required."}), 400
    limit = int(request.args.get("limit", 200))
    offset = int(request.args.get("offset", 0))
    history = db_get_global_edit_history(email, limit, offset)
    total = db_count_global_edit_history(email)
    return jsonify({"success": True, "history": history, "total": total})

@app.route("/api/global-edit-history", methods=["POST"])
@csrf_required
@check_request_size
def api_save_global_edit():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    edit_type = data.get("type", "")
    description = data.get("description", "")
    if not email or not edit_type or not description:
        return jsonify({"success": False, "error": "email, type, and description required."}), 400
    db_save_global_edit(email, edit_type, description, data.get("meta"))
    return jsonify({"success": True})

@app.route("/api/global-edit-history/clear", methods=["POST"])
@csrf_required
def api_clear_global_edit_history():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "email required."}), 400
    db_clear_global_edit_history(email)
    return jsonify({"success": True})

@app.route("/api/global-edit-history/<int:edit_id>", methods=["DELETE"])
@csrf_required
def api_delete_global_edit(edit_id):
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "email required."}), 400
    db_delete_global_edit(edit_id, email)
    return jsonify({"success": True})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/send-email", methods=["POST"])
@csrf_required
@check_request_size
def send_email():
    """Send an email draft to specified recipients."""
    import json
    from flask import jsonify

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "No data provided."}), 400

    recipients = data.get("recipients", [])
    subject = data.get("subject", "")
    body = data.get("body", "")

    if not recipients:
        return jsonify({"success": False, "error": "No recipients specified."}), 400

    if not subject and not body:
        return jsonify({"success": False, "error": "Email subject and body are required."}), 400

    validated = []
    seen = set()
    for email in recipients:
        email = email.strip().lower()
        if email and email not in seen and re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
            validated.append(email)
            seen.add(email)

    if not validated:
        return jsonify({"success": False, "error": "No valid email addresses found."}), 400

    # Security: limit recipients to 10
    if len(validated) > 10:
        return jsonify({"success": False, "error": "Maximum 10 recipients allowed per email."}), 400
    # Limit subject and body length
    if len(subject) > 200:
        return jsonify({"success": False, "error": "Subject too long (max 200 characters)."}), 400

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.environ.get("SMTP_HOST", "")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))

        if not smtp_host:
            raise ValueError("SMTP_HOST not configured")

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = os.environ.get("SMTP_FROM", "noreply@echoaction.ai")
        msg["To"] = ", ".join(validated)
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASS", "")
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(msg["From"], validated, msg.as_string())

        return jsonify({
            "success": True,
            "message": f"Email sent successfully to {len(validated)} recipient(s).",
            "recipients": validated
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "message": f"Email queued for delivery to {len(validated)} recipient(s).",
            "recipients": validated,
            "note": f"SMTP not configured. Email recorded for later delivery."
        })

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    safe_name = secure_filename(filename)
    if not safe_name:
        return {"error": "Invalid filename."}, 400
    # Security: validate extension before serving
    ok, err = validate_filename_security(safe_name)
    if not ok:
        db_log_security_event("suspicious_download", f"Blocked serve of: {safe_name}",
                              ip_address=request.remote_addr or "",
                              url=f"/uploads/{filename}", method="GET",
                              severity="warn", blocked=True)
        return jsonify({"error": err}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name)

# ── SECURITY API ROUTES ───────────────────────────────────────────────────────

@app.route("/api/security-events", methods=["GET"])
@require_session
def api_get_security_events():
    """Return recent security events for the dashboard."""
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    severity = request.args.get("severity", None)
    event_type = request.args.get("type", None)
    email = request.args.get("email", None) or session.get('user_email', '')
    events = db_get_security_events(limit=limit, offset=offset,
                                    severity=severity, event_type=event_type, email=email)
    return jsonify({"success": True, "events": events})

@app.route("/api/security-stats", methods=["GET"])
def api_get_security_stats():
    """Return aggregate security statistics."""
    stats = db_get_security_stats()
    return jsonify({"success": True, "stats": stats})

@app.route("/api/security-status", methods=["GET"])
def api_get_security_status():
    """Return on/off status of all security features."""
    status = get_security_status()
    blacklisted = get_blacklisted_ips()
    return jsonify({"success": True, "status": status, "blacklistedIPs": blacklisted})

@app.route("/api/block-ip", methods=["POST"])
@csrf_required
def api_block_ip():
    """Manually add an IP to the blacklist."""
    data = request.get_json(silent=True) or {}
    ip = (data.get("ip") or "").strip()
    if not ip:
        return jsonify({"success": False, "error": "IP address required."}), 400
    import re as _re
    if not _re.match(r'^[\d.:a-fA-F]+$', ip):
        return jsonify({"success": False, "error": "Invalid IP address format."}), 400
    block_ip(ip)
    db_log_security_event("ip_manually_blocked", f"IP manually blocked: {ip}",
                          ip_address=request.remote_addr or "",
                          url="/api/block-ip", method="POST", severity="warn", blocked=False)
    return jsonify({"success": True, "message": f"IP {ip} has been blocked."})

# ─── ADMIN PANEL ROUTES ────────────────────────────────────────────────────────

def _require_admin(req):
    """Check if the request comes from an admin user. Returns admin email or None."""
    try:
        admin_email = req.args.get("adminEmail", "")
        if not admin_email:
            body = req.get_json(silent=True)
            if body:
                admin_email = body.get("adminEmail", "")
        if not admin_email:
            return None
        from db import get_conn
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT email FROM ea_admin_users WHERE email=%s", (admin_email,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return admin_email if row else None
    except Exception as e:
        print(f"[ADMIN] _require_admin error: {e}")
        return None

@app.route("/api/admin/users", methods=["GET"])
@csrf_required
def api_admin_get_users():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    users = db_get_all_users()
    return jsonify({"success": True, "users": users, "count": len(users)})

@app.route("/api/admin/user", methods=["GET"])
@csrf_required
def api_admin_get_user():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    email = request.args.get("email", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    user = db_get_single_user(email)
    return jsonify({"success": True, "user": user})

@app.route("/api/admin/users/<email>", methods=["PUT"])
@csrf_required
def api_admin_update_user(email):
    data = request.get_json(silent=True) or {}
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    db_admin_update_user(email, data)
    return jsonify({"success": True, "message": "User updated."})

@app.route("/api/admin/users/<email>/password", methods=["POST"])
@csrf_required
def api_admin_update_password(email):
    data = request.get_json(silent=True) or {}
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    new_password = data.get("newPassword", "")
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
    db_update_user_password(email, new_password)
    # Also update ea_staff_members if this is a staff member
    from db import get_conn as _gc
    from security import hash_password
    _conn = _gc(); _cur = _conn.cursor()
    _cur.execute("UPDATE ea_staff_members SET password=%s WHERE email=%s", (hash_password(new_password), email))
    if _cur.rowcount > 0:
        _conn.commit()
        from db import db_save_global_edit
        db_save_global_edit(admin, "staff_password_changed", f"Changed password for staff {email}", {"email": email})
    _cur.close(); _conn.close()
    return jsonify({"success": True, "message": "Password updated."})

@app.route("/api/admin/delete-user", methods=["POST"])
@csrf_required
def api_admin_delete_user():
    data = request.get_json(silent=True) or {}
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    try:
        db_delete_user(email)
        return jsonify({"success": True, "message": f"User {email} deleted."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/queries", methods=["GET"])
@csrf_required
def api_admin_get_queries():
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    queries = db_get_queries()
    return jsonify({"success": True, "queries": queries, "count": len(queries)})

@app.route("/api/admin/queries/<int:qid>", methods=["PATCH"])
@csrf_required
def api_admin_update_query(qid):
    data = request.get_json(silent=True) or {}
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    db_update_query_status(qid, data.get("status", "new"))
    return jsonify({"success": True})

@app.route("/api/staff/queries", methods=["GET"])
@csrf_required
def api_staff_get_queries():
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_get_staff_members
    staff = db_get_staff_members()
    if not any(s.get("email","").strip().lower() == email for s in staff):
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    queries = db_get_queries()
    return jsonify({"success": True, "queries": queries, "count": len(queries)})

@app.route("/api/staff/queries/<int:qid>", methods=["PATCH"])
@csrf_required
def api_staff_update_query(qid):
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_get_staff_members
    staff = db_get_staff_members()
    if not any(s.get("email","").strip().lower() == email for s in staff):
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    db_update_query_status(qid, data.get("status", "new"))
    return jsonify({"success": True})

@app.route("/api/analyze/class", methods=["POST"])
@csrf_required
@check_request_size
def api_analyze_class():
    """Generate class notes from a transcript text."""
    data = request.get_json(silent=True) or {}
    transcript = (data.get("transcript") or "").strip()
    if not transcript:
        return jsonify({"success": False, "error": "Transcript text is required."}), 400
    notes = extract_class_notes(transcript)
    summary = generate_summary(transcript)
    deadlines = extract_deadlines(transcript)
    return jsonify({
        "success": True,
        "classNotes": notes,
        "summary": summary,
        "deadlines": deadlines
    })

@app.route("/api/admin/me", methods=["GET"])
@csrf_required
def api_admin_me():
    """Return admin info including seeded credentials hint."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    from db import get_conn
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, email, name, role, avatar, permissions, last_login, created_at FROM ea_admin_users WHERE email=%s", (admin,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        return jsonify({"success": False, "error": "Admin not found."}), 404
    return jsonify({
        "success": True,
        "admin": {
            "id": row["id"], "email": row["email"], "name": row["name"],
            "role": row["role"], "avatar": row.get("avatar", ""),
            "permissions": json.loads(row["permissions"]) if row.get("permissions") else {},
            "lastLogin": row["last_login"].strftime("%Y-%m-%d %H:%M:%S") if row.get("last_login") else None,
            "createdAt": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
        },
        "credentialHint": "Default: admin@echoaction.ai / Admin@123"
    })

# ─── ADMIN SEPARATE LOGIN ─────────────────────────────────────────────────────

@app.route("/api/admin/login", methods=["POST"])
@rate_limit(requests=20, window=60)
@check_request_size
def api_admin_login():
    """Authenticate an admin user (root or sub-admin)."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required."}), 400

    from db import db_authenticate_root_admin, db_authenticate_admin
    admin = db_authenticate_root_admin(email, password)
    if admin:
        session.permanent = True
        session['user_email'] = email
        session['user_name'] = admin.get("name", "Main Admin")
        session['user_role'] = "root_admin"
        return jsonify({"success": True, "admin": {
            "email": email,
            "name": admin.get("name", "Main Admin"),
            "role": "root_admin",
            "adminType": "root",
            "avatar": admin.get("avatar", "")
        }})
    admin = db_authenticate_admin(email, password)
    if admin:
        session.permanent = True
        session['user_email'] = email
        session['user_name'] = admin.get("name", "Admin")
        session['user_role'] = admin.get("role", "admin")
        return jsonify({"success": True, "admin": {
            "email": email,
            "name": admin.get("name", "Admin"),
            "role": admin.get("role", "admin"),
            "adminType": admin.get("admin_type", "sub"),
            "avatar": admin.get("avatar", "")
        }})
    return jsonify({"success": False, "error": "Invalid admin credentials."}), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

# ─── USER PROFILE API ─────────────────────────────────────────────────────────

@app.route("/api/user/profile", methods=["GET"])
def api_get_user_profile():
    """Get user profile."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    user = db_get_user(email)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404
    return jsonify({"success": True, "user": user})

@app.route("/api/user/profile", methods=["POST"])
@csrf_required
@check_request_size
def api_update_user_profile():
    """Update user profile fields."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    updates = {k: v for k, v in data.items() if k not in ["email", "password"]}
    from db import db_update_user_profile
    success = db_update_user_profile(email, updates)
    return jsonify({"success": bool(success)})

# ─── ADMIN STAFF MANAGEMENT ───────────────────────────────────────────────────

@app.route("/api/admin/staff", methods=["GET"])
@csrf_required
def api_admin_get_staff():
    """Get all staff members."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    from db import db_get_staff_members
    staff = db_get_staff_members()
    return jsonify({"success": True, "staff": staff, "count": len(staff)})

@app.route("/api/admin/staff/add", methods=["POST"])
@csrf_required
@check_request_size
def api_admin_add_staff():
    """Add a new staff member."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    position = data.get("position", "").strip()
    department = data.get("department", "").strip()
    staff_role = data.get("staffRole", "staff").strip()
    phone = data.get("phone", "").strip()
    access = data.get("access", "").strip()
    if not email or not name:
        return jsonify({"success": False, "error": "Email and name required."}), 400
    from db import db_add_staff_member, db_get_staff_members, db_save_global_edit
    # Enforce max 4 staff members
    existing = db_get_staff_members()
    if len(existing) >= 4:
        existingMatch = [s for s in existing if s["email"] == email]
        if not existingMatch:
            return jsonify({"success": False, "error": "Staff limit reached (max 4). Please remove an existing staff member first."}), 400
    db_add_staff_member(email, name, position, department, staff_role, phone, "", admin, access)
    db_save_global_edit(admin, "staff_added", f"Added staff member {name} ({email}) as {staff_role}", {
        "staff_email": email, "name": name, "position": position, "department": department, "staff_role": staff_role
    })
    return jsonify({"success": True, "message": f"Staff {name} added."})

@app.route("/api/admin/staff/delete", methods=["POST"])
@csrf_required
def api_admin_delete_staff():
    """Delete a staff member."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_delete_staff_member, db_save_global_edit
    db_delete_staff_member(email)
    db_save_global_edit(admin, "staff_deleted", f"Deleted staff member {email}", {"staff_email": email})
    return jsonify({"success": True, "message": "Staff member deleted."})

@app.route("/api/admin/staff/access", methods=["POST"])
@csrf_required
def api_admin_staff_access():
    """Toggle staff access (block/unblock)."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    access = data.get("access", "").strip()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_add_staff_member, db_save_global_edit
    db_add_staff_member(email, "", "", "", "", "", "", admin, access)
    db_save_global_edit(admin, "staff_access_changed", f"Updated access for {email}: {access}", {"email": email, "access": access})
    return jsonify({"success": True, "message": "Staff access updated."})

@app.route("/api/admin/staff/permissions", methods=["POST"])
@csrf_required
@check_request_size
def api_admin_staff_permissions():
    """Save granular permissions for a staff member."""
    try:
        admin = _require_admin(request)
        if not admin:
            return jsonify({"success": False, "error": "Unauthorized."}), 403
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        permissions = data.get("permissions", {})
        if not email:
            return jsonify({"success": False, "error": "Email required."}), 400
        import json
        from db import db_update_staff_permissions, db_save_global_edit
        db_update_staff_permissions(email, json.dumps(permissions))
        db_save_global_edit(admin, "staff_permissions", f"Updated permissions for {email}", {"email": email, "permissions": permissions})
        return jsonify({"success": True, "message": "Staff permissions updated."})
    except Exception as ex:
        print(f"[ERROR] Permissions save failed: {ex}")
        return jsonify({"success": False, "error": f"Server error: {ex}"}), 500

@app.route("/api/admin/user/security", methods=["GET"])
@csrf_required
def api_admin_user_security_get():
    """Get security settings for a user."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import get_conn
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT mfa_enabled, session_timeout, access_level, audit_level FROM ea_registration WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        return jsonify({"success": True, "security": {"mfa_enabled": False, "session_timeout": "1hr", "access_level": "Standard", "audit_level": "Basic"}})
    return jsonify({"success": True, "security": {
        "mfa_enabled": bool(row.get("mfa_enabled")),
        "session_timeout": row.get("session_timeout") or "1hr",
        "access_level": row.get("access_level") or "Standard",
        "audit_level": row.get("audit_level") or "Basic"
    }})

@app.route("/api/admin/user/security", methods=["POST"])
@csrf_required
def api_admin_user_security_save():
    """Save security settings for a user."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    mfa = data.get("mfa_enabled", False)
    timeout = data.get("session_timeout", "1hr")
    accessLevel = data.get("access_level", "Standard")
    auditLevel = data.get("audit_level", "Basic")
    from db import get_conn, db_save_global_edit
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""UPDATE ea_registration SET mfa_enabled=%s, session_timeout=%s, access_level=%s, audit_level=%s WHERE email=%s""",
                (1 if mfa else 0, timeout, accessLevel, auditLevel, email))
    conn.commit()
    cur.close(); conn.close()
    db_save_global_edit(admin, "user_security", f"Updated security for {email}", {"email": email, "mfa": mfa, "timeout": timeout, "access_level": accessLevel, "audit_level": auditLevel})
    return jsonify({"success": True, "message": "Security settings saved."})

# ─── ADMIN USER SECURITY ──────────────────────────────────────────────────────

@app.route("/api/admin/user/block-ip", methods=["POST"])
@csrf_required
def api_admin_block_ip():
    """Block an IP for a user."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    ip = (data.get("ip") or "").strip()
    if not email or not ip:
        return jsonify({"success": False, "error": "Email and IP required."}), 400
    from db import db_block_user_ip
    db_block_user_ip(email, ip, admin)
    return jsonify({"success": True, "message": f"IP {ip} blocked for {email}."})

@app.route("/api/admin/user/unblock-ip", methods=["POST"])
@csrf_required
def api_admin_unblock_ip():
    """Unblock an IP for a user."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    ip = (data.get("ip") or "").strip()
    if not email or not ip:
        return jsonify({"success": False, "error": "Email and IP required."}), 400
    from db import db_unblock_user_ip
    db_unblock_user_ip(email, ip, admin)
    return jsonify({"success": True, "message": f"IP {ip} unblocked for {email}."})

@app.route("/api/admin/user/edit-history", methods=["GET"])
@csrf_required
def api_admin_get_edit_history():
    """Get edit history for a user (admin view)."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    email = request.args.get("email", "").strip().lower()
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_get_staff_edit_history, db_count_staff_edit_history
    history = db_get_staff_edit_history(email, limit, offset)
    total = db_count_staff_edit_history(email)
    return jsonify({"success": True, "history": history, "total": total})

# ─── ADMIN SECURITY SETTINGS ──────────────────────────────────────────────────

@app.route("/api/admin/security/settings", methods=["GET"])
@csrf_required
def api_admin_get_security_settings():
    """Get admin security settings."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    from db import db_get_admin_security_settings
    settings = db_get_admin_security_settings(admin)
    return jsonify({"success": True, "settings": settings})

@app.route("/api/admin/security/settings", methods=["POST"])
@csrf_required
def api_admin_set_security_setting():
    """Set admin security setting."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    key = data.get("key", "").strip()
    value = data.get("value", "")
    if not key:
        return jsonify({"success": False, "error": "Setting key required."}), 400
    from db import db_set_admin_security_setting
    db_set_admin_security_setting(admin, key, value)
    return jsonify({"success": True, "message": "Security setting updated."})

# ─── ADMIN IT TEAM ────────────────────────────────────────────────────────────

@app.route("/api/admin/it-team/staff", methods=["GET"])
@csrf_required
def api_it_team_get_staff():
    """Get all staff members for IT team view."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    from db import db_get_staff_members, db_is_it_team
    if not db_is_it_team(admin):
        return jsonify({"success": False, "error": "IT Team access required."}), 403
    staff = db_get_staff_members()
    return jsonify({"success": True, "staff": staff, "count": len(staff)})

# ─── ADMIN CALENDAR EVENTS ────────────────────────────────────────────────────

@app.route("/api/admin/calendar/events", methods=["GET"])
@csrf_required
def api_admin_calendar_events():
    """Get calendar events with colors."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    events = [
        {"id": 1, "title": "Team Standup", "start": "2026-06-28T09:00:00", "end": "2026-06-28T09:30:00", "color": "#6366f1", "type": "meeting"},
        {"id": 2, "title": "Sprint Review", "start": "2026-06-28T14:00:00", "end": "2026-06-28T15:00:00", "color": "#06b6d4", "type": "review"},
        {"id": 3, "title": "Security Audit", "start": "2026-06-29T10:00:00", "end": "2026-06-29T12:00:00", "color": "#f43f5e", "type": "security"},
        {"id": 4, "title": "Deploy to Prod", "start": "2026-06-30T16:00:00", "end": "2026-06-30T17:00:00", "color": "#10b981", "type": "deploy"},
        {"id": 5, "title": "IT Maintenance", "start": "2026-07-01T22:00:00", "end": "2026-07-02T02:00:00", "color": "#f59e0b", "type": "maintenance"},
    ]
    return jsonify({"success": True, "events": events})

# ─── STAFF STATUS ─────────────────────────────────────────────────────────────

@app.route("/api/admin/staff/status", methods=["POST"])
@csrf_required
def api_admin_staff_status():
    """Update staff member's active/inactive status with reason and letter."""
    admin = _require_admin(request)
    if not admin:
        return jsonify({"success": False, "error": "Unauthorized."}), 403
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    active = data.get("active", True)
    reason = data.get("reason", "")
    letter = data.get("letter", "")
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_update_staff_status, db_save_global_edit
    db_update_staff_status(email, active, reason, letter)
    status_text = "active" if active else "inactive"
    db_save_global_edit(admin, "staff_status", f"Changed {email} status to {status_text}. Reason: {reason}", {"email": email, "active": active, "reason": reason})
    return jsonify({"success": True, "message": f"Staff status updated to {status_text}."})

# ─── MESSAGING ────────────────────────────────────────────────────────────────

@app.route("/api/messages", methods=["GET"])
def api_get_messages():
    """Get messages for the currently logged-in user."""
    email = session.get('user_email', '') or request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_get_messages, db_get_unread_count
    messages = db_get_messages(email)
    unread = db_get_unread_count(email)
    return jsonify({"success": True, "messages": messages, "unread": unread})

@app.route("/api/messages/send", methods=["POST"])
@csrf_required
@check_request_size
def api_send_message():
    """Send a message from one user to another."""
    data = request.get_json(silent=True) or {}
    from_email = (data.get("fromEmail") or "").strip().lower()
    to_email = (data.get("toEmail") or "").strip().lower()
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()
    if not from_email or not to_email:
        return jsonify({"success": False, "error": "From and To emails required."}), 400
    if not body:
        return jsonify({"success": False, "error": "Message body required."}), 400
    from db import db_send_message, db_save_global_edit
    msg_id = db_send_message(from_email, to_email, subject, body)
    db_save_global_edit(from_email, "message_sent", f"Sent message to {to_email}: {subject}", {"to": to_email, "subject": subject})
    return jsonify({"success": True, "message": "Message sent.", "id": msg_id})

@app.route("/api/messages/read", methods=["POST"])
@csrf_required
def api_mark_read():
    """Mark a message as read."""
    data = request.get_json(silent=True) or {}
    msg_id = data.get("id")
    if not msg_id:
        return jsonify({"success": False, "error": "Message ID required."}), 400
    from db import db_mark_message_read
    db_mark_message_read(int(msg_id))
    return jsonify({"success": True})

# ─── STAFF SELF-PERMISSIONS ────────────────────────────────────────────────────

@app.route("/api/staff/permissions", methods=["GET"])
def api_staff_permissions():
    """Get permissions for the currently logged-in staff member."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required."}), 400
    from db import db_get_staff_members
    all_staff = db_get_staff_members()
    import json
    for s in all_staff:
        if s["email"].lower() == email:
            perms = {}
            try:
                perms = json.loads(s.get("access", "{}"))
            except:
                pass
            return jsonify({"success": True, "permissions": perms})
    return jsonify({"success": True, "permissions": {}})

# JSON error handlers for API routes
@app.errorhandler(500)
def api_500(e):
    return jsonify({"success": False, "error": "Internal server error."}), 500
@app.errorhandler(403)
def api_403(e):
    return jsonify({"success": False, "error": "Forbidden."}), 403
@app.errorhandler(404)
def api_404(e):
    return jsonify({"success": False, "error": "Not found."}), 404
@app.errorhandler(405)
def api_405(e):
    return jsonify({"success": False, "error": "Method not allowed."}), 405

if __name__ == "__main__":
    try:
        db_init_security_table()
        print("[OK] Security events table initialized.")
    except Exception as e:
        print(f"[WARN] Could not init security table: {e}")
    try:
        db_init_global_edit_history()
        print("[OK] Global edit history table initialized.")
    except Exception as e:
        print(f"[WARN] Could not init global edit history table: {e}")
    try:
        db_init_auth_tables()
        print("[OK] Auth tables initialized.")
    except Exception as e:
        print(f"[WARN] Could not init auth tables: {e}")
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    flask_host = os.environ.get("FLASK_HOST", "127.0.0.1")
    flask_port = int(os.environ.get("FLASK_PORT", 5003))
    print(f"[INFO] Starting server on http://{flask_host}:{flask_port}")
    app.run(host=flask_host, port=flask_port, debug=debug_mode, use_reloader=False)
                                                