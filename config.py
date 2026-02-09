import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
    DB_HOST = os.environ.get('DB_HOST', '')
    DB_PORT = os.environ.get('DB_PORT', '')
    DB_NAME = os.environ.get('DB_NAME', '')
    DB_USER = os.environ.get('DB_USER', '')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    @property
    def DATABASE_URI(self):
        return f"dbname='{self.DB_NAME}' user='{self.DB_USER}' password='{self.DB_PASSWORD}' host='{self.DB_HOST}' port='{self.DB_PORT}'"
config = Config()