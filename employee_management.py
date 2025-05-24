from flask import Blueprint, jsonify, request
from config import get_db_connection
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

emp = Blueprint('employee', __name__)


def hashed_password(nic):
    return hashlib.sha512(nic.encode()).hexdigest()


@emp.route('/employees', methods=['GET'])
def get_employees():
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
        logging.info("Successfully processed employee data for response")
        return jsonify(users)

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing GET request for /employees: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()
        logging.info("Database connection closed after GET /employees")

@emp.route('/employees', methods=['POST'])
def add_employee():
    logging.info("POST request received for /employees")
    connection = None
    cursor = None
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
    hashed_nic = hashed_password(nic)
    permission = data.get('permission')
    logging.info(f"Hashed NIC for {nic}")

    if not first_name or not email or not nic:
        logging.warning("Required fields (first_name, email, nic) are missing in POST request")
        return jsonify({'error': 'Name, email and NIC are required'}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO employee (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category))
        connection.commit()
        logging.info(f"Employee with email '{email}' added to the employee table")

        cursor.execute("INSERT INTO login (email, hashed_password, permission) VALUES (%s, %s, %s)", (email, hashed_nic, permission))
        connection.commit()
        logging.info(f"Login details added for employee with email '{email}'")

        return jsonify({'message': 'Employee added successfully'}), 201

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing POST request for /employees: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after POST /employees")


@emp.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    logging.info(f"GET request received for /employees/{emp_id}")
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
            logging.info(f"Found employee with emp_id {emp_id}")
            return jsonify(employee), 200
        else:
            logging.warning(f"Employee with emp_id {emp_id} not found")
            return jsonify({'error': 'Employee not found'}), 404

    except Exception as e:
        logging.error(f"Error processing GET request for /employees/{emp_id}: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after GET /employees/{emp_id}")


@emp.route('/employees/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    logging.info(f"PUT request received for /employees/{emp_id}")
    connection = None
    cursor = None
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
    password = data.get('password')

    hashed_password_value = None
    if password:
        hashed_password_value = hashed_password(password)
        logging.info(f"Hashed password for employee with emp_id {emp_id}")

    if not data:
        logging.warning(f"No data provided in PUT request for /employees/{emp_id}")
        return jsonify({'error': 'No data provided'}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Update employee details
        cursor.execute(
            "UPDATE employee SET first_name = %s, last_name = %s, email = %s, address = %s, nic = %s, birth_day = %s, role = %s, workshop_name = %s, design_category = %s WHERE emp_id = %s",
            (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category, emp_id)
        )
        connection.commit()
        logging.info(f"Employee with emp_id {emp_id} updated successfully in employee table")

        # Update login details (conditionally update password if provided)
        if hashed_password_value:
            cursor.execute("UPDATE login SET email = %s, hashed_password = %s WHERE emp_id = %s", (email, hashed_password_value, emp_id))
            logging.info(f"Login details updated with new password for employee with email '{email}'")
        else:
            cursor.execute("UPDATE login SET email = %s WHERE emp_id = %s", (email, emp_id))
            logging.info(f"Login email updated for employee with email '{email}'")
        connection.commit()

        return jsonify({'message': 'Employee updated successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing PUT request for /employees/{emp_id}: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after PUT /employees/{emp_id}")

@emp.route('/employees/remove/<int:emp_id>', methods=['PUT'])
def update_permission(emp_id):
    logging.info(f"PUT request received for /employees/remove/{emp_id}")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received JSON data: {data}")
    if not data:
        logging.warning(f"No data provided in PUT request for /employees/remove/{emp_id}")
        return jsonify({'error': 'No data provided'}), 400

    permission = data.get('permission')
    logging.info(f"Attempting to update permission for emp_id {emp_id} to '{permission}'")

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE login SET permission = %s WHERE email IN (SELECT email FROM employee WHERE emp_id = %s)", (permission, emp_id))
        connection.commit()
        logging.info(f"Employee permission for emp_id {emp_id} updated to '{permission}' successfully")
        return jsonify({'message': 'Employee permission Removed successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing PUT request for /employees/remove/{emp_id}: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after PUT /employees/remove/{emp_id}")