class Config(object):
    DEBUG = False
    import os
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent
    db_path = os.path.join(BASE_DIR, 'instance', '')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'+db_path+'cs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://user@localhost/hyy:'

class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@127.0.0.1:5432/pro_flask'
    ALLOW_UPLOAD_TYPE = ["image/jpeg", "image/png", "image/gif"]
    
    RECAPTCHA_PUBLIC_KEY = '6LfGgaQZAAAAAKDGl49W3MUM4EuMRVn4DW17mAdx'
    RECAPTCHA_PRIVATE_KEY='6LfGgaQZAAAAALFg29Ktye6qiinyqwIhj-xqmYO5'


    MAIL_SERVER = "smtp.qq.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = '1021509854@qq.com'
    MAIL_PASSWORD = 'oocxmmpozlctbgad'
    MAIL_DEFAULT_SENDER='1021509854@qq.com'


class TestingConfig(Config):
    import datetime
    DEBUG = True
    aa = {'APPLICATION_ROOT': '/',
          'DEBUG': None,
          'ENV': None,
          'EXPLAIN_TEMPLATE_LOADING': False,
          'JSONIFY_MIMETYPE': 'application/json',
          'JSONIFY_PRETTYPRINT_REGULAR': False,
          'JSON_AS_ASCII': True,
          'JSON_SORT_KEYS': True,
          'MAX_CONTENT_LENGTH': None,
          'MAX_COOKIE_SIZE': 4093,
          'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days=31),
          'PREFERRED_URL_SCHEME': 'http',
          'PRESERVE_CONTEXT_ON_EXCEPTION': None,
          'PROPAGATE_EXCEPTIONS': None,
          'SECRET_KEY': None,
          'SEND_FILE_MAX_AGE_DEFAULT': datetime.timedelta(seconds=43200),
          'SERVER_NAME': None,
          'SESSION_COOKIE_DOMAIN': None,
          'SESSION_COOKIE_HTTPONLY': True,
          'SESSION_COOKIE_NAME': 'session',
          'SESSION_COOKIE_PATH': None,
          'SESSION_COOKIE_SAMESITE': None,
          'SESSION_COOKIE_SECURE': False,
          'SESSION_REFRESH_EACH_REQUEST': True,
          'TEMPLATES_AUTO_RELOAD': None,
          'TESTING': False,
          'TRAP_BAD_REQUEST_ERRORS': None,
          'TRAP_HTTP_EXCEPTIONS': False,
          'USE_X_SENDFILE': False
          }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}