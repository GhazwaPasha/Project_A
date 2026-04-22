#!/usr/bin/env python3
"""
Simple script to run the calculate_all_ratios function
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def run_ratios_function():
    """Run the calculate_all_ratios function"""

    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "accountuitive"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": os.getenv("DB_PORT", "5432"),
    }

    conn = None
    cur = None
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        sql_path = REPO_ROOT / "database" / "calculate_all_ratios.sql"
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        print("Creating/updating calculate_all_ratios function...")
        cur.execute(sql_content)
        conn.commit()
        print("✅ Function created successfully")

    except Exception as e:
        print(f"❌ Error: {e}")
        if conn is not None:
            conn.rollback()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    run_ratios_function()
