#!/usr/bin/env python
from backend.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

# Check existing voters
cursor.execute('SELECT id, voter_id, name, email, password, is_verified FROM voters')
voters = cursor.fetchall()

print("=== EXISTING VOTERS ===")
if voters:
    for v in voters:
        print(f"Voter ID: {v['voter_id']}")
        print(f"  Name: {v['name']}")
        print(f"  Email: {v['email']}")
        print(f"  Password: {v['password']}")
        print(f"  Verified: {v['is_verified']}")
        print()
else:
    print("No voters found!")
    print("\n=== CREATING TEST VOTER ===")
    # Create a test voter
    cursor.execute(
        "INSERT INTO voters (voter_id, name, email, password, is_verified) VALUES (%s, %s, %s, %s, %s)",
        ("V001", "Test Voter", "voter@example.com", "password123", 1)
    )
    conn.commit()
    print("Created test voter:")
    print("  Voter ID: V001")
    print("  Password: password123")
    print("  Email: voter@example.com")

cursor.close()
conn.close()
