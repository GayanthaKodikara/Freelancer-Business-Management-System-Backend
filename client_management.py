from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging
from verify_jwt import token_required

cli = Blueprint('clients',__name__)


# --- Add Client ---
@cli.route('/clients', methods=['POST'])
@token_required
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

        # Check if cliient_id already exists
        cursor.execute("SELECT client_id FROM clients WHERE client_id = %s", (client_id,))
        result = cursor.fetchone()
        if result:
            connection.rollback()
            logging.warning(f"Client ID '{client_id}' already exists")
            return jsonify({'error': 'Client ID already exists'}), 400

        cursor.execute("INSERT INTO clients (client_id, first_name, last_name, country, company, email, contact_nu) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
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



# --- Get Clients ---
@cli.route('/clients', methods=['GET'])
@token_required
def get_clients():
    logging.info("GET request received for /clients")
    connection = None
    cursor = None
    try:
        connection = get_db_connection() 
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM clients")
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} clients from the database")

        clients_data = []
        for row in results:
            clients_data.append({
                'client_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'country': row[3],
                'company': row[4],
                'email': row[5], 
                'contact_nu': row[6]
            })
        logging.info("Successfully processed client data for response")
        return jsonify(clients_data) 

    except Exception as e:
        if connection:
            connection.rollback() 
        logging.error(f"Error processing GET request for /clients: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor: 
            cursor.close()
        if connection: 
            connection.close()
        logging.info("Database connection closed after GET /clients")



# --- Serch Client ---
@cli.route('/clients/suggestions', methods=['GET'])
@token_required
def get_client_suggestions():
   
    logging.info("GET request received for /clients/suggestions.")
    query = request.args.get('query', '').strip()  # Get the 'query' parameter from the URL, default to empty string
    logging.info(f"Client suggestion query received: '{query}'")

    if not query:
        logging.warning("No query parameter provided for client suggestions. Returning empty list.")
        return jsonify([])  # Return an empty list if no search query is provided

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in get_client_suggestions.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        
        cursor = connection.cursor()

        search_pattern = f"%{query}%"
        cursor.execute(
            """
            SELECT
                client_id,
                first_name,
                company,
                country
            FROM
                clients
            WHERE
                first_name LIKE %s OR company LIKE %s
            ORDER BY
                first_name ASC
            LIMIT 10;
            """,
            (search_pattern, search_pattern)
        )
        
        results = cursor.fetchall()  # Fetch all matching rows
        logging.info(f"Found {len(results)} client suggestions for query '{query}'.")

        # Convert results to a list of dictionaries for JSON response
        clients = []
        for row in results:
            # Assuming `row` can be accessed like a dictionary (e.g., if using DictCursor or row_factory for SQLite)
            client = {
                'client_id': row[0],
                'first_name': row[1],
                'company': row[2],
                'country': row[3]
            }
            clients.append(client)
        
        return jsonify(clients), 200 

    except Exception as e:
        logging.error(f"Error fetching client suggestions for query '{query}': {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /clients/suggestions.")

@cli.route('/clients/<int:client_id>', methods=['GET'])
@token_required
def get_single_client(client_id):
    
    logging.info(f"GET request received for /clients/{client_id}")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection for GET /clients/<client_id>")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                client_id,
                first_name,
                last_name,
                country,
                company,
                email,
                contact_no
            FROM
                clients
            WHERE client_id = %s
        """, (client_id,)) # Pass client_id as a tuple

        result = cursor.fetchone()

        if result:
            client_data = {
                'client_id': result[0],
                'first_name': result[1],
                'last_name': result[2],
                'country': result[3],
                'company': result[4],
                'email': result[5],
                'contact_no': result[6]
            }
            logging.info(f"Client {client_id} fetched successfully.")
            return jsonify(client_data), 200
        else:
            logging.warning(f"Client with ID {client_id} not found.")
            return jsonify({'error': 'Client not found'}), 404

    except Exception as e:
        logging.error(f"Error fetching client {client_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after GET /clients/{client_id}")