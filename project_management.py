from flask import Blueprint, jsonify, request
from config import get_db_connection 
import logging
from verify_jwt import token_required
from datetime import datetime


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


prj = Blueprint('projects', __name__)


@prj.route('/projects', methods=['POST'])
@token_required
def add_project(decoded):
    
    logging.info("POST request received for /projects (add_project)")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received project data: {data}")

    # proj_id = data.get('proj_id')
    proj_name = data.get('proj_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    url = data.get('url')
    remarks = data.get('remarks') 
    client_id = data.get('client_id') 

    # Required field validation
    if not all([proj_name, start_date, end_date, status]):
        logging.warning("Missing required fields")
        return jsonify({'error': 'Project Name, Start Date, End Date, and Status are required.'}), 400

    # === Parse and validate dates ===
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

    # === Validate logical date order ===
    if start_date_obj >= end_date_obj:
        return jsonify({'error': 'Start Date must be before End Date'}), 400

    # === Validate future end date ===
    if end_date_obj <= datetime.now().date():
        return jsonify({'error': 'End Date must be a future date'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in add_project.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO projects ( proj_name, start_date, end_date, status, url, remarks, client_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ( proj_name, start_date, end_date, status, url, remarks, client_id)
        )

        current_datetime = datetime.now() # Get current date and time
        breakdown_description = f"Project created with initial status: {status}" 

        cursor.execute("SELECT proj_id FROM projects WHERE proj_name = %s AND client_id = %s", (proj_name, client_id))
        connection.commit()

        result = cursor.fetchone() 
    
        proj_id = None
        if result:
            proj_id = result[0]

        cursor.execute(
            "INSERT INTO proj_breakdown (proj_id, date_time, description) VALUES (%s, %s, %s)",
            (proj_id, current_datetime, breakdown_description)
        )

        connection.commit() 
        logging.info(f"Project with ID '{proj_id}' added successfully.")
        return jsonify({'message': 'Project added successfully', 'proj_id': proj_id}), 201 

    except Exception as e:
        if connection:
            connection.rollback() 
        logging.error(f"Error processing POST request for /projects: {e}") 
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after POST /projects.")


@prj.route('/projects', methods=['GET'])
@token_required
def get_projects(decoded):
    logging.info("GET request received for /project (get_projects)")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in get_projects.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                p.proj_id,
                p.proj_name,
                p.start_date,
                p.end_date,
                p.status,
                p.remarks,
                p.url,
                c.client_id,
                c.first_name AS client_first_name,
                c.company AS client_company,
                c.country AS client_country
            FROM projects p LEFT JOIN clients c ON p.client_id = c.client_id ORDER BY p.start_date DESC;
        """)
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} projects from the database.")

        projects = []
        for row in results:
            project = {
                'proj_id': row[0],
                'proj_name': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'status': row[4],
                'remarks': row[5], 
                'url': row[6],
                'client_id': row[7],
                'client_first_name': row[8],
                'client_company': row[9],
                'client_country': row[10]
            }
            projects.append(project)
        logging.info("Successfully formatted project data for response.")
        return jsonify(projects), 200 

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing GET request for /projects: {e}")
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /projects.")


@prj.route('/projects/<int:project_id>', methods=['GET'])
@token_required
def get_project_by_id(decoded, project_id):
    logging.info(f"GET request received for /projects/{project_id} (get_project_by_id)")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for project ID {project_id}.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.proj_id,
                p.proj_name,
                p.start_date,
                p.end_date,
                p.status,
                p.remarks,
                p.url,
                c.client_id,
                c.first_name AS client_first_name,
                c.company AS client_company,
                c.country AS client_country
            FROM projects p LEFT JOIN clients c ON p.client_id = c.client_id WHERE p.proj_id = %s;
        """, (project_id,))
        result = cursor.fetchone()

        if result:
            project = {
                'proj_id': result[0],
                'proj_name': result[1],
                'start_date': str(result[2]),
                'end_date': str(result[3]),
                'status': result[4],
                'remarks': result[5],
                'url':result[6],
                'client_id': result[7],
                'client_name': f"{result[8]} ({result[9]})" if result[8] else '', # Formatted for frontend
                'client_first_name': result[8],
                'client_company': result[9],
                'client_country': result[10]
            }
            logging.info(f"Successfully retrieved project with ID '{project_id}'.")
            return jsonify(project), 200
        else:
            logging.warning(f"Project with ID '{project_id}' not found.")
            return jsonify({'error': 'Project not found'}), 404

    except Exception as e:
        logging.error(f"Error processing GET request for /projects/{project_id}: {e}")
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after GET /projects/{project_id}.")


@prj.route('/projects/<int:project_id>', methods=['PUT'])
@token_required
def update_project(decoded, project_id):
   
    logging.info(f"PUT request received for /projects/{project_id} (update_project)")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received update data for project '{project_id}': {data}")

    proj_name = data.get('proj_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    url = data.get('url')
    remarks = data.get('remarks')
    client_id = data.get('client_id') 

   # Required field validation
    if not all([proj_name, start_date, end_date, status]):
        logging.warning("Missing required fields")
        return jsonify({'error': 'Project Name, Start Date, End Date, and Status are required.'}), 400

    # === Parse and validate dates ===
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

    # === Validate logical date order ===
    if start_date_obj >= end_date_obj:
        return jsonify({'error': 'Start Date must be before End Date'}), 400

    # === Validate future end date ===
    if end_date_obj <= datetime.now().date():
        return jsonify({'error': 'End Date must be a future date'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for updating project '{project_id}'.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE projects
            SET proj_name = %s, start_date = %s, end_date = %s, status = %s, url = %s, remarks = %s, client_id = %s
            WHERE proj_id = %s
            """,
            (proj_name, start_date, end_date, status, url, remarks, client_id, project_id)
        )

        current_datetime = datetime.now() # Get current date and time
        breakdown_description = f"Project updated: {status}" 

        cursor.execute(
            "INSERT INTO proj_breakdown (proj_id, date_time, description) VALUES (%s, %s, %s)",
            (project_id, current_datetime, breakdown_description)
        )

        connection.commit()

        if cursor.rowcount == 0:
            # If no rows were affected, the project_id might not exist
            logging.warning(f"Attempted to update non-existent project ID: {project_id}.")
            return jsonify({'error': 'Project not found or no changes made'}), 404
        
        logging.info(f"Project with ID '{project_id}' updated successfully.")
        return jsonify({'message': 'Project updated successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing PUT request for /projects/{project_id}: {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after PUT /projects/{project_id}.")


# @prj.route('/projects/status/<int:project_id>', methods=['PUT'])
# @token_required
# def update_project_status(decoded, project_id):
    
#     logging.info(f"PUT request received for /projects/status/{project_id} (update_project_status)")
#     connection = None
#     cursor = None
#     data = request.get_json()
#     status = data.get('status') 

#     if not status:
#         logging.warning("Status field is missing in update_project_status request.")
#         return jsonify({'error': 'Status field is required for status update.'}), 400

#     try:
#         connection = get_db_connection()
#         if connection is None:
#             logging.error(f"Failed to establish database connection for updating status of project '{project_id}'.")
#             return jsonify({'error': 'Failed to connect to the database'}), 500
#         cursor = connection.cursor()

#         cursor.execute(
#             "UPDATE projects SET status = %s WHERE proj_id = %s",
#             (status, project_id)
#         )
#         connection.commit()

#         if cursor.rowcount == 0:
#             logging.warning(f"Attempted to update status for non-existent project ID: {project_id}.")
#             return jsonify({'error': 'Project not found or no changes made'}), 404
        
#         logging.info(f"Status for project '{project_id}' updated to '{status}' successfully.")
#         return jsonify({'message': 'Project status updated successfully'}), 200

#     except Exception as e:
#         if connection:
#             connection.rollback()
#         logging.error(f"Error processing PUT request for /projects/status/{project_id}: {e}", exc_info=True)
#         return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
#     finally:
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()
#         logging.info(f"Database connection closed after PUT /projects/status/{project_id}.")

# @prj.route('/projects/<int:project_id>', methods=['DELETE'])
# @token_required
# def delete_project(decoded, project_id):
  
#     logging.info(f"DELETE request received for /projects/{project_id} (delete_project)")
#     connection = None
#     cursor = None
#     try:
#         connection = get_db_connection()
#         if connection is None:
#             logging.error(f"Failed to establish database connection for deleting project '{project_id}'.")
#             return jsonify({'error': 'Failed to connect to the database'}), 500
#         cursor = connection.cursor()

#         cursor.execute("DELETE FROM projects WHERE proj_id = %s", (project_id,))
#         connection.commit()

#         if cursor.rowcount == 0:
#             logging.warning(f"Attempted to delete non-existent project ID: {project_id}.")
#             return jsonify({'error': 'Project not found'}), 404
        
#         logging.info(f"Project with ID '{project_id}' deleted successfully.")
#         return jsonify({'message': 'Project deleted successfully'}), 200

#     except Exception as e:
#         if connection:
#             connection.rollback()
#         logging.error(f"Error processing DELETE request for /projects/{project_id}: {e}")
#         return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
#     finally:
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()
#         logging.info(f"Database connection closed after DELETE /projects/{project_id}.")