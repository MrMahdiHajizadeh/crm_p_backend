import pexpect
import sys
import time

VPS_IP = "87.107.108.69"
VPS_PORT = "22"
VPS_USER = "root"
VPS_PASS = "IoC275YMVRF9e7W"

def run_ssh_command(cmd, timeout=120):
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} -p {VPS_PORT} {cmd}"
    child = pexpect.spawn(ssh_cmd, encoding='utf-8', timeout=timeout)
    try:
        idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if idx == 0:
            child.sendline(VPS_PASS)
            child.expect(pexpect.EOF)
        output = child.before
        return output
    except Exception as e:
        return f"Error executing ssh command: {e}"

def run_scp_file(local_path, remote_path, timeout=60):
    scp_cmd = f"scp -P {VPS_PORT} -o StrictHostKeyChecking=no {local_path} {VPS_USER}@{VPS_IP}:{remote_path}"
    child = pexpect.spawn(scp_cmd, encoding='utf-8', timeout=timeout)
    try:
        idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if idx == 0:
            child.sendline(VPS_PASS)
            child.expect(pexpect.EOF)
        return child.before
    except Exception as e:
        return f"Error copying file: {e}"

print("==================================================")
print("  Connecting to VPS and Replacing Backend DB")
print("==================================================")

# Step 1: Verify container names
print("\n[1] Finding backend container on VPS...")
output = run_ssh_command("'docker ps --format \"{{.Names}}\"'")
print(output)

backend_container = "crm-p-backend-1"

# Step 2: Flush / Reset database tables
print("\n[2] Flushing existing database in container...")
flush_out = run_ssh_command(f"'docker exec {backend_container} python manage.py flush --no-input'")
print("Flush Output:", flush_out)

# Step 3: Run migrations to ensure clean schema
print("\n[3] Running database migrations...")
migrate_out = run_ssh_command(f"'docker exec {backend_container} python manage.py migrate'")
print("Migrate Output:", migrate_out)

# Step 4: Copy seed_persian_data.py to VPS and then into container
print("\n[4] Uploading seed_persian_data.py to VPS...")
scp_out = run_scp_file("seed_persian_data.py", "/tmp/seed_persian_data.py")
print("SCP Output:", scp_out)

print("\n[5] Copying seed script into backend container...")
cp_out = run_ssh_command(f"'docker cp /tmp/seed_persian_data.py {backend_container}:/app/seed_persian_data.py'")
print("Docker CP Output:", cp_out)

# Step 5: Execute seed script
print("\n[6] Running Persian data seed script in backend container...")
seed_out = run_ssh_command(f"'docker exec {backend_container} python /app/seed_persian_data.py'")
print("Seed Execution Output:\n", seed_out)

# Step 6: Verify final data counts
print("\n[7] Verifying database records...")
verify_script = """
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'
django.setup()
from common.models import User, Org, Profile
from leads.models import Lead, InteractionLog
from contacts.models import Contact
from accounts.models import Account
from opportunity.models import Opportunity
from tasks.models import Task
from invoices.models import Invoice

print('--- DB Summary ---')
print(f'Users: {User.objects.count()}')
print(f'Orgs: {Org.objects.count()}')
print(f'Accounts (Companies): {Account.objects.count()}')
print(f'Contacts: {Contact.objects.count()}')
print(f'Leads (Projects): {Lead.objects.count()}')
print(f'Opportunities: {Opportunity.objects.count()}')
print(f'Tasks: {Task.objects.count()}')
print(f'Interaction Logs: {InteractionLog.objects.count()}')
print(f'Invoices: {Invoice.objects.count()}')
"""

verify_cmd = f"'docker exec {backend_container} python -c \"{verify_script}\"'"
verify_out = run_ssh_command(verify_cmd)
print(verify_out)

print("\n==================================================")
print("  Database Reset & Seeding Completed Successfully!")
print("==================================================")
