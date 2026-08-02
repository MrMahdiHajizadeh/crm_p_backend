import paramiko
import sys
import os
import tarfile
import io
import time

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"
LOCAL_BASE = r"c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM"
REMOTE_DIR = "/opt/bottlecrm"

EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'media', 'staticfiles', 'htmlcov', '.pytest_cache', 'node_modules', 'mcp_server', 'mobile', '.svelte-kit', 'build', '.pnpm-store'}
EXCLUDE_FILES = {'server.log', 'security_audit.log', '.coverage', 'coverage.xml', 'db.sqlite3', '.env'}

def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)
    return ssh

def run_cmd(ssh, cmd, print_output=True):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if print_output:
        print(out.strip().encode('cp1252', errors='replace').decode('cp1252'))
    if err and print_output:
        print("STDERR:", err.strip().encode('cp1252', errors='replace').decode('cp1252'))
    return out, err

def create_tar_bytes():
    print("Creating archive...")
    buf = io.BytesIO()
    tf = tarfile.open(fileobj=buf, mode='w:gz')
    
    files_to_include = ['Dockerfile', 'docker-compose.vps.yml', '.env.docker']
    for f in files_to_include:
        path = os.path.join(LOCAL_BASE, f)
        if os.path.exists(path):
            tf.add(path, arcname=f)
    
    for folder in ['docker', 'backend', 'frontend']:
        folder_dir = os.path.join(LOCAL_BASE, folder)
        if os.path.exists(folder_dir):
            for root, dirs, files in os.walk(folder_dir):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f in EXCLUDE_FILES or f.endswith('.pyc'):
                        continue
                    path = os.path.join(root, f)
                    arcname = os.path.relpath(path, LOCAL_BASE).replace('\\', '/')
                    tf.add(path, arcname=arcname)
    
    tf.close()
    data = buf.getvalue()
    print(f'Archive size: {len(data) / 1024 / 1024:.2f} MB')
    return data

if __name__ == '__main__':
    tar_data = create_tar_bytes()
    print("\nConnecting to server...")
    ssh = connect()
    
    print("\nChecking for Docker...")
    out, err = run_cmd(ssh, 'command -v docker')
    if not out.strip():
        print("Docker not found. Installing Docker...")
        run_cmd(ssh, 'curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh')
        run_cmd(ssh, 'systemctl enable --now docker')
    else:
        print("Docker is already installed.")
    
    print("\nUploading archive...")
    sftp = ssh.open_sftp()
    sftp.putfo(io.BytesIO(tar_data), '/tmp/deploy.tar.gz')
    sftp.close()
    
    print("Extracting archive...")
    run_cmd(ssh, f'rm -rf {REMOTE_DIR} && mkdir -p {REMOTE_DIR}')
    run_cmd(ssh, f'cd {REMOTE_DIR} && tar -xzf /tmp/deploy.tar.gz && rm /tmp/deploy.tar.gz')
    
    print("Building and running docker compose...")
    run_cmd(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml up -d --build 2>&1')
    
    print("Waiting 15s...")
    time.sleep(15)
    
    print("Checking containers...")
    run_cmd(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml ps 2>&1')
    
    ssh.close()
    print("Deployment script finished.")
