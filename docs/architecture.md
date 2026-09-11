# 📘 سند جامع معماری نرم‌افزار — سازمان هوش مصنوعی (AI Company MVP)

این سند، معماری جامع فنی، لایه‌بندی نرم‌افزاری (**Clean Architecture**)، ساختار ماژولار مونولیت (**Modular Monolith**)، موتور گردش کار مبتنی بر ماشین وضعیت و زیرسیستم حافظه سازمانی (**Company Brain**) را تشریح می‌کند.

---

## 🎯 اصول و فلسفه معماری

```text
Monolith ماژولار
      ↓
Clean Architecture (جداسازی لایه‌ها و قوانین وابستگی)
      ↓
Event-Driven & State Machine (برای چرخه حیات Agentها)
      ↓
Human-in-the-Loop (گیت‌های کنترل و نظارت انسانی)
```

### ۱. چرایی استفاده از Modular Monolith:
- سادگی بالا در پیاده‌سازی و راه‌اندازی Phase 1 MVP
- رفع پیچیدگی‌های غیرضروری شبکه و Distributed Tracing در میکروسرویس‌ها
- ماژول‌های مستقل (هر Agent و Company Brain کاملاً مجزا هستند و در آینده در صورت نیاز به میکروسرویس تبدیل می‌شوند)

### ۲. قانون وابستگی در Clean Architecture:
```text
API Layer → Application Layer → Domain Layer ← Infrastructure Layer
```
- لایه **Domain** هیچ‌گونه وابستگی به پایگاه‌داده، فریم‌ورک‌های وب یا سرویس‌های خارجی ندارد.
- ورودی و خروجی تمام Agentها توسط قراردادهای داده‌ای مستحکم (**Pydantic v2**) گارانتی می‌شود.

---

## 🏛️ لایه‌های نرم‌افزاری

### ۱. لایه رابط برنامه‌نویسی (API Layer - `src/api/`)
- **فریم‌ورک:** FastAPI با پشتیبانی کامل از Async I/O
- **وظایف:** مدیریت درخواست‌های HTTP، احراز هویت، CORS، مدیریت خطاها، و سرو پنل کاربری فرانت‌اند SPA.
- **روترها:**
  - `/api/auth`: ثبت‌نام، ورود و مدیریت توکن
  - `/api/projects`: چرخه حیات پروژه‌ها و انتساب مخازن Git
  - `/api/requests`: دریافت درخواست‌های محصول و شروع پایپ‌لاین
  - `/api/workflows`: مانیتورینگ زنده مراحل اجرای Workflow و هزینه‌ها
  - `/api/approvals`: مدیریت تصمیم‌گیری‌های گیت‌های تایید انسانی
  - `/api/agents`: فهرست و وضعیت ۵ عامل هوش مصنوعی
  - `/api/brain`: جستجوی معنایی وکتوری، ثبت اسناد دانش و حافظه
  - `/health`: پایش سلامت سرور

### ۲. لایه کاربرد و سرویس‌ها (Application Layer - `src/application/`)
- پیاده‌سازی سناریوهای استفاده (Use Cases) و هماهنگی میان ریپازیتوری‌ها و موتور ارکستراسیون:
  - `ProjectService`: ساخت پروژه، پوشه‌بندی ساندباکس و راه‌اندازی Git
  - `RequestService`: ثبت و مدیریت وضعیت درخواست‌ها
  - `WorkflowService`: استارت پایپ‌لاین و فراخوانی موتور اجرا
  - `ApprovalService`: ثبت تصمیمات انسانی (Approve/Reject) و رزومه کردن خودکار Workflow
  - `BrainService`: ایندکس اسناد، محاسبه امبدینگ و استخراج حافظه‌ها

### ۳. لایه دامنه (Domain Layer - `src/domain/`)
- **قراردادهای داده‌ای (`src/domain/schemas/`):** مدل‌های Pydantic v2 برای تضمین ساختار JSON خروجی Agentها
- **عامل‌های هوشمند (`src/domain/agents/`):**
  - `BaseAgent`: کلاس پایه با چرخه حیات استاندارد، فراخوانی حافظه و ردیابی هزینه/توکن
  - `AICooAgent`: ارکستراتور کلان
  - `BusinessAnalystAgent`: تدوین مشخصات فنی
  - `DeveloperAgent`: تولید کد و کامیت
  - `QAAgent`: اجرای تست و تایید معیارهای پذیرش
  - `KnowledgeManagerAgent`: ثبت درس‌ها در مغز سازمانی
- **موتور گردش کار (`src/domain/workflows/engine.py`):**
  - ماشین وضعیت اجرای مرحله‌به‌مرحله
  - مدیریت گیت‌های تایید انسانی (ایجاد رکورد Approval و توقف امن اجرا تا زمان تایید)
  - مدیریت حلقه‌های اصلاح خطای خودکار (`FIX_LOOP` در صورت رد شدن تست‌های QA)

### ۴. لایه زیرساخت (Infrastructure Layer - `src/infrastructure/`)
- **دیتابیس (`src/infrastructure/database/`):** مدل‌های ORM با SQLAlchemy 2.0، پشتیبانی از وکتورهای ۱۵۳۶ بعدی با `pgvector` و Fallback برای SQLite.
- **موتور هوش مصنوعی (`src/infrastructure/llm/`):** رابط انتزاعی چندپرووایدر برای اتصال به OpenAI ،Anthropic و شبیه‌ساز محلی پرسرعت.
- **ابزارها (`src/infrastructure/tools/`):**
  - `FileTools`: عملیات امن فایل‌سیستم در پوشه ایزوله پروژه
  - `GitTools`: مدیریت شاخه‌ها، ایجاد کامیت و مقایسه Diff
  - `TestTools`: اجرای خودکار Pytest و پارس خروجی گزارش و Coverage
- **مغز سازمانی (`src/infrastructure/brain/`):**
  - `EmbeddingService`: تولید وکتور امبدینگ
  - `KnowledgeService`: محاسبه تشابه کسینوسی (RAG)، ذخیره تصمیمات (ADR) و حافظه درس‌های آموخته‌شده

---

## 🤖 ساختار قراردادهای ورودی و خروجی Agentها

### خروجی Business Analyst:
```python
class BAOutputContract(BaseModel):
    title: str
    summary: str
    requirements: list[RequirementItem]       # الزامات ساختاریافته با اولویت
    acceptance_criteria: list[str]           # معیارهای پذیرش به فرمت Given-When-Then
    business_rules: list[str]                # قوانین حاکم بر دامنه کسب‌وکار
    open_questions: list[str]                # ابهامات معماری
    tasks: list[str]                         # شکست تسک‌های اجرایی
```

### خروجی Developer:
```python
class DevOutputContract(BaseModel):
    technical_plan: list[str]                # طرح فنی مرحله‌به‌مرحله
    files_created: list[str]                 # مسیر فایل‌های ایجادشده
    files_modified: list[str]                # مسیر فایل‌های ویرایش‌شده
    tests_created: list[str]                 # تست‌های تولیدشده
    commit_hash: str                         # شناسه کامیت ثبت‌شده در Git
    commit_message: str                      # پیام کامیت استاندارد
    all_tests_passed: bool                   # نتیجه تست اولیه
```

### خروجی QA Engineer:
```python
class QAOutputContract(BaseModel):
    status: Literal["PASSED", "FAILED"]      # نتیجه نهایی بررسی کیفیت
    total_tests: int                         # تعداد کل تست‌های اجراشده
    passed_tests: int                        # تست‌های موفق
    failed_tests: int                        # تست‌های ناموفق
    coverage_percentage: float               # درصد پوشش کد (Coverage)
    bugs: list[BugReport]                    # لیست باگ‌های کشف‌شده همراه با سناریوی بازتولید
    requirement_verification: dict[str, bool]# اعتبارسنجی تک‌تک معیارهای پذیرش
```

---

## 🔁 دیاگرام وضعیت Workflow Engine

```text
    [شروع: STARTED]
           │
           ▼
    [اجرای تحلیل: Business Analyst]
           │
           ▼
    [🛑 گیت تایید مشخصات: WAITING_APPROVAL] ──(رد: REJECTED)──► [پایان ناموفق: CANCELLED]
           │
      (تایید: APPROVED)
           │
           ▼
    [اجرای پیاده‌سازی: Developer Agent]
           │
           ▼
    [اجرای تست و کنترل کیفیت: QA Agent]
           │
      ┌────┴────────────────────────┐
      ▼                             ▼
 (تست‌ها موفق: PASSED)        (تست‌ها ناموفق: FAILED)
      │                             │
      │                             ▼
      │                      [حلقه اصلاح خودکار: FIX_LOOP]
      │                             │
      │                             └────► بازگشت به QA
      ▼
    [🛑 گیت تایید نهایی: FINAL_APPROVAL] ──(رد: REJECTED)──► [لغو انتشار: CANCELLED]
           │
      (تایید: APPROVED)
           │
           ▼
    [ثبت دانش در Brain: Knowledge Manager]
           │
           ▼
    [تکمیل موفقیت‌آمیز: COMPLETED]
```
