from flask import Flask, request, render_template, session, url_for, escape, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from .views.forms import UserForm
import logging
from logging.config import dictConfig
from flask import g
from flask_mail import Mail,Message
import os,time
from pathlib import Path
from flask_cors import CORS
from flask_wtf.csrf import generate_csrf
import  jwt,datetime
from flask_wtf.recaptcha import RecaptchaField
from .views.model import db


mail = Mail() 
BASE_DIR = Path(__file__).resolve().parent.parent
log_path = os.path.join(BASE_DIR, 'logs')
conf_path = os.path.join(BASE_DIR, 'conf', '')

if not os.path.exists(log_path):
    os.mkdir(log_path)


app = Flask(__name__)
mail.init_app(app) 
app.config['RECAPTCHA_USE_SSL'] = False 
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LfGgaQZAAAAAKDGl49W3MUM4EuMRVn4DW17mAdx' 
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LfGgaQZAAAAALFg29Ktye6qiinyqwIhj-xqmYO5' 
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'} 


app.config["MAIL_SERVER"] = "smtp.gmail.com" 
app.config["MAIL_PORT"] = 465 
app.config["MAIL_USE_SSL"] = True 
app.config["MAIL_USERNAME"] = '[email protected]' 
app.config["MAIL_PASSWORD"] = 'password' 


app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config.from_object('settings.DevelopmentConfig')

# db = SQLAlchemy(app)
db.init_app(app)

CSRFProtect(app)
CORS(app)



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




dictConfig({
    'version': 1,
    'formatters': {'default': {
        # 'format': '[%(asctime)s] [%(name)-8s] [%(levelname)-8s]: %(filename)s line:%(lineno)d %(message)s',
        'format': '[%(asctime)s]  [%(levelname)-5s]  [%(message)s]',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(log_path, '{}.log'.format(time.strftime('%Y-%m-%d'))),
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 5,  # 备份数
            'formatter': 'default',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码，否则打印出来汉字乱码
        }
    },
    'loggers': {
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        },
        'config_studio': {
            'level': 'DEBUG',
            'handlers': ['file']
        }}
})

log = logging.getLogger('config_studio')


"""
蓝图在这里注册
"""

from .views import config_studio,user,auth
app.register_blueprint(auth.auth)
app.register_blueprint(user.user)
app.register_blueprint(config_studio.cs)



def make_toke():
    csrf_token = generate_csrf()
    return csrf_token


@app.route('/', methods=['GET'], endpoint='index')
def index():
    flash('大家都在等你，还不快过来。。。玩耍！！！')
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404/page_not_found.html'), 404


@app.before_first_request
def before_first():
    log.info("config_studio 重新启动...")




#装饰器
def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view



def encode_auth_token(email):
        # 申请Token,参数为自定义,user_id不必须,此处为以后认证作准备,程序员可以根据情况自定义不同参数
    """
    生成认证Token
    :param user_id: int
    :param login_time: int(timestamp)
    :return: string
    """
    try:

        headers = {
            # "typ": "JWT",
            # "alg": "HS256",
            "email": email
        }

        playload = {
            "headers": headers,
            "iss": 'hyy',
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=0, minutes=30, seconds=0),
            'iat': datetime.datetime.utcnow()
        }

        signature = jwt.encode(
            playload, app.secret_key, algorithm='HS256')

        return signature
    except Exception as e:
        return e

token = str(encode_auth_token('hyy'), encoding='utf-8')
