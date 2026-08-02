import paramiko, tarfile, io, os, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

# Upload updated files
print("=== Uploading updated Dockerfile.prod and compose ===")
buf = io.BytesIO()
tf = tarfile.open(fileobj=buf, mode="w:gz")
tf.add("frontend/Dockerfile.prod", arcname="frontend/Dockerfile.prod")
tf.add("docker-compose.vps.yml", arcname="docker-compose.vps.yml")
tf.close()
data = buf.getvalue()

sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(data), "/tmp/fix-env.tar.gz")
sftp.close()

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err: print("ERR:", err[:200])

run("cd /opt/bottlecrm && tar -xzf /tmp/fix-env.tar.gz && rm /tmp/fix-env.tar.gz")
print("  Files updated.")

# Verify
print("\n=== Verify new Dockerfile ===")
run("grep -A2 'EXPOSE 3000' /opt/bottlecrm/frontend/Dockerfile.prod")
print("\n=== Verify compose env ===")
run("grep -A1 'PUBLIC_DJANGO' /opt/bottlecrm/docker-compose.vps.yml")

# Rebuild frontend
print("\n=== Rebuilding frontend (no cache) ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml stop frontend 2>&1")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml rm -f frontend 2>&1")
run("docker rmi bottlecrm-frontend 2>/dev/null; echo 'old image removed'")

print("  Building...")
stdin,stdout,stderr = ssh.exec_command("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml build --no-cache frontend 2>&1", get_pty=True)
import select
while not stdout.channel.exit_status_ready():
    if stdout.channel.recv_ready():
        out = stdout.channel.recv(4096).decode("utf-8", errors="replace")
        # Only print key lines
        for line in out.split("\n"):
            if any(k in line for k in ["DONE","CACHED","ERROR","builder","stage","exporting","naming"]):
                print(line.strip())
stdout.channel.recv_exit_status()

print("\n=== Starting frontend ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d frontend 2>&1")
time.sleep(20)

# Verify env var
print("\n=== Verify runtime env ===")
run("docker exec bottlecrm-frontend-1 sh -c 'echo PUBLIC_DJANGO_API_URL=$PUBLIC_DJANGO_API_URL'")

# Test login flow
print("\n=== Test login via frontend ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1/login?/password -H 'Host: crm.valerion.ir' -H 'Content-Type: application/x-www-form-urlencoded' -d 'phone=09136603902&password=admin123' -w '|HTTP:%{http_code}|SIZE:%{size_download}' 2>&1""")
out = stdout.read().decode().strip()
print(out[:200])
print("..." if len(out) > 200 else "")

ssh.close()
print("\n=== DONE - Try http://crm.valerion.ir/login/ ===")
