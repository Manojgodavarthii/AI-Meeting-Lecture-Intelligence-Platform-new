"""
Migration script: Copy all ea_* tables from 'manoj' to new 'echoaction' database.
Run once: python migrate_db.py
"""
import mysql.connector

OLD_DB = {"host": "localhost", "user": "root", "password": "admin", "database": "manoj"}
NEW_DB = {"host": "localhost", "user": "root", "password": "admin", "database": "echoaction"}

TABLES = [
    "ea_users", "ea_meetings", "ea_action_items", "ea_jira_tickets", "ea_transcript",
    "ea_activities", "ea_settings", "ea_notifications", "ea_followers",
    "ea_profile_links", "ea_query_submissions", "ea_edit_history", "ea_global_edit_history"
]

def get_conn(cfg):
    return mysql.connector.connect(**cfg)

def main():
    conn_old = get_conn(OLD_DB)

    # Create new database
    conn_admin = mysql.connector.connect(host="localhost", user="root", password="admin")
    cur_admin = conn_admin.cursor()
    cur_admin.execute("CREATE DATABASE IF NOT EXISTS echoaction CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn_admin.commit()
    cur_admin.close()
    conn_admin.close()
    print("[OK] Database 'echoaction' created.")

    conn_new = get_conn(NEW_DB)

    for table in TABLES:
        try:
            # Get CREATE TABLE from old DB
            cur = conn_old.cursor()
            cur.execute(f"SHOW CREATE TABLE `{table}`")
            row = cur.fetchone()
            create_stmt = row[1]
            cur.close()

            # Drop and recreate in new DB
            cur = conn_new.cursor()
            cur.execute(f"DROP TABLE IF EXISTS `{table}`")
            cur.execute(create_stmt)
            conn_new.commit()
            cur.close()

            # Copy data
            cur = conn_old.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM `{table}`")
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            cur.close()

            if rows:
                col_names = ", ".join(f"`{c}`" for c in cols)
                placeholders = ", ".join(["%s"] * len(cols))
                insert_sql = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
                cur = conn_new.cursor()
                for row in rows:
                    vals = [row[c] for c in cols]
                    cur.execute(insert_sql, vals)
                conn_new.commit()
                cur.close()
                print(f"  [OK] {table}: {len(rows)} rows migrated.")
            else:
                print(f"  [OK] {table}: 0 rows (empty).")
        except Exception as e:
            print(f"  [WARN] {table}: {e}")

    conn_old.close()
    conn_new.close()
    print("\n[DONE] All tables migrated to 'echoaction' database.")

if __name__ == "__main__":
    main()
