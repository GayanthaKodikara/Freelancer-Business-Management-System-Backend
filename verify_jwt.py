from flask import request, jsonify, Blueprint
import jwt
import logging
from config import get_db_connection
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()
SECRET_KEY = os.getenv('jwt_secret_key')

tok = Blueprint('verify_jwt_token', __name__)

@tok.route('/verify-token', methods=['GET'])
def verify_jwt_token():
    token = request.headers.get('Authorization')
    if not token:
        logging.warning("Missing token in request headers")
        return None, jsonify({'error': 'Missing token'}), 401

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = decoded['user_id']
        email = decoded['email']
        logging.info(f"Token decoded for user ID: {user_id} and email: {email}")

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT jwt_token FROM login WHERE emp_id = %s AND email = %s", (user_id, email))
        result = cursor.fetchone()

        if result and result[0] == token:
            logging.info(f"Token is valid for user ID: {user_id}")
            return decoded, None, None
        else:
            logging.warning(f"Invalid or expired token for user ID: {user_id}")
            return None, jsonify({'error': 'Invalid or expired token'}), 403

    except jwt.ExpiredSignatureError:
        logging.warning("Token expired")
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        logging.warning("Invalid token")
        return jsonify({'error': 'Invalid token'}), 403
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# def check_path_permission(decoded, request_path):
#     user_role = decoded.get('role')  # Assuming the role is included in the JWT
#     connection = get_db_connection()
#     cursor = connection.cursor()
    
#     try:
#         cursor.execute("SELECT COUNT(*) FROM path_permission WHERE role = %s AND path = %s", (user_role, request_path))
#         result = cursor.fetchone()
        
#         if result and result[0] > 0:
#             return True
#         else:
#             logging.warning(f"Access denied for role: {user_role} on path: {request_path}")
#             return False
#     finally:
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()

def check_path_permission(decoded, request_path):
    user_role = decoded.get('role')  
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT path FROM path_permission WHERE role = %s", (user_role,))
        allowed_paths = [row[0] for row in cursor.fetchall()]

        # Check if any of the allowed paths is a prefix of the request_path
        for allowed_path in allowed_paths:
            # Ensure allowed_path ends with a '/' if it's a directory-like path
            # and request_path is a sub-path
            if allowed_path.endswith('/') and request_path.startswith(allowed_path):
                return True
            # For exact matches on non-dynamic paths
            elif request_path == allowed_path:
                return True
        
        logging.warning(f"Access denied for role: {user_role} on path: {request_path}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        decoded, error_response, status_code = verify_jwt_token()
        if error_response:
            return error_response, status_code
        
        request_path = request.path
        if not check_path_permission(decoded, request_path):
            return jsonify({'error': 'Access denied'}), 403
        
        return f(decoded, *args, **kwargs)
    return decorated
