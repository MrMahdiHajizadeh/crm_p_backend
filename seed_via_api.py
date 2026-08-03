#!/usr/bin/env python3
"""
Comprehensive CRM Fake Data Seeder via REST API
Seeds: Leads, Contacts, Accounts, Opportunities, Tasks, InteractionLogs
"""
import urllib.request
import urllib.error
import json
import random
import sys
from datetime import date, timedelta

BASE_URL = "https://back.crm.valerion.ir/api"

# ── Fake data pools ────────────────────────────────────────────────────────────
FIRST_NAMES = ["رضا","سارا","علی","مریم","امیرحسین","کامران","الهام","حامد","فاطمه","مهدی","نیلوفر","احسان","زهرا","محمد","آرش","سپیده","حسین","سمیرا","پیمان","مژگان"]
LAST_NAMES  = ["محمدی","احمدی","حسینی","عباسی","رضایی","کاظمی","بهرامی","نوری","شریفی","رستمی","مرادی","کریمی","صادقی","موسوی","حیدری","قاسمی","طاهری","نجفی","ابراهیمی","سعیدی"]
COMPANIES   = ["شرکت فناوری عمارت","گروه صنعتی آریا فولاد","صنایع دارویی سپهر","پردیس دیجیتال","بازرگانی پاسارگاد","مجتمع پتروشیمی زاگرس","مهندسی سیستک","گروه تجاری البرز","صنایع غذایی نگین شرق","شرکت ساختمانی توسعه آفتاب","فن‌آوران نوآوران پارس","گروه خلیج فارس","تمدن آریایی","کیا صنعت","سیستم‌های هوشمند صادقین"]
CITIES      = ["تهران","اصفهان","شیراز","مشهد","تبریز","کرج","اهواز","رشت","قم","یزد"]
LEAD_STATUSES = ["assigned", "in process", "converted", "recycled", "closed"]
RATINGS     = ["HOT","WARM","COLD"]
SOURCES     = ["call", "email", "existing customer", "partner", "public relations", "compaign", "other"]
INDUSTRIES  = ["TECHNOLOGY", "SOFTWARE", "FINANCE", "EDUCATION", "HEALTHCARE", "MANUFACTURING", "SERVICE", "ADVERTISING", "AGRICULTURE", "AUTOMOTIVE", "BANKING"]
OPP_STAGES  = ["PROSPECTING","QUALIFICATION","PROPOSAL","NEGOTIATION","CLOSED_WON","CLOSED_LOST"]
INT_TYPES   = ["call","email","meeting","note"]
TASK_STATI  = ["New","In Progress","Completed","Pending"]
TASK_PRIOS  = ["Low","Medium","High"]

OPP_TITLES = [
    "پروژه پیاده‌سازی CRM سازمانی",
    "توسعه نرم‌افزار هوش مصنوعی",
    "تجهیز زیرساخت شبکه",
    "قرارداد پشتیبانی سالانه",
    "پورتال جامع سازمانی",
    "مشاوره دیجیتال مارکتینگ",
    "لایسنس نرم‌افزاری ۵۰ کاربره",
    "سیستم مدیریت انبار",
    "یکپارچه‌سازی ERP و CRM",
    "تحلیل داده و هوش تجاری",
]
TASK_TITLES = [
    "تماس پیگیری جهت نهایی‌سازی پیش‌فاکتور",
    "جلسه حضوری دموی محصول",
    "ارسال مدارک مناقصه",
    "پیگیری واریز پیش‌پرداخت",
    "بررسی تغییرات لایسنس نرم‌افزار",
    "پیگیری معوق: عدم واریز فاکتور",
    "تنظیم جلسه با مدیران ارشد مالی",
    "ارسال پیشنهاد قیمت به مشتری",
    "پیگیری مذاکرات قراردادی",
    "ارسال ایمیل تبریک و معرفی محصول",
]
INT_SUBJECTS = [
    "پیگیری پیش‌فاکتور شماره ۱۴۰۳",
    "جلسه بررسی نیازمندی‌های فنی",
    "تماس اولیه جهت آشنایی با محصول",
    "ارسال کاتالوگ و اطلاعات فنی",
    "پیگیری قرارداد همکاری",
    "گزارش پیشرفت پروژه",
    "بررسی مشکل فنی مشتری",
    "معرفی ویژگی‌های جدید نسخه ۲.۰",
    "پیگیری نتیجه جلسه قبلی",
    "ثبت یادداشت داخلی پرونده",
]

def api(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        return {"_error": e.code, "_msg": err_body}
    except Exception as e:
        return {"_error": str(e)}

def post(path, data, token=None):
    return api("POST", path, data, token)

def get(path, token=None):
    return api("GET", path, None, token)

def ok(r):
    return "_error" not in r

def extract_ids(res):
    if not res or not isinstance(res, dict):
        return []
    
    # Try common fields
    for k in ["leads", "results", "opportunities", "accounts", "contacts"]:
        if k in res and isinstance(res[k], list):
            return [x.get("id") for x in res[k] if x.get("id")]
            
    # Try nested structure for active_accounts -> open_accounts
    active_accounts = res.get("active_accounts", {})
    if isinstance(active_accounts, dict):
        for k in ["open_accounts", "close_accounts"]:
            if k in active_accounts and isinstance(active_accounts[k], list):
                return [x.get("id") for x in active_accounts[k] if x.get("id")]
                
    # Fallback to recursively finding list of dicts with 'id'
    def find_ids(obj):
        ids = []
        if isinstance(obj, dict):
            if "id" in obj:
                ids.append(obj["id"])
            for val in obj.values():
                ids.extend(find_ids(val))
        elif isinstance(obj, list):
            for val in obj:
                ids.extend(find_ids(val))
        return ids

    return list(set(find_ids(res)))

# ────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  CRM Fake Data Seeder")
print("=" * 60)

# ── Step 1: Login ──────────────────────────────────────────────────────────
print("\n[1] Logging in...")
resp = post("/auth/phone-login/", {"phone": "09136603902", "password": "admin123"})
if not ok(resp):
    print(f"    Login failed: {resp}")
    sys.exit(1)
token = resp.get("access_token") or resp.get("access") or resp.get("token")
if not token:
    print(f"    No token found in: {list(resp.keys())}")
    sys.exit(1)
print(f"    Logged in. Token: {token[:20]}...")

# ── Step 2: Get org ID ──────────────────────────────────────────────────────
print("\n[2] Getting org info...")
me = get("/auth/me/", token)
org_id = me.get("org_id") or me.get("org", {}).get("id") or ""
print(f"    Org ID: {org_id}, User: {me.get('name','?')}")

# ── Step 3: Create Accounts ────────────────────────────────────────────────
print("\n[3] Creating 15 Accounts (Companies)...")
for i, company in enumerate(COMPANIES):
    unique_company = f"{company} {random.randint(100, 999)}"
    data = {
        "name": unique_company,
        "phone": f"021{random.randint(88000000,88999999)}",
        "email": f"info@company{i+1}_{random.randint(100,999)}.ir",
        "city": random.choice(CITIES),
        "website": f"https://company{i+1}.ir",
        "industry": random.choice(INDUSTRIES),
        "number_of_employees": random.choice([10,25,50,100,250,500]),
        "description": f"شرکت {unique_company} - یکی از برترین شرکت‌های فعال در حوزه تخصصی خود در ایران.",
    }
    r = post("/accounts/", data, token)
    if ok(r):
        print(f"    ✓ {unique_company}")
    else:
        print(f"    ✗ {unique_company}: {r.get('_msg', r)}")

# Query account IDs from GET
accs = get("/accounts/", token)
account_ids = extract_ids(accs)
print(f"    Total accounts in pool: {len(account_ids)}")

# ── Step 4: Create Contacts ────────────────────────────────────────────────
print("\n[4] Creating 20 Contacts...")
for i in range(20):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    data = {
        "first_name": fn,
        "last_name": ln,
        "email": f"contact{i+100}_{random.randint(1000,9999)}@domain{i+100}.ir",
        "phone": f"0912{random.randint(1000000,9999999)}",
        "organization": random.choice(COMPANIES),
        "title": random.choice(["مدیر فروش","کارشناس خرید","مدیر فناوری","مدیر مالی","رئیس هیئت مدیره"]),
        "department": random.choice(["فروش","خرید","فناوری اطلاعات","مالی","بازاریابی"]),
        "city": random.choice(CITIES),
        "country": "IR",
        "description": f"مخاطب {fn} {ln} - کارشناس ارشد در حوزه تخصصی خود.",
    }
    if account_ids:
        data["account"] = random.choice(account_ids)
    r = post("/contacts/", data, token)
    if ok(r):
        print(f"    ✓ {fn} {ln}")
    else:
        print(f"    ✗ {fn} {ln}: {r.get('_msg', r)}")

# Query contact IDs from GET
cnts = get("/contacts/", token)
contact_ids = extract_ids(cnts)
print(f"    Total contacts in pool: {len(contact_ids)}")

# ── Step 5: Create Leads ────────────────────────────────────────────────────
print("\n[5] Creating 30 Leads...")
for i in range(30):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    company = random.choice(COMPANIES)
    status = random.choice(LEAD_STATUSES)
    data = {
        "first_name": fn,
        "last_name": ln,
        "email": f"lead{i+1}_{random.randint(1000,9999)}@client{i+1}.ir",
        "phone": f"0935{random.randint(1000000,9999999)}",
        "company_name": company,
        "title": f"استعلام پروژه شماره {i+1}",
        "status": status,
        "rating": random.choice(RATINGS),
        "source": random.choice(SOURCES),
        "industry": random.choice(INDUSTRIES),
        "city": random.choice(CITIES),
        "country": "IR",
        "opportunity_amount": str(random.randint(50,900) * 1000000),
        "currency": "TOM", # TOM instead of IRR
        "description": f"درخواست استعلام قیمت برای پروژه {i+1} از شرکت {company}.",
    }
    r = post("/leads/", data, token)
    if ok(r):
        print(f"    ✓ {fn} {ln} ({company})")
    else:
        print(f"    ✗ Lead {i+1}: {r.get('_msg', r)}")

# Query lead IDs from GET
lds = get("/leads/", token)
lead_ids = extract_ids(lds)
print(f"    Total leads in pool: {len(lead_ids)}")

# ── Step 6: Create Opportunities ──────────────────────────────────────────
print("\n[6] Creating 20 Opportunities...")
opp_ids = []
for i in range(20):
    title = f"{random.choice(OPP_TITLES)} - کد {i+401}" # start code even higher to avoid name constraint
    data = {
        "name": title,
        "amount": str(random.randint(50,950) * 1000000),
        "stage": random.choice(OPP_STAGES),
        "probability": random.randint(10,90),
        "description": f"فرصت فروش {title}. در مرحله مذاکره و بررسی نهایی.",
        "close_date": (date.today() + timedelta(days=random.randint(7,90))).isoformat(),
    }
    r = post("/opportunities/", data, token)
    if ok(r):
        print(f"    ✓ {title[:50]}")
    else:
        print(f"    ✗ Opp {i+1}: {r.get('_msg', r)}")

# ── Step 7: Create Tasks ────────────────────────────────────────────────────
print("\n[7] Creating 25 Tasks...")
today = date.today()
due_date_options = [
    (today - timedelta(days=random.randint(1,5))).isoformat(),   # overdue
    today.isoformat(),                                            # today
    (today + timedelta(days=1)).isoformat(),                      # tomorrow
    (today + timedelta(days=random.randint(2,6))).isoformat(),   # this week
    (today + timedelta(days=random.randint(7,30))).isoformat(),  # later
]
for i in range(25):
    title = f"{random.choice(TASK_TITLES)} (#{i+200})" # start higher
    data = {
        "title": title,
        "status": random.choice(TASK_STATI),
        "priority": random.choice(TASK_PRIOS),
        "due_date": random.choice(due_date_options),
        "description": f"وظیفه شماره {i+200}: {title}. پیگیری و اقدام لازم است.",
    }
    r = post("/tasks/", data, token)
    if ok(r):
        print(f"    ✓ {title[:55]}")
    else:
        print(f"    ✗ Task {i+1}: {r.get('_msg', r)}")

# ── Step 8: Create Interaction Logs (Follow-ups) ────────────────────────────
print("\n[8] Creating 30 Interaction Logs (follow-ups)...")
interaction_count = 0
entity_pool = []
if lead_ids:
    entity_pool += [("Lead", lid) for lid in lead_ids]
if contact_ids:
    entity_pool += [("Contact", cid) for cid in contact_ids]
if account_ids:
    entity_pool += [("Account", aid) for aid in account_ids]

# Map follow-up dates to time categories
followup_dates = [
    (today - timedelta(days=random.randint(1,5))).isoformat(),   # overdue
    (today - timedelta(days=random.randint(1,5))).isoformat(),
    (today - timedelta(days=random.randint(1,5))).isoformat(),
    today.isoformat(),                                            # today
    today.isoformat(),
    today.isoformat(),
    today.isoformat(),
    today.isoformat(),
    (today + timedelta(days=1)).isoformat(),                      # tomorrow
    (today + timedelta(days=1)).isoformat(),
    (today + timedelta(days=1)).isoformat(),
    (today + timedelta(days=random.randint(2,6))).isoformat(),   # this_week
    (today + timedelta(days=random.randint(2,6))).isoformat(),
    (today + timedelta(days=random.randint(2,6))).isoformat(),
    (today + timedelta(days=random.randint(7,30))).isoformat(),  # later
    (today + timedelta(days=random.randint(7,30))).isoformat(),
    (today + timedelta(days=random.randint(7,30))).isoformat(),
]

if entity_pool:
    for i in range(30):
        entity_type, entity_id = random.choice(entity_pool)
        int_type = random.choice(INT_TYPES)
        subject = random.choice(INT_SUBJECTS)
        followup_date = random.choice(followup_dates)
        data = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "interaction_type": int_type,
            "subject": f"{subject} - {i+200}",
            "description": f"جزئیات تعامل شماره {i+200}: پیگیری توسط کارشناس فروش. نتیجه: در انتظار بازخورد مشتری.",
            "follow_up_date": followup_date,
            "duration_minutes": random.choice([None, 15, 30, 45, 60, 90]),
        }
        r = post("/leads/interactions/", data, token)
        if ok(r):
            interaction_count += 1
            print(f"    ✓ [{entity_type}] {subject[:40]} → {followup_date}")
        else:
            print(f"    ✗ Interaction {i+1}: {str(r.get('_msg', r))[:120]}")
else:
    print("    No entities available in the pool to attach follow-ups to.")

print(f"    Created {interaction_count} interaction logs.")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SEEDING COMPLETE!")
print("=" * 60)
print(f"""
  Login at: https://front.crm.valerion.ir
  Phone: 09136603902 | Password: admin123
""")
