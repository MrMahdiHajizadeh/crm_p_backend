"""
Setup Nginx reverse proxy for crm.valerion.ir on VPS
"""
import paramiko

HOST = "188.209.138.33"
PORT = 22
USER = "root"
PASS = "pcJOm45Ijao1xlv"

NGINX_CONFIG = """server {
    listen 80;
    server_name crm.valerion.ir;

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

    location /static/ {
        alias /opt/bottlecrm/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/bottlecrm/backend/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60, banner_timeout=60, auth_timeout=60)

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

print("=== Writing Nginx config ===")
# Escape for bash: write via Python heredoc-like approach
cmd = f"cat > /etc/nginx/sites-available/crm.valerion.ir << 'EOF'\n{NGINX_CONFIG}\nEOF"
run(ssh, cmd)
print("Config written.")

print("\n=== Enabling site ===")
run(ssh, "ln -sf /etc/nginx/sites-available/crm.valerion.ir /etc/nginx/sites-enabled/crm.valerion.ir && echo 'Symlink created.'")

print("\n=== Testing Nginx config ===")
out, err = run(ssh, "nginx -t 2>&1")

print("\n=== Reloading Nginx ===")
run(ssh, "systemctl reload nginx 2>&1 && echo 'RELOADED' || systemctl start nginx 2>&1")

print("\n=== Checking Nginx status ===")
run(ssh, "systemctl status nginx --no-pager -l 2>&1 | head -10")
run(ssh, "nginx -T 2>/dev/null | grep -A2 'server_name crm.valerion.ir'")

print("\n=== Testing local endpoint ===")
run(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:8000/swagger-ui/ 2>&1")
print()

ssh.close()

print("\n" + "=" * 60)
print("Nginx configured for https://crm.valerion.ir")
print("Proxying to backend on port 8000")
print("=" * 60)
