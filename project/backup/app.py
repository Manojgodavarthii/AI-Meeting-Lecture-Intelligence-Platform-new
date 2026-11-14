import sys
import pkgutil
import importlib.util
import json

# Monkeypatch pkgutil.get_loader for Python 3.14 compatibility with Flask/Werkzeug
def _get_loader(name):
    try:
        spec = importlib.util.find_spec(name)
        return spec.loader if spec is not None else None
    except Exception:
        return None
pkgutil.get_loader = _get_loader

import torch
import whisper
import re
import os
import datetime
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "echoaction_secret_key"

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    fallback_full = r"C:\Users\godav\Downloads\ffmpeg-8.1.1-full_build.exp\ffmpeg-8.1.1-full_build\bin"
    if os.path.exists(fallback_full):
        print(f"Found ffmpeg in fallback path: {fallback_full}")
        os.environ["PATH"] += os.pathsep + fallback_full
        return True
        
    print("WARNING: ffmpeg not found. Audio transcription may fail if it is not in the system PATH.")
    return False

configure_ffmpeg()


# Configure CUDA device if available, otherwise CPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load Whisper model (base) at startup
print("Loading Whisper base model...")
model = whisper.load_model("base").to(device)
print("Whisper base model loaded successfully.")

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
    
    concept_keywords = ["defined as", "refers to", "means", "known as", "concept of", "is when", "stands for", "is defined", "definition"]
    guide_keywords = ["remember", "key point", "focus on", "essential", "crucial", "tip", "always", "never", "formula", "note that"]
    assignment_keywords = ["homework", "assignment", "read", "study", "submit", "prepare", "exam", "quiz", "project", "review"]
    
    # 1. Extract Concepts
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in concept_keywords):
            concepts.append(s)
            
    # 2. Extract Study Guide
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in guide_keywords) and s not in concepts:
            study_guide.append(s)
            
    # 3. Extract Q&A
    for i in range(len(sentences)):
        s = sentences[i]
        s_lower = s.lower()
        if "?" in s or "question" in s_lower or "ask" in s_lower:
            question = s
            answer = "See transcript details for explanation."
            if i + 1 < len(sentences):
                answer = sentences[i+1]
            qa.append({
                "question": question,
                "answer": answer
            })
            
    # 4. Extract Assignments / Action Items
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in assignment_keywords):
            date = parse_date_from_text(s)
            assignments.append({
                'title': s,
                'deadline': date,
                'priority': 'High' if 'exam' in s_lower or 'quiz' in s_lower else 'Medium',
                'assignee': 'Sarah Jenkins'
            })
            
    # 5. Extract Lecture Notes outline
    lecture_notes = sentences[:6] if len(sentences) >= 6 else sentences
    
    return {
        'lecture_notes': ". ".join(lecture_notes) + ".",
        'concepts': concepts[:5],
        'study_guide': study_guide[:5],
        'qa': qa[:4],
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
    if not is_video_file(filename):
        return {"success": False, "error": f"Invalid file type. Supported video formats: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"}, 400

    sec_filename = secure_filename(filename)
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
        if os.path.exists(filepath):
            os.remove(filepath)

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
        file = request.files.get('file')
        use_default = False
        
        if not file or file.filename == '':
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
                    if os.path.exists(filepath):
                        os.remove(filepath)
            
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
            return {
                "success": True,
                "mode": mode,
                "filename": filename,
                "transcript": transcript,
                "summary": summary,
                "actions": actions,
                "deadlines": deadlines,
                "class_notes": class_notes
            }

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
        class_notes=class_notes
    )

# ─── USER AUTH + PROFILE API ENDPOINTS ──────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    """Register a new user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    password = data.get("password", "")
    role = data.get("role", "").strip()
    company = data.get("company", "").strip()
    phone = data.get("phone", "").strip()
    timezone = data.get("timezone", "UTC").strip()
    avatar = data.get("avatar", "").strip()

    if not email or not name or not password:
        return jsonify({"success": False, "error": "Email, name and password are required"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

    import re as _re
    if not _re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400

    from db import db_register_user, db_get_user
    existing = db_get_user(email)
    if existing:
        return jsonify({"success": False, "error": "Email already registered"}), 409

    try:
        user_id = db_register_user({
            "email": email, "name": name, "password": password,
            "role": role, "company": company, "phone": phone,
            "timezone": timezone, "avatar": avatar,
            "bio": "", "linkedin": "", "profileLinkSlug": ""
        })
        return jsonify({"success": True, "message": "Registered successfully", "userId": user_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def api_login():
    """Authenticate a regular user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    from db import db_authenticate_user, db_log_login, db_init_auth_tables
    try:
        db_init_auth_tables()
    except Exception:
        pass

    ip = request.remote_addr or ""
    ua = request.headers.get("User-Agent", "")

    user = db_authenticate_user(email, password)
    if not user:
        try:
            db_log_login(email, success=False, ip_address=ip, user_agent=ua)
        except Exception:
            pass
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    try:
        db_log_login(email, success=True, ip_address=ip, user_agent=ua)
    except Exception:
        pass

    return jsonify({"success": True, "user": user})


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    """Authenticate an admin user (root or sub-admin)."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    from db import db_authenticate_root_admin, db_authenticate_admin
    # Try root admin first
    admin = db_authenticate_root_admin(email, password)
    if admin:
        return jsonify({"success": True, "admin": {
            "email": email,
            "name": admin.get("name", "Main Admin"),
            "role": "root_admin",
            "adminType": "root",
            "avatar": admin.get("avatar", "")
        }})
    # Try sub-admin
    admin = db_authenticate_admin(email, password)
    if admin:
        return jsonify({"success": True, "admin": {
            "email": email,
            "name": admin.get("name", "Admin"),
            "role": admin.get("role", "admin"),
            "adminType": admin.get("admin_type", "sub"),
            "avatar": admin.get("avatar", "")
        }})

    return jsonify({"success": False, "error": "Invalid admin credentials"}), 401


@app.route("/api/user/profile", methods=["GET"])
def api_get_user_profile():
    """Get user profile."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_user
    user = db_get_user(email)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    return jsonify({"success": True, "user": user})


@app.route("/api/user/profile", methods=["POST"])
def api_update_user_profile():
    """Update user profile fields."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    updates = {k: v for k, v in data.items() if k not in ["email", "password"]}
    from db import db_update_user_profile
    success = db_update_user_profile(email, updates)
    return jsonify({"success": bool(success)})


@app.route("/api/user/delete", methods=["POST"])
def api_delete_user():
    """Delete current user account."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_delete_user
    db_delete_user(email)
    return jsonify({"success": True})


@app.route("/api/user/login-history", methods=["GET"])
def api_login_history():
    """Get login history for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_login_history
    history = db_get_login_history(email, limit=20)
    return jsonify({"success": True, "history": history})


@app.route("/api/meetings", methods=["GET"])
def api_get_meetings():
    """Get meetings for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_meetings
    meetings = db_get_meetings(email)
    return jsonify({"success": True, "meetings": meetings})


@app.route("/api/meetings", methods=["POST"])
def api_save_meeting():
    """Save a meeting for a user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    meeting = data.get("meeting", {})
    if not email or not meeting:
        return jsonify({"success": False, "error": "Email and meeting required"}), 400
    from db import db_save_meeting
    db_save_meeting(meeting, email)
    return jsonify({"success": True})


@app.route("/api/meetings/<meeting_id>", methods=["DELETE"])
def api_delete_meeting(meeting_id):
    """Delete a meeting."""
    from db import db_delete_meeting
    db_delete_meeting(meeting_id)
    return jsonify({"success": True})


@app.route("/api/activities", methods=["GET"])
def api_get_activities():
    """Get activities for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_activities
    activities = db_get_activities(email)
    return jsonify({"success": True, "activities": activities})


@app.route("/api/activities", methods=["POST"])
def api_save_activity():
    """Save an activity for a user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    activity = data.get("activity", {})
    if not email or not activity:
        return jsonify({"success": False, "error": "Email and activity required"}), 400
    from db import db_save_activity
    db_save_activity(activity, email)
    return jsonify({"success": True})


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    """Get settings for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_settings
    s = db_get_settings(email)
    return jsonify({"success": True, "settings": s})


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    """Save settings for a user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    settings_data = data.get("settings", {})
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_save_settings
    db_save_settings(email, settings_data)
    return jsonify({"success": True})


@app.route("/api/followers", methods=["GET"])
def api_get_followers():
    """Get followers for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_followers
    followers = db_get_followers(email)
    return jsonify({"success": True, "followers": followers})


@app.route("/api/follow", methods=["POST"])
def api_follow_user():
    """Follow or unfollow a user."""
    data = request.get_json() or {}
    user_email = data.get("userEmail", "").strip().lower()
    follower_email = data.get("followerEmail", "").strip().lower()
    action = data.get("action", "follow")
    if not user_email or not follower_email:
        return jsonify({"success": False, "error": "Both emails required"}), 400
    from db import db_follow_user, db_unfollow_user
    if action == "follow":
        db_follow_user(user_email, follower_email)
    else:
        db_unfollow_user(user_email, follower_email)
    return jsonify({"success": True})


@app.route("/api/profile-links", methods=["GET"])
def api_get_profile_links():
    """Get profile links for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_profile_links
    links = db_get_profile_links(email)
    return jsonify({"success": True, "links": links})


@app.route("/api/profile-links", methods=["POST"])
def api_save_profile_links():
    """Save profile links for a user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    links = data.get("links", [])
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_save_profile_links
    db_save_profile_links(email, links)
    return jsonify({"success": True})


@app.route("/api/notifications", methods=["GET"])
def api_get_notifications():
    """Get notifications for a user."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_get_notifications
    notifs = db_get_notifications(email)
    return jsonify({"success": True, "notifications": notifs})


@app.route("/api/notifications/read", methods=["POST"])
def api_mark_notifications_read():
    """Mark all notifications as read."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    from db import db_mark_notifications_read
    db_mark_notifications_read(email)
    return jsonify({"success": True})


@app.route("/api/query", methods=["POST"])
def api_submit_query():
    """Submit a user query/feedback."""
    data = request.get_json() or {}
    from db import db_save_query
    db_save_query(data)
    return jsonify({"success": True, "message": "Query submitted"})


@app.route("/api/admin/queries", methods=["GET"])
def api_admin_get_queries():
    """Get all user queries (admin only)."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    from db import db_get_queries
    queries = db_get_queries(limit=200)
    return jsonify({"success": True, "queries": queries})


@app.route("/api/admin/queries/status", methods=["POST"])
def api_admin_update_query_status():
    """Update query status (admin only)."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    data = request.get_json() or {}
    query_id = data.get("queryId")
    status = data.get("status", "resolved")
    if not query_id:
        return jsonify({"success": False, "error": "Query ID required"}), 400
    from db import db_update_query_status
    db_update_query_status(query_id, status)
    return jsonify({"success": True})


# ─── ADMIN API ENDPOINTS ───────────────────────────────────────────────────────

from functools import wraps
from security import hash_password, verify_password, generate_csrf_token

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Simple admin check - in production, use proper session/auth
        admin_email = request.headers.get("X-Admin-Email") or request.json.get("adminEmail") if request.is_json else None
        if not admin_email:
            return jsonify({"success": False, "error": "Admin authentication required"}), 401
        # Verify admin exists
        from db import db_get_admin_user
        admin = db_get_admin_user(admin_email)
        if not admin:
            return jsonify({"success": False, "error": "Invalid admin"}), 403
        return f(*args, **kwargs)
    return decorated

@app.route("/api/admin/staff", methods=["GET"])
def api_admin_get_staff():
    """Get all staff members."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    from db import db_get_staff_members
    staff = db_get_staff_members()
    return jsonify({"success": True, "staff": staff, "count": len(staff)})

@app.route("/api/admin/staff/add", methods=["POST"])
def api_admin_add_staff():
    """Add a new staff member."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    position = data.get("position", "").strip()
    department = data.get("department", "").strip()
    staff_role = data.get("staffRole", "staff").strip()
    phone = data.get("phone", "").strip()
    access = data.get("access", "").strip()
    
    if not email or not name:
        return jsonify({"success": False, "error": "Email and name required"}), 400
    
    from db import db_add_staff_member
    db_add_staff_member(email, name, position, department, staff_role, phone, "", admin_email, access)
    
    # Log to edit history
    from db import db_save_global_edit
    db_save_global_edit(admin_email, "staff_added", f"Added staff member {name} ({email}) as {staff_role}", {
        "staff_email": email, "name": name, "position": position, "department": department, "staff_role": staff_role
    })
    
    return jsonify({"success": True, "message": f"Staff {name} added"})

@app.route("/api/admin/staff/delete", methods=["POST"])
def api_admin_delete_staff():
    """Delete a staff member."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    
    from db import db_delete_staff_member, db_save_global_edit
    db_delete_staff_member(email)
    db_save_global_edit(admin_email, "staff_deleted", f"Deleted staff member {email}", {"staff_email": email})
    
    return jsonify({"success": True, "message": "Staff member deleted"})

@app.route("/api/admin/staff/access", methods=["POST"])
def api_admin_staff_access():
    """Toggle staff access (block/unblock)."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    access = data.get("access", "").strip()
    
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    
    from db import db_add_staff_member, db_save_global_edit
    # Update access field
    db_add_staff_member(email, "", "", "", "", "", "", "", admin_email, access)
    db_save_global_edit(admin_email, "staff_access_changed", f"Updated access for {email}: {access}", {"email": email, "access": access})
    
    return jsonify({"success": True})

@app.route("/api/admin/users", methods=["GET"])
def api_admin_get_users():
    """Get all users with full details for admin management."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    from db import db_get_all_users, db_get_user_security_settings, db_get_user_blocked_ips, db_is_it_team
    
    users = db_get_all_users()
    result = []
    for user in users:
        email = user.get("email")
        settings = db_get_user_security_settings(email)
        blocked_ips = db_get_user_blocked_ips(email)
        is_it = db_is_it_team(email)
        
        result.append({
            **user,
            "securitySettings": settings,
            "blockedIPs": blocked_ips,
            "isITTeam": is_it
        })
    
    return jsonify({"success": True, "users": result})

@app.route("/api/admin/user/update", methods=["POST"])
def api_admin_update_user():
    """Update user profile (name, phone, company, role, etc.)."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    updates = {k: v for k, v in data.items() if k not in ["email", "adminEmail", "password"]}
    
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    
    from db import db_update_user_profile
    success = db_update_user_profile(email, updates, admin_email)
    
    if success:
        return jsonify({"success": True, "message": "User updated"})
    else:
        return jsonify({"success": False, "error": "User not found"}), 404

@app.route("/api/admin/user/password", methods=["POST"])
def api_admin_reset_password():
    """Reset user password."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    new_password = data.get("password", "")
    
    if not email or not new_password:
        return jsonify({"success": False, "error": "Email and password required"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
    
    from db import db_update_user_password
    success = db_update_user_password(email, new_password, admin_email)
    
    if success:
        return jsonify({"success": True, "message": "Password reset successfully"})
    else:
        return jsonify({"success": False, "error": "User not found"}), 404

@app.route("/api/admin/user/block-ip", methods=["POST"])
def api_admin_block_ip():
    """Block an IP for a user."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    ip = data.get("ip", "").strip()
    
    if not email or not ip:
        return jsonify({"success": False, "error": "Email and IP required"}), 400
    
    from db import db_block_user_ip
    db_block_user_ip(email, ip, admin_email)
    return jsonify({"success": True, "message": f"IP {ip} blocked for {email}"})

@app.route("/api/admin/user/unblock-ip", methods=["POST"])
def api_admin_unblock_ip():
    """Unblock an IP for a user."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    ip = data.get("ip", "").strip()
    
    if not email or not ip:
        return jsonify({"success": False, "error": "Email and IP required"}), 400
    
    from db import db_unblock_user_ip
    db_unblock_user_ip(email, ip, admin_email)
    return jsonify({"success": True, "message": f"IP {ip} unblocked for {email}"})

@app.route("/api/admin/user/edit-history", methods=["GET"])
def api_admin_get_edit_history():
    """Get edit history for a user (admin view)."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    email = request.args.get("email", "").strip().lower()
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    
    from db import db_get_staff_edit_history, db_count_staff_edit_history
    history = db_get_staff_edit_history(email, limit, offset)
    total = db_count_staff_edit_history(email)
    
    return jsonify({"success": True, "history": history, "total": total})

@app.route("/api/admin/security/settings", methods=["GET"])
def api_admin_get_security_settings():
    """Get admin security settings."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    from db import db_get_admin_security_settings
    settings = db_get_admin_security_settings(admin_email)
    return jsonify({"success": True, "settings": settings})

@app.route("/api/admin/security/settings", methods=["POST"])
def api_admin_set_security_setting():
    """Set admin security setting."""
    admin_email = request.headers.get("X-Admin-Email") or (request.json.get("adminEmail") if request.is_json else None)
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    data = request.get_json() or {}
    key = data.get("key", "").strip()
    value = data.get("value", "")
    
    if not key:
        return jsonify({"success": False, "error": "Setting key required"}), 400
    
    from db import db_set_admin_security_setting
    db_set_admin_security_setting(admin_email, key, value)
    return jsonify({"success": True})

@app.route("/api/admin/it-team/staff", methods=["GET"])
def api_it_team_get_staff():
    """Get all staff members for IT team view."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    from db import db_get_staff_members, db_is_it_team
    if not db_is_it_team(admin_email):
        return jsonify({"success": False, "error": "IT Team access required"}), 403
    
    staff = db_get_staff_members()
    return jsonify({"success": True, "staff": staff, "count": len(staff)})

@app.route("/api/admin/calendar/events", methods=["GET"])
def api_admin_calendar_events():
    """Get calendar events with colors."""
    admin_email = request.args.get("adminEmail") or request.headers.get("X-Admin-Email")
    if not admin_email:
        return jsonify({"success": False, "error": "Admin email required"}), 401
    
    # Return mock events with colors - in production, fetch from database
    events = [
        {"id": 1, "title": "Team Standup", "start": "2026-06-28T09:00:00", "end": "2026-06-28T09:30:00", "color": "#6366f1", "type": "meeting"},
        {"id": 2, "title": "Sprint Review", "start": "2026-06-28T14:00:00", "end": "2026-06-28T15:00:00", "color": "#06b6d4", "type": "review"},
        {"id": 3, "title": "Security Audit", "start": "2026-06-29T10:00:00", "end": "2026-06-29T12:00:00", "color": "#f43f5e", "type": "security"},
        {"id": 4, "title": "Deploy to Prod", "start": "2026-06-30T16:00:00", "end": "2026-06-30T17:00:00", "color": "#10b981", "type": "deploy"},
        {"id": 5, "title": "IT Maintenance", "start": "2026-07-01T22:00:00", "end": "2026-07-02T02:00:00", "color": "#f59e0b", "type": "maintenance"},
    ]
    return jsonify({"success": True, "events": events})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
