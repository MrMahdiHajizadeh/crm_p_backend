import http.client, json

# Test 1: API directly
print("=== 1. API login (fcrm.valerion.ir) ===")
conn = http.client.HTTPConnection("fcrm.valerion.ir", 80, timeout=10)
conn.request("POST", "/api/auth/phone-login/", json.dumps({"phone":"09136603902","password":"admin123"}), {"Content-Type":"application/json"})
resp = conn.getresponse()
body = json.loads(resp.read())
org = body.get("current_org", {}).get("name", "NO ORG")
print("  HTTP", resp.status, "| Org:", org)
conn.close()

# Test 2: CORS headers
print("\n=== 2. CORS check ===")
conn = http.client.HTTPConnection("fcrm.valerion.ir", 80, timeout=10)
h = {"Origin":"http://crm.valerion.ir","Access-Control-Request-Method":"POST"}
conn.request("OPTIONS", "/api/auth/phone-login/", headers=h)
resp = conn.getresponse()
print("  Allow-Origin:", resp.getheader("Access-Control-Allow-Origin","NONE"))
print("  Allow-Creds:", resp.getheader("Access-Control-Allow-Credentials","NONE"))
conn.close()

# Test 3: Frontend
print("\n=== 3. Frontend (crm.valerion.ir) ===")
conn = http.client.HTTPConnection("crm.valerion.ir", 80, timeout=10)
conn.request("GET", "/")
resp = conn.getresponse()
print("  HTTP", resp.status, "| Redirect:", resp.getheader("Location","none"))
conn.close()

print("\n=== Try: http://crm.valerion.ir/login/ ===")
