"""Get full notification traceback from VPS backend logs."""
import paramiko
H="87.107.108.69"; P=22; U="root"; PW="IoC275YMVRF9e7W"
ssh=paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(H,port=P,username=U,password=PW,timeout=60)
def run(c):
    i,o,e=ssh.exec_command(c,timeout=60)
    print(o.read().decode('utf-8','replace'))
    err=e.read().decode('utf-8','replace')
    if err: print("ERR:",err)

# login then call notifications with token, capture status + body
print("=== authed call to notifications list on VPS ===")
run("""python3 - <<'PY'
import urllib.request, json
req=urllib.request.Request('https://back.crm.valerion.ir/api/auth/phone-login/', data=json.dumps({'phone':'09136603902','password':'admin123'}).encode(), headers={'Content-Type':'application/json'})
try:
    r=urllib.request.urlopen(req, timeout=15)
    tok=json.loads(r.read())['access_token']
    print('login ok')
except Exception as ex:
    print('login fail', ex); raise SystemExit
for ep in ['notifications/?limit=20','notifications/stream/']:
    try:
        r=urllib.request.urlopen(urllib.request.Request('https://back.crm.valerion.ir/api/'+ep, headers={'Authorization':'Bearer '+tok}), timeout=10)
        print(ep,'->',r.status, r.read(300))
    except urllib.error.HTTPError as e:
        print(ep,'-> HTTP',e.code, e.read(800).decode('utf-8','replace'))
    except Exception as e:
        print(ep,'-> EXC',type(e).__name__,e)
PY""")

print("=== last 60 backend log lines ===")
run("docker logs bottlecrm-backend-1 --tail 60 2>&1")
ssh.close()