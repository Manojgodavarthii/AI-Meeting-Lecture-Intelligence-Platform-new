import mysql.connector
import mysql.connector.pooling
import json
import time
import datetime
from security import encrypt_profile, decrypt_profile, hash_password

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "admin",
    "database": "echoaction"
}

_pool = None
def get_conn():
    global _pool
    if _pool is None:
        _pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="echoaction_pool", pool_size=5,
            pool_reset_session=True, **DB_CONFIG
        )
    return _pool.get_connection()

# ─── SCHEMA INIT & MIGRATION ──────────────────────────────────────────────────

def db_init_auth_tables():
    """Create registration and login_history tables; migrate existing passwords."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_registration (
                email VARCHAR(191) PRIMARY KEY,
                password VARCHAR(512) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_login_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(191) NOT NULL,
                device_name VARCHAR(255) DEFAULT '',
                ip_address VARCHAR(64) DEFAULT '',
                user_agent TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success TINYINT(1) DEFAULT 1,
                INDEX idx_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Migrate existing passwords from ea_users to ea_registration
        try:
            cur.execute("SELECT email, password FROM ea_users WHERE password IS NOT NULL AND password != ''")
            rows = cur.fetchall()
            for email, pwd in rows:
                cur.execute("INSERT IGNORE INTO ea_registration (email, password) VALUES (%s, %s)", (email, pwd))
            conn.commit()
        except Exception:
            conn.rollback()
        # Drop password column from ea_users (now in registration table)
        try:
            cur.execute("ALTER TABLE ea_users DROP COLUMN password")
            conn.commit()
        except Exception:
            conn.rollback()
        print("[DB] Auth tables initialized.")
        # Also create security events table
        try:
            _create_security_table(cur)
            conn.commit()
        except Exception:
            conn.rollback()
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_query_submissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(191) NOT NULL,
                    email VARCHAR(191) DEFAULT '',
                    phone VARCHAR(64) DEFAULT '',
                    type VARCHAR(32) DEFAULT 'feedback',
                    message TEXT,
                    rating VARCHAR(16) DEFAULT '',
                    project_type VARCHAR(64) DEFAULT '',
                    issue_type VARCHAR(64) DEFAULT '',
                    feedback_on VARCHAR(128) DEFAULT '',
                    status VARCHAR(32) DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        except Exception:
            conn.rollback()
        # Ensure ea_users table exists with user_id as PK
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(191) DEFAULT '',
                    email VARCHAR(191) NOT NULL,
                    role VARCHAR(64) DEFAULT '',
                    company VARCHAR(255) DEFAULT '',
                    phone VARCHAR(128) DEFAULT '',
                    bio TEXT,
                    linkedin VARCHAR(255) DEFAULT '',
                    timezone VARCHAR(64) DEFAULT 'UTC',
                    avatar LONGTEXT,
                    profile_link_slug VARCHAR(255) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        except Exception:
            conn.rollback()
        # Migrate old table if it exists with email-as-PK
        try:
            cur.execute("SHOW COLUMNS FROM ea_users LIKE 'id'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE ea_users ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST")
                cur.execute("ALTER TABLE ea_users MODIFY email VARCHAR(191) NOT NULL")
                conn.commit()
                print("[DB] Added id column to ea_users")
        except Exception:
            conn.rollback()
        # Add UNIQUE index on email if not present
        try:
            cur.execute("SHOW INDEX FROM ea_users WHERE Column_name='email' AND Non_unique=0")
            if not cur.fetchone():
                cur.execute("CREATE UNIQUE INDEX uk_email ON ea_users(email)")
                conn.commit()
        except Exception:
            conn.rollback()
        # Migrate existing avatar column to LONGTEXT
        try:
            cur.execute("ALTER TABLE ea_users MODIFY avatar LONGTEXT")
            conn.commit()
        except Exception:
            conn.rollback()

        # ── DB NORMALIZATION: Add user_id FK columns to all tables ──
        _user_id_tables = {
            "ea_meetings": "user_email VARCHAR(255)",
            "ea_activities": "user_email VARCHAR(255)",
            "ea_settings": "user_email VARCHAR(255)",
            "ea_notifications": "user_email VARCHAR(255)",
            "ea_followers": "user_email VARCHAR(255)",
            "ea_profile_links": "user_email VARCHAR(255)",
            "ea_edit_history": "user_email VARCHAR(255)",
            "ea_global_edit_history": "user_email VARCHAR(255)",
            "ea_login_history": "email VARCHAR(191)",
            "ea_security_events": "email VARCHAR(191)",
            "ea_query_submissions": "email VARCHAR(191)"
        }
        for tbl, ref_col in _user_id_tables.items():
            try:
                cur.execute(f"ALTER TABLE {tbl} ADD COLUMN user_id INT DEFAULT NULL")
                conn.commit()
            except Exception:
                conn.rollback()
        # Migrate existing data: populate user_id from email matches
        try:
            cur.execute("SELECT id, email FROM ea_users")
            for uid, uemail in cur.fetchall():
                for tbl, ref_col in _user_id_tables.items():
                    try:
                        cur.execute(f"UPDATE {tbl} SET user_id=%s WHERE user_id IS NULL AND {ref_col}=%s", (uid, uemail))
                    except Exception:
                        pass
            conn.commit()
            print("[DB] Populated user_id references.")
        except Exception:
            conn.rollback()
        # Create admin users table
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_admin_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(191) NOT NULL UNIQUE,
                    password VARCHAR(512) NOT NULL,
                    name VARCHAR(191) DEFAULT 'Admin',
                    role VARCHAR(64) DEFAULT 'super_admin',
                    avatar VARCHAR(512) DEFAULT '',
                    permissions TEXT,
                    last_login DATETIME DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            # Add missing columns if upgrading from old schema
            for col, col_def in [
                ("role", "VARCHAR(64) DEFAULT 'super_admin'"),
                ("avatar", "VARCHAR(512) DEFAULT ''"),
                ("permissions", "TEXT"),
                ("last_login", "DATETIME DEFAULT NULL")
            ]:
                try:
                    cur.execute(f"ALTER TABLE ea_admin_users ADD COLUMN {col} {col_def}")
                    conn.commit()
                except Exception:
                    conn.rollback()
            # Seed default admin if not exists
            cur.execute("SELECT COUNT(*) AS cnt FROM ea_admin_users")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO ea_admin_users (email, password, name, role, permissions) VALUES (%s, %s, %s, %s, %s)",
                    ("admin@echoaction.ai", hash_password("Admin@123"), "Super Admin", "super_admin", '{"users":"rw","queries":"rw","security":"rw","settings":"rw"}'))
                conn.commit()
                print("[DB] Default admin seeded: admin@echoaction.ai / Admin@123")
        except Exception as e:
            conn.rollback()
            print(f"[WARN] Could not create admin table: {e}")

        # Create root admins table (main admin login)
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_root_admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(191) NOT NULL UNIQUE,
                    password VARCHAR(512) NOT NULL,
                    name VARCHAR(191) DEFAULT 'Main Admin',
                    avatar VARCHAR(512) DEFAULT '',
                    last_login DATETIME DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        except Exception:
            conn.rollback()
        # Seed default root admin if not exists
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM ea_root_admins")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO ea_root_admins (email, password, name) VALUES (%s, %s, %s)",
                    ("godaverthinagamanojbalaji@gmail.com", hash_password("Manojbalaji@752003"), "Main Admin"))
                conn.commit()
                print("[DB] Root admin seeded: godaverthinagamanojbalaji@gmail.com")
        except Exception:
            conn.rollback()
        # Add admin_type, is_active, created_by columns to ea_admin_users
        for col, col_def in [
            ("admin_type", "VARCHAR(16) DEFAULT 'sub'"),
            ("is_active", "TINYINT(1) DEFAULT 1"),
            ("created_by", "VARCHAR(191) DEFAULT ''")
        ]:
            try:
                cur.execute(f"ALTER TABLE ea_admin_users ADD COLUMN {col} {col_def}")
                conn.commit()
            except Exception:
                conn.rollback()

        # Create user security settings table (per-user toggles)
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_user_security_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT DEFAULT NULL,
                    user_email VARCHAR(191) NOT NULL,
                    setting_key VARCHAR(64) NOT NULL,
                    setting_value VARCHAR(16) DEFAULT 'on',
                    updated_by VARCHAR(191) DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_user_setting (user_email, setting_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        except Exception:
            conn.rollback()

        # Create admin security settings table (IP blocking, etc.)
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_admin_security_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    admin_email VARCHAR(191) NOT NULL,
                    setting_key VARCHAR(64) NOT NULL,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_admin_setting (admin_email, setting_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        except Exception:
            conn.rollback()

        # Create staff members table with role categories
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_staff_members (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT DEFAULT NULL,
                    email VARCHAR(191) NOT NULL UNIQUE,
                    name VARCHAR(191) DEFAULT '',
                    position VARCHAR(128) DEFAULT '',
                    department VARCHAR(128) DEFAULT '',
                    staff_role VARCHAR(64) DEFAULT 'staff',
                    phone VARCHAR(64) DEFAULT '',
                    avatar LONGTEXT,
                    created_by VARCHAR(191) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access VARCHAR(512) DEFAULT '',
                    blocked_ips TEXT DEFAULT '',
                    active TINYINT(1) DEFAULT 1,
                    inactive_reason VARCHAR(512) DEFAULT '',
                    inactive_letter LONGTEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            # Add columns if they don't exist (for existing tables)
            try: cur.execute("ALTER TABLE ea_staff_members ADD COLUMN active TINYINT(1) DEFAULT 1")
            except: pass
            try: cur.execute("ALTER TABLE ea_staff_members ADD COLUMN inactive_reason VARCHAR(512) DEFAULT ''")
            except: pass
            try: cur.execute("ALTER TABLE ea_staff_members ADD COLUMN inactive_letter LONGTEXT")
            except: pass
            # Messages table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ea_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    from_email VARCHAR(191) NOT NULL,
                    to_email VARCHAR(191) NOT NULL,
                    subject VARCHAR(255) DEFAULT '',
                    body TEXT,
                    is_read TINYINT(1) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
        except Exception:
            conn.rollback()
        # Seed default staff members if table is empty
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM ea_staff_members")
            if cur.fetchone()[0] == 0:
                seed_staff = [
                    ("alex.wong@company.com", "Alex Wong", "Senior Developer", "Engineering", "staff", "+1-555-0101"),
                    ("maria.garcia@company.com", "Maria Garcia", "QA Lead", "Quality Assurance", "staff", "+1-555-0102"),
                    ("james.chen@company.com", "James Chen", "DevOps Engineer", "Infrastructure", "staff", "+1-555-0103"),
                    ("priya.shah@company.com", "Priya Shah", "Product Manager", "Product", "staff", "+1-555-0104"),
                ]
                for email, name, position, department, staff_role, phone in seed_staff:
                    cur.execute("""
                        INSERT INTO ea_staff_members (email, name, position, department, staff_role, phone, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (email, name, position, department, staff_role, phone, "system"))
                conn.commit()
                print("[DB] Seeded 4 staff members")
        except Exception:
            conn.rollback()

        # Initialize enterprise tables
        try:
            db_init_enterprise_tables()
        except Exception as e:
            print(f"[DB] Enterprise table init deferred: {e}")

    finally:
        cur.close(); conn.close()

# ─── ENTERPRISE SCHEMA INIT (all tables) ─────────────────────────────────────

def db_init_enterprise_tables():
    """Create all enterprise tables following the entity-relationship-optimised schema."""
    conn = get_conn(); cur = conn.cursor()
    try:
        # ── MASTER / LOOKUP TABLES ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_roles (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(64) NOT NULL UNIQUE,
                description VARCHAR(255) DEFAULT '',
                is_active TINYINT(1) DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_departments (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(128) NOT NULL UNIQUE,
                code VARCHAR(32) UNIQUE DEFAULT NULL,
                head_user_id INT DEFAULT NULL,
                is_active TINYINT(1) DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_teams (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(128) NOT NULL UNIQUE,
                department_id SMALLINT DEFAULT NULL,
                lead_user_id INT DEFAULT NULL,
                is_active TINYINT(1) DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_status_master (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(64) NOT NULL,
                name VARCHAR(64) NOT NULL,
                color VARCHAR(32) DEFAULT '#8899b0',
                sort_order SMALLINT DEFAULT 0,
                INDEX idx_status_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_types (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(128) NOT NULL UNIQUE,
                icon VARCHAR(64) DEFAULT 'fa-video',
                default_duration SMALLINT DEFAULT 30
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_notification_types (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(64) NOT NULL UNIQUE,
                icon VARCHAR(64) DEFAULT 'fa-bell',
                color VARCHAR(32) DEFAULT '#818cf8'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_permission_types (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(64) NOT NULL UNIQUE,
                code VARCHAR(64) NOT NULL UNIQUE,
                module VARCHAR(64) DEFAULT 'general'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── USERS & AUTH ────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_user_roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role_id SMALLINT NOT NULL,
                granted_by INT DEFAULT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ur_user (user_id),
                INDEX idx_ur_role (role_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_employee_profiles (
                user_id INT PRIMARY KEY,
                job_title VARCHAR(128) DEFAULT '',
                company VARCHAR(255) DEFAULT '',
                employee_id VARCHAR(64) UNIQUE DEFAULT NULL,
                manager_user_id INT DEFAULT NULL,
                date_of_joining DATETIME DEFAULT NULL,
                employment_type VARCHAR(32) DEFAULT 'full_time',
                work_location VARCHAR(128) DEFAULT ''
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_student_profiles (
                user_id INT PRIMARY KEY,
                student_id VARCHAR(64) UNIQUE DEFAULT NULL,
                course VARCHAR(128) DEFAULT '',
                semester VARCHAR(16) DEFAULT '',
                year_of_study SMALLINT DEFAULT 1,
                advisor_user_id INT DEFAULT NULL,
                enrollment_date DATETIME DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_staff_profiles (
                user_id INT PRIMARY KEY,
                staff_id VARCHAR(64) UNIQUE DEFAULT NULL,
                designation VARCHAR(128) DEFAULT '',
                shift VARCHAR(32) DEFAULT 'general',
                supervisor_user_id INT DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_admin_profiles (
                user_id INT PRIMARY KEY,
                access_level VARCHAR(32) DEFAULT 'admin',
                mfa_enabled TINYINT(1) DEFAULT 0,
                session_timeout_min SMALLINT DEFAULT 30,
                ip_whitelist JSON DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Add user_id FK to ea_users if not exists
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN role_id SMALLINT DEFAULT 1")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN department_id SMALLINT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN team_id SMALLINT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN password_hash VARCHAR(512) DEFAULT ''")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN display_name VARCHAR(255) DEFAULT ''")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN bio TEXT")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN is_deleted TINYINT(1) DEFAULT 0")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN deleted_at DATETIME DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN last_login_at DATETIME DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        except: pass

        # ── SESSIONS ────────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(512) NOT NULL UNIQUE,
                ip_address VARCHAR(64) DEFAULT '',
                device_info VARCHAR(255) DEFAULT '',
                is_active TINYINT(1) DEFAULT 1,
                expires_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_us_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── LOGIN HISTORY ARCHIVE ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_login_history_archive (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                device_name VARCHAR(255) DEFAULT '',
                ip_address VARCHAR(64) DEFAULT '',
                user_agent TEXT,
                login_time DATETIME DEFAULT NULL,
                success TINYINT(1) DEFAULT 1,
                session_id VARCHAR(128) DEFAULT NULL,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_lha_user (user_id),
                INDEX idx_lha_time (login_time),
                INDEX idx_lha_archived (archived_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── MEETINGS MODULE ─────────────────────────────────────────────────
        # Migrate ea_meetings: add missing columns
        for col, col_def in [
            ("host_user_id", "INT DEFAULT NULL"),
            ("meeting_type_id", "SMALLINT DEFAULT NULL"),
            ("status_id", "SMALLINT DEFAULT NULL"),
            ("scheduled_date", "DATETIME DEFAULT NULL"),
            ("duration_minutes", "SMALLINT DEFAULT 30"),
            ("timezone", "VARCHAR(64) DEFAULT 'UTC'"),
            ("location", "VARCHAR(255) DEFAULT ''"),
            ("agenda", "TEXT"),
            ("is_deleted", "TINYINT(1) DEFAULT 0"),
            ("deleted_at", "DATETIME DEFAULT NULL"),
        ]:
            try: cur.execute(f"ALTER TABLE ea_meetings ADD COLUMN {col} {col_def}")
            except: pass
        # Rename date->scheduled_date if needed
        try:
            cur.execute("SHOW COLUMNS FROM ea_meetings LIKE 'date'")
            if cur.fetchone():
                cur.execute("UPDATE ea_meetings SET scheduled_date = CONCAT(date, ' 00:00:00') WHERE scheduled_date IS NULL AND date IS NOT NULL")
        except: pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_participants (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                user_id INT NOT NULL,
                status_id SMALLINT DEFAULT NULL,
                rsvp_status VARCHAR(32) DEFAULT 'pending',
                attended TINYINT(1) DEFAULT 0,
                joined_at DATETIME DEFAULT NULL,
                left_at DATETIME DEFAULT NULL,
                UNIQUE KEY uq_meeting_participant (meeting_id, user_id),
                INDEX idx_mp_meeting (meeting_id),
                INDEX idx_mp_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_recordings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                storage_provider VARCHAR(64) DEFAULT 'local',
                file_size_bytes BIGINT DEFAULT 0,
                mime_type VARCHAR(64) DEFAULT 'audio/mp4',
                duration_sec INT DEFAULT 0,
                processed TINYINT(1) DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_mr_meeting (meeting_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_recordings_archive (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT DEFAULT NULL,
                file_path VARCHAR(512) NOT NULL,
                storage_provider VARCHAR(64) DEFAULT 'local',
                file_size_bytes BIGINT DEFAULT 0,
                mime_type VARCHAR(64) DEFAULT 'audio/mp4',
                duration_sec INT DEFAULT 0,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_mra_meeting (meeting_id),
                INDEX idx_mra_archived (archived_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_transcripts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                content TEXT NOT NULL,
                language VARCHAR(16) DEFAULT 'en',
                word_count INT DEFAULT 0,
                speaker_diarization JSON DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_mt_meeting (meeting_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_transcripts_archive (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT DEFAULT NULL,
                content TEXT NOT NULL,
                language VARCHAR(16) DEFAULT 'en',
                word_count INT DEFAULT 0,
                speaker_diarization JSON DEFAULT NULL,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_mta_meeting (meeting_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_summaries (
                meeting_id INT PRIMARY KEY,
                overview TEXT,
                key_points JSON DEFAULT NULL,
                decisions JSON DEFAULT NULL,
                ai_generated TINYINT(1) DEFAULT 1,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_action_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                assignee_user_id INT DEFAULT NULL,
                priority VARCHAR(16) DEFAULT 'medium',
                due_date DATETIME DEFAULT NULL,
                status_id SMALLINT DEFAULT NULL,
                is_completed TINYINT(1) DEFAULT 0,
                completed_at DATETIME DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_mai_meeting (meeting_id),
                INDEX idx_mai_assignee (assignee_user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_replays (
                meeting_id INT PRIMARY KEY,
                replay_data JSON DEFAULT NULL,
                highlights JSON DEFAULT NULL,
                replay_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                tag VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_meeting_tag (meeting_id, tag),
                INDEX idx_mt_tag (tag)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                user_id INT NOT NULL,
                rating SMALLINT DEFAULT 5,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_meeting_feedback (meeting_id, user_id),
                INDEX idx_mf_meeting (meeting_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── COMMUNICATION MODULE ─────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_conversations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) DEFAULT '',
                conversation_type VARCHAR(32) DEFAULT 'direct',
                created_by INT DEFAULT NULL,
                is_group TINYINT(1) DEFAULT 0,
                is_deleted TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_conversation_members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT NOT NULL,
                user_id INT NOT NULL,
                last_read_at DATETIME DEFAULT NULL,
                is_muted TINYINT(1) DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_conversation_member (conversation_id, user_id),
                INDEX idx_cm_conversation (conversation_id),
                INDEX idx_cm_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Migrate ea_messages to new schema
        try: cur.execute("ALTER TABLE ea_messages ADD COLUMN conversation_id INT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_messages ADD COLUMN message_type VARCHAR(32) DEFAULT 'text'")
        except: pass
        try: cur.execute("ALTER TABLE ea_messages ADD COLUMN is_deleted TINYINT(1) DEFAULT 0")
        except: pass
        try: cur.execute("ALTER TABLE ea_messages ADD COLUMN edited_at DATETIME DEFAULT NULL")
        except: pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_message_attachments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message_id BIGINT NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                storage_provider VARCHAR(64) DEFAULT 'local',
                filename VARCHAR(255) NOT NULL,
                mime_type VARCHAR(64) DEFAULT '',
                file_size_bytes BIGINT DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ma_message (message_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Migrate ea_notifications to new schema
        try: cur.execute("ALTER TABLE ea_notifications ADD COLUMN type_id SMALLINT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_notifications ADD COLUMN title VARCHAR(255) DEFAULT ''")
        except: pass
        try: cur.execute("ALTER TABLE ea_notifications ADD COLUMN body TEXT")
        except: pass
        try: cur.execute("ALTER TABLE ea_notifications ADD COLUMN link VARCHAR(512) DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_notifications ADD COLUMN read_at DATETIME DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_notifications ADD COLUMN is_archived TINYINT(1) DEFAULT 0")
        except: pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_notifications_archive (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                type_id SMALLINT DEFAULT NULL,
                title VARCHAR(255) NOT NULL,
                body TEXT,
                link VARCHAR(512) DEFAULT NULL,
                is_read TINYINT(1) DEFAULT 0,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_na_user (user_id),
                INDEX idx_na_archived (archived_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_announcements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                body TEXT,
                created_by INT DEFAULT NULL,
                target_role_id SMALLINT DEFAULT NULL,
                priority VARCHAR(16) DEFAULT 'normal',
                is_active TINYINT(1) DEFAULT 1,
                expires_at DATETIME DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── CALENDAR MODULE ──────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_calendar_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                event_date DATETIME NOT NULL,
                end_date DATETIME DEFAULT NULL,
                event_type VARCHAR(32) DEFAULT 'event',
                color VARCHAR(32) DEFAULT '#818cf8',
                is_all_day TINYINT(1) DEFAULT 0,
                is_deleted TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ce_user (user_id),
                INDEX idx_ce_date (event_date),
                INDEX idx_ce_user_date (user_id, event_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_calendar_attendees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT NOT NULL,
                user_id INT NOT NULL,
                status VARCHAR(32) DEFAULT 'pending',
                UNIQUE KEY uq_calendar_attendee (event_id, user_id),
                INDEX idx_ca_event (event_id),
                INDEX idx_ca_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_holidays (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                date DATETIME NOT NULL,
                type VARCHAR(32) DEFAULT 'public',
                is_recurring TINYINT(1) DEFAULT 0,
                created_by INT DEFAULT NULL,
                INDEX idx_hol_date (date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                remind_at DATETIME NOT NULL,
                is_sent TINYINT(1) DEFAULT 0,
                sent_at DATETIME DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_rem_user (user_id),
                INDEX idx_rem_time (remind_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── PROJECTS & TASKS MODULE ─────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status_id SMALLINT DEFAULT NULL,
                department_id SMALLINT DEFAULT NULL,
                owner_user_id INT DEFAULT NULL,
                start_date DATETIME DEFAULT NULL,
                end_date DATETIME DEFAULT NULL,
                priority VARCHAR(16) DEFAULT 'medium',
                is_deleted TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_proj_status (status_id),
                INDEX idx_proj_owner (owner_user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_project_members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                user_id INT NOT NULL,
                role VARCHAR(32) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_project_member (project_id, user_id),
                INDEX idx_pm_project (project_id),
                INDEX idx_pm_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Migrate ea_tasks to new schema
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN project_id INT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN status_id SMALLINT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN is_completed TINYINT(1) DEFAULT 0")
        except: pass
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN completed_at DATETIME DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN estimated_hours FLOAT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN is_deleted TINYINT(1) DEFAULT 0")
        except: pass
        try: cur.execute("ALTER TABLE ea_tasks ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        except: pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_task_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                user_id INT DEFAULT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_tc_task (task_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_project_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                storage_provider VARCHAR(64) DEFAULT 'local',
                file_size_bytes BIGINT DEFAULT 0,
                uploaded_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pd_project (project_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_project_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                type VARCHAR(32) DEFAULT 'weekly',
                generated_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pr_project (project_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_project_health (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                health_status VARCHAR(32) DEFAULT 'on_track',
                metrics JSON DEFAULT NULL,
                notes TEXT,
                recorded_by INT DEFAULT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ph_project (project_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_project_risks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                description TEXT NOT NULL,
                impact VARCHAR(32) DEFAULT 'medium',
                probability VARCHAR(32) DEFAULT 'medium',
                mitigation TEXT,
                status_id SMALLINT DEFAULT NULL,
                raised_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_prisk_project (project_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── AI MODULE ────────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_ai_chat_history (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id VARCHAR(128) DEFAULT NULL,
                role VARCHAR(16) NOT NULL,
                content TEXT NOT NULL,
                tokens_used INT DEFAULT 0,
                model VARCHAR(64) DEFAULT 'default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ai_user (user_id),
                INDEX idx_ai_session (session_id),
                INDEX idx_ai_created (created_at),
                INDEX idx_ai_user_session (user_id, session_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_ai_chat_history_archive (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                session_id VARCHAR(128) DEFAULT NULL,
                role VARCHAR(16) NOT NULL,
                content TEXT NOT NULL,
                tokens_used INT DEFAULT 0,
                model VARCHAR(64) DEFAULT 'default',
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_aia_user (user_id),
                INDEX idx_aia_archived (archived_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_ai_commands (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                command VARCHAR(255) NOT NULL,
                response TEXT,
                module VARCHAR(64) DEFAULT 'general',
                execution_time_ms INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_aic_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_knowledge_categories (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(128) NOT NULL UNIQUE,
                icon VARCHAR(64) DEFAULT 'fa-book',
                parent_id SMALLINT DEFAULT NULL,
                sort_order SMALLINT DEFAULT 0,
                is_active TINYINT(1) DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_knowledge_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id SMALLINT DEFAULT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT,
                file_path VARCHAR(512) DEFAULT NULL,
                tags JSON DEFAULT NULL,
                is_published TINYINT(1) DEFAULT 1,
                uploaded_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_kd_category (category_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_organization_brain (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_type VARCHAR(64) NOT NULL,
                entity_id INT NOT NULL,
                brain_key VARCHAR(128) NOT NULL,
                brain_value TEXT,
                metadata JSON DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_brain_entity_key (entity_type, entity_id, brain_key),
                INDEX idx_ob_entity (entity_type, entity_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_meeting_ai_insights (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                insight_type VARCHAR(64) NOT NULL,
                content TEXT NOT NULL,
                confidence FLOAT DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_mai_meeting (meeting_id),
                INDEX idx_mai_type (insight_type),
                INDEX idx_mai_meeting_type (meeting_id, insight_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_search_history (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                query VARCHAR(255) NOT NULL,
                result_count INT DEFAULT 0,
                search_type VARCHAR(32) DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sh_user (user_id),
                INDEX idx_sh_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── ANALYTICS MODULE ─────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_dashboard_metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                metric_key VARCHAR(128) NOT NULL,
                metric_value JSON NOT NULL,
                period VARCHAR(32) DEFAULT 'daily',
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_dashboard_metric (user_id, metric_key, period),
                INDEX idx_dm_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_analytics_cache (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cache_key VARCHAR(255) NOT NULL UNIQUE,
                cache_data JSON NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ac_key (cache_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_historical_statistics (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                stat_key VARCHAR(128) NOT NULL,
                stat_value JSON NOT NULL,
                period VARCHAR(32) NOT NULL,
                period_start DATETIME NOT NULL,
                period_end DATETIME NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_hs_key (stat_key),
                INDEX idx_hs_period (period_start, period_end)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_report_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                report_type VARCHAR(64) NOT NULL,
                parameters JSON DEFAULT NULL,
                file_path VARCHAR(512) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_rh_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── SUPPORT MODULE ───────────────────────────────────────────────────
        # Migrate ea_query_submissions
        try: cur.execute("ALTER TABLE ea_query_submissions ADD COLUMN user_id INT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_query_submissions ADD COLUMN subject VARCHAR(255) DEFAULT ''")
        except: pass
        try: cur.execute("ALTER TABLE ea_query_submissions ADD COLUMN category VARCHAR(64) DEFAULT 'general'")
        except: pass
        try: cur.execute("ALTER TABLE ea_query_submissions ADD COLUMN assigned_to INT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_query_submissions ADD COLUMN is_deleted TINYINT(1) DEFAULT 0")
        except: pass
        try: cur.execute("ALTER TABLE ea_query_submissions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        except: pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_tickets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query_id INT DEFAULT NULL,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(64) DEFAULT 'technical',
                priority VARCHAR(16) DEFAULT 'medium',
                status_id SMALLINT DEFAULT NULL,
                assigned_to INT DEFAULT NULL,
                is_deleted TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_tkt_user (user_id),
                INDEX idx_tkt_status (status_id),
                INDEX idx_tkt_assignee (assigned_to)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_ticket_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticket_id INT NOT NULL,
                user_id INT DEFAULT NULL,
                body TEXT NOT NULL,
                is_internal TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tc_ticket (ticket_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_ticket_attachments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticket_id INT NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                mime_type VARCHAR(64) DEFAULT '',
                file_size_bytes BIGINT DEFAULT 0,
                uploaded_by INT DEFAULT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ta_ticket (ticket_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_user_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                request_type VARCHAR(64) NOT NULL,
                description TEXT,
                status_id SMALLINT DEFAULT NULL,
                reviewed_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_urq_user (user_id),
                INDEX idx_urq_status (status_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                rating SMALLINT DEFAULT 5,
                message TEXT,
                category VARCHAR(64) DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── SECURITY MODULE ──────────────────────────────────────────────────
        # Migrate ea_security_events
        try: cur.execute("ALTER TABLE ea_security_events ADD COLUMN user_id INT DEFAULT NULL")
        except: pass
        try: cur.execute("ALTER TABLE ea_security_events ADD COLUMN source VARCHAR(64) DEFAULT 'system'")
        except: pass
        try: cur.execute("ALTER TABLE ea_security_events MODIFY id BIGINT AUTO_INCREMENT")
        except: pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_security_events_archive (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                event_type VARCHAR(64) NOT NULL,
                ip_address VARCHAR(64) DEFAULT '',
                details JSON DEFAULT NULL,
                severity VARCHAR(16) DEFAULT 'info',
                source VARCHAR(64) DEFAULT 'system',
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sea_type (event_type),
                INDEX idx_sea_archived (archived_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_failed_logins (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(191) NOT NULL,
                ip_address VARCHAR(64) DEFAULT '',
                attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason VARCHAR(64) DEFAULT 'invalid_password',
                INDEX idx_fl_email (email),
                INDEX idx_fl_time (attempt_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_blocked_devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                device_fingerprint VARCHAR(255) NOT NULL,
                device_name VARCHAR(255) DEFAULT '',
                reason VARCHAR(255) DEFAULT '',
                blocked_by INT DEFAULT NULL,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active TINYINT(1) DEFAULT 1,
                INDEX idx_bd_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_device_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                device_fingerprint VARCHAR(255) NOT NULL,
                device_name VARCHAR(255) DEFAULT '',
                ip_address VARCHAR(64) DEFAULT '',
                user_agent TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_trusted TINYINT(1) DEFAULT 0,
                INDEX idx_dh_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_access_logs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                action VARCHAR(128) NOT NULL,
                resource VARCHAR(255) DEFAULT NULL,
                ip_address VARCHAR(64) DEFAULT '',
                user_agent TEXT,
                success TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_al_user (user_id),
                INDEX idx_al_action (action),
                INDEX idx_al_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_security_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(128) NOT NULL UNIQUE,
                setting_value JSON NOT NULL,
                description VARCHAR(255) DEFAULT '',
                updated_by INT DEFAULT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── ADMINISTRATION MODULE ────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_organizations (
                id SMALLINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                code VARCHAR(32) UNIQUE DEFAULT NULL,
                domain VARCHAR(255) DEFAULT NULL,
                logo_path VARCHAR(512) DEFAULT NULL,
                contact_email VARCHAR(191) DEFAULT '',
                contact_phone VARCHAR(64) DEFAULT '',
                address TEXT,
                is_active TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_system_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(128) NOT NULL UNIQUE,
                setting_value JSON NOT NULL,
                module VARCHAR(64) DEFAULT 'general',
                description VARCHAR(255) DEFAULT '',
                updated_by INT DEFAULT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_automation_workflows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                trigger_type VARCHAR(64) NOT NULL,
                trigger_config JSON DEFAULT NULL,
                actions JSON NOT NULL,
                is_active TINYINT(1) DEFAULT 1,
                last_run_at DATETIME DEFAULT NULL,
                created_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_workflow_runs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                workflow_id INT NOT NULL,
                status_id SMALLINT DEFAULT NULL,
                triggered_by INT DEFAULT NULL,
                input_data JSON DEFAULT NULL,
                output_data JSON DEFAULT NULL,
                error_log TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME DEFAULT NULL,
                INDEX idx_wr_workflow (workflow_id),
                INDEX idx_wr_status (status_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_audit_logs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                action VARCHAR(128) NOT NULL,
                entity_type VARCHAR(64) DEFAULT NULL,
                entity_id INT DEFAULT NULL,
                old_values JSON DEFAULT NULL,
                new_values JSON DEFAULT NULL,
                ip_address VARCHAR(64) DEFAULT '',
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_al_user (user_id),
                INDEX idx_al_action (action),
                INDEX idx_al_entity (entity_type, entity_id),
                INDEX idx_al_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_audit_logs_archive (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                action VARCHAR(128) NOT NULL,
                entity_type VARCHAR(64) DEFAULT NULL,
                entity_id INT DEFAULT NULL,
                old_values JSON DEFAULT NULL,
                new_values JSON DEFAULT NULL,
                ip_address VARCHAR(64) DEFAULT '',
                user_agent TEXT,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ala_user (user_id),
                INDEX idx_ala_archived (archived_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_integrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                provider VARCHAR(64) NOT NULL,
                config JSON DEFAULT NULL,
                is_active TINYINT(1) DEFAULT 1,
                last_sync_at DATETIME DEFAULT NULL,
                created_by INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── SEED MASTER DATA ─────────────────────────────────────────────────
        # Seed default roles
        for role_name in ("employee", "student", "staff", "admin", "super_admin"):
            cur.execute("INSERT IGNORE INTO ea_roles (name) VALUES (%s)", (role_name,))
        # Seed default statuses
        for cat, names in [
            ("meeting", ["scheduled", "ongoing", "completed", "cancelled"]),
            ("task", ["pending", "in_progress", "completed", "overdue"]),
            ("ticket", ["open", "assigned", "pending", "closed", "escalated", "encapsulated"]),
            ("general", ["active", "inactive", "archived"]),
        ]:
            for i, n in enumerate(names):
                cur.execute("INSERT IGNORE INTO ea_status_master (category, name, sort_order) VALUES (%s, %s, %s)", (cat, n, i))
        # Seed default meeting types
        for mt in ("Standup", "Sprint Planning", "Design Review", "Client Call", "Retrospective", "One-on-One", "Workshop", "Presentation"):
            cur.execute("INSERT IGNORE INTO ea_meeting_types (name) VALUES (%s)", (mt,))
        # Seed default notification types
        for nt in ("info", "warning", "success", "error", "mention", "reminder", "announcement"):
            cur.execute("INSERT IGNORE INTO ea_notification_types (name) VALUES (%s)", (nt,))

        conn.commit()
        print("[DB] Enterprise tables initialized successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[DB] Error initializing enterprise tables: {e}")
        raise e
    finally:
        cur.close(); conn.close()

# ─── DB NORMALIZATION HELPER ────────────────────────────────────────────────

def _get_uid(email):
    """Get user_id from email. Returns None if not found."""
    if not email:
        return None
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM ea_users WHERE email=%s", (email,))
        row = cur.fetchone()
        return row["id"] if row else None
    finally:
        cur.close(); conn.close()

# ─── AUTHENTICATION (registration + login) ────────────────────────────────────

def db_register_user(user):
    """Register a user: password goes to ea_registration, profile to ea_users. Returns user_id."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        pwd = user.pop("password", "")
        safe = encrypt_profile(user.copy())
        email = safe.get("email","")
        # Insert into registration (password only)
        cur.execute("""
            INSERT INTO ea_registration (email, password) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE password=VALUES(password)
        """, (email, hash_password(pwd) if pwd else ""))
        # Insert into users (no password)
        cur.execute("""
            INSERT INTO ea_users (name,email,role,company,phone,bio,linkedin,timezone,avatar,profile_link_slug)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              name=VALUES(name),role=VALUES(role),
              company=VALUES(company),phone=VALUES(phone),bio=VALUES(bio),
              linkedin=VALUES(linkedin),timezone=VALUES(timezone),
              avatar=VALUES(avatar),profile_link_slug=VALUES(profile_link_slug)
        """, (safe.get("name",""), email,
              safe.get("role",""), safe.get("company",""), safe.get("phone",""),
              safe.get("bio",""), safe.get("linkedin",""), safe.get("timezone","UTC"),
              safe.get("avatar",""), safe.get("profileLinkSlug","")))
        conn.commit()
        # Get the user_id
        cur.execute("SELECT id FROM ea_users WHERE email=%s", (email,))
        row = cur.fetchone()
        return row["id"] if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()

def db_authenticate_user(email, password):
    """Verify email+password against registration table. Returns user dict or None."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT password FROM ea_registration WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row:
            return None
        from security import verify_password
        if not verify_password(password, row["password"]):
            return None
        # Fetch profile from users table
        cur.execute("SELECT * FROM ea_users WHERE email=%s", (email,))
        profile = cur.fetchone()
        if not profile:
            # Return minimal user dict if no profile row exists yet
            return {"id": None, "name": email.split("@")[0], "email": email, "role": "",
                    "company": "", "phone": "", "bio": "", "linkedin": "",
                    "timezone": "UTC", "avatar": "", "profileLinkSlug": ""}
        return decrypt_profile({
            "id": profile["id"], "name": profile["name"], "email": profile["email"],
            "role": profile["role"], "company": profile["company"],
            "phone": profile["phone"], "bio": profile["bio"],
            "linkedin": profile["linkedin"], "timezone": profile["timezone"],
            "avatar": profile["avatar"], "profileLinkSlug": profile["profile_link_slug"]
        })
    finally:
        cur.close(); conn.close()

def db_log_login(email, success=True, device_name="", ip_address="", user_agent=""):
    """Record a login attempt."""
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(email)
        cur.execute("""
            INSERT INTO ea_login_history (email, user_id, success, device_name, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email, uid, 1 if success else 0, device_name[:255] if device_name else "",
              ip_address[:64] if ip_address else "", user_agent[:512] if user_agent else ""))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_login_history(email, limit=20):
    """Get login history for a user."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id, email, device_name, ip_address, user_agent, login_time, success
            FROM ea_login_history WHERE email=%s
            ORDER BY login_time DESC LIMIT %s
        """, (email, limit))
        rows = cur.fetchall()
        return [{
            "id": r["id"],
            "device": r["device_name"],
            "ip": r["ip_address"],
            "userAgent": r["user_agent"],
            "time": r["login_time"].strftime("%Y-%m-%d %H:%M:%S") if r["login_time"] else "",
            "success": bool(r["success"])
        } for r in rows]
    finally:
        cur.close(); conn.close()

# ─── USERS (profile only, no password) ────────────────────────────────────────

def db_get_user(email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_users WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row: return None
        user = {"name":row["name"],"email":row["email"],
                "role":row["role"],"company":row["company"],"phone":row["phone"],
                "bio":row["bio"],"linkedin":row["linkedin"],"timezone":row["timezone"],
                "avatar":row["avatar"],"profileLinkSlug":row["profile_link_slug"]}
        return decrypt_profile(user)
    finally:
        cur.close(); conn.close()

def db_get_all_users():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT name,email,role,company,phone,bio,linkedin,timezone,avatar,profile_link_slug,created_at FROM ea_users")
        rows = cur.fetchall()
        return [decrypt_profile({"name":r["name"],"email":r["email"],
                 "role":r["role"],"company":r["company"],"phone":r["phone"],
                 "bio":r["bio"],"linkedin":r["linkedin"],"timezone":r["timezone"],
                 "avatar":r["avatar"],"profileLinkSlug":r["profile_link_slug"]}) for r in rows]
    finally:
        cur.close(); conn.close()

def db_delete_user(email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_registration WHERE email=%s", (email,))
        cur.execute("DELETE FROM ea_users WHERE email=%s", (email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── MEETINGS ─────────────────────────────────────────────────────────────────

def db_save_meeting(meeting, user_email=""):
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(user_email)
        cur.execute("""
            INSERT INTO ea_meetings
              (id,user_email,user_id,title,category,date,duration,attendees,audio_url,
               mode_type,file_type,summary_overview,summary_key_points,
               summary_sentiment,meeting_score,email_draft_subject,email_draft_body,class_notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              user_id=VALUES(user_id),
              title=VALUES(title),category=VALUES(category),date=VALUES(date),
              duration=VALUES(duration),attendees=VALUES(attendees),
              audio_url=VALUES(audio_url),mode_type=VALUES(mode_type),
              file_type=VALUES(file_type),summary_overview=VALUES(summary_overview),
              summary_key_points=VALUES(summary_key_points),
              summary_sentiment=VALUES(summary_sentiment),
              meeting_score=VALUES(meeting_score),
              email_draft_subject=VALUES(email_draft_subject),
              email_draft_body=VALUES(email_draft_body),
              class_notes=VALUES(class_notes)
        """, (
            meeting["id"], user_email, uid,
            meeting.get("title",""), meeting.get("category",""),
            meeting.get("date",""), meeting.get("duration",""),
            json.dumps(meeting.get("attendees",[])),
            meeting.get("audioUrl","#"),
            meeting.get("modeType","audio"), meeting.get("fileType","audio"),
            meeting.get("summary",{}).get("overview",""),
            json.dumps(meeting.get("summary",{}).get("keyPoints",[])),
            meeting.get("summary",{}).get("sentiment",""),
            meeting.get("summary",{}).get("meetingScore",85),
            meeting.get("emailDraft",{}).get("subject",""),
            meeting.get("emailDraft",{}).get("body",""),
            json.dumps(meeting.get("class_notes")) if meeting.get("class_notes") else None
        ))
        conn.commit()

        # Action Items
        cur.execute("DELETE FROM ea_action_items WHERE meeting_id=%s", (meeting["id"],))
        for item in meeting.get("actionItems", []):
            cur.execute("""
                INSERT INTO ea_action_items
                  (id,meeting_id,title,assignee,avatar,priority,deadline,status,category,match_keywords)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (item["id"], meeting["id"], item.get("title",""),
                  item.get("assignee",""), item.get("avatar",""),
                  item.get("priority","Medium"), item.get("deadline",""),
                  item.get("status","Pending"), item.get("category",""),
                  json.dumps(item.get("matchKeywords",[]))))

        # Jira Tickets
        cur.execute("DELETE FROM ea_jira_tickets WHERE meeting_id=%s", (meeting["id"],))
        for ticket in meeting.get("jiraTickets", []):
            cur.execute("""
                INSERT INTO ea_jira_tickets (id,meeting_id,title,type,priority,assignee,description)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (ticket["id"], meeting["id"], ticket.get("title",""),
                  ticket.get("type","Task"), ticket.get("priority","Medium"),
                  ticket.get("assignee",""), ticket.get("description","")))

        # Transcript
        cur.execute("DELETE FROM ea_transcript WHERE meeting_id=%s", (meeting["id"],))
        for line in meeting.get("transcript", []):
            cur.execute("""
                INSERT INTO ea_transcript (meeting_id,speaker,time_stamp,text)
                VALUES (%s,%s,%s,%s)
            """, (meeting["id"], line.get("speaker",""), line.get("time","00:00"), line.get("text","")))

        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_meetings(user_email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_meetings WHERE user_email=%s ORDER BY created_at DESC", (user_email,))
        rows = cur.fetchall()
        meetings = []
        for row in rows:
            mid = row["id"]
            cur.execute("SELECT * FROM ea_action_items WHERE meeting_id=%s", (mid,))
            action_items = [{"id":a["id"],"title":a["title"],"assignee":a["assignee"],
                             "avatar":a["avatar"],"priority":a["priority"],"deadline":a["deadline"],
                             "status":a["status"],"category":a["category"],
                             "matchKeywords":json.loads(a["match_keywords"]) if a["match_keywords"] else []}
                            for a in cur.fetchall()]

            cur.execute("SELECT * FROM ea_jira_tickets WHERE meeting_id=%s", (mid,))
            jira_tickets = [{"id":j["id"],"title":j["title"],"type":j["type"],
                             "priority":j["priority"],"assignee":j["assignee"],
                             "description":j["description"]} for j in cur.fetchall()]

            cur.execute("SELECT * FROM ea_transcript WHERE meeting_id=%s ORDER BY id ASC", (mid,))
            transcript = [{"speaker":t["speaker"],"time":t["time_stamp"],"text":t["text"]}
                          for t in cur.fetchall()]

            meetings.append({
                "id": row["id"], "title": row["title"], "category": row["category"],
                "date": row["date"], "duration": row["duration"],
                "attendees": json.loads(row["attendees"]) if row["attendees"] else [],
                "audioUrl": row["audio_url"] or "#",
                "modeType": row["mode_type"], "fileType": row["file_type"],
                "summary": {
                    "overview": row["summary_overview"],
                    "keyPoints": json.loads(row["summary_key_points"]) if row["summary_key_points"] else [],
                    "sentiment": row["summary_sentiment"],
                    "meetingScore": row["meeting_score"]
                },
                "emailDraft": {"subject": row["email_draft_subject"], "body": row["email_draft_body"]},
                "class_notes": json.loads(row["class_notes"]) if row["class_notes"] else None,
                "actionItems": action_items,
                "jiraTickets": jira_tickets,
                "transcript": transcript
            })
        return meetings
    finally:
        cur.close(); conn.close()

def db_delete_meeting(meeting_id):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_meetings WHERE id=%s", (meeting_id,))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── ACTIVITIES ───────────────────────────────────────────────────────────────

def db_save_activity(activity, user_email=""):
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(user_email)
        cur.execute("""
            INSERT IGNORE INTO ea_activities (id,user_email,user_id,type,author,source,text,task_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (activity["id"], user_email, uid, activity.get("type",""),
              activity.get("author",""), activity.get("source",""),
              activity.get("text",""), activity.get("taskId","")))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_activities(user_email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_activities WHERE user_email=%s ORDER BY created_at DESC", (user_email,))
        return [{"id":r["id"],"type":r["type"],"author":r["author"],"source":r["source"],
                 "text":r["text"],"taskId":r["task_id"],
                 "timestamp": r["created_at"].strftime("%b %d, %H:%M") if r["created_at"] else ""}
                for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

# ─── SETTINGS ─────────────────────────────────────────────────────────────────

def db_save_settings(user_email, settings):
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(user_email)
        cur.execute("""
            INSERT INTO ea_settings (user_email,user_id,llm,whisper,api_key)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE user_id=VALUES(user_id),llm=VALUES(llm),whisper=VALUES(whisper),api_key=VALUES(api_key)
        """, (user_email, uid, settings.get("llm","simulated"),
              settings.get("whisper","simulated"), settings.get("apiKey","")))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_settings(user_email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_settings WHERE user_email=%s", (user_email,))
        row = cur.fetchone()
        if row:
            return {"llm":row["llm"],"whisper":row["whisper"],"apiKey":row["api_key"]}
        return {"llm":"simulated","whisper":"simulated","apiKey":""}
    finally:
        cur.close(); conn.close()

# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

def db_add_notification(user_email, message, ntype="info"):
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(user_email)
        cur.execute("INSERT INTO ea_notifications (user_email,user_id,message,type) VALUES (%s,%s,%s,%s)",
                    (user_email, uid, message, ntype))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_notifications(user_email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_notifications WHERE user_email=%s ORDER BY created_at DESC LIMIT 50", (user_email,))
        return [{"id":r["id"],"message":r["message"],"type":r["type"],"isRead":bool(r["is_read"]),
                 "createdAt": r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""}
                for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

def db_mark_notifications_read(user_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_notifications SET is_read=1 WHERE user_email=%s", (user_email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_clear_notifications(user_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_notifications WHERE user_email=%s", (user_email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── FOLLOWERS ────────────────────────────────────────────────────────────────

def db_follow_user(user_email, follower_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("INSERT IGNORE INTO ea_followers (user_email,follower_email) VALUES (%s,%s)",
                    (user_email, follower_email))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_unfollow_user(user_email, follower_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_followers WHERE user_email=%s AND follower_email=%s",
                    (user_email, follower_email))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_followers(user_email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT follower_email FROM ea_followers WHERE user_email=%s", (user_email,))
        return [r["follower_email"] for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

# ─── PROFILE LINKS ────────────────────────────────────────────────────────────

def db_save_profile_links(user_email, links):
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(user_email)
        cur.execute("DELETE FROM ea_profile_links WHERE user_email=%s", (user_email,))
        for link in links:
            cur.execute("INSERT INTO ea_profile_links (user_email,user_id,label,url,is_visible) VALUES (%s,%s,%s,%s,%s)",
                        (user_email, uid, link.get("label",""), link.get("url",""), 1 if link.get("visible",True) else 0))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_profile_links(user_email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_profile_links WHERE user_email=%s", (user_email,))
        return [{"id":r["id"],"label":r["label"],"url":r["url"],"visible":bool(r["is_visible"])}
                for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

# ─── QUERY / CONTACT FORM ─────────────────────────────────────────────────────

def db_save_query(data):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ea_query_submissions (name,email,phone,type,message,rating,project_type,issue_type,feedback_on,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (data.get("name",""), data.get("email",""), data.get("phone",""),
              data.get("type","feedback"), data.get("message",""),
              data.get("rating",""), data.get("projectType",""),
              data.get("issueType",""), data.get("feedbackOn",""), "new"))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_queries(limit=100):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_query_submissions ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

def db_update_query_status(query_id, status):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_query_submissions SET status=%s WHERE id=%s", (status, query_id))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_admin_update_user(email, data):
    conn = get_conn(); cur = conn.cursor()
    try:
        fields = []
        vals = []
        for key in ("name", "role", "avatar", "bio", "company", "phone"):
            if key in data:
                fields.append(f"{key}=%s")
                vals.append(data[key])
        if fields:
            vals.append(email)
            cur.execute(f"UPDATE ea_users SET {','.join(fields)} WHERE email=%s", vals)
            conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_single_user(email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_users WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row: return None
        return decrypt_profile({
            "name": row["name"], "email": row["email"],
            "role": row["role"], "company": row["company"], "phone": row["phone"],
            "bio": row["bio"], "linkedin": row["linkedin"], "timezone": row["timezone"],
            "avatar": row["avatar"], "profileLinkSlug": row["profile_link_slug"]
        })
    finally:
        cur.close(); conn.close()

def db_update_user_password(email, new_password):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_registration SET password=%s WHERE email=%s",
            (hash_password(new_password), email))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── ADMIN USERS ──────────────────────────────────────────────────────────────

def db_authenticate_admin(email, password):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_admin_users WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row: return None
        from security import verify_password
        if not verify_password(password, row["password"]):
            return None
        # Update last_login
        cur.execute("UPDATE ea_admin_users SET last_login=NOW() WHERE email=%s", (email,))
        conn.commit()
        return {
            "email": row["email"], "name": row["name"], "id": row["id"],
            "role": row.get("role", "admin"), "avatar": row.get("avatar", ""),
            "permissions": json.loads(row["permissions"]) if row.get("permissions") else {}
        }
    finally:
        cur.close(); conn.close()

def db_get_all_admins():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, email, name, role, last_login, created_at FROM ea_admin_users ORDER BY created_at ASC")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

def db_update_admin(email, data):
    conn = get_conn(); cur = conn.cursor()
    try:
        fields = []
        vals = []
        for key in ("name", "role", "avatar", "permissions"):
            if key in data:
                if key == "permissions" and isinstance(data[key], dict):
                    fields.append("permissions=%s")
                    vals.append(json.dumps(data[key]))
                else:
                    fields.append(f"{key}=%s")
                    vals.append(data[key])
        if fields:
            vals.append(email)
            cur.execute(f"UPDATE ea_admin_users SET {','.join(fields)} WHERE email=%s", vals)
            conn.commit()
    finally:
        cur.close(); conn.close()

# ─── EDIT HISTORY ─────────────────────────────────────────────────────────────

def db_save_edit(meeting_id, user_email, field, old_val, new_val, description=""):
    conn = get_conn(); cur = conn.cursor()
    try:
        # Ensure description column exists (idempotent)
        try: cur.execute("ALTER TABLE ea_edit_history ADD COLUMN description TEXT AFTER new_value")
        except: pass
        cur.execute("""
            INSERT INTO ea_edit_history (meeting_id,user_email,field_changed,old_value,new_value,description)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (meeting_id, user_email, field, str(old_val), str(new_val), description))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_edit_history(meeting_id):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        # Ensure description column exists (idempotent)
        try: cur.execute("ALTER TABLE ea_edit_history ADD COLUMN description TEXT AFTER new_value")
        except: pass
        cur.execute("SELECT * FROM ea_edit_history WHERE meeting_id=%s ORDER BY edited_at DESC", (meeting_id,))
        return [{"field":r["field_changed"],"oldValue":r["old_value"],"newValue":r["new_value"],
                 "description":r.get("description",""), "editedBy":r["user_email"],
                 "editedAt": r["edited_at"].strftime("%Y-%m-%d %H:%M") if r["edited_at"] else ""}
                for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

# ─── GLOBAL EDIT HISTORY ──────────────────────────────────────────────────────

def db_init_global_edit_history():
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ea_global_edit_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                edit_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                meta TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_save_global_edit(user_email, edit_type, description, meta_json=None):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ea_global_edit_history (user_email, edit_type, description, meta)
            VALUES (%s, %s, %s, %s)
        """, (user_email, edit_type, description, json.dumps(meta_json) if meta_json else None))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_global_edit_history(user_email, limit=200, offset=0):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id, user_email, edit_type, description, meta, created_at
            FROM ea_global_edit_history
            WHERE user_email=%s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (user_email, limit, offset))
        rows = cur.fetchall()
        result = []
        for r in rows:
            item = {
                "id": r["id"],
                "type": r["edit_type"],
                "description": r["description"],
                "user": r["user_email"],
                "timestamp": r["created_at"].isoformat() if r["created_at"] else "",
                "displayTime": r["created_at"].strftime("%b %d, %I:%M %p") if r["created_at"] else ""
            }
            if r["meta"]:
                try:
                    item["meta"] = json.loads(r["meta"]) if isinstance(r["meta"], str) else r["meta"]
                except:
                    item["meta"] = {}
            else:
                item["meta"] = {}
            result.append(item)
        return result
    finally:
        cur.close(); conn.close()

def db_count_global_edit_history(user_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM ea_global_edit_history WHERE user_email=%s", (user_email,))
        return cur.fetchone()[0]
    finally:
        cur.close(); conn.close()

def db_clear_global_edit_history(user_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_global_edit_history WHERE user_email=%s", (user_email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_delete_global_edit(user_id, user_email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_global_edit_history WHERE id=%s AND user_email=%s", (user_id, user_email))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── ADMIN CALENDAR ──────────────────────────────────────────────────────────

def db_get_all_meetings():
    """Fetch all meetings across all users (for admin calendar)."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, title, user_email, date, duration, category, created_at FROM ea_meetings ORDER BY created_at DESC")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

# ─── ROOT ADMIN AUTH ───────────────────────────────────────────────────────

def db_authenticate_root_admin(email, password):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_root_admins WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row: return None
        from security import verify_password
        if not verify_password(password, row["password"]):
            return None
        cur.execute("UPDATE ea_root_admins SET last_login=NOW() WHERE email=%s", (email,))
        conn.commit()
        return {"id": row["id"], "email": row["email"], "name": row["name"],
                "avatar": row.get("avatar", ""), "isRootAdmin": True}
    finally:
        cur.close(); conn.close()

def db_get_root_admin(email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, email, name, avatar, last_login, created_at FROM ea_root_admins WHERE email=%s", (email,))
        return cur.fetchone()
    finally:
        cur.close(); conn.close()

def db_get_all_root_admins():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, email, name, avatar, last_login, created_at FROM ea_root_admins ORDER BY created_at DESC")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

def db_add_root_admin(email, password, name="Admin", added_by=""):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO ea_root_admins (email, password, name) VALUES (%s, %s, %s)",
            (email, hash_password(password), name))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()

def db_remove_root_admin(email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_root_admins WHERE email=%s", (email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── SUB-ADMIN MANAGEMENT (for root admins) ─────────────────────────────────

def db_add_admin(email, password, name="Admin", permissions=None, created_by="", admin_type="sub"):
    conn = get_conn(); cur = conn.cursor()
    try:
        perms = json.dumps(permissions or {"users":"r","queries":"r","security":"r","settings":"r"})
        cur.execute("""
            INSERT INTO ea_admin_users (email, password, name, role, admin_type, permissions, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, 1, %s)
        """, (email, hash_password(password), name, "admin", admin_type, perms, created_by))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close(); conn.close()

def db_delete_admin(email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_admin_users WHERE email=%s", (email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_all_admins():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id, email, name, role, admin_type, avatar, permissions, is_active, created_by, last_login, created_at
            FROM ea_admin_users ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        return [{
            "id": r["id"], "email": r["email"], "name": r["name"],
            "role": r["role"], "adminType": r.get("admin_type", "sub"),
            "avatar": r.get("avatar", ""),
            "permissions": json.loads(r["permissions"]) if r.get("permissions") else {},
            "isActive": bool(r["is_active"]),
            "createdBy": r.get("created_by", ""),
            "lastLogin": r["last_login"].strftime("%Y-%m-%d %H:%M:%S") if r.get("last_login") else None,
            "createdAt": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r.get("created_at") else None
        } for r in rows]
    finally:
        cur.close(); conn.close()

def db_update_admin_permissions(email, permissions, is_active=None):
    conn = get_conn(); cur = conn.cursor()
    try:
        fields = ["permissions=%s"]
        vals = [json.dumps(permissions)]
        if is_active is not None:
            fields.append("is_active=%s")
            vals.append(1 if is_active else 0)
        vals.append(email)
        cur.execute(f"UPDATE ea_admin_users SET {','.join(fields)} WHERE email=%s", vals)
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── USER SECURITY SETTINGS (per-user toggles) ─────────────────────────────

def db_get_user_security_settings(email):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT setting_key, setting_value, updated_by, updated_at FROM ea_user_security_settings WHERE user_email=%s", (email,))
        rows = cur.fetchall()
        settings = {}
        for r in rows:
            settings[r["setting_key"]] = {
                "value": r["setting_value"],
                "updatedBy": r["updated_by"],
                "updatedAt": r["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if r["updated_at"] else ""
            }
        return settings
    finally:
        cur.close(); conn.close()

def db_set_user_security_setting(email, setting_key, setting_value, updated_by=""):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ea_user_security_settings (user_email, setting_key, setting_value, updated_by)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value), updated_by=VALUES(updated_by)
        """, (email, setting_key, setting_value, updated_by))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_all_user_security_settings():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT u.email, u.name, u.avatar,
                   s.setting_key, s.setting_value, s.updated_by, s.updated_at
            FROM ea_users u
            LEFT JOIN ea_user_security_settings s ON u.email = s.user_email
            ORDER BY u.email, s.setting_key
        """)
        rows = cur.fetchall()
        users = {}
        for r in rows:
            email = r["email"]
            if email not in users:
                users[email] = {"email": email, "name": r["name"], "avatar": r.get("avatar", ""), "settings": {}}
            if r["setting_key"]:
                users[email]["settings"][r["setting_key"]] = {
                    "value": r["setting_value"],
                    "updatedBy": r["updated_by"],
                    "updatedAt": r["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if r["updated_at"] else ""
                }
        return list(users.values())
    finally:
        cur.close(); conn.close()

# ─── STAFF / COMPANY MEMBERS ────────────────────────────────────────────────

def db_add_staff_member(email, name="", position="", department="", staff_role="staff", phone="", avatar="", created_by="", access=""):
    conn = get_conn(); cur = conn.cursor()
    try:
        uid = _get_uid(email)
        cur.execute("""
            INSERT INTO ea_staff_members (user_id, email, name, position, department, staff_role, phone, avatar, created_by, access)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name), position=VALUES(position),
              department=VALUES(department), staff_role=VALUES(staff_role),
              phone=VALUES(phone), avatar=VALUES(avatar), access=VALUES(access)
        """, (uid, email, name, position, department, staff_role, phone, avatar or "", created_by, access))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_get_staff_members():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT s.id, s.email, s.name, s.position, s.department, s.staff_role, s.phone, s.avatar,
                   s.created_by, s.created_at, s.access, s.active, s.inactive_reason, s.inactive_letter,
                   u.id as user_id
            FROM ea_staff_members s
            LEFT JOIN ea_users u ON s.email = u.email
            ORDER BY s.active DESC, s.name
        """)
        rows = cur.fetchall()
        return [{
            "id": r["id"], "email": r["email"], "name": r["name"],
            "position": r["position"], "department": r["department"],
            "staffRole": r.get("staff_role", "staff"),
            "phone": r["phone"], "avatar": r.get("avatar", "") or "",
            "access": r.get("access", "") or "",
            "createdBy": r["created_by"], "userId": r["user_id"],
            "active": r.get("active", 1) if r.get("active") is not None else 1,
            "inactiveReason": r.get("inactive_reason", "") or "",
            "inactiveLetter": r.get("inactive_letter", "") or "",
            "createdAt": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else ""
        } for r in rows]
    finally:
        cur.close(); conn.close()

def db_delete_staff_member(email):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ea_staff_members WHERE email=%s", (email,))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_update_staff_permissions(email, access_json):
    """Update only the access/permissions field for a staff member."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_staff_members SET access=%s WHERE email=%s", (access_json, email))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_is_staff_member(email):
    """Check if a user is a staff member. Returns staff dict or None."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT staff_role, position, department, active FROM ea_staff_members WHERE email=%s", (email,))
        return cur.fetchone()
    finally:
        cur.close(); conn.close()

def db_update_staff_status(email, active, reason="", letter=""):
    """Update staff member's active status with optional reason and signed letter."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_staff_members SET active=%s, inactive_reason=%s, inactive_letter=%s WHERE email=%s",
                    (1 if active else 0, reason, letter, email))
        conn.commit()
    finally:
        cur.close(); conn.close()

def db_send_message(from_email, to_email, subject, body):
    """Send a message from one user to another."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ea_messages (from_email, to_email, subject, body)
            VALUES (%s, %s, %s, %s)
        """, (from_email, to_email, subject, body))
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close(); conn.close()

def db_get_messages(email, limit=50):
    """Get messages for a user (both sent and received)."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id, from_email, to_email, subject, body, is_read, created_at
            FROM ea_messages
            WHERE from_email=%s OR to_email=%s
            ORDER BY created_at DESC
            LIMIT %s
        """, (email, email, limit))
        rows = cur.fetchall()
        return [{
            "id": r["id"],
            "fromEmail": r["from_email"],
            "toEmail": r["to_email"],
            "subject": r["subject"],
            "body": r["body"],
            "isRead": bool(r["is_read"]),
            "createdAt": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else ""
        } for r in rows]
    finally:
        cur.close(); conn.close()

def db_get_unread_count(email):
    """Get count of unread messages for a user."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM ea_messages WHERE to_email=%s AND is_read=0", (email,))
        return cur.fetchone()[0]
    finally:
        cur.close(); conn.close()

def db_mark_message_read(message_id):
    """Mark a message as read."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_messages SET is_read=1 WHERE id=%s", (message_id,))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── ADMIN SECURITY SETTINGS ──────────────────────────────────────────────────

def db_get_admin_security_settings(admin_email):
    """Get security settings for an admin (IP blocking, etc.)."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT setting_key, setting_value, updated_at
            FROM ea_admin_security_settings
            WHERE admin_email=%s
        """, (admin_email,))
        rows = cur.fetchall()
        return {r["setting_key"]: {"value": r["setting_value"], "updatedAt": r["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if r["updated_at"] else ""} for r in rows}
    finally:
        cur.close(); conn.close()

def db_set_admin_security_setting(admin_email, setting_key, setting_value):
    """Set a security setting for an admin."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ea_admin_security_settings (admin_email, setting_key, setting_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)
        """, (admin_email, setting_key, setting_value))
        conn.commit()
    finally:
        cur.close(); conn.close()

# ─── ADMIN USER MANAGEMENT ────────────────────────────────────────────────────

def db_update_user_profile(email, updates, updated_by=""):
    """Update user profile fields (name, phone, company, etc.) and log to edit history."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM ea_users WHERE email=%s", (email,))
        current = cur.fetchone()
        is_staff = False
        if not current:
            cur.execute("SELECT * FROM ea_staff_members WHERE email=%s", (email,))
            current = cur.fetchone()
            if current:
                is_staff = True
            else:
                return False
        allowed_fields = ["name", "phone", "company", "role", "timezone", "bio", "linkedin", "avatar"]
        set_clauses = []
        params = []
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field}=%s")
                params.append(updates[field])
        if not set_clauses and not is_staff:
            return True
        if not is_staff:
            params.append(email)
            cur.execute(f"UPDATE ea_users SET {', '.join(set_clauses)} WHERE email=%s", params)
        staff_fields = {"name": "name", "phone": "phone", "position": "position", "department": "department"}
        staff_updates = {staff_fields[k]: v for k, v in updates.items() if k in staff_fields}
        if staff_updates:
            staff_set = ", ".join(f"{k}=%s" for k in staff_updates.keys())
            staff_params = list(staff_updates.values()) + [email]
            cur.execute(f"UPDATE ea_staff_members SET {staff_set} WHERE email=%s", staff_params)
        conn.commit()
        for field in allowed_fields:
            if field in updates and str(current.get(field, "")) != str(updates[field]):
                db_save_global_edit(
                    email,
                    "profile_update",
                    f"Admin {updated_by} changed {field} from '{current.get(field, '')}' to '{updates[field]}'",
                    {"field": field, "old": current.get(field, ""), "new": updates[field], "updated_by": updated_by}
                )
        return True
    finally:
        cur.close(); conn.close()

def db_update_user_password(email, new_password, updated_by=""):
    """Update user password and log to edit history."""
    from security import hash_password
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("UPDATE ea_registration SET password=%s WHERE email=%s", (hash_password(new_password), email))
        conn.commit()
        db_save_global_edit(
            email,
            "password_reset",
            f"Admin {updated_by} reset password",
            {"updated_by": updated_by}
        )
        return True
    finally:
        cur.close(); conn.close()

def db_block_user_ip(email, ip_address, admin_email):
    """Block an IP address for a user."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT blocked_ips FROM ea_staff_members WHERE email=%s", (email,))
        row = cur.fetchone()
        current_blocked = row[0] if row else ""
        blocked_list = [ip.strip() for ip in current_blocked.split(",") if ip.strip()] if current_blocked else []
        if ip_address not in blocked_list:
            blocked_list.append(ip_address)
            cur.execute("UPDATE ea_staff_members SET blocked_ips=%s WHERE email=%s", (",".join(blocked_list), email))
        cur.execute("""
            INSERT INTO ea_admin_security_settings (admin_email, setting_key, setting_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)
        """, (admin_email, f"blocked_ip_{email}_{ip_address}", json.dumps({"email": email, "ip": ip_address, "blocked_at": datetime.datetime.now().isoformat()})))
        conn.commit()
        db_save_global_edit(
            email,
            "ip_blocked",
            f"Admin {admin_email} blocked IP {ip_address} for user {email}",
            {"ip": ip_address, "blocked_by": admin_email}
        )
        return True
    finally:
        cur.close(); conn.close()

def db_unblock_user_ip(email, ip_address, admin_email):
    """Unblock an IP address for a user."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT blocked_ips FROM ea_staff_members WHERE email=%s", (email,))
        row = cur.fetchone()
        current_blocked = row[0] if row else ""
        blocked_list = [ip.strip() for ip in current_blocked.split(",") if ip.strip()] if current_blocked else []
        if ip_address in blocked_list:
            blocked_list.remove(ip_address)
            cur.execute("UPDATE ea_staff_members SET blocked_ips=%s WHERE email=%s", (",".join(blocked_list), email))
        cur.execute("DELETE FROM ea_admin_security_settings WHERE admin_email=%s AND setting_key=%s", (admin_email, f"blocked_ip_{email}_{ip_address}"))
        conn.commit()
        db_save_global_edit(
            email,
            "ip_unblocked",
            f"Admin {admin_email} unblocked IP {ip_address} for user {email}",
            {"ip": ip_address, "unblocked_by": admin_email}
        )
        return True
    finally:
        cur.close(); conn.close()

def db_get_user_blocked_ips(email):
    """Get blocked IPs for a user."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT blocked_ips FROM ea_staff_members WHERE email=%s", (email,))
        row = cur.fetchone()
        if row and row[0]:
            return [ip.strip() for ip in row[0].split(",") if ip.strip()]
        return []
    finally:
        cur.close(); conn.close()

def db_is_it_team(email):
    """Check if a user is in IT team."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT staff_role FROM ea_staff_members WHERE email=%s", (email,))
        row = cur.fetchone()
        return row and row[0] in ("it_team", "it_admin", "it_manager")
    finally:
        cur.close(); conn.close()

def db_get_staff_edit_history(email, limit=100, offset=0):
    """Get edit history for a staff member (visible to IT team and admin)."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id, user_email, edit_type, description, meta, created_at
            FROM ea_global_edit_history
            WHERE user_email=%s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (email, limit, offset))
        rows = cur.fetchall()
        result = []
        for r in rows:
            item = {
                "id": r["id"],
                "type": r["edit_type"],
                "description": r["description"],
                "user": r["user_email"],
                "timestamp": r["created_at"].isoformat() if r["created_at"] else "",
                "displayTime": r["created_at"].strftime("%b %d, %I:%M %p") if r["created_at"] else ""
            }
            if r["meta"]:
                try:
                    item["meta"] = json.loads(r["meta"]) if isinstance(r["meta"], str) else r["meta"]
                except:
                    item["meta"] = {}
            else:
                item["meta"] = {}
            result.append(item)
        return result
    finally:
        cur.close(); conn.close()

def db_count_staff_edit_history(email):
    """Count edit history entries for a staff member."""
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM ea_global_edit_history WHERE user_email=%s", (email,))
        return cur.fetchone()[0]
    finally:
        cur.close(); conn.close()

# ─── SECURITY EVENTS ──────────────────────────────────────────────────────────

def _create_security_table(cur):
    """Create ea_security_events table (called internally)."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ea_security_events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_type VARCHAR(64) NOT NULL,
            severity VARCHAR(16) DEFAULT 'info',
            ip_address VARCHAR(64) DEFAULT '',
            email VARCHAR(191) DEFAULT '',
            url VARCHAR(512) DEFAULT '',
            method VARCHAR(10) DEFAULT '',
            detail TEXT,
            user_agent VARCHAR(512) DEFAULT '',
            blocked TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_event_type (event_type),
            INDEX idx_ip (ip_address),
            INDEX idx_email (email),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

def db_init_security_table():
    """Public init for security events table."""
    conn = get_conn(); cur = conn.cursor()
    try:
        _create_security_table(cur)
        conn.commit()
        print("[DB] Security events table initialized.")
    finally:
        cur.close(); conn.close()

def db_log_security_event(event_type, detail="", ip_address="", email="",
                          url="", method="", user_agent="", severity="info", blocked=False):
    """Log a security event to the database."""
    try:
        conn = get_conn(); cur = conn.cursor()
        try:
            uid = _get_uid(email)
            cur.execute("""
                INSERT INTO ea_security_events
                  (event_type, severity, ip_address, email, user_id, url, method, detail, user_agent, blocked)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event_type[:64], severity[:16],
                (ip_address or "")[:64], (email or "")[:191],
                uid, (url or "")[:512], (method or "")[:10],
                (detail or "")[:2000], (user_agent or "")[:512],
                1 if blocked else 0
            ))
            conn.commit()
        finally:
            cur.close(); conn.close()
    except Exception:
        pass  # Never let security logging crash the app

def db_get_security_events(limit=100, offset=0, severity=None, event_type=None, email=None):
    """Retrieve security events for the dashboard."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        where_clauses = []
        params = []
        if severity:
            where_clauses.append("severity=%s")
            params.append(severity)
        if event_type:
            where_clauses.append("event_type=%s")
            params.append(event_type)
        if email:
            where_clauses.append("email=%s")
            params.append(email)
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        params += [int(limit), int(offset)]
        cur.execute(f"""
            SELECT id, event_type, severity, ip_address, email, url, method,
                   detail, user_agent, blocked, created_at
            FROM ea_security_events
            {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params)
        rows = cur.fetchall()
        return [{
            "id": r["id"],
            "type": r["event_type"],
            "severity": r["severity"],
            "ip": r["ip_address"],
            "email": r["email"],
            "url": r["url"],
            "method": r["method"],
            "detail": r["detail"],
            "userAgent": r["user_agent"],
            "blocked": bool(r["blocked"]),
            "time": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else ""
        } for r in rows]
    finally:
        cur.close(); conn.close()

def db_get_security_stats():
    """Get summary statistics for the security dashboard."""
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        stats = {}
        # Total events
        cur.execute("SELECT COUNT(*) as cnt FROM ea_security_events")
        stats["total"] = cur.fetchone()["cnt"]
        # Blocked events
        cur.execute("SELECT COUNT(*) as cnt FROM ea_security_events WHERE blocked=1")
        stats["blocked"] = cur.fetchone()["cnt"]
        # Events last 24h
        cur.execute("SELECT COUNT(*) as cnt FROM ea_security_events WHERE created_at >= NOW() - INTERVAL 24 HOUR")
        stats["last24h"] = cur.fetchone()["cnt"]
        # Failed logins
        cur.execute("SELECT COUNT(*) as cnt FROM ea_security_events WHERE event_type='login_failed'")
        stats["failedLogins"] = cur.fetchone()["cnt"]
        # Top attacking IPs
        cur.execute("""
            SELECT ip_address, COUNT(*) as cnt FROM ea_security_events
            WHERE blocked=1 AND ip_address != ''
            GROUP BY ip_address ORDER BY cnt DESC LIMIT 5
        """)
        stats["topAttackers"] = [{"ip": r["ip_address"], "count": r["cnt"]} for r in cur.fetchall()]
        # Events by type
        cur.execute("""
            SELECT event_type, COUNT(*) as cnt FROM ea_security_events
            GROUP BY event_type ORDER BY cnt DESC LIMIT 10
        """)
        stats["byType"] = [{"type": r["event_type"], "count": r["cnt"]} for r in cur.fetchall()]
        return stats
    finally:
        cur.close(); conn.close()
