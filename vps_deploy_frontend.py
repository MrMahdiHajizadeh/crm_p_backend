"""
Deploy frontend + updated Nginx + compose to VPS
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

NGINX_CONFIG = """server {
    listen 80;
    server_name crm.valerion.ir;

    client_max_body_size 50M;

    # Proxy API, admin, static to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /media/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /swagger-ui/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # Everything else goes to frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

# Create tar with frontend and updated compose file
print("=== Creating deployment archive ===")
buf = io.BytesIO()
tf = tarfile.open(fileobj=buf, mode='w:gz')

# Add frontend (excluding node_modules, .svelte-kit, build)
frontend_dir = os.path.join(LOCAL_BASE, 'frontend')
exclude = {'.svelte-kit', 'node_modules', 'build', '.git', '.env', 'staticfiles'}
for root, dirs, files in os.walk(frontend_dir):
    dirs[:] = [d for d in dirs if d not in exclude]
    for f in files:
        path = os.path.join(root, f)
        arcname = os.path.relpath(path, LOCAL_BASE).replace('\\', '/')
        tf.add(path, arcname=arcname)

# Add updated compose file
tf.add(os.path.join(LOCAL_BASE, 'docker-compose.vps.yml'), arcname='docker-compose.vps.yml')

tf.close()
data = buf.getvalue()
print(f"  Archive size: {len(data) / 1024 / 1024:.2f} MB")

# Connect and deploy
print("\n=== Connecting to VPS ===")
ssh = connect()

print("=== Uploading ===")
sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(data), '/tmp/frontend-deploy.tar.gz')
sftp.close()
print("  Upload complete.")

print("=== Extracting frontend ===")
run(ssh, f'cd {REMOTE_DIR} && tar -xzf /tmp/frontend-deploy.tar.gz && rm /tmp/frontend-deploy.tar.gz')
run(ssh, f'ls {REMOTE_DIR}/frontend/ | head -10')

print("\n=== Updating Nginx config ===")
cmd = f"cat > /etc/nginx/sites-available/crm.valerion.ir << 'EOF'\n{NGINX_CONFIG}\nEOF"
run(ssh, cmd)
print("  Config written.")

run(ssh, "nginx -t 2>&1")
run(ssh, "systemctl reload nginx 2>&1 && echo 'Nginx reloaded.'")
print("  Nginx reloaded.")

print("\n=== Building and starting frontend ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml up -d --build frontend 2>&1', print_output=False)

print("  Waiting 60s for build...")
time.sleep(60)

print("\n=== Checking containers ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml ps 2>&1')

print("\n=== Frontend logs ===")
run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml logs frontend --tail=10 2>&1')

ssh.close()

print("\n" + "=" * 60)
print("DEPLOYMENT COMPLETE")
print("=" * 60)
print("Frontend: http://crm.valerion.ir")
print("API:      http://crm.valerion.ir/api/")
print("Swagger:  http://crm.valerion.ir/swagger-ui/")
print("Admin:    http://crm.valerion.ir/admin/")
