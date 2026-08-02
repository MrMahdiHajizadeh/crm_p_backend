"""Quick VPS inspection before replacing frontend/backend."""
import paramiko

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print("ERR:", err)
    print("---")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)

print("=== Disk ===")
run(ssh, "df -h /")

print("=== Docker containers ===")
run(ssh, 'docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"')

print("=== Project dir ===")
run(ssh, "ls -la /opt/bottlecrm 2>/dev/null || echo 'no /opt/bottlecrm'")

print("=== Nginx sites ===")
run(ssh, "ls -la /etc/nginx/sites-enabled/ 2>/dev/null")
run(ssh, "cat /etc/nginx/sites-available/crm.conf 2>/dev/null || echo 'no crm.conf'")

print("=== SSL certs ===")
run(ssh, "certbot certificates 2>/dev/null | head -40")

ssh.close()
print("done")