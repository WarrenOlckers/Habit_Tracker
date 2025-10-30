import psycopg2
from psycopg2 import sql

# Connect to the default 'postgres' database as a superuser
conn = psycopg2.connect(
    dbname="postgres",
    user="tutor",         # Replace with your superuser name
    password="warren", # Replace with your password
    host="localhost",
    port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

# Create the database
db_name = "habitdb"
try:
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    print(f"Database '{db_name}' created successfully.")
except psycopg2.errors.DuplicateDatabase:
    print(f"Database '{db_name}' already exists.")

cursor.close()
conn.close()