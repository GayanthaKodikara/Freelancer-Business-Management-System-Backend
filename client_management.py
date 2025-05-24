from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging


cli = Blueprint('clients',__name__)


# add project
@cli.route('/clients', methods=['POST'])
def add_client():
    logging.info("POST request received for /clients")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received JSON data: {data}")

    client_id = data['client_id']
    first_name = data['first_name']
    last_name = data['last_name']
    country = data['country']
    company = data['company']
    email = data['email']
    contact_nu = data['contact_nu']

    if not client_id or not email:
        logging.warning("Required fields (client_id, email) are missing in POST request")
        return jsonify({'error': 'Client ID and Client email are required'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Check if proj_id already exists
        cursor.execute("SELECT client_id FROM client WHERE client_id = %s", (client_id,))
        result = cursor.fetchone()
        if result:
            connection.rollback()
            logging.warning(f"Client ID '{client_id}' already exists")
            return jsonify({'error': 'Client ID already exists'}), 400

        cursor.execute("INSERT INTO client (client_id, first_name, last_name, country, company, email, contact_nu) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                       (client_id, first_name, last_name, country, company, email, contact_nu))
        connection.commit()
        logging.info(f"Client with ID '{client_id}' added successfully")
        return jsonify({'message': 'Client added successfully'}), 201

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing POST request for /clients: {e}")
        return jsonify({'error': str(e)}, 500)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after POST /clients")


# @cli.route('/clients', methods=['GET'])
# def get_clients():
#     logging.info("GET request received for /clients")
#     connection = None
#     cursor = None
#     try:
#         connection = get_db_connection()
#         cursor = connection.cursor()
#         cursor.execute("""
#             SELECT employee.*, login.permission
#             FROM employee
#             INNER JOIN login ON employee.emp_id = login.emp_id
#         """)
#         results = cursor.fetchall()
#         logging.info(f"Retrieved {len(results)} employees from the database")

#         users = []
#         for row in results:
#             users.append({
#                 'emp_id': row[0],
#                 'first_name': row[1],
#                 'last_name': row[2],
#                 'email': row[9],
#                 'address': row[3],
#                 'nic': row[4],
#                 'birth_day': row[5],
#                 'role': row[6],
#                 'workshop_name': row[7],
#                 'design_category': row[8],
#                 'permission': row[10]
#             })
#         logging.info("Successfully processed employee data for response")
#         return jsonify(users)

#     except Exception as e:
#         if connection:
#             connection.rollback()
#         logging.error(f"Error processing GET request for /employees: {e}")
#         return jsonify({'error': str(e)}), 500

#     finally:
#         cursor.close()
#         connection.close()
#         logging.info("Database connection closed after GET /employees")


