import http.client, json

print("=== Test login ===")
conn = http.client.HTTPConnection("crm.valerion.ir", 80, timeout=10)
body = "phone=09136603902&password=admin123"
conn.request("POST", "/login?/password", body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
resp = conn.getresponse()
data = resp.read().decode()
if "access" in data and len(data) > 200:
    print("  LOGIN SUCCESS!")
elif "Login failed" in data:
    print("  LOGIN FAILED:", data[:100])
else:
    print("  HTTP", resp.status, "|", data[:100])
conn.close()
