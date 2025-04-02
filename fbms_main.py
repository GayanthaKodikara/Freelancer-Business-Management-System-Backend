from flask import Flask
from flask_cors import CORS
from employee_management import appp
from login import app


fbms = Flask(__name__)
CORS(fbms) # use for cross origin resource sharing


fbms.register_blueprint(app)
fbms.register_blueprint(appp)


if __name__ == '__main__':
    fbms.run(debug=True)