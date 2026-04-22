#!/usr/bin/env python3
"""
Script to set up all report generation functions in the database
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def setup_reports_functions():
    """Set up all report generation functions in the database"""

    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "accountuitive"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": os.getenv("DB_PORT", "5432"),
    }

    sql_names = [
        "get_balance_sheet_data.sql",
        "get_income_statement_data.sql",
        "get_trial_balance_data.sql",
        "get_aged_receivables_data.sql",
        "get_aged_payables_data.sql",
    ]

    conn = None
    cur = None
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        for name in sql_names:
            sql_file = REPO_ROOT / "database" / name
            print(f"Creating function from {sql_file}...")
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            cur.execute(sql_content)
            print(f"✅ Successfully created function from {sql_file}")

        conn.commit()
        print("✅ All report functions created successfully")

        print("Testing get_balance_sheet_data function...")
        cur.execute(
            """
            SELECT get_balance_sheet_data(
                '00000000-0000-0000-0000-000000000000'::uuid,
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
        print(f"❌ Error setting up report functions: {e}")
        if conn is not None:
            conn.rollback()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    setup_reports_functions()
