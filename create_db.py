import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='quoctrang',
    database='postgres'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

cursor = conn.cursor()

# Check if database exists
cursor.execute("SELECT 1 FROM pg_database WHERE datname='ai_tutor'")
exists = cursor.fetchone()

if not exists:
    print("Creating database 'ai_tutor'...")
    cursor.execute("CREATE DATABASE ai_tutor")
    print("Database created successfully!")
else:
    print("Database 'ai_tutor' already exists.")

cursor.close()
conn.close()
print("Done!")
