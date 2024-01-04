


# from main import db
import ast
import csv
import datetime
import random
import string
from datetime import datetime

from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, app, db


class ContactUs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    message = db.Column(db.Text)

    def __init__(self, name, email, message):
        self.name = name
        self.email = email
        self.message = message

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    response = db.Column(db.JSON)
    score = db.Column(db.JSON)
    profile_picture = db.Column(db.String(255))
    name = db.Column(db.String(50))
    description = db.Column(db.String(255))
    role = db.Column(db.String(50))
    affiliation = db.Column(db.String(50))

    def __init__(self, username, password, response, score, profile_picture, name, description, role, affiliation):
        self.username = username
        self.password = password
        self.response = response
        self.score = score
        self.profile_picture = profile_picture
        self.name = name
        self.description = description
        self.role = role
        self.affiliation = affiliation
    
    def __repr__(self):
        return f"<User(username='{self.username}', password='{self.password}')>"