import http.client

# Test login
print("=== Login test ===")
conn = http.client.HTTPConnection("crm.valerion.ir", 80, timeout=10)
conn.request("POST", "/login?/password", body="phone=09136603902&password=admin123",
    headers={"Content-Type": "application/x-www-form-urlencoded"})
resp = conn.getresponse()
data = resp.read().decode()
if "access" in data and len(data) > 200:
    print("  LOGIN SUCCESS - auto-assigned to Default Org")
else:
    print("  Response:", data[:100])
conn.close()
