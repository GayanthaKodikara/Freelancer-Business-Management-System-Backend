from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging, bcrypt
from verify_jwt import token_required
from datetime import datetime
import re
import jwt
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv('jwt_secret_key')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

emp = Blueprint('employee', __name__)


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

#get all employees
@emp.route('/employees', methods=['GET'])
@token_required
def get_employees(decoded):
    logging.info("GET request received for /employees")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT employee.*, login.permission
            FROM employee INNER JOIN login ON employee.emp_id = login.emp_id
        """)
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} employees from the database")

        users = []
        for row in results:
            users.append({
                'emp_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'email': row[9],
                'address': row[3],
                'nic': row[4],
                'birth_day': row[5],
                'role': row[6],
                'workshop_name': row[7],
                'design_category': row[8],
                'permission': row[10]
            })
        return jsonify(users)

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#add employee
@emp.route('/employees', methods=['POST'])
@token_required
def add_employee(decoded):
    logging.info("POST request received for /employees")
    data = request.get_json()
    logging.info(f"Received JSON data: {data}")
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    address = data.get('address')
    nic = data.get('nic')
    birth_day = data.get('birth_day')
    role = data.get('role')
    workshop_name = data.get('workshop_name')
    design_category = data.get('design_category')
    permission = data.get('permission')
    hashed_pw = hash_password(nic)  

    if not first_name or not email or not nic:
        return jsonify({'error': 'Name, email and NIC are required'}), 400
    
    # ===== Name Validation =====
    name_pattern = r'^[A-Za-z\s\-]+$'
    if not re.match(name_pattern, first_name):
        return jsonify({'error': 'First name must contain only letters, spaces, or hyphens'}), 400
    if last_name and not re.match(name_pattern, last_name):
        return jsonify({'error': 'Last name must contain only letters, spaces, or hyphens'}), 400

    # ===== Email Validation =====
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
    if not re.match(email_pattern, email):
        return jsonify({'error': 'Invalid email format'}), 400

    # ===== NIC Validation =====
    nic_pattern_12 = r'^\d{12}$'
    nic_pattern_9v = r'^\d{9}V$'
    if not (re.match(nic_pattern_12, nic) or re.match(nic_pattern_9v, nic)):
        return jsonify({'error': 'NIC must be 12 digits or 9 digits followed by capital "V"'}), 400

    # ===== Birthday Validation =====
    try:
        birth_date = datetime.strptime(birth_day, '%Y-%m-%d')
        age = (datetime.now() - birth_date).days / 365.25
        if age < 18:
            return jsonify({'error': 'Employee must be at least 18 years old'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid birth_day format. Use YYYY-MM-DD'}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO employee (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category))
        connection.commit()
        
        cursor.execute("SELECT emp_id FROM employee WHERE email = %s AND nic = %s", (email, nic))
        connection.commit()

        result = cursor.fetchone() 
    
        emp_id = None
        if result:
            emp_id = result[0]

        cursor.execute(
            "INSERT INTO login (emp_id, email, hashed_password, permission) VALUES (%s, %s, %s, %s)",
            (emp_id, email, hashed_pw, permission) 
        )
        connection.commit()

        return jsonify({'message': 'Employee added successfully'}), 201

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#get single employee
@emp.route('/employees/<int:emp_id>', methods=['GET'])
@token_required
def get_employee(decoded, emp_id):
    logging.info(f"GET request for /employees/{emp_id}")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM employee WHERE emp_id = %s", (emp_id,))
        result = cursor.fetchone()

        if result:
            employee = {
                'emp_id': result[0], 'first_name': result[1], 'last_name': result[2], 'email': result[9],
                'address': result[3], 'nic': result[4], 'birth_day': str(result[5]), 'role': result[6],
                'workshop_name': result[7], 'design_category': result[8]
            }
            return jsonify(employee), 200
        else:
            return jsonify({'error': 'Employee not found'}), 404

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# employee update
@emp.route('/employees/<int:emp_id>', methods=['PUT'])
@token_required
def update_employee(decoded, emp_id):
    logging.info(f"PUT request for /employees/{emp_id}")
    data = request.get_json()
    logging.info(f"Received JSON: {data}")
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    address = data.get('address')
    nic = data.get('nic')
    birth_day = data.get('birth_day')
    role = data.get('role')
    workshop_name = data.get('workshop_name')
    design_category = data.get('design_category')
    password = data.get('password')

    hashed_pw = None
    if password:
        hashed_pw = hash_password(password)

    # ===== Required Field Checks =====
    if not first_name or not email or not nic:
        return jsonify({'error': 'First name, email, and NIC are required'}), 400
    
    # ===== Name Validation =====
    name_pattern = r'^[A-Za-z\s\-]+$'
    if not re.match(name_pattern, first_name):
        return jsonify({'error': 'First name must contain only letters, spaces, or hyphens'}), 400
    if last_name and not re.match(name_pattern, last_name):
        return jsonify({'error': 'Last name must contain only letters, spaces, or hyphens'}), 400

    # ===== Email Validation =====
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
    if not re.match(email_pattern, email):
        return jsonify({'error': 'Invalid email format'}), 400

    # ===== NIC Validation =====
    nic_pattern_12 = r'^\d{12}$'
    nic_pattern_9v = r'^\d{9}V$'
    if not (re.match(nic_pattern_12, nic) or re.match(nic_pattern_9v, nic)):
        return jsonify({'error': 'NIC must be 12 digits or 9 digits followed by capital "V"'}), 400

    # ===== Birthday Validation =====
    try:
        birth_date = datetime.strptime(birth_day, '%Y-%m-%d')
        age = (datetime.now() - birth_date).days / 365.25
        if age < 18:
            return jsonify({'error': 'Employee must be at least 18 years old'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid birth_day format. Use YYYY-MM-DD'}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE employee SET first_name = %s, last_name = %s, email = %s, address = %s, nic = %s,
            birth_day = %s, role = %s, workshop_name = %s, design_category = %s WHERE emp_id = %s
        """, (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category, emp_id))
        connection.commit()

        if hashed_pw:
            cursor.execute("UPDATE login SET email = %s, hashed_password = %s WHERE emp_id = %s", (email, hashed_pw, emp_id))
        else:
            cursor.execute("UPDATE login SET email = %s WHERE emp_id = %s", (email, emp_id))
        connection.commit()

        return jsonify({'message': 'Employee updated successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#remove employee permission from system
@emp.route('/employees/remove/<int:emp_id>', methods=['PUT'])
@token_required
def update_permission(decoded ,emp_id):

    token = request.headers.get('Authorization')
    if not token:
        logging.warning("Missing token in request headers")
        return None, jsonify({'error': 'Missing token'}), 401

    if token.startswith("Bearer "):
        token = token[7:]  

    decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = decoded['user_id']

    logging.info(f"PUT request to update permission for emp_id: {emp_id}")
    data = request.get_json()
    permission = data.get('permission')

    # Prevent self-modification
    if user_id == emp_id:
        logging.warning(f"User with emp_id {emp_id} attempted to modify their own permission.")
        return jsonify({'error': 'You cannot modify your own account permissions'}), 403

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE login SET permission = %s WHERE email IN (SELECT email FROM employee WHERE emp_id = %s)", (permission, emp_id))
        connection.commit()

        return jsonify({'message': 'Employee permission updated successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
