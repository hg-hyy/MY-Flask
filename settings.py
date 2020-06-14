class Config(object):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///D:\\Web\\python\\scwg\\pro_flask\\pro_flask.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://user@localhost/hyy:'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@127.0.0.1:5432/pro_flask'



class TestingConfig(Config):
    DEBUG = True
