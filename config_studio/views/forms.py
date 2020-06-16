from urllib.parse import urlparse
from collections import abc
from flask import Blueprint, render_template, request, redirect, url_for, current_app
import json
import xlrd
from pathlib import Path
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_wtf.recaptcha import RecaptchaField, validators
from flask_wtf.recaptcha.validators import Recaptcha
from wtforms import widgets, Form
from wtforms import StringField, Label, HiddenField
from wtforms.validators import DataRequired, Regexp, Length, IPAddress, ValidationError, InputRequired, Email
from wtforms import PasswordField, SubmitField, RadioField
from wtforms import BooleanField
from wtforms.fields import core
from wtforms import TextAreaField, SelectField
from wtforms.fields.html5 import EmailField
import requests
from .model import User
from werkzeug.urls import url_encode
from wtforms import ValidationError
from urllib import request as http


GOOGLE_RECAPTCHA_SECRET_KEY = '6LfGgaQZAAAAALFg29Ktye6qiinyqwIhj-xqmYO5'

URL = 'https://recaptcha.net/recaptcha/api/siteverify'


class FileForm(FlaskForm):
    files = FileField('上传文件', validators=[
        FileRequired(),
        FileAllowed(['xls', 'xlsx'], 'excel only!')],
        widget=widgets.FileInput(),
        render_kw={'class': 'form-control form-control-md w-25 db-inline'}
    )


class PhotoForm(FlaskForm):
    photo = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')],
        widget=widgets.FileInput(),
        render_kw={'class': 'form-control form-control-md w-25'
                   })


class UserForm(FlaskForm):

    username = StringField('username',
                           validators=[DataRequired()],
                           widget=widgets.TextInput(),
                           render_kw={
                               'class': 'offset-1 form-control form-control-md mb-1 w-50', 'placeholder': 'foo'}
                           )
    email = StringField('email',
                        #  validators=[DataRequired()],
                        widget=widgets.TextInput(),
                        render_kw={
                            'class': 'offset-1 form-control form-control-md mb-3 w-50 ', 'placeholder': 'foo@example.com'}
                        )
    password = StringField('password',
                           validators=[DataRequired()],
                           widget=widgets.PasswordInput(),
                           render_kw={
                               'class': 'offset-1 form-control form-control-md mb-3 w-50 ', 'placeholder': 'foo@example.com'}
                           )
    gender = core.RadioField(
        label="1,性别",
        choices=(
                (1, "男"),
                (2, "女"),
        ),
        coerce=int,  # 限制是int类型的
        default=[1]
    )
    city = core.SelectField(
        label="城市",
        choices=(
                ("bj", "北京"),
                ("sh", "上海"),
        )
    )
    # def validate_email(self, field):
    #     if User.objects.filter(email=field.data).count() > 0:
    #         raise ValidationError('Email already registered')

    # def validate_username(self, field):
    #     if User.objects.filter(username=field.data).count() > 0:
    #         raise ValidationError('Username has exist')

# 自定义验证


def username_length_check(form, field):
    if len(field.data) > 50:
        raise ValidationError('Field must be less than 50 characters')


RECAPTCHA_VERIFY_SERVER = 'https://recaptcha.net/recaptcha/api/siteverify'
RECAPTCHA_ERROR_CODES = {
    'missing-input-secret': 'The secret parameter is missing.',
    'invalid-input-secret': 'The secret parameter is invalid or malformed.',
    'missing-input-response': 'The response parameter is missing.',
    'invalid-input-response': 'The response parameter is invalid or malformed.'
}


text_type = str
string_types = (str,)


def to_bytes(text):
    """Transform string to bytes."""
    if isinstance(text, text_type):
        text = text.encode('utf-8')
    return text


def to_unicode(input_bytes, encoding='utf-8'):
    """Decodes input_bytes to text if needed."""
    if not isinstance(input_bytes, string_types):
        input_bytes = input_bytes.decode(encoding)
    return input_bytes


class Recaptcha(object):
    """Validates a ReCaptcha."""

    def __init__(self, message=None):
        if message is None:
            message = RECAPTCHA_ERROR_CODES['missing-input-response']
        self.message = message

    def __call__(self, form, field):
        if current_app.testing:
            return True

        if request.json:
            response = request.json.get('g-recaptcha-response', '')
        else:
            response = request.form.get('g-recaptcha-response', '')
        remote_ip = request.remote_addr

        if not response:
            raise ValidationError(field.gettext(self.message))

        if not self._validate_recaptcha(response, remote_ip):
            field.recaptcha_error = 'incorrect-captcha-sol'
            raise ValidationError(field.gettext(self.message))

    def _validate_recaptcha(self, response, remote_addr):
        """Performs the actual validation."""
        try:
            
            private_key = current_app.config['RECAPTCHA_PRIVATE_KEY']
        except KeyError:
            raise RuntimeError("No RECAPTCHA_PRIVATE_KEY config set")

        data = url_encode({
            'secret':     private_key,
            'remoteip':   remote_addr,
            'response':   response
        })

        http_response = http.urlopen(RECAPTCHA_VERIFY_SERVER, to_bytes(data))

        if http_response.code != 200:
            return False

        json_resp = json.loads(to_unicode(http_response.read()))

        if json_resp["success"]:
            return True

        for error in json_resp.get("error-codes", []):
            if error in RECAPTCHA_ERROR_CODES:
                raise ValidationError(RECAPTCHA_ERROR_CODES[error])

        return False


def check_password(form, field):
    print(field)
    if len(field.data) > 50:
        raise ValidationError('Field must be less than 50 characters')


class LoginForm(FlaskForm):

    username = StringField('name',
                           validators=[DataRequired(), username_length_check],
                           widget=widgets.TextInput(),
                           render_kw={'class': 'form-control form-control-md',
                                      'placeholder': 'Email address', 'required': 'required'}
                           )
    password = PasswordField('password',
                             validators=[DataRequired(), 
                                         #   Length(
                                         #       min=8, message='用户名长度必须大于%(min)d'),
                                         #   Regexp(regex="^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]{8,}",
                                         #          message='密码至少8个字符，至少1个大写字母，1个小写字母，1个数字和1个特殊字符')
                                         ],
                             widget=widgets.PasswordInput(),
                             render_kw={'class': 'form-control form-control-md my-3',
                                        'placeholder': 'password', 'required': 'required'}
                             )
    recaptcha = RecaptchaField('验证码')
    # recaptcha = RecaptchaField('验证码', validators=[check],
    #                            widget=widgets.TextInput(),
    #                            render_kw={'class': 'form-control form-control-md'})

    remember_me = BooleanField(label='remember me')

    submit = SubmitField('登录',
                         render_kw={
                             'class': 'form-control btn btn-md btn-primary btn-block'}
                         )

    # def validate(self):
    #     """Validator for check the account information."""
    #     check_validata = super(LoginForm, self).validate()

    #     # If validator no pass
    #     if not check_validata:
    #         return False
    #     print()
    #     # Check the user whether exist.
    #     user = User.query.filter_by(username=self.username.data).first()
    #     if not user:
    #         self.username.errors.append('Invalid username or password.')
    #         return False

    #     # Check the password whether right.
    #     if not user.check_password(self.password.data):
    #         self.username.errors.append('Invalid username or password.')
    #         return False

    #     return True

    # def check_password(self, form, field):
    #     print(field)
    #     if len(field.data) > 50:
    #         raise ValidationError('Field must be less than 50 characters')


class CommentForm(FlaskForm):

    comment = TextAreaField("Comment", validators=[DataRequired()])
    recaptcha = RecaptchaField()


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[
                       InputRequired('Please enter your name.')])
    email = EmailField("Email", validators=[InputRequired(
        "Please enter your email address."), Email("Please enter your email address.")])
    subject = StringField("Subject", validators=[
                          InputRequired("Please enter the subject.")])
    message = TextAreaField("Message", validators=[
                            InputRequired("Please enter your message.")])
    recaptcha = RecaptchaField()
    submit = SubmitField()


class OpcForm(FlaskForm):
    module = SelectField('module_name',
                         validators=[DataRequired()],
                         choices=(
                             ("s_opcda_server1", "s_opcda_server1"),
                             ("s_opcda_server2", "s_opcda_server2"),
                             ("s_opcda_server3", "s_opcda_server3"),
                             ("s_opcda_client1", "s_opcda_client1"),
                             ("s_opcda_client2", "s_opcda_client2"),
                             ("s_opcda_client3", "s_opcda_client3"),
                             ("s_opcae_server1", "s_opcae_server1"),
                             ("s_opcae_server2", "s_opcae_server2"),
                             ("s_opcae_server3", "s_opcae_server3"),
                             ("s_opcae_client1", "s_opcae_client1"),
                             ("s_opcae_client2", "s_opcae_client2"),
                             ("s_opcae_client3", "s_opcae_client3"),
                             ("modbus1", "modbus1"),
                             ("modbus2 ", "modbus2"),
                         ),
                         coerce=str,  # 限制是int类型的
                         default=['s_opcda_client1'],
                         widget=widgets.Select(),
                         render_kw={'class': 'form-control form-control-md',
                                    'placeholder': 'module name', 'required': 'required'}
                         )

    main_server_ip = StringField('main_server_ip',
                                 validators=[DataRequired()],
                                 widget=widgets.TextInput(),
                                 render_kw={'class': 'form-control form-control-md',
                                            'placeholder': 'main_server_ip', 'required': 'required'}
                                 )
    main_server_progid = SelectField('main_server_progid',
                                     validators=[DataRequired()],
                                     choices=(
                                         ('Intellution.OPCiFIX.1',
                                          'Intellution.OPCiFIX.1'),
                                         ('Kepware.KEPServerEX.V6',
                                          'Kepware.KEPServerEX.V6'),
                                         ('Yokogawa.CSHIS_OPC.1',
                                          'Yokogawa.CSHIS_OPC.1'),
                                         ('SUPCON.SCRTCore.1',
                                          'SUPCON.SCRTCore.1'),
                                         ('OPCSystems.NET.1', 'OPCSystems.NET.1')
                                     ),
                                     coerce=str,  # 限制是int类型的
                                     default=['Intellution.OPCiFIX.1'],
                                     widget=widgets.Select(),
                                     render_kw={'class': 'form-control form-control-md',
                                                'placeholder': 'main_server_prgid', 'required': 'required'}
                                     )
    main_server_classid = SelectField('main_server_classid',
                                      validators=[DataRequired()],
                                      choices=(
                                          ('3C5702A2-EB8E-11D4-83A4-00105A984CBD',
                                           '3C5702A2-EB8E-11D4-83A4-00105A984CBD'),
                                          ('7BC0CC8E-482C-47CA-ABDC-0FE7F9C6E729',
                                           '7BC0CC8E-482C-47CA-ABDC-0FE7F9C6E729'),
                                          ('E6C32641-F1CF-11D0-B0E4-080009CCD384',
                                           'E6C32641-F1CF-11D0-B0E4-080009CCD384'),
                                          ('41EBD53D-36C4-4027-B2B4-09A6E4A362DD',
                                           '41EBD53D-36C4-4027-B2B4-09A6E4A362DD'),
                                          ('6031BF75-9CF2-11D1-A97B-00C04FC01389',
                                           '6031BF75-9CF2-11D1-A97B-00C04FC01389'),
                                          ('32FB9E42-29D6-4841-9218-9DA5E1515623',
                                           '32FB9E42-29D6-4841-9218-9DA5E1515623')
                                      ),
                                      coerce=str,  # 限制是int类型的
                                      default=[
                                          '3C5702A2-EB8E-11D4-83A4-00105A984CBD'],
                                      widget=widgets.Select(),
                                      render_kw={'class': 'form-control form-control-md',
                                                 'placeholder': 'main_server_clsid', 'required': 'required'}
                                      )
    main_server_domain = StringField('main_server_domain',
                                     validators=[DataRequired()],
                                     widget=widgets.TextInput(),
                                     render_kw={'class': 'form-control form-control-md',
                                                'placeholder': 'main_server_domain', 'required': 'required'}
                                     )
    main_server_username = StringField('main_server_username',
                                       validators=[DataRequired()],
                                       widget=widgets.TextInput(),
                                       render_kw={'class': 'form-control form-control-md',
                                                  'placeholder': 'main_server_user', 'required': 'required'}
                                       )
    main_server_password = StringField('main_server_password',
                                       validators=[DataRequired()],
                                       widget=widgets.TextInput(),
                                       render_kw={'class': 'form-control form-control-md',
                                                  'placeholder': 'main_server_password', 'required': 'required'}
                                       )

    back_server_ip = StringField('back_server_ip',
                                 validators=[DataRequired()],
                                 widget=widgets.TextInput(),
                                 render_kw={'class': 'form-control form-control-md',
                                            'placeholder': 'bak_server_ip', 'required': 'required'}
                                 )
    back_server_progid = SelectField('back_server_progid',
                                     validators=[DataRequired()],
                                     choices=(
                                         ('Intellution.OPCiFIX.1',
                                          'Intellution.OPCiFIX.1'),
                                         ('Kepware.KEPServerEX.V6',
                                          'Kepware.KEPServerEX.V6'),
                                         ('Yokogawa.CSHIS_OPC.1',
                                          'Yokogawa.CSHIS_OPC.1'),
                                         ('SUPCON.SCRTCore.1',
                                          'SUPCON.SCRTCore.1'),
                                         ('OPCSystems.NET.1', 'OPCSystems.NET.1')
                                     ),
                                     coerce=str,  # 限制是int类型的
                                     default=['Kepware.KEPServerEX.V6'],
                                     widget=widgets.Select(),
                                     render_kw={'class': 'form-control form-control-md',
                                                'placeholder': 'bak_server_prgid', 'required': 'required'}
                                     )
    back_server_classid = SelectField('back_server_classid',
                                      validators=[DataRequired()],
                                      choices=(
                                          ('3C5702A2-EB8E-11D4-83A4-00105A984CBD',
                                           '3C5702A2-EB8E-11D4-83A4-00105A984CBD'),
                                          ('7BC0CC8E-482C-47CA-ABDC-0FE7F9C6E729',
                                           '7BC0CC8E-482C-47CA-ABDC-0FE7F9C6E729'),
                                          ('E6C32641-F1CF-11D0-B0E4-080009CCD384',
                                           'E6C32641-F1CF-11D0-B0E4-080009CCD384'),
                                          ('41EBD53D-36C4-4027-B2B4-09A6E4A362DD',
                                           '41EBD53D-36C4-4027-B2B4-09A6E4A362DD'),
                                          ('6031BF75-9CF2-11D1-A97B-00C04FC01389',
                                           '6031BF75-9CF2-11D1-A97B-00C04FC01389'),
                                          ('32FB9E42-29D6-4841-9218-9DA5E1515623',
                                           '32FB9E42-29D6-4841-9218-9DA5E1515623')
                                      ),
                                      coerce=str,  # 限制是int类型的
                                      default=[
                                          '3C5702A2-EB8E-11D4-83A4-00105A984CBD'],
                                      widget=widgets.Select(),
                                      render_kw={'class': 'form-control form-control-md',
                                                 'placeholder': 'bak_server_clsid', 'required': 'required'}
                                      )
    back_server_domain = StringField('back_server_domain',
                                     validators=[DataRequired()],
                                     widget=widgets.TextInput(),
                                     render_kw={'class': 'form-control form-control-md',
                                                'placeholder': 'bak_server_domain', 'required': 'required'}
                                     )
    back_server_username = StringField('back_server_username',
                                       validators=[DataRequired()],
                                       widget=widgets.TextInput(),
                                       render_kw={'class': 'form-control form-control-md',
                                                  'placeholder': 'bak_server_user', 'required': 'required'}
                                       )
    back_server_password = StringField('back_server_password',
                                       validators=[DataRequired()],
                                       widget=widgets.TextInput(),
                                       render_kw={'class': 'form-control form-control-md',
                                                  'placeholder': 'bak_server_password', 'required': 'required'}
                                       )

    file = FileField('上传文件', validators=[
        FileRequired(),
        FileAllowed(['xls', 'xlsx'], 'excel only!')],
        widget=widgets.FileInput(),
        render_kw={'class': 'form-control form-control-md'}
    )
    # submit = SubmitField('保存', widget=widgets.SubmitInput(),
    #                      render_kw={'class': 'btn btn-info btn-block btn-md',})
