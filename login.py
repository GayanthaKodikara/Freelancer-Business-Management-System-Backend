from flask import Blueprint, request, jsonify
from config import get_db_connection
import jwt, datetime, os, logging, bcrypt
from dotenv import load_dotenv


auth = Blueprint('login', __name__)
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SECRET_KEY = os.getenv('jwt_secret_key')

def generate_jwt(user_id, email, role):
    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=150)
    }, SECRET_KEY, algorithm='HS256')
    logging.info(f"JWT generated for user ID: {user_id} and email: {email}")
    return token

# user login
@auth.route('/login', methods=['POST'])
def login():

    logging.info("POST request received for /login")
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        logging.warning("Email and password are required for login")
        return jsonify({"error": "Email and password are required"}), 400
        
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Database connection failed")
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()
        cursor.execute("SELECT login.emp_id, login.email, login.hashed_password, login.permission, employee.role FROM login INNER JOIN employee ON login.emp_id = employee.emp_id WHERE login.email = %s", (email,))
        user = cursor.fetchone()

        if user:
            emp_id, email, db_hashed_password, permission, role = user
            logging.info(f"User  found: {email} with permission: {permission}")
            
            if bcrypt.checkpw(password.encode('utf-8'), db_hashed_password.encode('utf-8')):
                if permission == "TRUE":
                    token = generate_jwt(emp_id, email, role)

                    # Store token in DB
                    cursor.execute("UPDATE login SET jwt_token = %s WHERE emp_id = %s", (token, emp_id))
                    connection.commit()
                    logging.info(f"Token stored for user ID: {emp_id}")
                    logging.info(f"Successfully Login for user ID: {emp_id}")

                    return jsonify({
                        "message": "Login successful",
                        "user": {"emp_id": emp_id, "email": email, "permission": permission, "role":role},
                        "token": token
                    }), 200
                    
                else:
                    logging.warning(f"Permission denied for user ID: {emp_id} - Account not active")
                    return jsonify({"error": "Permission denied. Your account is not active."}), 403
            else:
                logging.warning(f"Invalid password attempt for email: {email}")
                return jsonify({"error": "Invalid email or password"}), 401
        else:
            logging.warning(f"Invalid login attempt for email: {email} - User not found")
            return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




