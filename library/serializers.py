"""DRF serializers convert model instances to/from JSON and validate input."""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Author, Book, BorrowRecord, MemberProfile

User = get_user_model()


class MemberProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = MemberProfile
        fields = [
            'id', 'user', 'username', 'full_name', 'membership_id',
            'phone', 'joined_at',
        ]
        read_only_fields = ['id', 'username', 'full_name', 'joined_at']

    def validate_membership_id(self, value):
        return value.strip().upper()


class AuthorSerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(source='books.count', read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'bio', 'book_count']
        read_only_fields = ['id', 'book_count']

    def validate_name(self, value):
        name = value.strip()
        possible_duplicates = Author.objects.filter(name__iexact=name)
        if self.instance:
            possible_duplicates = possible_duplicates.exclude(pk=self.instance.pk)
        if possible_duplicates.exists():
            raise serializers.ValidationError('An author with this name already exists.')
        return name


class BookSerializer(serializers.ModelSerializer):
    # Nested object is read-only; IDs are write-only for creating/updating books.
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        source='authors', many=True, queryset=Author.objects.all(),
        write_only=True, allow_empty=False,
    )
    available_copies = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'genre', 'published_year', 'total_copies',
            'available_copies', 'authors', 'author_ids',
        ]
        read_only_fields = ['id', 'available_copies', 'authors']

    def validate_published_year(self, value):
        if value is not None and value > timezone.localdate().year:
            raise serializers.ValidationError('Published year cannot be in the future.')
        return value

    def validate(self, data):
        if self.instance:
            proposed_total = data.get('total_copies', self.instance.total_copies)
            if proposed_total < self.instance.active_loan_count:
                raise serializers.ValidationError({
                    'total_copies': 'Copies cannot be fewer than active loans.'
                })
        return data

    def create(self, validated_data):
        authors = validated_data.pop('authors')
        book = Book.objects.create(**validated_data)
        book.authors.set(authors)
        return book

    def update(self, instance, validated_data):
        authors = validated_data.pop('authors', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if authors is not None:
            instance.authors.set(authors)
        return instance


class BorrowRecordSerializer(serializers.ModelSerializer):
    member_detail = MemberProfileSerializer(source='member', read_only=True)
    book_detail = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = BorrowRecord
        fields = [
            'id', 'member', 'member_detail', 'book', 'book_detail',
            'borrow_date', 'due_date', 'returned_at', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'member_detail', 'book_detail', 'status', 'created_at']

    def get_book_detail(self, instance):
        return {'id': instance.book_id, 'title': instance.book.title}

    def get_status(self, instance):
        if instance.returned_at is not None:
            return 'returned'
        if instance.due_date < timezone.localdate():
            return 'overdue'
        return 'borrowed'

    def validate(self, data):
        current = self.instance
        member = data.get('member', current.member if current else None)
        book = data.get('book', current.book if current else None)
        borrow_date = data.get(
            'borrow_date', current.borrow_date if current else timezone.localdate()
        )
        due_date = data.get('due_date', current.due_date if current else None)
        returned_at = data.get('returned_at', current.returned_at if current else None)
        errors = {}
        today = timezone.localdate()

        if borrow_date and borrow_date > today:
            errors['borrow_date'] = 'Borrow date cannot be in the future.'
        if borrow_date and due_date and due_date < borrow_date:
            errors['due_date'] = 'Due date cannot be before borrow date.'
        if returned_at:
            if borrow_date and returned_at < borrow_date:
                errors['returned_at'] = 'Return date cannot be before borrow date.'
            if returned_at > today:
                errors['returned_at'] = 'Return date cannot be in the future.'

        if member and book and returned_at is None:
            active = BorrowRecord.objects.filter(
                book=book, returned_at__isnull=True,
            )
            if current:
                active = active.exclude(pk=current.pk)
            if active.filter(member=member).exists():
                errors['book'] = 'This member already has an active loan for this book.'
            elif not errors and active.count() >= book.total_copies:
                errors['book'] = 'No copies available for borrowing.'
        if errors:
            raise serializers.ValidationError(errors)
        return data
