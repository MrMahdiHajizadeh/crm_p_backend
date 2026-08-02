"""
VPS Deployment Script for Backend
"""
import paramiko
import sys

HOST = "188.209.138.33"
PORT = 22
USER = "root"
PASS = "pcJOm45Ijao1xlv"

def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30)
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

if len(sys.argv) < 2:
    print("Usage: python vps_deploy.py [check|clean|deploy]")
    sys.exit(1)

action = sys.argv[1]

if action == "check":
    ssh = connect()
    print("=== Disk Usage ===")
    run_cmd(ssh, 'du -sh /var/lib/docker/* 2>/dev/null | sort -rh | head -10')
    print("=== Docker System DF ===")
    run_cmd(ssh, 'docker system df 2>/dev/null')
    print("=== Docker Containers ===")
    run_cmd(ssh, 'docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null')
    print("=== Top 20 dirs ===")
    run_cmd(ssh, 'du -sh /* 2>/dev/null | sort -rh | head -20')
    ssh.close()

elif action == "clean":
    ssh = connect()
    print("=== Cleaning Docker system ===")
    run_cmd(ssh, 'docker system prune -af --volumes 2>&1')
    print("=== Cleaning apt cache ===")
    run_cmd(ssh, 'apt-get clean 2>&1')
    run_cmd(ssh, 'apt-get autoremove -y 2>&1')
    print("=== Removing old logs ===")
    run_cmd(ssh, 'journalctl --vacuum-size=50M 2>&1')
    run_cmd(ssh, 'find /var/log -type f -name "*.log" -exec truncate -s 0 {} \; 2>/dev/null')
    print("=== Disk after cleanup ===")
    run_cmd(ssh, 'df -h /')
    ssh.close()

elif action == "deploy":
    ssh = connect()
    print("=== Creating project directory ===")
    run_cmd(ssh, 'mkdir -p /opt/bottlecrm && rm -rf /opt/bottlecrm/*')
    
    print("=== Uploading files via SCP ===")
    sftp = ssh.open_sftp()
    import os
    local_base = r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM'
    
    # Upload backend
    backend_src = os.path.join(local_base, 'backend')
    for root, dirs, files in os.walk(backend_src):
        # Skip .venv, __pycache__, .git, media, staticfiles, htmlcov, .pytest_cache, node_modules, server.log, security_audit.log
        rel = os.path.relpath(root, local_base)
        dirs[:] = [d for d in dirs if d not in ('.venv', '__pycache__', '.git', 'media', 'staticfiles', 'htmlcov', '.pytest_cache', 'node_modules')]
        target_dir = '/opt/bottlecrm/' + rel.replace('\\', '/')
        try:
            sftp.mkdir(target_dir)
        except:
            pass
        for f in files:
            if f in ('server.log', 'security_audit.log', '.coverage', 'coverage.xml', 'db.sqlite3'):
                continue
            if f.endswith('.pyc'):
                continue
            local_path = os.path.join(root, f)
            remote_path = target_dir + '/' + f
            print(f'  Uploading: {rel}/{f}')
            try:
                sftp.put(local_path, remote_path)
            except Exception as e:
                print(f'  ERROR: {e}')
    
    # Upload Docker files
    for fname in ['Dockerfile', '.env.docker', 'docker-compose.vps.yml']:
        local = os.path.join(local_base, fname)
        remote = f'/opt/bottlecrm/{fname}'
        print(f'  Uploading: {fname}')
        sftp.put(local, remote)
    
    # Upload docker dir
    docker_dir = os.path.join(local_base, 'docker')
    for root, dirs, files in os.walk(docker_dir):
        rel = os.path.relpath(root, local_base)
        target_dir = '/opt/bottlecrm/' + rel.replace('\\', '/')
        try:
            sftp.mkdir(target_dir)
        except:
            pass
        for f in files:
            local_path = os.path.join(root, f)
            remote_path = target_dir + '/' + f
            print(f'  Uploading: {rel}/{f}')
            sftp.put(local_path, remote_path)
    
    sftp.close()
    
    print("=== Running docker compose ===")
    run_cmd(ssh, 'cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --build 2>&1', print_output=False)
    
    # Wait for build and startup
    import time
    time.sleep(15)
    
    print("=== Checking containers ===")
    run_cmd(ssh, 'cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml ps 2>&1')
    
    print("=== Backend logs (last 40 lines) ===")
    out, _ = run_cmd(ssh, 'cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml logs backend --tail=40 2>&1')
    print(out)
    
    ssh.close()
    print("\n=== DEPLOYMENT COMPLETE ===")
    print("Backend API: http://188.209.138.33:8000")
    print("Swagger UI: http://188.209.138.33:8000/swagger-ui/")
