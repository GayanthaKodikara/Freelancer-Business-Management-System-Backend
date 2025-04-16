from flask import Blueprint, jsonify, request
from config import get_db_connection


prj = Blueprint('add_project',__name__)


# add project
@prj.route('/projects', methods=['POST'])
def add_project():
    try:
        connection = get_db_connection
        cursor = connection.cursor

    
    except Exception as e:
        connection.rollback()
        return jsonify ({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()


# project list
@prj.route('/projects', methods=['GET'])
def get_projects():
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
