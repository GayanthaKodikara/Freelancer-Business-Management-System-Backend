from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging


prj = Blueprint('projects',__name__)


# add project
@prj.route('/projects', methods=['POST'])
def add_project():
    logging.info("POST request received for /projects")
    connection = None
    cursor = None
    data = request.get_json()
    logging.info(f"Received JSON data: {data}")

    proj_id = data.get('proj_id')
    proj_name = data.get('proj_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    proj_type = data.get('proj_type')

    if not proj_id or not proj_name:
        logging.warning("Required fields (proj_id, proj_name) are missing in POST request")
        return jsonify({'error': 'Project ID and Project Name are required'}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        # Check if proj_id already exists
        cursor.execute("SELECT proj_id FROM project WHERE proj_id = %s", (proj_id,))
        result = cursor.fetchone()
        if result:
            connection.rollback()
            logging.warning(f"Project ID '{proj_id}' already exists")
            return jsonify({'error': 'Project ID already exists'}), 400

        cursor.execute("INSERT INTO project (proj_id, proj_name, start_date, end_date, status, proj_type) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (proj_id, proj_name, start_date, end_date, status, proj_type))
        connection.commit()
        logging.info(f"Project with ID '{proj_id}' added successfully")
        return jsonify({'message': 'Project added successfully'}), 201

    except Exception as e:
        if connection:
            connection.rollback()
        logging.error(f"Error processing POST request for /projects: {e}")
        return jsonify({'error': str(e)}, 500)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after POST /projects")




# project list
@prj.route('/projects', methods=['GET'])
def get_projects():
    logging.info("GET request received for /projects")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500
        cursor = connection.cursor()

        cursor.execute("SELECT * from project")
        results = cursor.fetchall()
        logging.info(f"Retrieved {len(results)} projects from the database")

        projects = []
        for row in results:
            project = {
                'proj_id': row[0],
                'proj_name': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'status': row[4],
                'proj_type': row[5],
            }
            projects.append(project)
        logging.info("Successfully processed project data for response")
        return jsonify(projects), 200  

    except Exception as e:
        if connection:
            connection.rollback()  
        logging.error(f"Error processing GET request for /projects: {e}")
        return jsonify({'error': str(e)}, 500)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database connection closed after GET /projects")


# update project
@prj.route('/projects/<int:project_id>', methods=['PUT'])
def update_project():
    print('success')
    try:
        connection = get_db_connection
        cursor = connection.cursor

    
    except Exception as e:
        connection.rollback()
        return jsonify ({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

# update project status
@prj.route('/projects/status/<int:project_id>')
def update_status():
    print('success')
    try:
        connection = get_db_connection
        cursor = connection.cursor

    
    except Exception as e:
        connection.rollback()
        return jsonify ({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

# recieved project
