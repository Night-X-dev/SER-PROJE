from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
import pymysql.cursors
import os
import bcrypt
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# JWT Secret Key
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = 86400  # 24 hours in seconds

# Create Blueprint
management_bp = Blueprint(
    'management',
    __name__,
    template_folder='templates/personel',
    static_folder='static',
    static_url_path='/personel/static',
    url_prefix='/personel'
)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST_NEW", "localhost"),
        user=os.getenv("MYSQL_USER_NEW", "serik"),
        password=os.getenv("MYSQL_PASSWORD_NEW", "Ser.1712_"),
        database=os.getenv("MYSQL_DATABASE_NEW", "ser_ik"),
        port=int(os.getenv("MYSQL_PORT_NEW", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        autocommit=True
    )

