import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

print("Cleaning duplicates before adding UNIQUE constraint...")

# Step 1: Identify and keep only the first occurrence of each external_id
cursor.execute('''
    DELETE FROM trades 
    WHERE id NOT IN (
        SELECT MIN(id) FROM trades 
        GROUP BY external_id 
    )
''')

deleted_count = cursor.rowcount
print(f"Deleted {deleted_count} duplicate trades")

conn.commit()
conn.close()

print("✅ Duplicates cleaned!")
print("🎯 Now adding UNIQUE constraint...")
