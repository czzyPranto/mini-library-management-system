"""Check the admin registry and repeatable sample-data command."""
from django.contrib import admin
from django.core.management import call_command
from django.test import TestCase

from library.admin import BookAdmin, BorrowRecordInline
from library.models import Author, Book, BorrowRecord, MemberProfile


class AdminAndSeedTests(TestCase):
    def test_all_four_models_registered_and_book_admin_customized(self):
        for model in [MemberProfile, Author, Book, BorrowRecord]:
            self.assertIn(model, admin.site._registry)
        registered = admin.site._registry[Book]
        self.assertIsInstance(registered, BookAdmin)
        self.assertIn('authors', registered.filter_horizontal)
        self.assertIn(BorrowRecordInline, registered.inlines)
        self.assertIn('title', registered.search_fields)
        self.assertIn('genre', registered.list_filter)
        self.assertIn('available_copies', registered.readonly_fields)

    def test_seed_data_command_idempotent(self):
        call_command('seed_demo', verbosity=0)
        first_counts = (
            MemberProfile.objects.count(), Author.objects.count(),
            Book.objects.count(), BorrowRecord.objects.count(),
        )
        self.assertEqual(first_counts, (3, 7, 6, 3))
        call_command('seed_demo', verbosity=0)
        second_counts = (
            MemberProfile.objects.count(), Author.objects.count(),
            Book.objects.count(), BorrowRecord.objects.count(),
        )
        self.assertEqual(second_counts, first_counts)
