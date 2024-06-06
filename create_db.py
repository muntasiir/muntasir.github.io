from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
     'mysql+pymysql://root:muntasir1234@localhost/5.0db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Other imports and routes go here

if __name__ == "__main__":
    app.run(debug=True)
