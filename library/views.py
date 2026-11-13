"""ModelViewSet provides list/create/retrieve/update/partial_update/destroy."""
from rest_framework import viewsets

from .models import Author, Book, BorrowRecord, MemberProfile
from .serializers import (
    AuthorSerializer, BookSerializer, BorrowRecordSerializer,
    MemberProfileSerializer,
)


class MemberProfileViewSet(viewsets.ModelViewSet):
    queryset = MemberProfile.objects.select_related('user').all()
    serializer_class = MemberProfileSerializer
    filterset_fields = ['user', 'membership_id']
    search_fields = ['membership_id', 'user__username', 'user__first_name']
    ordering_fields = ['id', 'membership_id', 'joined_at']
    ordering = ['membership_id']


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filterset_fields = ['name']
    search_fields = ['name', 'email', 'bio']
    ordering_fields = ['id', 'name']
    ordering = ['name']


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.prefetch_related('authors').all()
    serializer_class = BookSerializer
    filterset_fields = ['genre', 'authors']
    search_fields = ['title', 'isbn', 'authors__name']
    ordering_fields = ['id', 'title', 'total_copies', 'published_year']
    ordering = ['title']


class BorrowRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.select_related(
        'member', 'member__user', 'book'
    ).all()
    serializer_class = BorrowRecordSerializer
    filterset_fields = {
        'book': ['exact'],
        'member': ['exact'],
        'borrow_date': ['exact', 'gte', 'lte'],
        'due_date': ['exact', 'gte', 'lte'],
        'returned_at': ['exact', 'isnull'],
    }
    search_fields = [
        'book__title', 'member__membership_id', 'member__user__username',
    ]
    ordering_fields = ['id', 'borrow_date', 'due_date', 'created_at']
    ordering = ['-borrow_date', '-id']
