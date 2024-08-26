# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet,FavouriteViewSet
from .views import BookViewSet, login, register

router = DefaultRouter()
router.register(r'books', BookViewSet),
router.register(r'authors', AuthorViewSet),
# router.register(r'favorites', FavouriteViewSet)
router.register(r'favorites', FavouriteViewSet)  # Specify the basename


urlpatterns = [
    path('', include(router.urls)),
    path('login/', login, name='login'),           # URL for login view
    path('register/', register, name='register'),  # URL for register view
]
