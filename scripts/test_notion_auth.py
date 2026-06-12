import subprocess, json, sys

with open(r"C:\Users\Admin\.hermes\.env") as f:
    for line in f:
        line = line.strip()
        if "NOTION_API_KEY" in line and "=" in line:
            key = line.split("=", 1)[1].strip()
            break

print(f"Key found: {key[:10]}... (len={len(key)})")

# Test auth
result = subprocess.run([
    "curl", "-s", "-X", "GET",
    "https://api.notion.com/v1/users/me",
    "-H", "Authorization: Bearer " + key,
    "-H", "Notion-Version: 2022-06-28",
], capture_output=True, text=True)
print("Auth test:", result.stdout[:300])
