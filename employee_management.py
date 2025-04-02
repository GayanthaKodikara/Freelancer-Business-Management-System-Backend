from flask import Blueprint, jsonify, request
from config import get_db_connection


appp = Blueprint('get_employees',__name__)


@appp.route('/employees', methods=['GET'])
def get_employees():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM employee")
    results = cursor.fetchall()
    cursor.close()
    #print(results) # print in console
    users = [] # initial blank list
    for row in results: #for loop
        users.append({'emp_id': row[0], 'first_name': row[1], 'last_name': row[2], 'email':row[9], 'address':row[3],
        'nic': row[4],'birth_day': row[5],'role': row[6],'workshop_name': row[7],'design_category': row[8],})
    #print(users) # print in console
    return jsonify(users)
    #return jsonify(results) 
    #return str(results)  #for string result


@appp.route('/add_employee', methods=['POST'])
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

    print(data)

    if not first_name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
        

    try:
        cursor.execute("INSERT INTO employee (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
         (first_name, last_name, email, address, nic, birth_day, role, workshop_name, design_category))
        connection.commit()
        cursor.close()
        connection.close() # Close the connection
        return jsonify({'message': 'Employee added successfully'}), 201
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close() # Close the connection
        return jsonify({'error': str(e)}), 500


