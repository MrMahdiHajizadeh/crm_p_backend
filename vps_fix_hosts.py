"""Fix ALLOWED_HOSTS and restart backend"""
import paramiko

HOST = "188.209.138.33"
USER = "root"
PASS = "pcJOm45Ijao1xlv"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, 22, USER, PASS, timeout=60, banner_timeout=60, auth_timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("ERR:", err)

print("=== Current ALLOWED_HOSTS ===")
run("grep ALLOWED_HOSTS /opt/bottlecrm/.env.docker")

print("\n=== Updating ALLOWED_HOSTS ===")
# Use sed to replace the line
run(r"sed -i 's/^ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,backend,crm.valerion.ir/' /opt/bottlecrm/.env.docker")

print("\n=== Updated ALLOWED_HOSTS ===")
run("grep ALLOWED_HOSTS /opt/bottlecrm/.env.docker")

print("\n=== Restarting backend container ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --force-recreate backend 2>&1")

import time
print("\n=== Waiting 30s for restart ===")
time.sleep(30)

print("\n=== Backend logs (last 5) ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml logs backend --tail=5 2>&1")

print("\n=== Testing via domain ===")
run("curl -s -o /dev/null -w 'HTTP %{http_code}' -H 'Host: crm.valerion.ir' http://127.0.0.1:8000/swagger-ui/")

ssh.close()
print("\nDone!")
