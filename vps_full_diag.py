import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err and "docker-entrypoint" not in err: print("ERR:", err[:300])

# 1. All containers
print("=== 1. CONTAINERS ===")
run("docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")

# 2. Backend logs (last 20, errors only)
print("\n=== 2. BACKEND LOGS ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml logs backend --tail=30 2>&1")

# 3. Frontend logs
print("\n=== 3. FRONTEND LOGS ===")
run("docker logs bottlecrm-frontend-1 --tail=10 2>&1")

# 4. Nginx error log
print("\n=== 4. NGINX ERROR LOG ===")
run("tail -20 /var/log/nginx/error.log 2>/dev/null || echo 'no errors'")

# 5. Nginx access log recent
print("\n=== 5. NGINX ACCESS LOG (recent) ===")
run("tail -5 /var/log/nginx/access.log 2>/dev/null || echo 'no access log'")

# 6. Test login API directly with verbose output
print("\n=== 6. DIRECT API LOGIN TEST ===")
stdin,stdout,stderr = ssh.exec_command("""curl -v -X POST http://127.0.0.1:8000/api/auth/phone-login/ -H 'Content-Type: application/json' -d '{"phone":"09136603902","password":"admin123"}' 2>&1 | head -40""")
print(stdout.read().decode().strip())

# 7. Check database for user
print("\n=== 7. DATABASE - CHECK USER ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c \"python manage.py shell -c 'from common.models import User; u=User.objects.filter(phone=chr(57)+chr(49)+chr(51)+chr(51)+chr(54)+chr(54)+chr(48)+chr(51)+chr(57)+chr(48)+chr(50)).first(); print(f(\\\"FOUND: {u.email}, active={u.is_active}, super={u.is_superuser}, has_usable_pw={u.has_usable_password()}\\\")) if u else print(\\\"USER NOT FOUND\\\")'\" 2>&1")

# 8. Check org and profile
print("\n=== 8. DATABASE - CHECK ORG/PROFILE ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c \"python manage.py shell -c 'from common.models import Org, Profile; orgs=Org.objects.all(); print(f(\\\"Orgs: {orgs.count()}\\\")); profiles=Profile.objects.all(); print(f(\\\"Profiles: {profiles.count()}\\\"))'\" 2>&1")

ssh.close()
