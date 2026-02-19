"""Extract the relevant error info from debug_output.txt."""
import os

try:
    with open("debug_output.txt", "r", encoding="utf-16-le") as f:
        content = f.read()
except:
    with open("debug_output.txt", "r", encoding="utf-8") as f:
        content = f.read()

# Write to a simple ASCII file
with open("error_extract.txt", "w", encoding="ascii", errors="replace") as f:
    f.write(content)

print("Extracted. Lines:")
lines = content.strip().split("\n")
for i, line in enumerate(lines):
    print(f"  {i}: {line.strip()}")
