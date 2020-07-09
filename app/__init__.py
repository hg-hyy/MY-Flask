from flask import Flask, render_template, request, url_for, redirect, flash
from flask_wtf.csrf import CSRFProtect
import logging
from logging.config import dictConfig
from flask import g
from flask_mail import Mail
import os
import functools
import time
from flask_cors import CORS
from flask_wtf.csrf import generate_csrf
import jwt
import datetime
from .model import db
from .settings import Config
from .utils import log_class


def create_log(log_path,log_level):

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
            'app': {
                'level': log_level,
                'handlers': ['file']
            }}
    })

    logging.getLogger('log_name')


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_object('app.settings.DevelopmentConfig')
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    db.init_app(app)
    db.app = app
    db.create_all()
    mail = Mail()
    mail.init_app(app)
    CSRFProtect(app)
    CORS(app)
    create_log(Config.log_path,Config.log_level)
    app.add_template_filter(log_class, "log_class")

    """
    蓝图注册
    """
    from app import opc, user, auth, issue,charts,modbus
    app.register_blueprint(auth.auth)
    app.register_blueprint(user.admin)
    app.register_blueprint(opc.cs)
    app.register_blueprint(modbus.mt)
    app.register_blueprint(issue.faq)
    app.register_blueprint(charts.ct)

    def make_toke():
        csrf_token = generate_csrf()
        return csrf_token

    def login_required(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))
            return view(**kwargs)
        return wrapped_view

    @app.route('/', methods=['GET'], endpoint='index')
    @login_required
    def index():
        flash('爱上一个地方，就应该背上包去旅行，走得更远。大家都在等你，还不快过来玩耍！','success')
        return render_template('index.html', home='bg-primary')

    @app.route('/impress', methods=['GET'], endpoint='impress')
    def impress():
        return render_template('impress.html')

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404/page_not_found.html'), 404

    @app.before_first_request
    def before_first():
        app.logger.debug("config_studio 重新启动")

    # @csrf_exempt
    @app.route('/signin',methods=['POST','GET'],endpoint='signin')
    def signin():
        response = {}
        try:
            username = request.args.get("Username")
            password = request.args.get("Password")
            # user = authenticate(request, username=username, password=password)
            
            if username=='admin' and password=='111111' :
                app.logger.debug('登录成功')
                response['login'] = True
                response['msg'] = 'success'
                response['code'] = 200
                token = (str(encode_auth_token(username), encoding='utf-8'))
                response['token'] = token
                return response
            response['login'] = False
            response['msg'] = '登录失败'
            response['code'] = 500
            return response
        except Exception as e:
            print(e)
            return str(e)






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
