from flask import Blueprint, request, jsonify
from config import get_db_connection
import hashlib, jwt, pymysql, datetime, os, logging
from dotenv import load_dotenv

auth = Blueprint('login', __name__)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SECRET_KEY = os.getenv('jwt_secret_key')


def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()


def generate_jwt(user_id, email):
    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }, SECRET_KEY, algorithm='HS256')
    logging.info(f"JWT generated for user ID: {user_id} and email: {email}")
    return token

# Logging Page
@auth.route('/login', methods=['POST'])
def login():
    logging.info("POST request received for /login")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received JSON data for login")
    email = data.get("email")
    password = data.get("password")
    hashed_password = hash_password(password)
    logging.info(f"Hashed password for email: {email}")

    if not email or not password:
        logging.warning("Email and password are required for login")
        return jsonify({"error": "Email and password are required"}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Database connection failed during login")
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM login WHERE email = %s AND hashed_password = %s", (email, hashed_password))
        user = cursor.fetchone()

        if user:
            user_permission = user[3]

            if user_permission == "TRUE": 
                user_data = {
                    "emp_id": user[0],
                    "email": user[1],
                    "permission": user_permission
                }
                token = generate_jwt(user[0], user[1])
                logging.info(f"Login successful for user with email: {email}")
                return jsonify({"message": "Login successful", "user": user_data, "token": token}), 200
            else:
                logging.warning(f"Login denied for user with email: {email} due to insufficient permissions.")
                return jsonify({"error": "Permission denied. Your account is not active."}), 403 # 403 Forbidden
        else:
            logging.warning(f"Invalid login attempt for email: {email}")
            return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        logging.error(f"An unexpected error occurred during login: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after /login request")

@auth.route('/register', methods=['POST'])
def register():
    logging.info("POST request received for /register")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received JSON data for registration: {data}")
    email = data.get("email")
    password = data.get("password")
    hashed_password = hash_password(password)
    logging.info(f"Hashed password for registration of email: {email}")

    if not email or not password:
        logging.warning("Email and password are required for registration")
        return jsonify({"error": "Email and password are required"}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Database connection failed during registration")
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()
        cursor.execute("INSERT INTO login (email, hashed_password) VALUES (%s, %s)", (email, hashed_password))
        connection.commit()
        logging.info(f"Registration successful for email: {email}")
        return jsonify({"message": "Registration successful"}), 201

    except pymysql.IntegrityError:
        logging.warning(f"Registration failed: Email '{email}' already registered")
        return jsonify({"error": "Email already registered"}), 400

    except Exception as e:
        logging.error(f"An unexpected error occurred during registration: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after /register request")