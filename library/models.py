"""Four custom models; Django's built-in User is reused for accounts."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .validators import validate_isbn13, validate_membership_id


class MemberProfile(models.Model):
    """OneToOne: one login account has at most one library membership."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='member_profile',
    )
    membership_id = models.CharField(
        max_length=8, unique=True, validators=[validate_membership_id]
    )
    phone = models.CharField(max_length=20, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['membership_id']
        verbose_name = 'Member profile'

    def __str__(self):
        return f'{self.membership_id} ({self.user.username})'

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Author(models.Model):
    """An author may have multiple books; one book may have many authors."""

    name = models.CharField(max_length=120, unique=True)
    email = models.EmailField(blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.name:
            duplicate = Author.objects.filter(name__iexact=self.name.strip())
            if self.pk:
                duplicate = duplicate.exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError({'name': 'An author with this name already exists.'})

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.full_clean()
        return super().save(*args, **kwargs)


class Book(models.Model):
    """ManyToMany authors; available copies are computed from active loans."""

    class Genre(models.TextChoices):
        PROGRAMMING = 'programming', 'Programming'
        FICTION = 'fiction', 'Fiction'
        SCIENCE = 'science', 'Science'
        OTHER = 'other', 'Other'

    title = models.CharField(max_length=200)
    isbn = models.CharField(
        max_length=13, unique=True, validators=[validate_isbn13]
    )
    authors = models.ManyToManyField(Author, related_name='books')
    genre = models.CharField(
        max_length=20, choices=Genre.choices, default=Genre.OTHER
    )
    total_copies = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    published_year = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def active_loan_count(self):
        if not self.pk:
            return 0
        return self.loans.filter(returned_at__isnull=True).count()

    @property
    def available_copies(self):
        return max(self.total_copies - self.active_loan_count, 0)

    def clean(self):
        super().clean()
        if self.pk and self.total_copies is not None:
            if self.total_copies < self.active_loan_count:
                raise ValidationError({
                    'total_copies': 'Copies cannot be fewer than active loans.'
                })
        if self.published_year and self.published_year > timezone.localdate().year:
            raise ValidationError({
                'published_year': 'Published year cannot be in the future.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class BorrowRecord(models.Model):
    """ForeignKeys to Book and MemberProfile represent a library loan."""

    member = models.ForeignKey(
        MemberProfile, on_delete=models.CASCADE, related_name='loans'
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='loans'
    )
    borrow_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    returned_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-borrow_date', '-id']

    def __str__(self):
        return f'{self.member.membership_id} borrowed {self.book.title}'

    def clean(self):
        super().clean()
        errors = {}
        today = timezone.localdate()
        if self.borrow_date and self.borrow_date > today:
            errors['borrow_date'] = 'Borrow date cannot be in the future.'
        if self.borrow_date and self.due_date and self.due_date < self.borrow_date:
            errors['due_date'] = 'Due date cannot be before borrow date.'
        if self.returned_at:
            if self.borrow_date and self.returned_at < self.borrow_date:
                errors['returned_at'] = 'Return date cannot be before borrow date.'
            if self.returned_at > today:
                errors['returned_at'] = 'Return date cannot be in the future.'

        if self.member_id and self.book_id and self.returned_at is None:
            active = BorrowRecord.objects.filter(
                book_id=self.book_id, returned_at__isnull=True,
            )
            if self.pk:
                active = active.exclude(pk=self.pk)
            if active.filter(member_id=self.member_id).exists():
                errors['book'] = 'This member already has an active loan for this book.'
            elif not errors:
                total_copies = Book.objects.filter(pk=self.book_id).values_list(
                    'total_copies', flat=True
                ).first()
                if total_copies is not None and active.count() >= total_copies:
                    errors['book'] = 'No copies available for borrowing.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
