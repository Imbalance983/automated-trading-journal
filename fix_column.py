# fix_column.py
with open("day8_trade_modal.py", "r") as f:
    content = f.read()

# Fix the column name
content = content.replace('level_name', 'name')

with open("day8_trade_modal.py", "w") as f:
    f.write(content)

print("✅ Fixed! Changed 'level_name' to 'name'")