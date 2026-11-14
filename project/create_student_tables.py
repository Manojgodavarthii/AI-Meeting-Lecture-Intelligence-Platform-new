"""
Create s_echoaction_* mirror tables (from localStorage keys in static/app.js)
and seed login accounts for all 4 roles (admin, employee, staff, student).
"""
import mysql.connector
from werkzeug.security import generate_password_hash

conn = mysql.connector.connect(host="localhost", user="root", password="admin", database="echoaction")
cur = conn.cursor()

tables = {
    "s_echoaction_users": """
        CREATE TABLE IF NOT EXISTS s_echoaction_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(191) DEFAULT '',
            email VARCHAR(191) UNIQUE DEFAULT '',
            password_hash VARCHAR(512) DEFAULT '',
            role VARCHAR(32) DEFAULT '',
            phone VARCHAR(64) DEFAULT '',
            college VARCHAR(128) DEFAULT '',
            roll_number VARCHAR(64) DEFAULT '',
            college_mail VARCHAR(191) DEFAULT '',
            avatar MEDIUMTEXT,
            bio TEXT,
            linkedin VARCHAR(255) DEFAULT '',
            timezone VARCHAR(64) DEFAULT 'UTC',
            department VARCHAR(128) DEFAULT '',
            team VARCHAR(128) DEFAULT '',
            display_name VARCHAR(191) DEFAULT '',
            profile_slug VARCHAR(255) DEFAULT '',
            is_active TINYINT(1) DEFAULT 1,
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_activities": """
        CREATE TABLE IF NOT EXISTS s_echoaction_activities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            activity_type VARCHAR(32) DEFAULT '',
            author VARCHAR(191) DEFAULT '',
            source VARCHAR(64) DEFAULT '',
            text TEXT,
            task_id VARCHAR(64) DEFAULT '',
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_act_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_ai_suggestions": """
        CREATE TABLE IF NOT EXISTS s_echoaction_ai_suggestions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            suggestion_text TEXT,
            suggestion_type VARCHAR(32) DEFAULT 'study',
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sug_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_app_version": """
        CREATE TABLE IF NOT EXISTS s_echoaction_app_version (
            id INT AUTO_INCREMENT PRIMARY KEY,
            version VARCHAR(32) NOT NULL,
            changelog TEXT,
            released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_audit_trail": """
        CREATE TABLE IF NOT EXISTS s_echoaction_audit_trail (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            action VARCHAR(128) NOT NULL,
            entity_type VARCHAR(64) DEFAULT '',
            entity_id VARCHAR(64) DEFAULT '',
            old_value TEXT,
            new_value TEXT,
            ip_address VARCHAR(64) DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_at_user (user_email),
            INDEX idx_at_action (action)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_current_user": """
        CREATE TABLE IF NOT EXISTS s_echoaction_current_user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(191) UNIQUE DEFAULT '',
            user_id INT DEFAULT NULL,
            session_data JSON DEFAULT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_dismissed_notifs": """
        CREATE TABLE IF NOT EXISTS s_echoaction_dismissed_notifs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            notif_id VARCHAR(64) DEFAULT '',
            dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_dismiss (user_email, notif_id),
            INDEX idx_dis_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_notif_read": """
        CREATE TABLE IF NOT EXISTS s_echoaction_notif_read (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            notif_id VARCHAR(64) DEFAULT '',
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_read (user_email, notif_id),
            INDEX idx_read_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_settings": """
        CREATE TABLE IF NOT EXISTS s_echoaction_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            setting_key VARCHAR(128) NOT NULL,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_setting (user_email, setting_key),
            INDEX idx_set_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_meetings": """
        CREATE TABLE IF NOT EXISTS s_echoaction_meetings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            title VARCHAR(255) NOT NULL,
            category VARCHAR(64) DEFAULT '',
            date VARCHAR(64) DEFAULT '',
            duration VARCHAR(32) DEFAULT '',
            attendees JSON DEFAULT NULL,
            audio_url VARCHAR(512) DEFAULT '#',
            mode_type VARCHAR(32) DEFAULT 'audio',
            file_type VARCHAR(32) DEFAULT 'audio',
            summary JSON DEFAULT NULL,
            meeting_score FLOAT DEFAULT 85,
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_meet_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_std_assignments": """
        CREATE TABLE IF NOT EXISTS s_echoaction_std_assignments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            title VARCHAR(255) NOT NULL,
            subject VARCHAR(128) DEFAULT '',
            due VARCHAR(64) DEFAULT '',
            status VARCHAR(32) DEFAULT 'pending',
            details TEXT,
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_asg_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_std_exams": """
        CREATE TABLE IF NOT EXISTS s_echoaction_std_exams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            name VARCHAR(255) NOT NULL,
            subject VARCHAR(128) DEFAULT '',
            exam_date VARCHAR(64) DEFAULT '',
            exam_time VARCHAR(32) DEFAULT '',
            room VARCHAR(64) DEFAULT '',
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_exm_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_std_materials": """
        CREATE TABLE IF NOT EXISTS s_echoaction_std_materials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            title VARCHAR(255) NOT NULL,
            material_type VARCHAR(32) DEFAULT 'note',
            subject VARCHAR(128) DEFAULT '',
            content TEXT,
            file_path VARCHAR(512) DEFAULT NULL,
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_mat_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_std_submitted": """
        CREATE TABLE IF NOT EXISTS s_echoaction_std_submitted (
            id INT AUTO_INCREMENT PRIMARY KEY,
            assignment_id VARCHAR(64) DEFAULT '',
            user_email VARCHAR(255) DEFAULT '',
            status VARCHAR(32) DEFAULT 'submitted',
            grade VARCHAR(16) DEFAULT '',
            feedback TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_assign_user (assignment_id, user_email),
            INDEX idx_sub_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_std_timetable": """
        CREATE TABLE IF NOT EXISTS s_echoaction_std_timetable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            day VARCHAR(16) DEFAULT '',
            time VARCHAR(32) DEFAULT '',
            subject VARCHAR(128) DEFAULT '',
            teacher VARCHAR(128) DEFAULT '',
            room VARCHAR(64) DEFAULT '',
            class_name VARCHAR(128) DEFAULT '',
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_tt_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_student_messages": """
        CREATE TABLE IF NOT EXISTS s_echoaction_student_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            sender VARCHAR(191) DEFAULT '',
            receiver VARCHAR(191) DEFAULT '',
            body TEXT,
            is_read TINYINT(1) DEFAULT 0,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sm_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "s_echoaction_tasks": """
        CREATE TABLE IF NOT EXISTS s_echoaction_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255) DEFAULT '',
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(32) DEFAULT 'pending',
            priority VARCHAR(16) DEFAULT 'medium',
            due VARCHAR(64) DEFAULT '',
            is_completed TINYINT(1) DEFAULT 0,
            meta JSON DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_task_user (user_email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
}

created = []
for name, sql in tables.items():
    try:
        cur.execute(sql)
        conn.commit()
        created.append(name)
    except Exception as e:
        print(f"  WARN {name}: {e}")

print(f"Created {len(created)} s_echoaction_* tables")

# ── Seed login accounts for all 4 roles ────────────────────────
cur.execute("INSERT IGNORE INTO ea_registration (email, password) VALUES (%s, %s)",
            ("employee@echoaction.ai", generate_password_hash("password")))
cur.execute("INSERT IGNORE INTO ea_users (name, email, role, role_id) VALUES (%s, %s, %s, %s)",
            ("John Doe", "employee@echoaction.ai", "employee", 1))
print("Seeded EMPLOYEE login: employee@echoaction.ai / password")

cur.execute("INSERT IGNORE INTO ea_registration (email, password) VALUES (%s, %s)",
            ("student@echoaction.ai", generate_password_hash("password")))
cur.execute("INSERT IGNORE INTO ea_users (name, email, role, role_id) VALUES (%s, %s, %s, %s)",
            ("Alice Wang", "student@echoaction.ai", "student", 2))
print("Seeded STUDENT login: student@echoaction.ai / password")

# Staff - ensure password column handling
cols = [r[0] for r in cur.execute("SELECT * FROM ea_staff_members LIMIT 1")
        ] if False else None
cur.execute("""
    INSERT IGNORE INTO ea_staff_members
        (email, password, name, position, department, staff_role, created_by, active)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", ("staff@echoaction.ai", generate_password_hash("password"), "Bob Martinez",
      "Support Staff", "Administration", "staff", "system", 1))
cur.execute("""
    INSERT IGNORE INTO ea_staff_members
        (email, password, name, position, department, staff_role, created_by, active)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", ("priya@echoaction.ai", generate_password_hash("password123"), "Priya Sharma",
      "Faculty", "Academics", "staff", "system", 1))
print("Seeded STAFF login: staff@echoaction.ai / password (and priya@echoaction.ai / password123)")

conn.commit()

# Admin logins already seeded earlier (verify)
cur.execute("SELECT email FROM ea_admin_users")
admins = [r[0] for r in cur.fetchall()]
cur.execute("SELECT email FROM ea_root_admins")
roots = [r[0] for r in cur.fetchall()]
print(f"ADMIN logins ready: root={roots}, sub-admin={admins}")

cur.close()
conn.close()
print("\n[DONE] s_echoaction_* tables created and 4-role logins seeded.")