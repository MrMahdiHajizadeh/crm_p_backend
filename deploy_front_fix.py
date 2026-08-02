import paramiko

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"

def run_cmd(ssh, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out.encode('cp1252', errors='replace').decode('cp1252'))
    if err: print("ERR:", err.encode('cp1252', errors='replace').decode('cp1252'))
    return out, err

try:
    print("Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)

    print("Pulling latest code and restarting frontend container...")
    run_cmd(ssh, "cd /opt/bottlecrm && git pull origin main")
    run_cmd(ssh, "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --build frontend")

    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
