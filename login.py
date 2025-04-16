from flask import Blueprint, request, jsonify
from flask_cors import CORS
from config import get_db_connection
import hashlib, jwt, pymysql, datetime, os
from dotenv import load_dotenv

auth = Blueprint('login',__name__)
load_dotenv()


SECRET_KEY= os.getenv('jwt_secret_key')


def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()

def generate_jwt(user_id, email):

    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.now(datetime.timezone.utc)+ datetime.timedelta(hours=1) 
    }, SECRET_KEY, algorithm='HS256')

    return token


@auth.route('/login', methods=['POST'])
def login():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor()
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    hashed_password = hash_password(password)

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        cursor.execute("SELECT * FROM login WHERE email = %s AND hashed_password = %s", (email, hashed_password))
        user = cursor.fetchone()

        if user:
            user_data = {
                "id": user[0],
                "email": user[1],
            }
            token = generate_jwt(user[0], user[1]) 
            cursor.execute("SELECT * FROM login WHERE email = %s AND hashed_password = %s", (email, hashed_password))

            return jsonify({"message": "Login successful", "user": user_data, "token": token}), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401

    except pymysql.MySQLError as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    finally:
        cursor.close()
        connection.close()

@auth.route('/register', methods=['POST'])
def register():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor()
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    hashed_password = hash_password(password)

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        cursor.execute("INSERT INTO login (email, hashed_password) VALUES (%s, %s)", (email, hashed_password))
        connection.commit()
        return jsonify({"message": "Registration successful"}), 201

    except pymysql.IntegrityError: 
        return jsonify({"error": "Email already registered"}), 400

    except pymysql.MySQLError as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    finally:
        cursor.close()
        connection.close()


#################################################################################################

# def decode_token(token):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
#         return payload
#     except jwt.ExpiredSignatureError:
#         return 'Signature expired. Please log in again.'
#     except jwt.InvalidTokenError:
#         return 'Invalid token. Please log in again.'

# @app.route('/protected', methods=['GET'])
# def protected():
    
#     token = request.headers.get('Authorization')

#     if not token:
#         return jsonify({"error": "Token is missing"}), 401

#     token = token.replace('Bearer ', '')

#     payload = decode_token(token)

#     if isinstance(payload, str):
#         return jsonify({"error": payload}), 401

#     user_id = payload['sub']
#     email = payload['email']

#     return jsonify({"message": "Protected resource accessed", "user_id": user_id, "email": email}), 200

###########################################################################################

