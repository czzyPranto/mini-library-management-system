"""RESTful endpoints using DRF's automatic router."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthorViewSet, BookViewSet, BorrowRecordViewSet, MemberProfileViewSet,
)

router = DefaultRouter()
router.register(r'members', MemberProfileViewSet, basename='member')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrow-records', BorrowRecordViewSet, basename='borrow-record')

urlpatterns = [path('', include(router.urls))]
