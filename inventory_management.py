from flask import Blueprint, jsonify
from config import get_db_connection
import logging

inv = Blueprint('inventory', __name__)

@inv.route('/inventory', methods=['GET'])
def get_inventory():
    logging.info("GET request received for /inventory")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("SELECT * from inventory")
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} inventory items from the database")

        inventory_list = []  
        for row in results:
            inventory_item = {  
                'item_code': row[0],  
                'proj_id': row[1],
                'item_name': row[2], 
                'purchase_date': row[3],
                'price': row[4],
                'shop': row[5],
                'availability': row[6], 
            }
            inventory_list.append(inventory_item) 
        logging.info("Successfully processed inventory data for response")
        return jsonify(inventory_list), 200 
    except Exception as e:
        if connection:
            connection.rollback() 
        logging.error(f"Error processing GET request for /inventory: {e}")
        return jsonify({'error': str(e)}, 500)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /inventory")
