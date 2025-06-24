from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging, bcrypt
from verify_jwt import token_required

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

emp = Blueprint('employee', __name__)


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


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
    hashed_pw = hash_password(nic)  # Use NIC as initial password

    if not first_name or not email or not nic:
        return jsonify({'error': 'Name, email and NIC are required'}), 400

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

        cursor.execute("INSERT INTO login (email, hashed_password, permission) VALUES (%s, %s, %s)", (email, hashed_pw, permission))
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

    hashed_pw = hash_password(password) #if password else None

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


@emp.route('/employees/remove/<int:emp_id>', methods=['PUT'])
@token_required
def update_permission(decoded ,emp_id):
    logging.info(f"PUT request to update permission for emp_id: {emp_id}")
    data = request.get_json()
    permission = data.get('permission')

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
