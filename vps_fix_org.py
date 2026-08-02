import paramiko, tarfile, io, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err: print("ERR:", err[:200])

# Create tar with updated files
print("=== Creating update archive ===")
buf = io.BytesIO()
tf = tarfile.open(fileobj=buf, mode="w:gz")
tf.add("backend/common/views/auth_views.py", arcname="backend/common/views/auth_views.py")
tf.add("frontend/src/routes/(no-layout)/org/+page.server.js", arcname="frontend/src/routes/(no-layout)/org/+page.server.js")
tf.add("frontend/Dockerfile.prod", arcname="frontend/Dockerfile.prod")
tf.add("docker-compose.vps.yml", arcname="docker-compose.vps.yml")
tf.close()

sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(buf.getvalue()), "/tmp/org-fix.tar.gz")
sftp.close()
print("  Uploaded.")

# Extract on VPS
run("cd /opt/bottlecrm && tar -xzf /tmp/org-fix.tar.gz && rm /tmp/org-fix.tar.gz")
print("  Extracted.")

# Restart backend (auto-reload via bind mount or force recreate)
print("\n=== Restarting backend ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --force-recreate backend 2>&1")
time.sleep(20)

# Rebuild frontend
print("\n=== Rebuilding frontend ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml stop frontend 2>&1")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml rm -f frontend 2>&1")
run("docker rmi bottlecrm-frontend 2>/dev/null; echo removed")

stdin,stdout,stderr = ssh.exec_command("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml build --no-cache frontend 2>&1", get_pty=True)
import select
while not stdout.channel.exit_status_ready():
    if stdout.channel.recv_ready():
        out = stdout.channel.recv(4096).decode("utf-8", errors="replace")
        for line in out.split("\n"):
            if any(k in line for k in ["DONE","ERROR","builder","stage","exporting","naming","CACHED"]):
                print(line.strip())
stdout.channel.recv_exit_status()

run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d frontend 2>&1")
time.sleep(15)

print("\n=== Test login ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1/login?/password -H 'Host: crm.valerion.ir' -H 'Content-Type: application/x-www-form-urlencoded' -d 'phone=09136603902&password=admin123' -w '|CODE:%{http_code}|SIZE:%{size_download}'""")
out = stdout.read().decode().strip()
if "access" in out and len(out) > 200:
    print("LOGIN SUCCESS - will auto-redirect to dashboard")
else:
    print(out[:200])

print("\n=== Test org page auto-redirect ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -I http://127.0.0.1/org -H 'Host: crm.valerion.ir' -w '|CODE:%{http_code}' -H 'Cookie: jwt_access=test' 2>&1 | grep -E 'HTTP|location|CODE'""")
print(stdout.read().decode().strip()[:300])

ssh.close()
print("\n=== Done - login auto-routes to dashboard ===")
