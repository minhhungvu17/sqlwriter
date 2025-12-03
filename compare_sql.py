#!/usr/bin/env python3
"""Compare the working SQL file with the SQL in seed_qna.csv"""

import csv

# Read the SQL from seed_qna.csv (row 2, column 1, which is index [2][1])
with open('business/seed_qna.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)
    seed_sql = rows[2][1]  # Row 2 (0-indexed) is the 3rd row, column 1 (SQL)

# Read the working SQL file
with open('/Users/vu.minh.hung/Downloads/cohortmatching.sql', 'r', encoding='utf-8') as f:
    working_sql = f.read()

# Compare lengths
print(f"Working SQL length: {len(working_sql)}")
print(f"Seed SQL length: {len(seed_sql)}")
print(f"Length difference: {abs(len(working_sql) - len(seed_sql))}")

# Check if they're identical
if working_sql == seed_sql:
    print("✅ SQLs are IDENTICAL")
else:
    print("❌ SQLs are DIFFERENT")
    # Find first difference
    for i, (w, s) in enumerate(zip(working_sql, seed_sql)):
        if w != s:
            print(f"\nFirst difference at position {i}:")
            print(f"  Working: {repr(w)}")
            print(f"  Seed: {repr(s)}")
            start = max(0, i-50)
            end = min(len(working_sql), i+50)
            print(f"  Context (working): ...{working_sql[start:end]}...")
            print(f"  Context (seed): ...{seed_sql[start:end]}...")
            break

# Check for problematic characters
print("\nChecking for problematic characters in seed SQL:")
has_cr = '\r' in seed_sql
has_nl = '\n' in seed_sql
has_tab = '\t' in seed_sql
has_nonascii = any(ord(c) > 127 for c in seed_sql)
print(f"  Has \\r (carriage return): {has_cr}")
print(f"  Has \\n (newline): {has_nl}")
print(f"  Has \\t (tab): {has_tab}")
print(f"  Has non-ASCII: {has_nonascii}")

# Check query type detection
query_type_seed = seed_sql.strip().upper().split()[0]
query_type_working = working_sql.strip().upper().split()[0]
print(f"\nQuery type detection:")
print(f"  Seed: {query_type_seed}")
print(f"  Working: {query_type_working}")

