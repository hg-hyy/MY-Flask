from flask import Blueprint, render_template, request, redirect, url_for
import json
import xlrd
from pathlib import Path
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import widgets
from .forms import FileForm, PhotoForm,OpcForm
from flask_wtf.csrf import CSRFProtect,CSRFError
from config_studio import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(120), unique=True, nullable=False)


    def __repr__(self):
        return '<User %r>' % self.username

    def __str__(self):
        return self.username

class Opc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    main_server_ip = db.Column(db.String(80), unique=True, nullable=False)
    main_server_progid = db.Column(db.String(120), unique=True, nullable=True)
    main_server_username = db.Column(db.String(120), unique=True, nullable=True)
    main_server_password = db.Column(db.String(120), unique=True, nullable=False)

    back_server_ip = db.Column(db.String(80), unique=True, nullable=False)
    back_server_progid = db.Column(db.String(120), unique=True, nullable=True)
    back_server_username = db.Column(db.String(120), unique=True, nullable=True)
    back_server_password = db.Column(db.String(120), unique=True, nullable=False)


    def __repr__(self):
        return '<Opc %r>' % self.main_server_progid

    def __str__(self):
        return self.main_server_progid

