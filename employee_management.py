from flask import Blueprint, jsonify, request
from config import get_db_connection
import hashlib

emp = Blueprint('get_employees, add_employee' ,__name__)


def hashed_password(nic):
    return hashlib.sha512(nic.encode()).hexdigest()


@emp.route('/employees', methods=['GET'])
def get_employees():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM employee")
        results = cursor.fetchall()
        

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
            })
        return jsonify(users)

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        connection.close()



@emp.route('/employees', methods=['POST'])
def add_employee():
    connection = get_db_connection()
    cursor = connection.cursor()
    data = request.get_json()
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


    if not first_name or not email or not nic:
        return jsonify({'error': 'Name, email and NIC are required'}), 400
        
    try:
        cursor.execute("INSERT INTO employee (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
         (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category))
        connection.commit()
         
        cursor.execute("INSERT INTO login (email, hashed_password, permission) VALUES (%s, %s, %s)",(email,hashed_nic,permission))  
        connection.commit()

        return jsonify({'message': 'Employee added successfully'}), 201
    
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        connection.close()
     


@emp.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
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
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        connection.close()


@emp.route('/employees/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    data = request.get_json()
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

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "UPDATE employee SET first_name = %s, last_name = %s, email = %s, address = %s, nic = %s, birth_day = %s, role = %s, workshop_name = %s, design_category = %s, permission = %s WHERE emp_id = %s",
            (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category, emp_id, permission)
        )
        connection.commit()
        return jsonify({'message': 'Employee updated successfully'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        connection.close()


@emp.route('/employees/remove/<int:emp_id>', methods=['PUT'])
def update_permission(emp_id):

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    permission = data.get('permission')

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE login SET permission = %s WHERE emp_id = %s", (permission, emp_id))
        connection.commit()
        return jsonify({'message': 'Employee permission Removed successfully'}), 200

    except Exception as e:
         connection.rollback()
         return jsonify({'error': str(e)}), 500

    finally:
            cursor.close()
            connection.close()
    
