from flask import Blueprint, render_template, request, redirect, url_for
import json
import xlrd
from pathlib import Path
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_wtf.recaptcha import RecaptchaField
from wtforms import widgets
from wtforms import StringField
from wtforms.validators import DataRequired, Regexp, Length, IPAddress, ValidationError,InputRequired,Email 
from wtforms import PasswordField, SubmitField, RadioField
from wtforms import BooleanField
from wtforms.fields import core
from wtforms import TextAreaField
from wtforms.fields.html5 import EmailField



class FileForm(FlaskForm):
    files = FileField('上传文件', validators=[
        FileRequired(),
        FileAllowed(['xls', 'xlsx'], 'excel only!')],
        widget=widgets.FileInput(),
        render_kw={'class': 'form-control form-control-lg w-25 db-inline'}
    )


class PhotoForm(FlaskForm):
    photo = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')],
        widget=widgets.FileInput(),
        render_kw={'class': 'form-control form-control-lg w-25'
                   })


class UserForm(FlaskForm):
    username = StringField('username',
                           validators=[DataRequired()],
                           widget=widgets.TextInput(),
                           render_kw={
                               'class': 'offset-1 form-control form-control-lg mb-1 w-50', 'placeholder': 'foo'}
                           )
    email = StringField('email',
                        #  validators=[DataRequired()],
                        widget=widgets.TextInput(),
                        render_kw={
                            'class': 'offset-1 form-control form-control-lg mb-3 w-50 ', 'placeholder': 'foo@example.com'}
                        )
    password = StringField('password',
                           validators=[DataRequired()],
                           widget=widgets.PasswordInput(),
                           render_kw={
                               'class': 'offset-1 form-control form-control-lg mb-3 w-50 ', 'placeholder': 'foo@example.com'}
                           )
    gender = core.RadioField(
        label="性别",
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


class LoginForm(FlaskForm):
    username = StringField('name',
                           validators=[DataRequired(), username_length_check],
                           widget=widgets.TextInput(),
                           render_kw={'class': 'form-control form-control-lg',
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
                             render_kw={'class': 'form-control form-control-lg my-3',
                                        'placeholder': 'password', 'required': 'required'}
                             )
    recaptcha = RecaptchaField()

    remember_me = BooleanField(label='remember me')

    submit = SubmitField('登录',
                         render_kw={
                             'class': 'form-control btn btn-lg btn-primary btn-block'}
                         )


class OpcForm(FileForm):
    ip = StringField('IP地址',
                     validators=[DataRequired(), IPAddress(
                         message='请输入正确的IP地址')],
                     widget=widgets.TextInput(),
                     render_kw={
                         'class': 'offset-1 form-control form-control-lg mb-1 w-50', 'placeholder': 'foo'}
                     )
    progid = StringField('OPC名称',
                         validators=[DataRequired()],
                         widget=widgets.TextInput(),
                         render_kw={
                             'class': 'offset-1 form-control form-control-lg mb-1 w-50', 'placeholder': 'foo'}
                         )


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
    submit = SubmitField("Send")
