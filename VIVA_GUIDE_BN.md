# Mini Library Management System — বাংলা Viva Preparation

**Project type:** Django REST Framework Backend Only  
**Team:** ৩–৪ জন  
**Core custom models:** `MemberProfile`, `Author`, `Book`, `BorrowRecord`  
**Database:** SQLite  
**API:** `http://127.0.0.1:8000/api/`

## ১. ৪০–৬০ সেকেন্ডে প্রজেক্ট পরিচিতি

> Assalamu Alaikum, Sir. Our project is a Mini Library Management System developed with Django and Django REST Framework. We use SQLite and four custom models: MemberProfile, Author, Book, and BorrowRecord. MemberProfile has a OneToOne relationship with Django's built-in User. Book and Author have a ManyToMany relationship. BorrowRecord has ForeignKey relationships with MemberProfile and Book. We implemented CRUD APIs, serializers, nested data, model and serializer validation, filtering, searching, ordering, pagination, and customized Django Admin. We can test everything through Postman or the DRF Browsable API.

## ২. কোন ফাইলের কাজ কী?

| File | সহজ ব্যাখ্যা | গুরুত্বপূর্ণ Syntax |
|---|---|---|
| `manage.py` | Django command চালানোর entry point | `python manage.py runserver` |
| `config/settings.py` | Database, App, REST framework config | `INSTALLED_APPS`, `REST_FRAMEWORK` |
| `config/urls.py` | Main URL routing | `path('api/', include(...))` |
| `library/models.py` | Database table, field, relationship, business rule | `models.Model`, `ForeignKey`, `clean()` |
| `library/validators.py` | ISBN ও Member ID যাচাই | `raise ValidationError(...)` |
| `library/serializers.py` | Python/model object ↔ JSON এবং input validation | `serializers.ModelSerializer` |
| `library/views.py` | Request handling; CRUD actions | `viewsets.ModelViewSet` |
| `library/urls.py` | ViewSet-এর API URL auto-generate | `DefaultRouter` |
| `library/pagination.py` | বড় list কে ছোট page-এ ভাগ করা | `PageNumberPagination` |
| `library/admin.py` | Django Admin customize | `@admin.register(Book)` |
| `library/migrations/0001_initial.py` | Database schema তৈরি | `migrations.CreateModel` |
| `seed_demo.py` | Test করার জন্য fake data ঢোকায় | `get_or_create()` |
| `library/tests/` | CRUD/validation/filtering automatically test | `TestCase`, `APIClient` |

## ৩. Database relationship — Viva-তে সবচেয়ে গুরুত্বপূর্ণ

**OneToOne:** একজন `User`-এর একটি মাত্র `MemberProfile` থাকবে।

```python
user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
```

**OneToMany:** একজন Member-এর অনেক BorrowRecord থাকতে পারে; কিন্তু এক BorrowRecord-এর একজন Member। Django-তে `ForeignKey` দিয়ে implement করি।

```python
member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
```

**ManyToMany:** একটি বইয়ের একাধিক Author থাকতে পারে; এক Author একাধিক বই লিখতে পারেন।

```python
authors = models.ManyToManyField(Author, related_name='books')
```

**মনে রাখবে:** Custom Model class ৪টি হলেও `auth_user`-এর মতো Django built-in table এবং ManyToMany intermediate/join table অতিরিক্ত তৈরি হয়।

## ৪. CRUD এবং HTTP Methods

| Method | Meaning | Django ModelViewSet action | Status |
|---|---|---|---|
| GET `/api/books/` | সব বই | `list` | 200 |
| POST `/api/books/` | নতুন বই | `create` | 201 |
| GET `/api/books/1/` | নির্দিষ্ট বই | `retrieve` | 200 |
| PUT `/api/books/1/` | পুরো record replace | `update` | 200 |
| PATCH `/api/books/1/` | নির্দিষ্ট field update | `partial_update` | 200 |
| DELETE `/api/books/1/` | record delete | `destroy` | 204 |

**প্রশ্ন: `ModelViewSet` কেন?** কারণ একটি class দিয়েই standard ৬টি CRUD action পাওয়া যায়; বারবার আলাদা view লিখতে হয় না।

**প্রশ্ন: `DefaultRouter` কেন?** ViewSet থেকে URL patterns automatically বানায়; যেমন `/api/books/` ও `/api/books/1/`।

## ৫. Serializer — Most important topic

Serializer Django Model object-কে JSON response-এ রূপান্তর করে এবং JSON request data validate করে Python data বানায়।

```python
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'bio']
```

প্রকৃত code-এ AuthorSerializer-এ অতিরিক্ত `book_count` আছে।

**Nested Serializer:** `BookSerializer`-এর মধ্যে `AuthorSerializer(many=True, read_only=True)` দিয়ে author-এর details দেখাই।

**Write-only field:** Book create/update করার সময় `author_ids` পাঠাই; response-এ `author_ids` দেখাই না।

**Read-only field:** `available_copies` API-তে output হিসেবে দেখা যায়, কিন্তু user সেট করতে পারে না। এটি active loan count থেকে calculate হয়।

**Serializer `validate()` কী করে?** একাধিক field একসাথে যাচাই করে। BorrowRecord-এ due date borrow date-এর আগে কি না, stock আছে কি না, duplicate active loan আছে কি না—এসব check করে।

**Model `clean()` কেন?** Database Model স্তরেও একই business rule enforce করার জন্য; শুধু API নয়, Admin/management command থেকেও invalid save আটকাতে সাহায্য করে।

## ৬. Filter, Search, Ordering, Pagination

`GET /api/books/?genre=programming` → programming genre-এর বই।  
`GET /api/books/?search=Python` → title/ISBN/author-এ Python search।  
`GET /api/books/?ordering=-total_copies` → বেশি stock আগে (descending)।  
`GET /api/books/?page=2&page_size=3` → দ্বিতীয় page, প্রতি page ৩টি record।

**`-` কেন?** Ordering field-এর আগে minus (`-`) দিলে descending sort হয়।

**DRF filter backend কী?** `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` ব্যবহার করে query parameter থেকে filtered records ফিরিয়ে দেয়।

**Pagination response keys কী?** `count`, `next`, `previous`, `results`। Default page size = 5।

## ৭. Django Admin

`admin.py`-তে সব ৪টি custom model register করা হয়েছে।

- `list_display`: তালিকায় কোন কোন column দেখাবো।
- `search_fields`: Admin search box কোন field-এ খুঁজবে।
- `list_filter`: Sidebar থেকে filter।
- `ordering`: Default sorting।
- `readonly_fields`: যে value Admin change করতে পারবে না।
- `filter_horizontal`: Book-এর ManyToMany Authors UI।
- `BorrowRecordInline`: Book edit page থেকে related borrow records দেখা/এডিট করা যায়।

## ৮. Common Viva Questions & Short Answers

**Q1. Django কী?**  
Python-এর high-level web framework, যেটা web application ও backend তৈরিতে ব্যবহার হয়।

**Q2. DRF কী?**  
Django REST Framework হলো Django-তে RESTful API বানানোর একটি toolkit।

**Q3. API কী?**  
Application Programming Interface; frontend বা অন্য client backend-এর সাথে HTTP request/response মাধ্যমে যোগাযোগ করে।

**Q4. REST কী?**  
HTTP method ও resource-based URL ব্যবহার করে API design করার architectural approach।

**Q5. Model কী?**  
Python class যা Database Table-এর structure represent করে।

**Q6. `models.Model` কী?**  
Django ORM-এর base class; এটি extend করলে database model তৈরি হয়।

**Q7. ORM কী?**  
Object Relational Mapper; Python code দিয়ে SQL table query করা যায়। যেমন `Book.objects.all()`।

**Q8. `__str__()` কেন?**  
Object readable নাম দেখানোর জন্য, যেমন Admin-এ `Clean Code`।

**Q9. `on_delete=models.CASCADE` কী?**  
Related parent record delete করলে child record-ও delete হয়।

**Q10. `related_name` কী?**  
Reverse relation access করার নাম। যেমন `book.loans.all()`।

**Q11. Migration কী?**  
Model-এর design database schema-তে apply করার versioned changes।

**Q12. `makemigrations` vs `migrate`?**  
`makemigrations` migration file generate করে, `migrate` database-এ সেই file apply করে।

**Q13. `GET` vs `POST`?**  
GET data পড়ে, POST new record তৈরি করে।

**Q14. `PUT` vs `PATCH`?**  
PUT সম্পূর্ণ update, PATCH কয়েকটি field update।

**Q15. `200`, `201`, `204`, `400`, `401`, `404`?**  
200 success; 201 created; 204 success with no body; 400 invalid input; 401 authentication required; 404 record not found।

**Q16. `serializer.is_valid()` কী?**  
Input validate করে; invalid হলে field error দেয়।

**Q17. `validated_data` কী?**  
Validation শেষে cleaned Python data।

**Q18. `serializer.save()` কী?**  
Serializer-এর `create()` বা `update()` ব্যবহার করে data save করে।

**Q19. `read_only=True` vs `write_only=True`?**  
Read-only output-এ থাকে, input দিয়ে change করা যায় না; write-only input নেওয়া হয়, output-এ পাঠানো হয় না।

**Q20. `queryset` কী?**  
Database থেকে query করার lazy collection; যেমন `Book.objects.all()`।

**Q21. কেন ISBN validation?**  
ভুল/ফেক ISBN আটকাতে; এখানে ১৩-ডিজিট checksum rule ব্যবহার করা হয়।

**Q22. Duplicate active loan কীভাবে বন্ধ?**  
একই Member, একই Book ও `returned_at IS NULL` record আগে আছে কি না দেখা হয়।

**Q23. Available copies কীভাবে হিসাব হয়?**  
`total_copies - active loan count`। Return হলে active count কমে, availability বাড়ে।

**Q24. কেন SQLite?**  
Small project-এ separate database server ছাড়া file-based database ব্যবহার করা যায়।

**Q25. Authentication কী?**  
কে user সেটি যাচাই করা। Demo-তে Django Session/Basic authentication আছে।

**Q26. Permission কী?**  
কে কোন API action করতে পারবে। এখানে `IsAuthenticatedOrReadOnly` মানে login ছাড়া GET করা যায়, কিন্তু POST/PUT/PATCH/DELETE-এ login লাগে।

**Q27. `admin.py`-এর কাজ কী?**  
Web-based backend data manage করার interface configure করা।

**Q28. `seed_demo` কী?**  
Sample Users/Books/Authors/BorrowRecords create করার custom management command।

**Q29. `select_related` / `prefetch_related` কেন?**  
Related data efficiently query করার জন্য। ForeignKey-এ `select_related`, ManyToMany-এ `prefetch_related` কার্যকর।

**Q30. Flutter/frontend কোথায়?**  
এই assessmentটি backend-only; স্যারের নির্দেশ অনুযায়ী frontend পরে full-stack part-এ করা হবে।

## ৯. Live Viva Demo — ২ মিনিট

1. `python manage.py runserver` চালাও, browser-এ `/api/` দেখাও।
2. `/api/books/` GET দেখাও; nested authors এবং `available_copies` explain করো।
3. `/api/books/?search=Python` এবং `?ordering=-total_copies` দেখাও।
4. Postman-এ authenticated POST দিয়ে নতুন author বা book create করো।
5. Wrong ISBN বা out-of-stock loan দিলে HTTP 400 দেখাও।
6. `/admin/`-এ Book Admin-এর search/filter/author selection দেখাও।
7. `python manage.py test library` চালিয়ে automated test result দেখাও।

## ১০. ৪ জনের Group Division

| Member | Primary responsibility | কিন্তু সবার যেটা জানা দরকার |
|---|---|---|
| 1 | `models.py`, relations, migrations | ৪টি model ও relationship explain |
| 2 | `serializers.py`, validators | create/update + read/write fields |
| 3 | `views.py`, `urls.py`, filtering/pagination | CRUD endpoints ও HTTP status |
| 4 | `admin.py`, tests, README, Postman | Admin settings ও API demo |

**সবার জন্য:** `Model → Serializer → ViewSet → URL → JSON Response` এই data flow মুখস্থ না করে বুঝে যাও। স্যার যাকে প্রশ্ন করবেন তাকে নিজের অংশ ছাড়াও basic syntax বলতে হবে।

## ১১. Last-minute commands (copy/paste)

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py check
python manage.py test library
python manage.py runserver
```

**মনে রাখবে:** Demo login শুধু local machine-এর জন্য। Actual deployment-এ hardcoded demo credential কখনো ব্যবহার করা যাবে না।
