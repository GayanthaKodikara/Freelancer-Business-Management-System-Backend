from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

inv = Blueprint('inventory', __name__)

@inv.route('/inventory', methods=['GET'])
def get_inventory():
    logging.info("GET request received for /inventory")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection for GET /inventory")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Ensure the column order in the SELECT matches the order in which you assign to inventory_item dictionary keys
        cursor.execute("SELECT inventory_code, name, shop, buying_date, price, quantity, available_quantity, location FROM inventory")
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} inventory items from the database")

        inventory_list = []
        for row in results:
            inventory_item = {
                'item_code': row[0],
                'item_name': row[1],
                'shop': row[2],
                'purchase_date': row[3],
                'price': row[4],
                'quantity': row[5],
                'available_quantity': row[6],
                'location': row[7],
            }
            inventory_list.append(inventory_item)
        logging.info("Successfully processed inventory data for GET response")
        return jsonify(inventory_list), 200
    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing GET request for /inventory: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /inventory")

@inv.route('/inventory', methods=['POST'])
def add_inventory():
    logging.info("POST request received for /inventory")
    connection = None
    cursor = None
    try:
        data = request.get_json()
        logging.info(f"Received data for new inventory: {data}")

        name = data.get('name')
        shop = data.get('shop') 
        buying_date = data.get('buying_date')
        price = data.get('price')
        quantity = data.get('quantity')
        available_quantity = data.get('quantity')
        location = data.get('location')

        # server-side validation
        if not all([name, buying_date, price, quantity, available_quantity, location]):
            logging.warning("Missing required fields for new inventory item")
            return jsonify({'error': 'Missing one or more required fields: name, buying_date, price, quantity, available_quantity, location'}), 400

        # Convert types and validate
        # try:
        #     # buying_date = datetime.strptime(buying_date_str, '%Y-%m-%d').date()
        #     price = float(price)
        #     quantity = int(quantity)
        #     # available_quantity = int(available_quantity)
        # except ValueError as ve:
        #     logging.error(f"Data type conversion error for new inventory: {ve}")
        #     return jsonify({'error': f'Invalid data type for fields: {ve}'}), 400

        # if quantity < 0 or available_quantity < 0:
        #     return jsonify({'error': 'Quantity and Available Quantity cannot be negative'}), 400
        # if available_quantity > quantity:
        #     return jsonify({'error': 'Available Quantity cannot be greater than total Quantity'}), 400
        if price <= 0:
            return jsonify({'error': 'Price must be greater than zero'}), 400


        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection for POST /inventory")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # SQL INSERT query
        insert_query = """
        INSERT INTO inventory (name, shop, buying_date, price, quantity, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (name, shop, buying_date, price, quantity, location))
        connection.commit()
        logging.info(f"Successfully added new inventory item: {name}")

        return jsonify({'message': 'Inventory item added successfully', 'inventory_code': cursor.lastrowid}), 201

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing POST request for /inventory: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after POST /inventory")



@inv.route('/inventory/<string:inventory_code>', methods=['GET'])
# @token_required
def get_inventory_item(inventory_code):
    logging.info(f"GET request received for /inventory/{inventory_code}")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection for GET /inventory/<item_code>")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("""
            SELECT inventory_code, name, shop, buying_date, price, quantity, available_quantity, location
            FROM inventory
            WHERE inventory_code = %s
        """, (inventory_code,))

        result = cursor.fetchone() 
        
        if result:
            logging.info(f"Retrieved inventory item with code: {inventory_code}")
            inventory_item = {
                'item_code': result[0],
                'item_name': result[1], 
                'shop': result[2],
                'buying_date': str(result[3]),
                'price': result[4],
                'quantity': result[5],
                'available_quantity': result[6],
                'location': result[7],
            }
            logging.info(f"Successfully processed inventory data for item {inventory_code}")
            return jsonify(inventory_item), 200
        else:
            logging.warning(f"Inventory item with code {inventory_code} not found.")
            return jsonify({'error': 'Inventory item not found'}), 404

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing GET request for /inventory/{inventory_code}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after GET /inventory/{inventory_code}")




@inv.route('/inventory/<int:inventory_code>', methods=['PUT'])
def update_inventory(inventory_code):
    logging.info(f"PUT request received for /inventory/{inventory_code}")
    connection = None
    cursor = None
    try:
        data = request.get_json()
        logging.info(f"Received data for inventory update (code {inventory_code}): {data}")

        # Extract data with validation for required fields
        name = data.get('name')
        shop = data.get('shop')
        buying_date = data.get('buying_date')
        price = data.get('price')
        quantity = data.get('quantity')
        location = data.get('location')

        # Basic server-side validation
        if not all([name, buying_date, price, quantity, location]):
            logging.warning(f"Missing required fields for inventory update (code {inventory_code})")
            return jsonify({'error': 'Missing one or more required fields: name, buying_date, price, quantity, available_quantity, location'}), 400

        if price <= 0:
            return jsonify({'error': 'Price must be greater than zero'}), 400


        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for PUT /inventory/{inventory_code}")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("""UPDATE inventory SET name = %s, shop = %s, buying_date = %s, price = %s, quantity = %s, location = %s
        WHERE inventory_code = %s """, (name, shop, buying_date, price, quantity, location, inventory_code))
        connection.commit()

        logging.info(f"Successfully updated inventory item: {name} (Code: {inventory_code})")
        return jsonify({'message': 'Inventory item updated successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing PUT request for /inventory/{inventory_code}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after PUT /inventory/{inventory_code}")
