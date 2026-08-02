import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("ERR:", err[:200])

print("=== 1. Frontend container ===")
run("docker ps --filter name=bottlecrm-frontend --format '{{.Status}}'")

print("\n=== 2. Runtime env ===")
run("docker exec bottlecrm-frontend-1 sh -c 'echo PUBLIC_DJANGO_API_URL=$PUBLIC_DJANGO_API_URL'")

print("\n=== 3. Test login via frontend ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1/login?/password -H 'Host: crm.valerion.ir' -H 'Content-Type: application/x-www-form-urlencoded' -d 'phone=09136603902&password=admin123' -w '|SIZE:%{size_download}|CODE:%{http_code}'""")
print(stdout.read().decode().strip()[:300])

print("\n=== 4. Frontend logs ===")
run("docker logs bottlecrm-frontend-1 --tail=5 2>&1")

# If login still returns small response, check connectivity
print("\n=== 5. Test backend from frontend container ===")
run("docker exec bottlecrm-frontend-1 sh -c 'wget -q -O - --post-data=\"{\"phone\":\"09136603902\",\"password\":\"admin123\"}\" --header=\"Content-Type: application/json\" http://fcrm.valerion.ir/api/auth/phone-login/ 2>&1 | head -c 80 || echo FAILED'")

ssh.close()
