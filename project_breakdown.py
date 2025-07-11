from flask import Blueprint, jsonify, request
from config import get_db_connection 
import logging
from verify_jwt import token_required
from datetime import datetime


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


breakdown = Blueprint('get_project_breakdown', __name__)


@breakdown.route('/projectbreakdown/<int:proj_id>', methods=['GET'])
@token_required
def get_project_breakdown(decoded, proj_id):

    logging.info(f"GET request received for /projectbreakdown/{proj_id}")
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in get_project_breakdown.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor() 


        # Join projects and clients tables to get combined information
        project_query = """
            SELECT
                p.proj_id,
                p.proj_name,
                p.start_date,
                p.end_date,
                p.status,
                p.remarks,
                c.first_name,
                c.company
            FROM
                projects p
            JOIN
                clients c ON p.client_id = c.client_id
            WHERE
                p.proj_id = %s;
        """
        cursor.execute(project_query, (proj_id,))
        project_details = cursor.fetchone()

        if not project_details:
            logging.warning(f"Project with ID '{proj_id}' not found.")
            return jsonify({'error': f"Project with ID '{proj_id}' not found."}), 404

        # Get project breakdown entries
        breakdown_query = """
            SELECT
                date_time,
                description
            FROM
                proj_breakdown
            WHERE
                proj_id = %s
            ORDER BY
                date_time ASC; -- Order by date for chronological display
        """
        cursor.execute(breakdown_query, (proj_id,))
        breakdown_entries = cursor.fetchall()

        # Date and Time Format
        # DATE_FORMAT = "%Y-%m-%d"
        # DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        # Format breakdown entries 
        formatted_breakdown = []
        for entry in breakdown_entries:
            formatted_breakdown.append({
                'date_time': entry[0].isoformat() if entry[0] else None,
                # 'date_time': entry[0].strftime(DATETIME_FORMAT) if entry[0] else None,
                'description': entry[1]
            })

        # Combine all information into a single response dictionary
        response_data = {
            'project_details': {
                'proj_id': project_details[0],
                'proj_name': project_details[1],
                'start_date': project_details[2].isoformat() if project_details[2] else None,
                'end_date': project_details[3].isoformat() if project_details[3] else None,
                'status': project_details[4],
                'remarks': project_details[5],
                'client_name': project_details[6],
                'company': project_details[7]
            },
            'breakdown_history': formatted_breakdown
        }

        logging.info(f"Successfully retrieved breakdown for project ID '{proj_id}'.")
        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Error processing GET request for /projectbreakdown/{proj_id}: {e}")
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /projectbreakdown.")


@breakdown.route('/costbreakdown/<string:proj_id>', methods=['GET'])
@token_required
def get_cost_breakdown(decoded, proj_id):
    logging.info(f"GET request received for /costbreakdown/{proj_id}")
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in get_cost_breakdown.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cost_breakdown_query = """
            SELECT
                pc.cost_id,
                pc.inventory_code,
                pc.quantity,
                pc.date_time,
                pc.description,
                i.name AS inventory_name,
                i.price AS inventory_price
            FROM
                proj_cost pc
            JOIN
                inventory i ON pc.inventory_code = i.inventory_code
            WHERE
                pc.proj_id = %s
            ORDER BY
                pc.date_time ASC; -- Order by date for chronological display
        """
        cursor.execute(cost_breakdown_query, (proj_id,))
        cost_entries = cursor.fetchall()

        if not cost_entries:
            logging.info(f"No cost breakdown entries found for project ID '{proj_id}'.")
            return jsonify({'message': f"No cost breakdown entries found for project ID '{proj_id}'."}), 200 # Return 200 with empty list or message

        formatted_cost_entries = []
        total_project_cost = 0.0 # Initialize total cost

        for entry in cost_entries:
            inventory_price = float(entry[6]) if entry[6] is not None else 0.0
            quantity = entry[2] if entry[2] is not None else 0

            # Calculate cost for current entry and add to total
            item_cost = inventory_price * quantity
            total_project_cost += item_cost

            formatted_cost_entries.append({
                'cost_id':entry[0],
                'inventory_code': entry[1],
                'quantity': quantity,
                'date_time': entry[3].isoformat() if entry[3] else None,
                'description': entry[4],
                'inventory_name': entry[5],
                'inventory_price': inventory_price,
                'item_total_cost': item_cost 
            })

        logging.info(f"Successfully retrieved cost breakdown for project ID '{proj_id}'. Total cost: {total_project_cost}")
        return jsonify({
            'cost_breakdown': formatted_cost_entries,
            'total_project_cost': total_project_cost
        }), 200

    except Exception as e:
        logging.error(f"Error processing GET request for /costbreakdown/{proj_id}: {e}")
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /costbreakdown.")