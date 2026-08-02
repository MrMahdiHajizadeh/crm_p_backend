"""Pull last notification-related errors from the VPS backend container."""
import paramiko

H="87.107.108.69"; P=22; U="root"; PW="IoC275YMVRF9e7W"
ssh=paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(H,port=P,username=U,password=PW,timeout=60)
def run(c):
    i,o,e=ssh.exec_command(c,timeout=60); out=o.read().decode('utf-8','replace'); err=e.read().decode('utf-8','replace')
    if out: print(out)
    if err: print("ERR:",err)
    print("---")

print("=== backend logs (last 120, filtered) ===")
run("docker logs bottlecrm-backend-1 --tail 400 2>&1 | grep -iE 'notification|500|error|traceback|exception' | tail -80")
print("=== try live calls ===")
run("curl -sk -o /dev/null -w 'list-noauth=%{http_code}\\n' https://back.crm.valerion.ir/api/notifications/?limit=20")
run("curl -sk -o /dev/null -w 'stream-noauth=%{http_code}\\n' https://back.crm.valerion.ir/api/notifications/stream/")
ssh.close()