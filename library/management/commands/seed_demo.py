"""Create safe, fictional demo accounts, books, authors and loan records."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from library.models import Author, Book, BorrowRecord, MemberProfile


class Command(BaseCommand):
    help = 'Create repeatable demo data for the library project (safe to rerun).'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        admin, created = User.objects.get_or_create(
            username='library_admin',
            defaults={'email': 'admin@example.local', 'is_staff': True,
                      'is_superuser': True},
        )
        if created:
            admin.set_password('LibraryDemo123!')
            admin.save()

        # A spare User (without a MemberProfile) makes POST /api/members/ easy to demo.
        spare_user, spare_created = User.objects.get_or_create(
            username='student4', defaults={'first_name': 'Fariah'}
        )
        if spare_created:
            spare_user.set_password('StudentDemo123!')
            spare_user.save()

        members = {}
        for n, name in [(1, 'Ayesha'), (2, 'Rahim'), (3, 'Nadia')]:
            username = f'student{n}'
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': name, 'email': f'{username}@example.local'},
            )
            if user_created:
                user.set_password('StudentDemo123!')
                user.save()
            profile, _ = MemberProfile.objects.get_or_create(
                user=user,
                defaults={'membership_id': f'LIB-{n:04d}', 'phone': '01700000000'},
            )
            members[n] = profile

        author_names = [
            'Robert C. Martin', 'Luciano Ramalho', 'Brian W. Kernighan',
            'Dennis M. Ritchie', 'Thomas H. Cormen', 'Eric Freeman',
            'Joshua Bloch',
        ]
        authors = {}
        for name in author_names:
            authors[name], _ = Author.objects.get_or_create(name=name)

        sample_books = [
            ('Clean Code', '9780132350884', 'programming', 3, 2008,
             ['Robert C. Martin']),
            ('Fluent Python', '9781491957660', 'programming', 2, 2015,
             ['Luciano Ramalho']),
            ('The C Programming Language', '9780131103627', 'programming',
             2, 1988, ['Brian W. Kernighan', 'Dennis M. Ritchie']),
            ('Introduction to Algorithms', '9780262033848', 'science', 2, 2009,
             ['Thomas H. Cormen']),
            ('Head First Design Patterns', '9780596007126', 'programming',
             1, 2004, ['Eric Freeman']),
            ('Effective Java', '9780134685991', 'programming', 2, 2018,
             ['Joshua Bloch']),
        ]
        books = {}
        for title, isbn, genre, copies, year, book_authors in sample_books:
            book, _ = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    'title': title, 'genre': genre,
                    'total_copies': copies, 'published_year': year,
                },
            )
            book.authors.add(*(authors[name] for name in book_authors))
            books[title] = book

        today = timezone.localdate()
        loans = [
            (1, 'Clean Code', today - timedelta(days=5),
             today + timedelta(days=9), None),
            (2, 'Fluent Python', today - timedelta(days=2),
             today + timedelta(days=12), None),
            (3, 'The C Programming Language', today - timedelta(days=12),
             today - timedelta(days=2), today - timedelta(days=1)),
        ]
        for member_number, title, borrowed, due, returned in loans:
            # An existing record for this member/book means it has already
            # been demonstrated; avoid duplicates on subsequent seed runs.
            member = members[member_number]
            book = books[title]
            if not BorrowRecord.objects.filter(member=member, book=book).exists():
                BorrowRecord.objects.create(
                    member=member, book=book, borrow_date=borrowed,
                    due_date=due, returned_at=returned,
                )

        self.stdout.write(self.style.SUCCESS(
            'Demo ready: 5 users, 3 profiles, 7 authors, 6 books, 3 loans.'
        ))
        self.stdout.write('Admin (local only): library_admin / LibraryDemo123!')
        self.stdout.write('Student (local only): student1 / StudentDemo123!')
        self.stdout.write(f'Spare user ID (for member POST): {spare_user.pk}')
        self.stdout.write('Visit http://127.0.0.1:8000/api/ or /admin/')
