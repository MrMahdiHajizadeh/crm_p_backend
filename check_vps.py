import paramiko

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)

    print("--- UFW Status ---")
    _,out,_ = ssh.exec_command('ufw status')
    print(out.read().decode('utf-8'))

    print("--- Nginx Status ---")
    _,out,_ = ssh.exec_command('systemctl is-active nginx')
    print(out.read().decode('utf-8').strip())

    print("--- Port 80 Check ---")
    _,out,_ = ssh.exec_command('netstat -tulpn | grep :80')
    print(out.read().decode('utf-8'))

    print("--- Curl Front ---")
    _,out,_ = ssh.exec_command('curl -s -I -H "Host: front.crm.valerion.ir" http://127.0.0.1')
    print(out.read().decode('utf-8'))

    print("--- Curl Back ---")
    _,out,_ = ssh.exec_command('curl -s -I -H "Host: back.crm.valerion.ir" http://127.0.0.1')
    print(out.read().decode('utf-8'))

    ssh.close()
except Exception as e:
    print(f"Error: {e}")
