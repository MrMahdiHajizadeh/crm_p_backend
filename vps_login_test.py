import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60, banner_timeout=60, auth_timeout=60)
stdin, stdout, stderr = ssh.exec_command('curl -s -w "|HTTP:%{http_code}" -X POST http://127.0.0.1:8000/api/auth/phone-login/ -H "Content-Type: application/json" -d '"'"'{"phone":"09136603902","password":"admin123"}'"'"'')
out = stdout.read().decode()
print(out[:500])
ssh.close()
