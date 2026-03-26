"""
MySQL database setup for AI Trading Analytics.

Creates DB and tables from schema/schema.sql. Uses config.DB_* credentials.
Run from the AI trading analytics folder: python setup_database.py. For SQLite use scripts/setup_sqlite.py.
"""

import os
import mysql.connector
from mysql.connector import Error
import config


def create_database_and_tables():
    """Create MySQL database and tables from schema/schema.sql. Returns True on success."""
    print("=" * 50)
    print("AI Trading Analytics - Database Setup")
    print("=" * 50)
    try:
        print("\n1. Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            port=config.DB_PORT
        )
        
        if not connection.is_connected():
            print("✗ Failed to connect to MySQL server!")
            return False
        
        print("✓ Connected to MySQL server successfully!")
        cursor = connection.cursor()
        print(f"\n2. Creating database '{config.DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
        print(f"✓ Database '{config.DB_NAME}' ready!")
        cursor.execute(f"USE {config.DB_NAME}")
        print("\n3. Creating tables from schema/schema.sql...")
        schema_path = os.path.join(os.path.dirname(__file__), 'schema', 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        statements = []
        for statement in sql_script.split(';'):
            statement = statement.strip()
            if statement and not all(line.strip().startswith('--') or line.strip() == ''
                                    for line in statement.split('\n')):
                statements.append(statement)
        for statement in statements:
            try:
                if 'CREATE DATABASE' in statement.upper() or statement.strip().upper().startswith('USE '):
                    continue
                cursor.execute(statement)
                if 'CREATE TABLE' in statement.upper():
                    table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                    print(f"  ✓ Created table: {table_name}")
            except Error as e:
                if 'already exists' not in str(e).lower():
                    print(f"  ⚠ Warning: {e}")
        
        connection.commit()
        print("\n4. Committing changes...")
        print("✓ All tables created successfully!")
        print("\n5. Verifying tables...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\nCreated tables:")
        for table in tables:
            print(f"  • {table[0]}")
        
        print("\n" + "=" * 50)
        print("✓ Database setup completed successfully!")
        print("=" * 50)
        print("\nYou can now run: python app.py")
        
        return True
        
    except Error as e:
        print(f"\n✗ Error during database setup: {e}")
        return False
        
    except FileNotFoundError:
        print("\n✗ Error: schema/schema.sql not found. Run from project root.")
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    success = create_database_and_tables()
    if not success:
        print("\n⚠ Setup failed. Check MySQL credentials in config.py.")
        exit(1)

