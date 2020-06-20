from flask import Flask, request, render_template, session, url_for, escape, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import logging
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler
from flask import g
from flask_mail import Mail, Message
import os
import functools
import time
from pathlib import Path
from flask_cors import CORS
from flask_wtf.csrf import generate_csrf
import jwt
import datetime
from .model import db
from flask_script import Manager







def create_log(log_name):

    BASE_DIR = Path(__file__).resolve().parent.parent
    log_path = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(log_path):
        os.mkdir(log_path)

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

    logging.getLogger('log_name')


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "cs.sqlite"),
    )
    app.config.from_object('settings.DevelopmentConfig')
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    db.init_app(app)
    db.app = app
    db.create_all()
    mail = Mail()
    mail.init_app(app)
    CSRFProtect(app)
    CORS(app)
    manager = Manager(app)
    create_log('config_studio')

    """
    蓝图注册
    """
    from app import opc, user, auth, issue
    app.register_blueprint(auth.auth)
    app.register_blueprint(user.user)
    app.register_blueprint(opc.cs)
    app.register_blueprint(issue.issue)

    def make_toke():
        csrf_token = generate_csrf()
        return csrf_token

    def login_required(view):
        """View decorator that redirects anonymous users to the login page."""

        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))

            return view(**kwargs)

        return wrapped_view

    @app.route('/', methods=['GET'], endpoint='index')
    @manager.command
    @login_required
    def index():
        flash('爱上一个地方，就应该背上包去旅行，走得更远。大家都在等你，还不快过来。。。玩耍！！！')
        if request.method == 'POST':
            return{'class': 'bg-info'}
        return render_template('index.html', home='bg-primary')

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404/page_not_found.html'), 404

    @app.before_first_request
    def before_first():
        app.logger.debug("config_studio 重新启动...")

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

    app.add_url_rule("/", endpoint="index")

    return app
