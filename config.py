import os


class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
