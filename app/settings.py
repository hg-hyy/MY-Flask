class Config(object):
    import os
    from pathlib import Path
    DEBUG = False
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
    BASE_DIR = Path(__file__).resolve().parent.parent
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    log_level = 'DEBUG'
    log_path = os.path.join(BASE_DIR, 'logs')
    conf_path = os.path.join(BASE_DIR, 'conf', '')
    p = Path(conf_path)


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://user@localhost/hyy:'


class DevelopmentConfig(Config):
    import os
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@127.0.0.1:5432/pro_flask'
    ALLOW_UPLOAD_TYPE = ["image/jpeg", "image/png", "image/gif"]

    RECAPTCHA_PUBLIC_KEY = '6LfGgaQZAAAAAKDGl49W3MUM4EuMRVn4DW17mAdx'
    RECAPTCHA_PRIVATE_KEY = '6LfGgaQZAAAAALFg29Ktye6qiinyqwIhj-xqmYO5'

    MAIL_SERVER = os.getenv('MAIL_SERVER'),
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER = '1021509854@qq.com'


class TestingConfig(Config):
    import datetime
    DEBUG = True
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=31),
