"""Model-level integrity and relationship tests."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from library.models import Author, Book, BorrowRecord, MemberProfile
from library.validators import validate_isbn13, validate_membership_id


class LibraryModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username='user1', password='VerySafe123!')
        cls.other_user = User.objects.create_user(
            username='user2', password='VerySafe123!'
        )
        cls.member = MemberProfile.objects.create(
            user=cls.user, membership_id='LIB-0001'
        )
        cls.other_member = MemberProfile.objects.create(
            user=cls.other_user, membership_id='LIB-0002'
        )
        cls.author = Author.objects.create(name='First Writer')
        cls.coauthor = Author.objects.create(name='Second Writer')
        cls.book = Book.objects.create(
            title='A Test Book', isbn='9780132350884', total_copies=1
        )
        cls.book.authors.add(cls.author, cls.coauthor)

    def test_all_three_relationship_types(self):
        self.assertEqual(self.user.member_profile, self.member)  # OneToOne
        self.assertEqual(self.book.authors.count(), 2)  # ManyToMany
        self.assertIn(self.book, self.author.books.all())
        loan = BorrowRecord.objects.create(
            member=self.member, book=self.book,
            due_date=timezone.localdate() + timedelta(days=7),
        )
        self.assertEqual(loan.book, self.book)  # ForeignKey
        self.assertEqual(loan.member, self.member)

    def test_model_str_methods(self):
        self.assertIn('LIB-0001', str(self.member))
        self.assertEqual(str(self.author), 'First Writer')
        self.assertEqual(str(self.book), 'A Test Book')

    def test_isbn_and_membership_validators(self):
        validate_isbn13('9780132350884')
        validate_membership_id('LIB-1234')
        with self.assertRaises(ValidationError):
            validate_isbn13('9780132350885')
        with self.assertRaises(ValidationError):
            validate_membership_id('1234')

    def test_model_rejects_negative_or_zero_stock(self):
        with self.assertRaises(ValidationError):
            Book.objects.create(
                title='Bad Stock', isbn='9781491957660', total_copies=0
            )

    def test_case_insensitive_duplicate_author(self):
        with self.assertRaises(ValidationError):
            Author.objects.create(name='first writer')

    def test_model_rejects_duplicate_active_loan(self):
        due = timezone.localdate() + timedelta(days=5)
        BorrowRecord.objects.create(member=self.member, book=self.book, due_date=due)
        with self.assertRaises(ValidationError):
            BorrowRecord.objects.create(member=self.member, book=self.book, due_date=due)
        with self.assertRaises(ValidationError):
            BorrowRecord.objects.create(
                member=self.other_member, book=self.book, due_date=due
            )

    def test_available_copies_restored_after_return(self):
        due = timezone.localdate() + timedelta(days=7)
        loan = BorrowRecord.objects.create(
            member=self.member, book=self.book, due_date=due
        )
        self.assertEqual(self.book.available_copies, 0)
        loan.returned_at = timezone.localdate()
        loan.save()
        self.assertEqual(self.book.available_copies, 1)

    def test_cannot_reduce_stock_below_active_loans(self):
        BorrowRecord.objects.create(
            member=self.member, book=self.book,
            due_date=timezone.localdate() + timedelta(days=7),
        )
        self.book.total_copies = 0
        with self.assertRaises(ValidationError):
            self.book.save()

    def test_due_date_and_return_date_rules(self):
        today = timezone.localdate()
        with self.assertRaises(ValidationError):
            BorrowRecord.objects.create(
                member=self.member, book=self.book,
                borrow_date=today, due_date=today - timedelta(days=1),
            )
        with self.assertRaises(ValidationError):
            BorrowRecord.objects.create(
                member=self.member, book=self.book,
                borrow_date=today, due_date=today + timedelta(days=7),
                returned_at=today + timedelta(days=1),
            )
