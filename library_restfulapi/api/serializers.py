# api/serializers.py

from rest_framework import serializers
from .models import Book, Author,Favourite



class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'  # Or list specific fields you want to include

    def create(self, validated_data):
        # Check if an author with the same name and country already exists
        author_name = validated_data.get('author_name')
        author_country = validated_data.get('author_country')

        if Author.objects.filter(author_name=author_name, author_country=author_country).exists():
            raise serializers.ValidationError("Author with this name and country already exists.")

        # If not, create the author
        return super().create(validated_data)
    

class BookSerializer(serializers.ModelSerializer):
    book_author_name = serializers.CharField(source='book_author.author_name', read_only=True)  # Display author name
    book_author = serializers.CharField(write_only=True)  # Accept author ID or name during creation

    class Meta:
        model = Book
        fields = '__all__'

    def validate_book_author(self, value):
        # Attempt to retrieve the author by ID or name
        if value.isdigit():
            author = Author.objects.filter(pk=value).first()
        else:
            author = Author.objects.filter(author_name=value).first()

        if not author:
            raise serializers.ValidationError("Author not found.")

        return author  # Return the Author instance

    def create(self, validated_data):
        validated_data['book_author'] = validated_data.pop('book_author')
        return super().create(validated_data)
    
    
    def create(self, validated_data):
        # Check if a book with the same title and author already exists
        book_title = validated_data.get('book_title')
        book_author = validated_data.get('book_author')

        if Book.objects.filter(book_title=book_title, book_author=book_author).exists():
            raise serializers.ValidationError("Book with this title and author already exists.")

        # If not, create the book
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'book_author' in validated_data:
            validated_data['book_author'] = validated_data.pop('book_author')
        return super().update(instance, validated_data)
    

class FavouriteSerializer(serializers.ModelSerializer):
     book_title = serializers.CharField(source='book.book_title', read_only=True)  # Display the book's title instead of ID

     class Meta:
        model = Favourite
        fields = ['id', 'book', 'book_title']  #  'book' (for input),'book_title' (for output)
        
    #  def get_book_table_id(self, obj):
    #     return obj.book.book_id