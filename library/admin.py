"""All four models are registered with useful Django Admin customization."""
from django.contrib import admin

from .models import Author, Book, BorrowRecord, MemberProfile


class BorrowRecordInline(admin.TabularInline):
    model = BorrowRecord
    extra = 0
    fields = ['member', 'borrow_date', 'due_date', 'returned_at']


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['membership_id', 'user', 'phone', 'joined_at']
    search_fields = ['membership_id', 'user__username', 'user__email']
    list_filter = ['joined_at']
    ordering = ['membership_id']
    readonly_fields = ['joined_at']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']
    search_fields = ['name', 'email']
    ordering = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'genre', 'total_copies', 'available_copies']
    search_fields = ['title', 'isbn', 'authors__name']
    list_filter = ['genre']
    ordering = ['title']
    readonly_fields = ['available_copies']
    filter_horizontal = ['authors']
    inlines = [BorrowRecordInline]


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = [
        'member', 'book', 'borrow_date', 'due_date', 'returned_at',
    ]
    search_fields = ['member__membership_id', 'book__title']
    list_filter = ['borrow_date', 'due_date', 'returned_at']
    ordering = ['-borrow_date']
    readonly_fields = ['created_at']
