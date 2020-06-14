from flask import Flask, request, render_template, session, url_for, escape, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from .views.forms import UserForm
import logging
from logging.config import dictConfig
from flask import g
import os,time
from pathlib import Path
from flask_cors import CORS
from flask_wtf.csrf import generate_csrf


BASE_DIR = Path(__file__).resolve().parent.parent
log_path = os.path.join(BASE_DIR, 'logs')
conf_path = os.path.join(BASE_DIR, 'conf', '')

if not os.path.exists(log_path):
    os.mkdir(log_path)


app = Flask(__name__)


app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config.from_object('settings.DevelopmentConfig')

db = SQLAlchemy(app)

CSRFProtect(app)
CORS(app)


dictConfig({
    'version': 1,
    'formatters': {'default': {
        # 'format': '[%(asctime)s] [%(name)-8s] [%(levelname)-8s]: %(filename)s line:%(lineno)d %(message)s',
        'format': '[%(asctime)s] [%(levelname)-5s] [%(message)s]',
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
        'modbus_tool': {
            'level': 'DEBUG',
            'handlers': ['file']
        }}
})

log = logging.getLogger('modbus_tool')


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
    log.debug("第一次请求你会看到这条信息")




#装饰器
def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view

