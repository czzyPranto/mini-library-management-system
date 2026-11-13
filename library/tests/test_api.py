"""Automated DRF endpoint, CRUD, validation, filter, pagination tests."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from library.models import Author, Book, BorrowRecord, MemberProfile


class LibraryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username='alice', password='GoodPass123!')
        cls.user2 = User.objects.create_user(username='bob', password='GoodPass123!')
        cls.member = MemberProfile.objects.create(
            user=cls.user, membership_id='LIB-0001'
        )
        cls.author = Author.objects.create(name='Test Author')
        cls.book = Book.objects.create(
            title='Python Basics', isbn='9780132350884',
            genre='programming', total_copies=1,
        )
        cls.book.authors.add(cls.author)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.today = timezone.localdate()
        self.due = (self.today + timedelta(days=7)).isoformat()

    def test_anonymous_read_is_allowed_but_write_requires_login(self):
        guest = APIClient()
        self.assertEqual(guest.get('/api/books/').status_code, status.HTTP_200_OK)
        result = guest.post('/api/authors/', {'name': 'Anonymous'}, format='json')
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_author_full_crud(self):
        created = self.client.post(
            '/api/authors/', {'name': 'Second Author', 'email': 'author@example.com'},
            format='json',
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        pk = created.data['id']
        self.assertEqual(self.client.get(f'/api/authors/{pk}/').status_code, 200)
        changed = self.client.put(
            f'/api/authors/{pk}/',
            {'name': 'Second Author', 'email': 'new@example.com', 'bio': 'Short bio'},
            format='json',
        )
        self.assertEqual(changed.status_code, 200, changed.data)
        patched = self.client.patch(
            f'/api/authors/{pk}/', {'bio': 'Patched'}, format='json'
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(self.client.delete(f'/api/authors/{pk}/').status_code, 204)
        self.assertEqual(self.client.get(f'/api/authors/{pk}/').status_code, 404)

    def test_member_full_crud(self):
        created = self.client.post(
            '/api/members/',
            {'user': self.user2.pk, 'membership_id': 'LIB-0002',
             'phone': '01800000000'},
            format='json',
        )
        self.assertEqual(created.status_code, 201, created.data)
        pk = created.data['id']
        self.assertEqual(created.data['username'], 'bob')
        self.assertEqual(self.client.get(f'/api/members/{pk}/').status_code, 200)
        updated = self.client.put(
            f'/api/members/{pk}/',
            {'user': self.user2.pk, 'membership_id': 'LIB-0002', 'phone': '01111'},
            format='json',
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(self.client.patch(
            f'/api/members/{pk}/', {'phone': '02222'}, format='json'
        ).status_code, 200)
        self.assertEqual(self.client.delete(f'/api/members/{pk}/').status_code, 204)

    def test_book_full_crud_and_nested_read_only_authors(self):
        payload = {
            'title': 'Advanced Python', 'isbn': '9781491957660',
            'author_ids': [self.author.pk], 'genre': 'programming',
            'total_copies': 2, 'published_year': 2015,
        }
        created = self.client.post('/api/books/', payload, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['authors'][0]['name'], 'Test Author')
        self.assertNotIn('author_ids', created.data)
        self.assertEqual(created.data['available_copies'], 2)
        pk = created.data['id']
        self.assertEqual(self.client.get(f'/api/books/{pk}/').status_code, 200)
        updated = self.client.put(
            f'/api/books/{pk}/', {**payload, 'title': 'Updated Book'},
            format='json',
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        patched = self.client.patch(
            f'/api/books/{pk}/', {'total_copies': 3}, format='json'
        )
        self.assertEqual(patched.status_code, 200, patched.data)
        self.assertEqual(self.client.delete(f'/api/books/{pk}/').status_code, 204)

    def test_borrow_record_full_crud_and_return(self):
        payload = {
            'member': self.member.pk, 'book': self.book.pk,
            'borrow_date': self.today.isoformat(), 'due_date': self.due,
        }
        created = self.client.post('/api/borrow-records/', payload, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['status'], 'borrowed')
        self.assertEqual(created.data['book_detail']['title'], 'Python Basics')
        self.assertEqual(created.data['member_detail']['membership_id'], 'LIB-0001')
        pk = created.data['id']
        self.assertEqual(self.book.available_copies, 0)
        self.assertEqual(self.client.get(f'/api/borrow-records/{pk}/').status_code, 200)
        put = self.client.put(
            f'/api/borrow-records/{pk}/',
            {**payload, 'due_date': (self.today + timedelta(days=9)).isoformat()},
            format='json',
        )
        self.assertEqual(put.status_code, 200, put.data)
        returned = self.client.patch(
            f'/api/borrow-records/{pk}/',
            {'returned_at': self.today.isoformat()}, format='json',
        )
        self.assertEqual(returned.status_code, 200, returned.data)
        self.assertEqual(returned.data['status'], 'returned')
        self.assertEqual(self.book.available_copies, 1)
        self.assertEqual(self.client.delete(f'/api/borrow-records/{pk}/').status_code, 204)

    def test_duplicate_author_case_insensitive(self):
        response = self.client.post(
            '/api/authors/', {'name': 'test author'}, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data)

    def test_invalid_isbn_stock_and_missing_authors(self):
        payload = {'title': 'Invalid', 'isbn': '1234567890123',
                   'genre': 'fiction', 'total_copies': 1,
                   'author_ids': [self.author.pk]}
        invalid_isbn = self.client.post('/api/books/', payload, format='json')
        self.assertEqual(invalid_isbn.status_code, 400)
        self.assertIn('isbn', invalid_isbn.data)
        payload['isbn'] = '9781491957660'
        payload['total_copies'] = 0
        self.assertEqual(self.client.post(
            '/api/books/', payload, format='json'
        ).status_code, 400)
        payload['total_copies'] = 1
        payload.pop('author_ids')
        missing_authors = self.client.post('/api/books/', payload, format='json')
        self.assertEqual(missing_authors.status_code, 400)
        self.assertIn('author_ids', missing_authors.data)

    def test_future_published_year_returns_useful_400(self):
        payload = {
            'title': 'Future Book', 'isbn': '9781491957660',
            'genre': 'science', 'total_copies': 1,
            'published_year': self.today.year + 1,
            'author_ids': [self.author.pk],
        }
        result = self.client.post('/api/books/', payload, format='json')
        self.assertEqual(result.status_code, 400)
        self.assertIn('published_year', result.data)

    def test_cannot_duplicate_active_loan_or_overbook(self):
        payload = {'member': self.member.pk, 'book': self.book.pk,
                   'due_date': self.due}
        first = self.client.post('/api/borrow-records/', payload, format='json')
        self.assertEqual(first.status_code, 201, first.data)
        duplicate = self.client.post('/api/borrow-records/', payload, format='json')
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn('book', duplicate.data)
        member2 = MemberProfile.objects.create(
            user=self.user2, membership_id='LIB-0002'
        )
        out_of_stock = self.client.post('/api/borrow-records/',
                                        {**payload, 'member': member2.pk},
                                        format='json')
        self.assertEqual(out_of_stock.status_code, 400)
        self.assertIn('book', out_of_stock.data)

    def test_invalid_borrow_dates(self):
        payload = {
            'member': self.member.pk, 'book': self.book.pk,
            'borrow_date': self.today.isoformat(),
            'due_date': (self.today - timedelta(days=1)).isoformat(),
        }
        wrong_due = self.client.post('/api/borrow-records/', payload, format='json')
        self.assertEqual(wrong_due.status_code, 400)
        self.assertIn('due_date', wrong_due.data)
        payload['due_date'] = self.due
        payload['returned_at'] = (self.today + timedelta(days=1)).isoformat()
        future_return = self.client.post('/api/borrow-records/', payload, format='json')
        self.assertEqual(future_return.status_code, 400)
        self.assertIn('returned_at', future_return.data)

    def test_cannot_reduce_copies_below_active_borrow_count(self):
        self.client.post('/api/borrow-records/',
                         {'member': self.member.pk, 'book': self.book.pk,
                          'due_date': self.due}, format='json')
        result = self.client.patch(
            f'/api/books/{self.book.pk}/', {'total_copies': 0}, format='json'
        )
        self.assertEqual(result.status_code, 400)

    def test_filter_search_and_ordering(self):
        other = Book.objects.create(
            title='Astronomy Guide', isbn='9781491957660',
            genre='science', total_copies=2,
        )
        other.authors.add(self.author)
        filtered = self.client.get('/api/books/?genre=science')
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.data['count'], 1)
        self.assertEqual(filtered.data['results'][0]['title'], 'Astronomy Guide')
        searched = self.client.get('/api/books/?search=Python')
        self.assertEqual(searched.data['count'], 1)
        ordered = self.client.get('/api/books/?ordering=-title')
        self.assertEqual(ordered.data['results'][0]['title'], 'Python Basics')

    def test_borrow_filter_and_search(self):
        self.client.post(
            '/api/borrow-records/',
            {'member': self.member.pk, 'book': self.book.pk, 'due_date': self.due},
            format='json',
        )
        active = self.client.get('/api/borrow-records/?returned_at__isnull=true')
        self.assertEqual(active.data['count'], 1)
        searched = self.client.get('/api/borrow-records/?search=Python')
        self.assertEqual(searched.data['count'], 1)

    def test_paginated_list_on_all_four_endpoints(self):
        for endpoint in ['members', 'authors', 'books', 'borrow-records']:
            result = self.client.get(f'/api/{endpoint}/')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(
                set(['count', 'next', 'previous', 'results'])
                .issubset(result.data.keys()), True
            )
        for n in range(7):
            Author.objects.create(name=f'Pagination Writer {n}')
        page = self.client.get('/api/authors/?page_size=3')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(page.data['results']), 3)
        self.assertIsNotNone(page.data['next'])
        self.assertEqual(self.client.get('/api/authors/?page=2&page_size=3').status_code, 200)
