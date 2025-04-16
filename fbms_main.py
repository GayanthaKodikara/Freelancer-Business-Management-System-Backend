from flask import Flask
from flask_cors import CORS
from employee_management import emp
from login import auth
from project_management import prj


app = Flask(__name__)
CORS(app) # use for cross origin resource sharing


app.register_blueprint(auth)
app.register_blueprint(emp)
app.register_blueprint(prj)


if __name__ == '__main__':
    app.run(debug=True)