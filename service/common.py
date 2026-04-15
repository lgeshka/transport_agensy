import hashlib
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for, jsonify, Blueprint
from config import config
from service import get_db_connection

import psycopg2

def hash_password(password: str) -> tuple:
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt, hash_obj.hex()

def check_password(password: str, salt: str, stored_hash: str) -> bool:
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hash_obj.hex() == stored_hash