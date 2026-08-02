# 01 - API Endpoints Specification

This document details all active backend API endpoints in Django REST Framework used by the Emarat Connect (عمارت کانکت) CRM frontend.

## Common Headers

All authenticated requests require the following HTTP headers:

```http
Authorization: Bearer <access_jwt_token>
org: <organization_uuid>
Content-Type: application/json
```

---

## 1. Authentication & User Profile (`api_common`)

### `POST /api/auth/phone/login/`
Request phone code for one-time password login.
- **Request Body**:
  ```json
  { "phone": "09123456789" }
  ```
- **Response (200 OK)**:
  ```json
  { "message": "Code sent successfully" }
  ```

### `POST /api/auth/phone/verify/`
Verify phone OTP code or password login.
- **Request Body**:
  ```json
  { "phone": "09123456789", "code": "123456" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>",
    "user": { "id": "<uuid>", "phone": "09123456789", "name": "Mahdi" },
    "orgs": [{ "id": "<org_uuid>", "name": "عمارت کانکت" }]
  }
  ```

### `GET /api/auth/me/`
Get current user details & profile.
- **Response (200 OK)**:
  ```json
  {
    "id": "<user_uuid>",
    "email": "user@example.com",
    "name": "Mahdi",
    "role": "ADMIN",
    "org": { "id": "<org_uuid>", "name": "عمارت کانکت" }
  }
  ```

---

## 2. Executive Dashboard (`/api/dashboard/`)

### `GET /api/dashboard/`
Returns consolidated executive dashboard data in a single request.
- **Response (200 OK)**:
  ```json
  {
    "accounts_count": 17,
    "contacts_count": 27,
    "leads_count": 31,
    "opportunities_count": 10,
    "urgent_counts": {
      "overdue_tasks": 0,
      "tasks_due_today": 0,
      "followups_today": 2,
      "hot_leads": 3
    },
    "revenue_metrics": {
      "won_this_month": 470600,
      "conversion_rate": 6.1,
      "currency": "TOM"
    },
    "hot_leads": [
      {
        "id": "<lead_uuid>",
        "first_name": "Wesley",
        "last_name": "Lewis",
        "company": "Tidepool Cosmetics",
        "rating": "HOT",
        "next_follow_up": "2026-07-25"
      }
    ],
    "opportunities": [
      {
        "id": "<opp_uuid>",
        "name": "Enterprise Deal",
        "amount": 668585,
        "stage": "QUALIFICATION",
        "probability": 40,
        "account": { "name": "Tessellate Design" }
      }
    ],
    "team_performance": {
      "my_stats": {
        "leads_count": 7,
        "contacts_count": 1,
        "accounts_count": 1,
        "followups_today": 0,
        "followups_week": 2,
        "followups_month": 2,
        "followups_total": 2
      },
      "team_members": [
        {
          "user_id": "<uuid>",
          "user_name": "Admin User",
          "user_email": "admin@example.com",
          "role": "ADMIN",
          "stats": {
            "leads_count": 16,
            "contacts_count": 11,
            "accounts_count": 5,
            "followups_today": 0,
            "followups_week": 2,
            "followups_month": 3,
            "followups_total": 3
          }
        }
      ]
    },
    "activities": [
      {
        "id": "<uuid>",
        "user": { "name": "Mahdi" },
        "action": "CREATE",
        "entity_type": "Lead",
        "entity_name": "New Lead",
        "humanized_time": "2 hours ago"
      }
    ]
  }
  ```

---

## 3. Leads Management (`/api/leads/`)

### `GET /api/leads/`
List leads with filtering and pagination.
- **Query Params**: `rating` (HOT/WARM/COLD), `status` (assigned/in process/converted), `search`, `limit`, `offset`.
- **Response**: Array of lead objects (`first_name`, `last_name`, `email`, `phone`, `company_name`, `rating`, `status`, `next_follow_up`).

### `POST /api/leads/`
Create a new sales lead.
- **Payload**:
  ```json
  {
    "first_name": "Reza",
    "last_name": "Ahmadi",
    "company_name": "Emarat Tech",
    "phone": "09120000000",
    "rating": "HOT",
    "status": "assigned"
  }
  ```

### `GET /api/leads/<id>/` | `PUT /api/leads/<id>/` | `DELETE /api/leads/<id>/`
Retrieve, update, or remove a lead record.

---

## 4. Contacts & Accounts (`/api/contacts/` & `/api/accounts/`)

### `GET /api/contacts/`
List contacts (`first_name`, `last_name`, `email`, `phone`, `organization`).

### `GET /api/accounts/`
List account companies (`name`, `website`, `phone`, `industry`, `billing_city`).

---

## 5. Opportunities / Deals (`/api/opportunities/`)

### `GET /api/opportunities/`
List sales deals.
- **Response**: List of opportunity objects (`name`, `amount`, `currency`, `stage`, `probability`, `closed_on`, `account`).

---

## 6. Tickets / Support Desk (`/api/cases/`)

### `GET /api/cases/`
List support tickets.
- **Response**: List of ticket objects (`name`, `status`, `priority`, `case_type`, `account`, `contacts`).

---

## 7. Invoices & Billing (`/api/invoices/`)

### `GET /api/invoices/`
List organization invoices (`invoice_number`, `total_amount`, `currency`, `status`, `issue_date`, `due_date`).

---

## 8. Follow-ups Stream (`/api/follow-ups/`)

### `GET /api/follow-ups/`
List active follow-ups for leads and opportunities.
