import http.client, json

print("=== 1. Frontend login (crm.valerion.ir) ===")
conn = http.client.HTTPConnection("crm.valerion.ir", 80, timeout=10)
body = "phone=09136603902&password=admin123"
h = {"Content-Type": "application/x-www-form-urlencoded", "Origin": "http://crm.valerion.ir"}
conn.request("POST", "/login?/password", body=body, headers=h)
resp = conn.getresponse()
data = resp.read().decode()
print(f"  HTTP {resp.status} | Size: {len(data)} bytes")
# Check if it contains access_token
if "access" in data and len(data) > 200:
    print("  LOGIN SUCCESS - JWT token returned!")
elif "Login failed" in data:
    print("  LOGIN FAILED")
else:
    print(f"  Response: {data[:100]}")
conn.close()

print("\n=== 2. Frontend page ===")
conn = http.client.HTTPConnection("crm.valerion.ir", 80, timeout=10)
conn.request("GET", "/login")
resp = conn.getresponse()
print(f"  HTTP {resp.status}")
conn.close()

print("\n=== Try: http://crm.valerion.ir/login/ ===")
