"""
Recreate all database tables after MySQL reinstallation.
This uses the existing schema definitions in db.py.
Run once: python recreate_db.py
"""
import mysql.connector
import sys

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "admin"
}

def main():
    print("=== EchoAction Database Recreator ===\n")

    # Step 1: Create the database
    print("[1/3] Creating database 'echoaction'...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS echoaction CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cur.close()
        conn.close()
        print("  OK - Database 'echoaction' created/verified.")
    except mysql.connector.Error as e:
        print(f"  ERROR connecting to MySQL: {e}")
        print("\n  Make sure MySQL is running and credentials are correct.")
        print(f"  Current config: user={DB_CONFIG['user']}, password={'*' * len(DB_CONFIG['password'])}")
        sys.exit(1)

    # Step 2: Run the full schema initialization from db.py
    print("\n[2/3] Creating all tables via db_init_auth_tables()...")
    try:
        from db import db_init_auth_tables
        db_init_auth_tables()
        print("  OK - Auth tables created.")
    except Exception as e:
        print(f"  ERROR in db_init_auth_tables: {e}")

    print("\n[3/3] Creating all enterprise tables via db_init_enterprise_tables()...")
    try:
        from db import db_init_enterprise_tables
        db_init_enterprise_tables()
        print("  OK - Enterprise tables created.")
    except Exception as e:
        print(f"  ERROR in db_init_enterprise_tables: {e}")

    # Verify
    print("\n=== Verifying tables ===")
    try:
        DB_CONFIG["database"] = "echoaction"
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tables = sorted([t[0] for t in cur.fetchall()])
        print(f"Total tables created: {len(tables)}\n")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{t}`")
            count = cur.fetchone()[0]
            print(f"  {t} ({count} rows)")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  Verification error: {e}")

    print("\n[DONE] All database tables recreated successfully!")
    print("Default admin seeded: admin@echoaction.ai / Admin@123")
    print("Default root admin seeded: godaverthinagamanojbalaji@gmail.com")

if __name__ == "__main__":
    main()
