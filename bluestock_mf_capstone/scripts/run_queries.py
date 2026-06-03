"""
Bluestock Mutual Fund Capstone Project - Day 2
SQL Query Execution Utility

This script reads sql/queries.sql, splits it into individual queries,
executes them against the SQLite database (bluestock_mf.db), and prints
the outputs in a clean DataFrame format.
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "scripts":
        project_root = script_dir.parent
    else:
        project_root = Path("bluestock_mf_capstone")
        
    db_path = project_root / "data" / "db" / "bluestock_mf.db"
    queries_path = project_root / "sql" / "queries.sql"
    
    if not db_path.exists():
        print(f"❌ [ERROR] Database not found at {db_path}")
        sys.exit(1)
    if not queries_path.exists():
        print(f"❌ [ERROR] SQL queries file not found at {queries_path}")
        sys.exit(1)
        
    print(f"⚙️ [INFO] Opening connection to SQLite database at {db_path.name}...")
    conn = sqlite3.connect(db_path)
    
    try:
        with open(queries_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        # Split by query separator (semicolon followed by newline)
        # We can identify individual queries
        raw_queries = sql_content.split(";")
        
        query_idx = 1
        for raw_q in raw_queries:
            q_stripped = raw_q.strip()
            if not q_stripped:
                continue
                
            # Extract query title from comments if possible
            title = f"Query {query_idx}"
            lines = q_stripped.split("\n")
            for line in lines:
                if line.startswith("-- Query"):
                    title = line.replace("--", "").strip()
                    break
                    
            print("\n" + "=" * 80)
            print(f"📊 {title}")
            print("=" * 80)
            
            # Execute
            try:
                # Add semicolon back
                sql_to_run = q_stripped + ";"
                df = pd.read_sql_query(sql_to_run, conn)
                print(df.to_string(index=False))
                print(f"   [INFO] Rows returned: {len(df)}")
            except Exception as e:
                print(f"❌ [ERROR] Failed to run query: {e}")
                print(f"SQL content:\n{q_stripped}")
                
            query_idx += 1
            
    except Exception as e:
        print(f"❌ [ERROR] Unexpected exception occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
