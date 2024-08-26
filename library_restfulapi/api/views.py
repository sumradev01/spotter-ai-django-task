# api/views.py

from rest_framework import viewsets, permissions, filters
from .models import Book, Author, Favourite
from .serializers import BookSerializer, AuthorSerializer, FavouriteSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.decorators import api_view,action, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import viewsets, status,permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


import pandas as pd
from threading import Lock
import os




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
            permission_classes = [permissions.IsAuthenticated]  # Require authentication
        else:
            permission_classes = [permissions.AllowAny]  # read-only access for any user
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

        if Favourite.objects.filter(user=user).count() >= 20:
            return Response(
                {"detail": "You cannot have more than 20 favorites."},
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


# Global variables for caching
# df_cache = None
# tfidf_matrix_cache = None
# vectorizer_cache = None

# class FavouriteViewSet(viewsets.ViewSet):
    
#     permission_classes = [IsAuthenticated]
                     
#     df = None
#     tfidf_matrix = None
#     vectorizer = None
#     book_id_to_index = {}
#     data_loaded = False
#     load_lock = Lock()

#     @classmethod
#     def load_data(cls):
        
#         """
#         Load the Parquet file
#         """
#         with cls.load_lock:
#             if not cls.data_loaded:
#                 # print("Loading data and initializing TF-IDF matrix...")
#                 current_dir = os.path.dirname(os.path.abspath(__file__))
#                 parquet_path = os.path.join(current_dir, '..', 'output.parquet')
                
#                 # specific columns 
#                 cls.df = pd.read_parquet(parquet_path, columns=['book_id', 'book_title', 'description'])
                
#                    # 'book_id' is a string
                   
#                 cls.df['book_id'] = cls.df['book_id'].astype(str).str.strip()
                
#                 # combined_text
                   
#                 cls.df['combined_text'] = cls.df['book_title'].fillna('') + ' ' + cls.df['description'].fillna('')
                
#                 # Initialize and fit the TF-IDF vectorizer
#                 cls.vectorizer = TfidfVectorizer()
#                 cls.tfidf_matrix = cls.vectorizer.fit_transform(cls.df['combined_text'].astype(str))
                
#                 # mapping book_id to DataFrame index for quick lookup
                
#                 cls.book_id_to_index = {book_id: idx for idx, book_id in cls.df['book_id'].items()}
                
#                 cls.data_loaded = True
#                 print("Data loaded and TF-IDF matrix initialized.")

#     def create(self, request, *args, **kwargs):
#         user = request.user

#         # Check if the user already has 20 favorites
#         current_favorites_count = Favourite.objects.filter(user=user).count()
#         if current_favorites_count >= 20:
#             return Response({"detail": "You cannot have more than 20 favorites."}, status=status.HTTP_400_BAD_REQUEST)

#         # Load data if not already loaded
#         if not self.__class__.data_loaded:
#             self.__class__.load_data()

#         # Extract 'book_id' from the request, ensuring it is provided
#         book_id = request.data.get('book_id')
#         if not book_id:
#             return Response({"detail": "Book ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
#         book_id = book_id.strip()

#         # Lookup the book index using the precomputed dictionary
        
#         book_idx = self.__class__.book_id_to_index.get(book_id)
#         if book_idx is None:
#             return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

#         # Retrieve selected book details
#         book = self.__class__.df.iloc[book_idx]
#         print(f"Selected Book: {book['book_title']}")

#         # Compute cosine similarity 
#         # Since tfidf_matrix is a sparse matrix, this operation is efficient
        
#         book_vector = self.__class__.tfidf_matrix[book_idx]
#         similarity_scores = cosine_similarity(book_vector, self.__class__.tfidf_matrix).flatten()

#         # Exclude the selected book
        
#         similarity_scores[book_idx] = -1

#         # Get the indices of the top N recommended books
#         num_recommendations = 5
#         top_indices = similarity_scores.argsort()[-num_recommendations:][::-1]

#            # Retrieve recommended books from the DataFrame
#         recommended_books = self.__class__.df.iloc[top_indices]

        
#         response_data = {
#             "favorite": {
#                 "book_id": book['book_id'],
#                 "book_title": book['book_title']
#             },
#             "recommended_books": [
#                 {"book_id": row.book_id, "book_title": row.book_title}
#                 for _, row in recommended_books.iterrows()
#             ]
#         }

#         return Response(response_data, status=status.HTTP_201_CREATED)
    
    
#     def list(self, request, *args, **kwargs):
#         user = request.user
#         # Fetch data from the database
#         favorites = Favourite.objects.filter(user=user)
#         serializer = FavouriteSerializer(favorites, many=True)

#         return Response({"favorites": serializer.data}, status=status.HTTP_200_OK)
    
    