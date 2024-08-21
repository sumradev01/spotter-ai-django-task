# api/models.py

from django.db import models
from django.contrib.auth.models import User



class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    author_name = models.CharField(max_length=100)
    author_country = models.CharField(max_length=100)
    author_rating = models.FloatField()
    author_publication = models.CharField(max_length=100)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.author_name
    
class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    book_sku = models.CharField(max_length=50)
    book_title = models.CharField(max_length=200)
    book_author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    book_lang = models.CharField(max_length=50)
    book_reviews = models.IntegerField()
    book_edition = models.CharField(max_length=100)
    description = models.TextField(max_length=500)  # New description field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.book_title

class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)  # Ensure this references the 'Book' model correctly

    class Meta:
        unique_together = (('user', 'book'),)

