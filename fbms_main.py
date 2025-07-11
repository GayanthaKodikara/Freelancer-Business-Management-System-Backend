from flask import Flask
from flask_cors import CORS
from employee_management import emp
from login import auth
from project_management import prj
from client_management import cli
from inventory_management import inv
from verify_jwt import tok
from project_breakdown import breakdown

app = Flask(__name__)
CORS(app) # use for cross origin resource sharing

app.register_blueprint(auth)
app.register_blueprint(emp)
app.register_blueprint(prj)
app.register_blueprint(cli)
app.register_blueprint(inv)
app.register_blueprint(tok)
app.register_blueprint(breakdown)


if __name__ == '__main__':
    app.run(debug=True)