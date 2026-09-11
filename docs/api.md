# 🌐 مستندات کامل API — سازمان هوش مصنوعی (AI Company MVP)

آدرس پایه: `http://localhost:8000/api`  
مستندات تعاملی Swagger: `http://localhost:8000/docs`

---

## ۱. احراز هویت و کاربران (`/api/auth`)

### ۱.۱. ثبت‌نام کاربر جدید
- **متد:** `POST /api/auth/register`
- **ورودی:**
```json
{
  "email": "engineer@company.ai",
  "password": "SecurePassword123!",
  "full_name": "نام کاربر",
  "role": "MEMBER"
}
```
- **پاسخ موفق (HTTP 200):** مشخصات کاربر ثبت‌شده.

### ۱.۲. ورود به سیستم و دریافت توکن
- **متد:** `POST /api/auth/login`
- **ورودی:**
```json
{
  "email": "engineer@company.ai",
  "password": "SecurePassword123!"
}
```
- **پاسخ موفق (HTTP 200):**
```json
{
  "access_token": "engineer@company.ai",
  "token_type": "bearer",
  "user": { ... }
}
```

### ۱.۳. دریافت پروفایل کاربر جاری
- **متد:** `GET /api/auth/me`

---

## ۲. مدیریت پروژه‌ها (`/api/projects`)

### ۲.۱. ایجاد پروژه جدید به همراه راه‌اندازی مخزن Git
- **متد:** `POST /api/projects`
- **ورودی:**
```json
{
  "name": "سرویس پرداخت و صورتحساب",
  "description": "درگاه پرداخت ارزی با تاییدیه خودکار",
  "tech_stack": ["FastAPI", "PostgreSQL", "Docker", "Pytest"]
}
```
- **پاسخ موفق (HTTP 201):** رکورد پروژه به همراه مسیر محلی مخزن ایجادشده در پوشه ساندباکس (`workspace_repos/<project_id>`).

### ۲.۲. دریافت لیست پروژه‌ها
- **متد:** `GET /api/projects`

### ۲.۳. دریافت جزئیات یک پروژه
- **متد:** `GET /api/projects/{project_id}`

---

## ۳. درخواست‌های محصول و تسک‌ها (`/api/requests`)

### ۳.۱. ثبت درخواست محصول جدید
- **متد:** `POST /api/requests`
- **ورودی:**
```json
{
  "project_id": "uuid-پروژه",
  "title": "پیاده‌سازی API ثبت‌نام دانشجویان",
  "description": "دانشجویان بتوانند در دوره‌ها ثبت‌نام کنند. بررسی پیش‌نیازها الزامی است.",
  "request_type": "FEATURE",
  "priority": 4,
  "auto_start_workflow": true
}
```
- **پاسخ موفق (HTTP 201):** در صورت فعال بودن `auto_start_workflow`، گردش کار بلافاصله استارت خورده و وارد گام‌های تحلیل Business Analyst و گیت تایید می‌شود.

### ۳.۲. دریافت لیست درخواست‌های یک پروژه
- **متد:** `GET /api/requests/project/{project_id}`

### ۳.۳. دریافت جزئیات درخواست، نیازمندی‌ها و تسک‌ها
- **متد:** `GET /api/requests/{request_id}`

---

## ۴. خط لوله و ارکستراسیون گردش کار (`/api/workflows`)

### ۴.۱. لیست تعاریف گردش کار
- **متد:** `GET /api/workflows`

### ۴.۲. شروع اجرای دستی یک Workflow برای درخواست
- **متد:** `POST /api/workflows/runs`
- **ورودی:**
```json
{
  "request_id": "uuid-درخواست",
  "workflow_id": "uuid-اختیاری"
}
```

### ۴.۳. استعلام لحظه‌ای وضعیت اجرای پایپ‌لاین
- **متد:** `GET /api/workflows/runs/{run_id}`
- **پاسخ موفق:** برگرداندن وضعیت کلی (`STARTED`, `IN_PROGRESS`, `WAITING_APPROVAL`, `COMPLETED`)، مرحله جاری، گام‌های اجراشده به تفکیک Agent، توکن‌های مصرفی و هزینه‌ها.

---

## ۵. گیت‌های تایید انسانی — Human-in-the-Loop (`/api/approvals`)

### ۵.۱. دریافت لیست تاییدیه‌های معلق کاربر جاری
- **متد:** `GET /api/approvals/pending`
- **پاسخ موفق:** برگرداندن لیست تمام گیت‌های منتظر تایید (`REQUIREMENT_APPROVAL` یا `FINAL_APPROVAL`).

### ۵.۲. تایید یا رد گیت تایید انسانی
- **متد:** `POST /api/approvals/{approval_id}/action`
- **ورودی:**
```json
{
  "status": "APPROVED",
  "comment": "مشخصات فنی بررسی شد و مورد تایید است. ادامه دهید."
}
```
یا برای رد:
```json
{
  "status": "REJECTED",
  "comment": "معیارهای پذیرش کامل نیست، لطفاً تست‌های اعتبارسنجی را اضافه کنید."
}
```
- **رفتار سیستم:** پس از تایید، موتور گردش کار به‌صورت خودکار مرحله بعدی را استارت می‌زند.

---

## ۶. مغز سازمانی و RAG معنایی (`/api/brain`)

### ۶.۱. تزریق سند دانش به Company Brain
- **متد:** `POST /api/brain/documents`
- **ورودی:**
```json
{
  "project_id": "uuid-اختیاری",
  "title": "استاندارد نام‌گذاری متغیرها و اعتبارسنجی Pydantic",
  "document_type": "CODING_STANDARD",
  "content": "تمام فیلدهای ورودی باید از طریق Pydantic v2 با Type Hint معتبر شوند..."
}
```

### ۶.۲. جستجوی معنایی وکتوری (Semantic Search)
- **متد:** `GET /api/brain/search?query=احراز+هویت+امن&top_k=5`
- **پاسخ موفق:** برگرداندن چانک‌های با بیشترین تشابه کسینوسی به همراه متادیتا و درصد امتیاز.

### ۶.۳. مشاهده حافظه درس‌های آموخته‌شده Agentها
- **متد:** `GET /api/brain/memories?project_id={project_id}`
- **پاسخ موفق:** لیست حافظه‌های ثبت‌شده (`LESSON`, `PATTERN`, `FEEDBACK`) به همراه ضریب اهمیت (۱ تا ۱۰).

---

## ۷. شناسنامه Agentها و سلامت سیستم (`/api/agents` و `/health`)

### ۷.۱. فهرست Agentهای پیکربندی‌شده
- **متد:** `GET /api/agents`

### ۷.۲. وضعیت عامل‌های هوشمند فعال در Runtime
- **متد:** `GET /api/agents/runtime/active`

### ۷.۳. پایش سلامت سرور
- **متد:** `GET /health`
- **پاسخ موفق (HTTP 200):**
```json
{
  "status": "healthy",
  "system": "AI Company MVP",
  "version": "0.1.0",
  "environment": "development",
  "llm_provider": "mock"
}
```
