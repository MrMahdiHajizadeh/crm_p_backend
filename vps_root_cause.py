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

# 1. Can frontend container reach the backend?
print("=== 1. Frontend -> Backend connectivity ===")
run("docker exec bottlecrm-frontend-1 sh -c 'curl -s -o /dev/null -w %{http_code} http://fcrm.valerion.ir/api/auth/phone-login/ -H \"Content-Type: application/json\" -d \"{\\\"phone\\\":\\\"09136603902\\\",\\\"password\\\":\\\"admin123\\\"}\" --connect-timeout 5' 2>&1 || echo 'FAILED'")

# 2. DNS resolution from frontend
print("\n=== 2. DNS resolution ===")
run("docker exec bottlecrm-frontend-1 sh -c 'getent hosts fcrm.valerion.ir 2>/dev/null || nslookup fcrm.valerion.ir 2>/dev/null || echo NO_DNS'")

# 3. Check what PUBLIC_DJANGO_API_URL the frontend process sees
print("\n=== 3. Frontend env var ===")
run("docker exec bottlecrm-frontend-1 sh -c 'echo PUBLIC_DJANGO_API_URL=$PUBLIC_DJANGO_API_URL'")

# 4. RLS audit log error - fix it
print("\n=== 4. RLS audit log issue ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c \"python manage.py shell -c 'from common.models import User; u=User.objects.get(email=chr(97)+chr(100)+chr(109)+chr(105)+chr(110)+chr(50)+chr(64)+chr(108)+chr(111)+chr(99)+chr(97)+chr(108)+chr(104)+chr(111)+chr(115)+chr(116)); print(u.email, u.is_active)'\" 2>&1")

# 5. Check the 93-byte response
print("\n=== 5. Simulate full login flow ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1/login?/password -H 'Host: crm.valerion.ir' -H 'Content-Type: application/x-www-form-urlencoded' -d 'phone=09136603902&password=admin123' -w '|HTTP:%{http_code}|SIZE:%{size_download}' 2>&1""")
out = stdout.read().decode().strip()
print(out[:500])

ssh.close()
