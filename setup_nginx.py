import paramiko
import time

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"

NGINX_CONF = """server {
    listen 80;
    server_name front.crm.valerion.ir;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name back.crm.valerion.ir;
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
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
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)
    return ssh

def run_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out.encode('cp1252', errors='replace').decode('cp1252'))
    if err: print("ERR:", err.encode('cp1252', errors='replace').decode('cp1252'))
    return out, err

if __name__ == "__main__":
    print("Connecting to server...")
    ssh = connect()
    
    print("Installing nginx...")
    run_cmd(ssh, "apt-get update && apt-get install -y nginx")
    
    print("Writing Nginx configuration...")
    cmd = f"cat > /etc/nginx/sites-available/crm.conf << 'EOF'\n{NGINX_CONF}\nEOF"
    run_cmd(ssh, cmd)
    
    print("Enabling site...")
    run_cmd(ssh, "ln -sf /etc/nginx/sites-available/crm.conf /etc/nginx/sites-enabled/crm.conf")
    run_cmd(ssh, "rm -f /etc/nginx/sites-enabled/default")
    
    print("Testing Nginx configuration...")
    run_cmd(ssh, "nginx -t")
    
    print("Reloading Nginx...")
    run_cmd(ssh, "systemctl reload nginx || systemctl restart nginx")
    
    ssh.close()
    print("Nginx setup complete!")
