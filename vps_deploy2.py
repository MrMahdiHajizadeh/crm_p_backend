"""
VPS Deployment Script - Tar-based transfer
"""
import paramiko
import sys
import os
import tarfile
import io
import time

HOST = "188.209.138.33"
PORT = 22
USER = "root"
PASS = "pcJOm45Ijao1xlv"
LOCAL_BASE = r"c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM"
REMOTE_DIR = "/opt/bottlecrm"

EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'media', 'staticfiles', 'htmlcov', '.pytest_cache', 'node_modules', 'frontend', 'mcp_server', 'mobile'}
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
        print(out)
    if err:
        print("STDERR:", err)
    return out, err

def create_tar_bytes():
    """Create tar.gz in memory with only needed files."""
    buf = io.BytesIO()
    tf = tarfile.open(fileobj=buf, mode='w:gz')
    
    files_to_include = [
        'Dockerfile',
        'docker-compose.vps.yml',
        '.env.docker',
    ]
    
    for f in files_to_include:
        path = os.path.join(LOCAL_BASE, f)
        if os.path.exists(path):
            print(f'  Adding: {f}')
            tf.add(path, arcname=f)
    
    # Add docker/ directory
    docker_dir = os.path.join(LOCAL_BASE, 'docker')
    if os.path.exists(docker_dir):
        for root, dirs, files in os.walk(docker_dir):
            for d in list(dirs):
                if d in EXCLUDE_DIRS:
                    dirs.remove(d)
            for f in files:
                if f in EXCLUDE_FILES:
                    continue
                path = os.path.join(root, f)
                arcname = os.path.relpath(path, LOCAL_BASE).replace('\\', '/')
                print(f'  Adding: {arcname}')
                tf.add(path, arcname=arcname)
    
    # Add backend/ directory (with exclusions)
    backend_dir = os.path.join(LOCAL_BASE, 'backend')
    if os.path.exists(backend_dir):
        for root, dirs, files in os.walk(backend_dir):
            # Filter dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f in EXCLUDE_FILES:
                    continue
                if f.endswith('.pyc'):
                    continue
                path = os.path.join(root, f)
                arcname = os.path.relpath(path, LOCAL_BASE).replace('\\', '/')
                tf.add(path, arcname=arcname)
    
    tf.close()
    data = buf.getvalue()
    print(f'  Total archive size: {len(data) / 1024 / 1024:.2f} MB')
    return data

if __name__ == '__main__':
    print("=== Creating deployment archive ===")
    tar_data = create_tar_bytes()
    
    print("\n=== Connecting to VPS ===")
    ssh = connect()
    
    print("=== Uploading archive ===")
    # Upload via SFTP
    sftp = ssh.open_sftp()
    remote_tar = '/tmp/deploy.tar.gz'
    sftp.putfo(io.BytesIO(tar_data), remote_tar)
    sftp.close()
    print("  Upload complete.")
    
    print("\n=== Preparing remote directory ===")
    run_cmd(ssh, f'rm -rf {REMOTE_DIR} && mkdir -p {REMOTE_DIR}')
    
    print("=== Extracting archive ===")
    run_cmd(ssh, f'cd {REMOTE_DIR} && tar -xzf /tmp/deploy.tar.gz && rm /tmp/deploy.tar.gz && ls -la')
    
    print("\n=== Running docker compose ===")
    run_cmd(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml up -d --build 2>&1', print_output=False)
    
    print("  Waiting 30s for services to start...")
    time.sleep(30)
    
    print("\n=== Checking containers ===")
    run_cmd(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml ps 2>&1')
    
    print("\n=== Backend logs (last 40 lines) ===")
    run_cmd(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml logs backend --tail=40 2>&1')
    
    ssh.close()
    
    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE")
    print("="*60)
    print("Backend API : http://188.209.138.33:8000")
    print("Swagger UI : http://188.209.138.33:8000/swagger-ui/")
    print("Admin      : http://188.209.138.33:8000/admin/")
    print("Login      : admin@localhost / admin")
