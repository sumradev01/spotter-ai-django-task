# api/views.py

from rest_framework import viewsets, permissions, filters
from .models import Book, Author, Favourite
from .serializers import BookSerializer, AuthorSerializer, FavouriteSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import viewsets, status,permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rest_framework.decorators import api_view, permission_classes



@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username is already taken'}, status=status.HTTP_409_CONFLICT)
    user = User.objects.create_user(username=username, password=password)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    else:
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    
    def get_permissions(self):
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]  # Require authentication for these actions
        else:
            permission_classes = [permissions.AllowAny]  # Allow read-only access for any user
        return [permission() for permission in permission_classes]




class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['book_title', 'book_author__author_name']  # Fields to search in

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class FavouriteViewSet(viewsets.ModelViewSet):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        book_id = request.data.get('book')
        
        # print("testing!!!")
        # print(book_id)

        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the favorite already there
        
        if Favourite.objects.filter(user=user, book=book).exists():
            return Response(
                {"detail": "This book is already in your favorites."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        # If  not exist, then create favorite
        
        favourite = Favourite.objects.create(user=user, book=book)

        # Get recommended books
        
        favorite_books = Book.objects.filter(favourite__user=user)
        recommendations = self.get_recommendations(favorite_books)

        # Serialize the current favorite
        favorite_data = FavouriteSerializer(favourite).data

        # response data
        response_data = {
            "favorite": favorite_data,
            "recommended_books": [{"book_id": book.book_id,"book_title": book.book_title} for book in recommendations]
        }

        # Return the response
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        
        # users only see their own favorites
        return self.queryset.filter(user=self.request.user)

    def get_recommendations(self, favorite_books, num_recommendations=5):
        combined_texts = [f"{book.book_title} {book.description}" for book in Book.objects.all()]

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(combined_texts)

        # Store recommendations with their scores
        similarity_scores = {}

        for book in favorite_books:
            book_index = list(Book.objects.all()).index(book)
            cosine_similarities = cosine_similarity(tfidf_matrix[book_index:book_index+1], tfidf_matrix).flatten()

            # accumulate their similarity scores
            
            for idx, score in enumerate(cosine_similarities):
                if Book.objects.all()[idx] not in favorite_books:  # Exclude already in favorites
                    if idx in similarity_scores:
                        similarity_scores[idx] += score
                    else:
                        similarity_scores[idx] = score

        # similarity score in descending 
        sorted_books = sorted(similarity_scores.items(), key=lambda item: item[1], reverse=True)
        print("sorted books!!!")
        print(sorted_books)
        
        # Fetch  recommended  based on score
        
        recommended_books = [Book.objects.all()[int(idx)] for idx, score in sorted_books[:num_recommendations]]
        
        return recommended_books
