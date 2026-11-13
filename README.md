# Mini Library Management System — Django REST Framework

A small **backend-only** final course project that follows the provided **Django REST Framework Final Project Evaluation Guideline (100 Marks)**. No Flutter frontend is required for this deliverable.

## 1. Problem statement

A small library needs to store members, authors, and books, and keep track of book borrowing and returns. Staff can create and update records through REST APIs and Django Admin. The system prevents duplicate active borrowing and borrowing when no copies are available.

## 2. Technology stack

- Python **3.10+** (Python 3.13 also supported by the pinned Django range)
- Django **5.2 LTS**
- Django REST Framework **3.16.x**
- django-filter **25.x**
- SQLite (included in Python)
- Django Admin; DRF Browsable API; Postman for manual tests

### Project directory

```text
Mini_Library_Management_System/
├── manage.py
├── requirements.txt
├── README.md
├── VIVA_GUIDE_BN.md
├── config/
│   ├── settings.py           # Database, installed apps, DRF configuration
│   ├── urls.py               # /api/, /admin/, /api-auth/
│   ├── asgi.py
│   └── wsgi.py
├── library/
│   ├── models.py             # 4 custom models; relationships and clean()
│   ├── validators.py         # ISBN-13 and membership-ID checks
│   ├── serializers.py        # JSON conversion and serializer validation
│   ├── views.py              # 4 ModelViewSets (all 6 CRUD actions)
│   ├── urls.py               # DefaultRouter routes
│   ├── pagination.py         # PageNumberPagination
│   ├── admin.py              # Admin list/filter/search, M2M and inline
│   ├── migrations/0001_initial.py
│   ├── management/commands/seed_demo.py
│   └── tests/               # Model, API, Admin and seed tests
├── scripts/              # Quick-start scripts for Windows/Linux/macOS
├── postman/
│   └── Mini_Library.postman_collection.json
└── samples/
    └── sample_api_payloads.json
```

## 3. Installation — Linux, macOS, Windows

You need **Python, pip, and internet access to install the packages** the first time.

```bash
# Extract ZIP, then open a terminal in Mini_Library_Management_System
python -m venv .venv
```

Activate the virtual environment:

- Linux/macOS: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows CMD: `.venv\Scripts\activate.bat`

Then:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

If your machine needs `python3` instead of `python`, replace it in all commands.

**One-command alternative:** Linux/macOS: `bash scripts/start_linux_mac.sh`; Windows CMD: `scripts\start_windows.bat`. They run install, migrate, seed, check, and server setup.

Open:

- REST API root: **http://127.0.0.1:8000/api/**
- Django Admin: **http://127.0.0.1:8000/admin/**
- DRF browsable API login: **http://127.0.0.1:8000/api-auth/login/**

### Demo credentials (LOCAL CLASSROOM USE ONLY)

| Account | Username | Password |
|---|---|---|
| Django Admin / API write access | `library_admin` | `LibraryDemo123!` |
| Normal demo member | `student1` | `StudentDemo123!` |

For a new personal account: `python manage.py createsuperuser`.

**Important:** This is a development demo. Never deploy with `DEBUG=True`, the example secret key, these passwords, or BasicAuthentication over unencrypted HTTP. Change settings, secrets, authentication, and permissions before any public deployment. For this classroom demo run `runserver` on localhost only.

## 4. Database design — 4 custom models

| Model | Fields (selected) | Relationship |
|---|---|---|
| `MemberProfile` | `user`, `membership_id`, `phone` | `OneToOneField(User)` |
| `Author` | `name`, `email`, `bio` | `Book.authors` links to this model |
| `Book` | `title`, `isbn`, `genre`, `total_copies`, `authors` | `ManyToManyField(Author)` |
| `BorrowRecord` | `member`, `book`, `borrow_date`, `due_date`, `returned_at` | Two `ForeignKey` fields |

```text
Django User ─── (OneToOne) ─── MemberProfile
                                     │
                               (ForeignKey)
                                     │
                                BorrowRecord
                                     │
                               (ForeignKey)
                                     │
                                    Book ── (ManyToMany) ── Author
```

There are **4 custom model classes**, but actual SQLite tables also include Django's built-in auth/admin tables and the automatically-created many-to-many join table. That is normal Django behavior.

### Business rules

1. Book ISBN must be exactly 13 digits and have a valid **ISBN-13 check digit**.
2. Membership ID must match `LIB-0001`, `LIB-0002`, etc.
3. Book's `total_copies` must be **at least 1**; it cannot be reduced below active loans.
4. An author name must be unique (including a case-insensitive check).
5. A borrower cannot borrow the **same book twice simultaneously**.
6. Active loans cannot exceed the book's total copies.
7. Due date must be on/after borrow date; borrow/return dates cannot be in the future; return date cannot be before borrow date.
8. `available_copies` is a **read-only computed value**: `total_copies - active loans`. Returning or deleting a loan automatically affects availability. There is no separate stock field to get out of sync.
9. Read APIs are public locally; create/edit/delete require login (Basic or Session authentication).

## 5. API endpoints

All endpoints have a **trailing slash**. Each has standard ViewSet actions:

| HTTP method | URL example | Meaning |
|---|---|---|
| `GET` | `/api/books/` | List books |
| `POST` | `/api/books/` | Add book |
| `GET` | `/api/books/1/` | Read one book |
| `PUT` | `/api/books/1/` | Replace an existing book |
| `PATCH` | `/api/books/1/` | Update selected fields |
| `DELETE` | `/api/books/1/` | Delete a book |

Use the same six methods with each resource:

```text
/api/members/
/api/authors/
/api/books/
/api/borrow-records/
```

Successful statuses: `200 OK`, `201 Created`, `204 No Content`; invalid requests: `400 Bad Request`; unauthenticated modification: `401 Unauthorized`; missing record: `404 Not Found`.

### Nested serializers and read-only / write-only fields

- Book: send **`author_ids`** when writing (`write_only=True`); response includes nested **`authors`** (`read_only=True`).
- BorrowRecord: send member/book IDs; response includes `member_detail` and `book_detail` (read-only nested information).
- `available_copies`, `status`, `created_at`, `joined_at` are read-only.

### Example — add a book (authenticated)

```http
POST http://127.0.0.1:8000/api/books/
Authorization: Basic <base64 of username:password>
Content-Type: application/json

{
  "title": "Introduction to Programming",
  "isbn": "9780131177055",
  "genre": "programming",
  "total_copies": 2,
  "published_year": 2004,
  "author_ids": [1]
}
```

Example successful response (IDs vary):

```json
{
  "id": 7,
  "title": "Introduction to Programming",
  "isbn": "9780131177055",
  "genre": "programming",
  "published_year": 2004,
  "total_copies": 2,
  "available_copies": 2,
  "authors": [
    {"id": 1, "name": "Robert C. Martin", "email": "", "bio": "", "book_count": 2}
  ]
}
```

### Example — borrow a book

Change `member`, `book`, and the dates to valid values. The `due_date` must not be earlier than the `borrow_date`.

```json
{
  "member": 1,
  "book": 1,
  "borrow_date": "2026-11-13",
  "due_date": "2026-11-27"
}
```

Mark it returned with:

```http
PATCH /api/borrow-records/1/
Content-Type: application/json

{"returned_at": "2026-11-13"}
```

The example dates are for the November 2026 viva. Use today's actual date when running it later.

### Example — validation error

If book copies are zero, API returns HTTP `400` with a meaningful field error, for example:

```json
{"total_copies": ["Ensure this value is greater than or equal to 1."]}
```

## 6. Filtering, searching, ordering and pagination

These work on all four list endpoints. Examples:

```text
GET /api/books/?genre=programming
GET /api/books/?authors=1
GET /api/books/?search=Python
GET /api/books/?ordering=-total_copies
GET /api/members/?search=student1
GET /api/authors/?ordering=name
GET /api/borrow-records/?returned_at__isnull=true
GET /api/borrow-records/?due_date__lte=2026-11-30
GET /api/books/?page=2&page_size=3
```

Default page size: **5**, maximum user-chosen page size: **50**. All list endpoints return:

```json
{"count": 6, "next": "http://127.0.0.1:8000/api/books/?page=2", "previous": null, "results": []}
```

The `results` above is an illustration of the response shape, not a real first page. It normally contains the matching records.

## 7. Django Admin

Visit `/admin/`, log in, and view all four models. It demonstrates `list_display`, `search_fields`, `list_filter`, `ordering`, `readonly_fields`, `filter_horizontal` for book authors, and a `BorrowRecordInline` inside Book Admin. Django's built-in Users page creates accounts. To POST a new member profile, first create an unused User in Admin (or use the seeded `student4` account, which intentionally has no profile).

## 8. Load sample data

```bash
python manage.py seed_demo
```

Creates **5 fake Users** (admin, 3 member accounts and 1 spare account), **3 MemberProfiles**, **7 Authors**, **6 Books**, and **3 BorrowRecords**. One book has two authors to demonstrate many-to-many. One loan is returned and two are active. The command can be rerun without duplicating this sample data.

To find an unused seeded User's ID:

```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.get(username='student4').pk)"
```

Set this ID as `unassigned_user_id` in the Postman collection before testing create-member. On a completely fresh sample database it is normally `2`; **never assume an ID** if the database already contains Users.

## 9. Test the APIs

### Automated Django test suite

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test library --verbosity 2
```

Expected: all checks and tests pass. `makemigrations --check --dry-run` should report no model changes, because initial migration is included.

### Manual Postman collection

Import `postman/Mini_Library.postman_collection.json` into Postman.

Collection variables:

- `base_url` = `http://127.0.0.1:8000`
- `username` = `library_admin`
- `password` = `LibraryDemo123!`
- `unassigned_user_id` = the `student4` ID from the shell command above

The collection includes list, create, retrieve, PUT, PATCH, DELETE, search/filter/ordering/pagination, and an invalid input example. Create operations capture the new IDs automatically for later requests. Use create → read/edit → delete within each resource folder; POST on the member folder will fail if `student4` already received a membership, so use a fresh database or create another unused User.

You can also use the DRF Browsable API in a browser. Login at `/api-auth/login/` for create/update/delete controls.

## 10. Evaluation rubric map (100 marks)

| Rubric section | Marks | Where implemented |
|---|---:|---|
| Database/models/relationships | 20 | `library/models.py` and migration |
| ModelSerializers, nested and read/write fields | 15 | `library/serializers.py` |
| Complete REST CRUD | 15 | `library/views.py`, `library/urls.py` |
| Field/serializer/model validation | 10 | `validators.py`, `serializers.py`, `models.py` |
| Filter/search/ordering | 10 | ViewSet settings and `config/settings.py` |
| Pagination | 5 | `library/pagination.py` |
| Django Admin | 10 | `library/admin.py` |
| Code structure | 5 | Separate `config`, `library`, tests, helpers |
| API testing | 5 | `library/tests/` and Postman collection |
| Documentation | 5 | `README.md`, `VIVA_GUIDE_BN.md` |
| **Total possible** | **100** | **Implementation coverage, not a guarantee of marks** |

## 11. Notes

- This is intentionally **backend-only**, matching the instructor's viva instruction. There is no Flutter screen.
- `MemberProfile.user` uses Django's **built-in** User instead of defining a fifth custom model.
- SQLite is appropriate for this small course demonstration. For high-concurrency production checkout, stock checks should be wrapped in a stronger transactional locking strategy on PostgreSQL; this sample is not production-hardened.
- Database migration source is committed, but the generated `db.sqlite3` is excluded from ZIP. Run `migrate` and `seed_demo` to create it locally.
- Bengali questions, syntax explanations, and a sample viva script are in `VIVA_GUIDE_BN.md`.
