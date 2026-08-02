"""
Split domains: crm.valerion.ir → frontend, fcrm.valerion.ir → backend
"""
import paramiko
import os
import tarfile
import io
import time

HOST = "188.209.138.33"
USER = "root"
PASS = "pcJOm45Ijao1xlv"
LOCAL_BASE = r"c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM"
REMOTE_DIR = "/opt/bottlecrm"

# Nginx config: two server blocks
NGINX_CONFIG = r"""
# Frontend: crm.valerion.ir
server {
    listen 80;
    server_name crm.valerion.ir;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API: fcrm.valerion.ir
server {
    listen 80;
    server_name fcrm.valerion.ir;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_redirect off;
    }
}
"""

def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, 22, USER, PASS, timeout=60, banner_timeout=60, auth_timeout=60)
    return ssh

def run(ssh, cmd, print_output=True):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if print_output and out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

ssh = connect()

# 1. Update Nginx config
print("=== Updating Nginx config ===")
cmd = f"cat > /etc/nginx/sites-available/crm.valerion.ir << 'EOF'\n{NGINX_CONFIG}\nEOF"
run(ssh, cmd)
run(ssh, "nginx -t 2>&1")
run(ssh, "systemctl reload nginx 2>&1 && echo 'Nginx reloaded.'")

# 2. Update ALLOWED_HOSTS for Django
print("\n=== Updating Django ALLOWED_HOSTS ===")
run(ssh, r"sed -i 's/^ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,backend,crm.valerion.ir,fcrm.valerion.ir/' /opt/bottlecrm/.env.docker")
run(ssh, "grep ALLOWED_HOSTS /opt/bottlecrm/.env.docker")

# 3. Rebuild frontend with new API URL
print("\n=== Rebuilding frontend with fcrm.valerion.ir ===")

# Update docker-compose.vps.yml with new API URL
run(ssh, r"sed -i 's|PUBLIC_DJANGO_API_URL: .*|PUBLIC_DJANGO_API_URL: http://fcrm.valerion.ir|' /opt/bottlecrm/docker-compose.vps.yml")
run(ssh, "grep PUBLIC_DJANGO_API_URL /opt/bottlecrm/docker-compose.vps.yml")

# Restart backend with new ALLOWED_HOSTS
print("\n=== Restarting backend ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml up -d --force-recreate backend 2>&1', print_output=False)

# Rebuild frontend
print("\n=== Rebuilding frontend ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml up -d --build --force-recreate frontend 2>&1', print_output=False)

print("  Waiting 90s for build + startup...")
time.sleep(90)

# Check containers
print("\n=== Container status ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml ps 2>&1')

# Check frontend logs
print("\n=== Frontend logs ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml logs frontend --tail=5 2>&1')

# Check backend logs
print("\n=== Backend logs ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml logs backend --tail=5 2>&1')

ssh.close()

print("\n" + "=" * 60)
print("DONE - Split domain setup")
print("=" * 60)
print("Frontend : http://crm.valerion.ir   → port 3000 (SvelteKit)")
print("Backend  : http://fcrm.valerion.ir  → port 8000 (Django)")
print("Swagger  : http://fcrm.valerion.ir/swagger-ui/")
print("Admin    : http://fcrm.valerion.ir/admin/")
