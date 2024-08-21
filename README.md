# Library Restful API

## Setup Instructions

1. **Create Virtual Environment**
   - Use the following command to create a virtual environment:
     ```
     virtualenv virtual_name
     ```

2. **Activate the Virtual Environment**
   - On Windows:
     ```
     virtual_name\Scripts\activate
     ```

3. **Move to the Project Directory**
   - Navigate to the project directory:
     ```
     cd library_restfulapi
     ```

4. **Install requirements.txt**
   - Install the required packages using the `requirements.txt` file:
     ```
     pip install -r requirements.txt
     ```

5. **Run the Server**
   - Start the Django development server using:
     ```
     python manage.py runserver
     ```

## API Usage

1. **Register a User**
   - Send a `POST` request to:
     ```
     http://127.0.0.1:8000/api/register/
     ```
   - Body (JSON):
     ```json
     {
       "username": "Username",
       "password": "password"
     }
     ```

2. **Create a Token**
   - Send a `POST` request to:
     ```
     http://127.0.0.1:8000/api/login/
     ```

3. **Use the Token**
   - Paste the created access token in the Bearer tab under the Auth tab to hit other endpoints like:
     - `http://127.0.0.1:8000/api/authors/`
     - `http://127.0.0.1:8000/api/books/`
     - `http://127.0.0.1:8000/api/favorites/`
