import paramiko, io, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err: print("ERR:", err[:200])

print("=== Verify compose URL ===")
run("grep PUBLIC_DJANGO_API_URL /opt/bottlecrm/docker-compose.vps.yml")

# Also add CORS origin to Django env
print("\n=== Adding CORS origins ===")
run("grep CORS_ALLOWED_ORIGINS /opt/bottlecrm/.env.docker || echo 'CORS_ALLOWED_ORIGINS not set'")
run("sed -i 's/^CORS_ALLOW_ALL=.*/CORS_ALLOW_ALL=False/' /opt/bottlecrm/.env.docker")
run("grep CORS_ALLOWED_ORIGINS /opt/bottlecrm/.env.docker || echo 'CORS_ALLOWED_ORIGINS=http://crm.valerion.ir,http://localhost:5173,http://localhost:3000' >> /opt/bottlecrm/.env.docker")
run("grep CSRF_TRUSTED_ORIGINS /opt/bottlecrm/.env.docker || echo 'CSRF_TRUSTED_ORIGINS=http://crm.valerion.ir,http://localhost:5173' >> /opt/bottlecrm/.env.docker")

print("\n=== Stopping frontend ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml stop frontend")

print("\n=== Removing old frontend image ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml rm -f frontend 2>&1")
run("docker rmi bottlecrm-frontend 2>/dev/null; echo 'Old image removed (if any)'")

print("\n=== Rebuilding frontend with correct API URL ===")
print("(this may take 2-3 minutes)...")
stdin, stdout, stderr = ssh.exec_command("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml build --no-cache frontend 2>&1", get_pty=True)
# Read output as it comes
import select
import sys
while not stdout.channel.exit_status_ready():
    if stdout.channel.recv_ready():
        out = stdout.channel.recv(4096).decode("utf-8", errors="replace")
        print(out, end="", flush=True)
stdout.channel.recv_exit_status()

print("\n=== Starting frontend ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d frontend 2>&1")

print("\n=== Waiting 30s ===")
time.sleep(30)

print("\n=== Verify frontend running ===")
run("docker logs bottlecrm-frontend-1 --tail=3 2>/dev/null")

print("\n=== Verify API URL in build ===")
run("docker exec bottlecrm-frontend-1 sh -c \"strings /app/build/index.js 2>/dev/null | grep -o 'http[s]*://fcrm.valerion.ir' | head -3\" 2>/dev/null || echo 'checking other files...'")
run("docker exec bottlecrm-frontend-1 sh -c \"grep -r 'fcrm.valerion.ir' /app/build/ 2>/dev/null | head -2\" || echo 'check done'")

# Restart backend for new CORS settings
print("\n=== Restarting backend for CORS ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --force-recreate backend 2>&1")

time.sleep(15)
print("\n=== Test via Nginx frontend -> backend ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -w '|HTTP:%{http_code}' -X POST http://127.0.0.1:8000/api/auth/phone-login/ -H "Content-Type: application/json" -H "Origin: http://crm.valerion.ir" -d '{"phone":"09136603902","password":"admin123"}' | head -c 100""")
print("CORS login test:", stdout.read().decode()[:150])

ssh.close()
print("\n\n=== DONE ===")
print("Frontend rebuilt with API → fcrm.valerion.ir")
print("Try: http://crm.valerion.ir/login/")
