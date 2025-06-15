# blueprints/projects.py - Flask Blueprint for Project API Endpoints

from flask import Blueprint, jsonify, request
from config import get_db_connection # Assuming this provides your database connection
import logging

# Configure logging for this blueprint
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a Blueprint instance for project-related routes
prj = Blueprint('projects', __name__)

# --- Project API Endpoints ---

@prj.route('/projects', methods=['POST'])
def add_project():
    """
    Handles POST requests to add a new project.
    Expects project details (proj_id, proj_name, start_date, end_date, status, remarks, client_id)
    in the JSON request body.
    """
    logging.info("POST request received for /projects (add_project)")
    connection = None
    cursor = None
    data = request.get_json() # Get JSON data from the request body
    logging.info(f"Received project data: {data}")

    # Extract data from the request, providing default None for optional fields
    proj_id = data.get('proj_id')
    proj_name = data.get('proj_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    remarks = data.get('remarks') # Added remarks field
    client_id = data.get('client_id') # New: client_id from frontend suggestion selection

    # Input validation: Check for required fields
    if not all([proj_id, proj_name, start_date, end_date, status]):
        logging.warning("Required fields (proj_id, proj_name, start_date, end_date, status) are missing in POST request.")
        return jsonify({'error': 'Project ID, Project Name, Start Date, End Date, and Status are required.'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in add_project.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Check if proj_id already exists to prevent duplicates
        cursor.execute("SELECT proj_id FROM project WHERE proj_id = %s", (proj_id,))
        result = cursor.fetchone()
        if result:
            connection.rollback() # Rollback any pending transaction
            logging.warning(f"Project ID '{proj_id}' already exists. Aborting insertion.")
            return jsonify({'error': f"Project ID '{proj_id}' already exists."}), 409 # Conflict status code

        # Insert new project into the 'projects' table
        # If client_id is None, it will be inserted as NULL in the database
        cursor.execute(
            "INSERT INTO project (proj_id, proj_name, start_date, end_date, status, remarks, client_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (proj_id, proj_name, start_date, end_date, status, remarks, client_id)
        )
        connection.commit() # Commit the transaction to save changes
        logging.info(f"Project with ID '{proj_id}' added successfully.")
        return jsonify({'message': 'Project added successfully', 'proj_id': proj_id}), 201 # Created status

    except Exception as e:
        # Catch any exceptions during database operation
        if connection:
            connection.rollback() # Rollback in case of error
        logging.error(f"Error processing POST request for /projects: {e}", exc_info=True) # exc_info for full traceback
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500

    finally:
        # Ensure cursor and connection are closed in all cases
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after POST /projects.")


@prj.route('/projects', methods=['GET'])
def get_projects():
    """
    Handles GET requests to retrieve a list of all projects.
    Joins with the 'clients' table to include client details (first_name, company)
    for each project.
    """
    logging.info("GET request received for /project (get_projects)")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error("Failed to establish database connection in get_projects.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Execute a JOIN query to fetch project details along with associated client info
        cursor.execute("""
            SELECT
                p.proj_id,
                p.proj_name,
                p.start_date,
                p.end_date,
                p.status,
                p.remarks,
                c.client_id,
                c.first_name AS client_first_name,
                c.company AS client_company,
                c.country AS client_country
            FROM
                project p
            LEFT JOIN
                client c ON p.client_id = c.client_id
            ORDER BY
                p.start_date DESC;
        """)
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} projects from the database.")

        # Format results into a list of dictionaries for JSON response
        projects = []
        for row in results:
            # Assuming row is a dictionary or can be accessed by column name (e.g., if using DictCursor)
            # If row is a tuple and order matters, adjust indices.
            # Example for dictionary/named access:
            project = {
                'proj_id': row['proj_id'],
                'proj_name': row['proj_name'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'status': row['status'],
                'remarks': row['remarks'], 
                'client_id': row['client_id'],
                'client_first_name': row['client_first_name'],
                'client_company': row['client_company'],
                'client_country': row['client_country']
            }
            projects.append(project)
        logging.info("Successfully formatted project data for response.")
        return jsonify(projects), 200 

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing GET request for /projects: {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /projects.")

@prj.route('/projects/<string:project_id>', methods=['GET'])
def get_project_by_id(project_id):
    """
    Handles GET requests to retrieve a single project by its ID.
    Useful for populating an 'Update Project' form.
    """
    logging.info(f"GET request received for /projects/{project_id} (get_project_by_id)")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for project ID {project_id}.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Fetch the project by proj_id, also joining for client details
        cursor.execute("""
            SELECT
                p.proj_id,
                p.proj_name,
                p.start_date,
                p.end_date,
                p.status,
                p.remarks,
                c.client_id,
                c.first_name AS client_first_name,
                c.company AS client_company,
                c.country AS client_country
            FROM
                project p
            LEFT JOIN
                clients c ON p.client_id = c.client_id
            WHERE
                p.proj_id = %s;
        """, (project_id,))
        result = cursor.fetchone()

        if result:
            project = {
                'proj_id': result['proj_id'],
                'proj_name': result['proj_name'],
                'start_date': result['start_date'],
                'end_date': result['end_date'],
                'status': result['status'],
                'remarks': result['remarks'],
                'client_id': result['client_id'],
                'client_name': f"{result['client_first_name']} ({result['client_company']})" if result['client_first_name'] else '', # Formatted for frontend
                'client_first_name': result['client_first_name'],
                'client_company': result['client_company'],
                'client_country': result['client_country']
            }
            logging.info(f"Successfully retrieved project with ID '{project_id}'.")
            return jsonify(project), 200
        else:
            logging.warning(f"Project with ID '{project_id}' not found.")
            return jsonify({'error': 'Project not found'}), 404

    except Exception as e:
        logging.error(f"Error processing GET request for /projects/{project_id}: {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after GET /projects/{project_id}.")


@prj.route('/projects/<string:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Handles PUT requests to update an existing project by its ID.
    Expects updated project details in the JSON request body.
    """
    logging.info(f"PUT request received for /projects/{project_id} (update_project)")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received update data for project '{project_id}': {data}")

    # Extract updated fields
    proj_name = data.get('proj_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    remarks = data.get('remarks')
    client_id = data.get('client_id') # Allow updating associated client

    # Basic validation for required update fields
    if not all([proj_name, start_date, end_date, status]):
        logging.warning("Missing required fields for project update.")
        return jsonify({'error': 'Project Name, Start Date, End Date, and Status are required for update.'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for updating project '{project_id}'.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Update the project record
        cursor.execute(
            """
            UPDATE project
            SET proj_name = %s, start_date = %s, end_date = %s, status = %s, remarks = %s, client_id = %s
            WHERE proj_id = %s
            """,
            (proj_name, start_date, end_date, status, remarks, client_id, project_id)
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


@prj.route('/projects/status/<string:project_id>', methods=['PUT'])
def update_project_status(project_id):
    """
    Handles PUT requests to update only the status of an existing project by its ID.
    Expects 'status' in the JSON request body.
    """
    logging.info(f"PUT request received for /projects/status/{project_id} (update_project_status)")
    connection = None
    cursor = None
    data = request.get_json()
    status = data.get('status') # Get only the status field

    if not status:
        logging.warning("Status field is missing in update_project_status request.")
        return jsonify({'error': 'Status field is required for status update.'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for updating status of project '{project_id}'.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE projects SET status = %s WHERE proj_id = %s",
            (status, project_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            logging.warning(f"Attempted to update status for non-existent project ID: {project_id}.")
            return jsonify({'error': 'Project not found or no changes made'}), 404
        
        logging.info(f"Status for project '{project_id}' updated to '{status}' successfully.")
        return jsonify({'message': 'Project status updated successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing PUT request for /projects/status/{project_id}: {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after PUT /projects/status/{project_id}.")

@prj.route('/projects/<string:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Handles DELETE requests to remove a project by its ID.
    """
    logging.info(f"DELETE request received for /projects/{project_id} (delete_project)")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            logging.error(f"Failed to establish database connection for deleting project '{project_id}'.")
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("DELETE FROM projects WHERE proj_id = %s", (project_id,))
        connection.commit()

        if cursor.rowcount == 0:
            logging.warning(f"Attempted to delete non-existent project ID: {project_id}.")
            return jsonify({'error': 'Project not found'}), 404
        
        logging.info(f"Project with ID '{project_id}' deleted successfully.")
        return jsonify({'message': 'Project deleted successfully'}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing DELETE request for /projects/{project_id}: {e}", exc_info=True)
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info(f"Database connection closed after DELETE /projects/{project_id}.")