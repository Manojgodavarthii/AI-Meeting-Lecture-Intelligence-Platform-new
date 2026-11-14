import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='naga', database='echoaction')
cur = conn.cursor()
# Create admin security settings table
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
print('Table created')
cur.close()
conn.close()