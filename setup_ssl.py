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

    print("Installing Certbot...")
    run_cmd(ssh, "apt-get update && NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get install -y certbot python3-certbot-nginx")

    print("Generating SSL Certificates...")
    certbot_cmd = "certbot --nginx -d front.crm.valerion.ir -d back.crm.valerion.ir --non-interactive --agree-tos -m admin@valerion.ir --redirect"
    run_cmd(ssh, certbot_cmd)

    ssh.close()
    print("SSL setup complete!")
except Exception as e:
    print(f"Error: {e}")
