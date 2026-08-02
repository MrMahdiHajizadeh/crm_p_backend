import paramiko
import os

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"

FILES_TO_SYNC = [
    ".env.docker",
    "backend/common/models.py",
    "backend/common/views/auth_views.py",
    "frontend/src/routes/(no-layout)/org/+page.server.js"
]

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

    sftp = ssh.open_sftp()
    
    # Base local path
    local_base = r"C:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM"
    remote_base = "/opt/bottlecrm"

    for file_path in FILES_TO_SYNC:
        local_path = os.path.join(local_base, file_path.replace('/', '\\'))
        remote_path = f"{remote_base}/{file_path}"
        
        print(f"Uploading {local_path} -> {remote_path}")
        sftp.put(local_path, remote_path)

    sftp.close()

    print("Restarting containers...")
    run_cmd(ssh, "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --build backend frontend")

    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
