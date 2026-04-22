#!/usr/bin/env python3
"""
Script to set up the calculate_all_ratios function in the database
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def setup_ratios_function():
    """Set up the calculate_all_ratios function in the database"""

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

        sql_file_path = REPO_ROOT / "database" / "calculate_all_ratios.sql"
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        print("Creating calculate_all_ratios function...")
        cur.execute(sql_content)

        conn.commit()
        print("✅ Successfully created calculate_all_ratios function")

        print("Testing the function...")
        cur.execute(
            """
            SELECT calculate_all_ratios(
                '00000000-0000-0000-0000-000000000000'::uuid,
                CURRENT_DATE - INTERVAL '30 days',
                CURRENT_DATE,
                CURRENT_DATE
            )
        """
        )

        result = cur.fetchone()
        if result:
            print("✅ Function test successful")
            print(f"Sample result: {result[0]}")
        else:
            print("⚠️  Function test returned no result")

    except Exception as e:
        print(f"❌ Error setting up ratios function: {e}")
        if conn is not None:
            conn.rollback()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    setup_ratios_function()
