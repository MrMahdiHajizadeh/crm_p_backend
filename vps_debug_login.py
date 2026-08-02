"""Debug login issue on VPS"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60, banner_timeout=60, auth_timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("ERR:", err)

# Test phone login
print("=== Phone login ===")
run("""curl -s -w '\\nHTTP:%{http_code}' -X POST http://127.0.0.1:8000/api/auth/login/ -H 'Content-Type: application/json' -d '{"phone":"09136603902","password":"admin123"}'""")

# Test email login
print("\n=== Email login ===")
run("""curl -s -w '\\nHTTP:%{http_code}' -X POST http://127.0.0.1:8000/api/auth/login/ -H 'Content-Type: application/json' -d '{"email":"admin2@localhost","password":"admin123"}'""")

# Test with org context (login might need org)
print("\n=== Email login with org header ===")
run("""curl -s -w '\\nHTTP:%{http_code}' -X POST http://127.0.0.1:8000/api/auth/login/ -H 'Content-Type: application/json' -H 'X-Org-ID: 1' -d '{"email":"admin2@localhost","password":"admin123"}'""")

# Check backend logs
print("\n=== Backend logs ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml logs backend --tail=15 2>&1 | grep -i -E 'error|login|auth|400|500|forbidden' || echo 'No errors'")

# Check if user has an org
print("\n=== User org check ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell -c \"from common.models import User; u = User.objects.get(phone=chr(57)+chr(49)+chr(51)+chr(51)+chr(54)+chr(54)+chr(48)+chr(51)+chr(57)+chr(48)+chr(50)); print(f(\\\"Email: {u.email}, Has org: {u.profile_set.exists()}\\\"))\"' 2>/dev/null || echo 'check-failed'")

ssh.close()
