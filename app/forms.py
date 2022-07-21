from flask import  current_app, session, flash, g
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_wtf.recaptcha import RecaptchaField
from wtforms import widgets
from wtforms import StringField
from wtforms.validators import DataRequired, Regexp, Length, ValidationError, InputRequired, Email
from wtforms import PasswordField, SubmitField
from wtforms import BooleanField
from wtforms import TextAreaField, SelectField
from wtforms import EmailField
from .model import User, db, Category, Issue, Contact
from wtforms.validators import EqualTo
import datetime


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

# 自定义验证

def username_length_check(form, field):
    if len(field.data) > 50:
        raise ValidationError('Field must be less than 50 characters')


class LoginForm(FlaskForm):

    username = StringField('username',
                           validators=[DataRequired()],
                           widget=widgets.TextInput(),
                           render_kw={'class': 'form-control form-control-md',
                                      'placeholder': 'username', 'required': 'required', 'autocomplete': 'off'}
                           )
    password = PasswordField('password',
                             validators=[DataRequired(),
                                         ],
                             widget=widgets.PasswordInput(),
                             render_kw={'class': 'form-control form-control-md my-3',
                                        'placeholder': 'password', 'required': 'required'}
                             )
    # recaptcha = RecaptchaField('验证码')

    remember_me = BooleanField(label='remember me')

    submit = SubmitField('登录',
                         render_kw={
                             'class': 'form-control btn btn-md btn-primary btn-block'}
                         )

    def validate(self):
        """Validator for check the account information."""
        check_validata = super(LoginForm, self).validate()

        # If validator no pass
        if not check_validata:
            return False
        remember_me = self.remember_me.data
        user = User.query.filter_by(username=self.username.data).first_or_404(
            description='THE {} is not found'.format(self.username.data))
        if user.username == self.username.data and user.check_password(self.password.data):
            session.clear()
            if remember_me == True:
                session.permanent = True
                current_app.permanent_session_lifetime = datetime.timedelta(
                    seconds=60)
                session['user_id'] = user.id
                user.last_login_time = datetime.datetime.now()
                db.session.commit()
            else:
                session['user_id'] = user.id
            flash('You were successfully logged in', 'success')
            return True
        else:
            self.username.errors.append('Invalid username or password.')
            flash('密码错误', 'error')
            return False


class RegisterForm(FlaskForm):
    username = StringField('username',
                           validators=[DataRequired(), Length(1, 60),
                                       Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名必须只有字母，数字，点或下划线'), username_length_check],
                           widget=widgets.TextInput(),
                           render_kw={'class': 'form-control form-control-md',
                                      'placeholder': 'username', 'required': 'required'}
                           )
    email = EmailField('email address',
                       validators=[DataRequired()],
                       render_kw={'class': 'form-control form-control-md',
                                  'placeholder': 'Email address'}
                       )
    password = PasswordField('password',
                             validators=[DataRequired(),
                                         Length(
                                 min=8, message='密码名长度必须大于%(min)d'),
                                 Regexp(regex="^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]{8,}",
                                        message='密码至少8个字符，至少1个大写字母，1个小写字母，1个数字和1个特殊字符')
                             ],
                             widget=widgets.PasswordInput(),
                             render_kw={'class': 'form-control form-control-md my-3',
                                        'placeholder': 'password', 'required': 'required'}
                             )
    comfirm = PasswordField('Confirm Password',
                            validators=[DataRequired(), EqualTo('password')],
                            widget=widgets.PasswordInput(),
                            render_kw={'class': 'form-control form-control-md',
                                       'placeholder': 'password', 'required': 'required'}
                            )
    recaptcha = RecaptchaField('验证码')

    submit = SubmitField('注册',
                         render_kw={
                             'class': 'form-control btn btn-md btn-primary btn-block'}
                         )

    def validate(self):
        """Validator for check the account information."""
        check_validata = super(RegisterForm, self).validate()

        # If validator no pass
        if not check_validata:
            flash(self.errors, 'error')
            return False

        print(self.username.data, self.password.data)

        user = User.query.filter_by(username=self.username.data).first()
        # db.session.query(Users).filter(username=self.username.data).first()
        if user:
            self.username.errors.append('用户名已存在！')
            flash(self.username.errors, 'error')
            return False
        else:
            # rw_pwd = generate_password_hash(self.password.data)
            user = User(username=self.username.data,
                        email=self.email.data, password=self.password.data)
            db.session.add(user)
            db.session.commit()
        return True


class CategoryForm(FlaskForm):

    category_name = StringField("category_name",
                                validators=[DataRequired()],
                                render_kw={
                                    'class': 'form-control ', 'autocomplete': 'off'})
    submit = SubmitField(
        '创建', render_kw={'class': 'form-control btn btn-md btn-primary btn-block'})

    def validate(self):
        """Validator for check the account information."""
        check_validata = super(CategoryForm, self).validate()
        if not check_validata:
            return False

        category_name = self.category_name.data
        category = Category.query.filter_by(
            name=self.category_name.data).first()

        if category:
            flash("OOOPSS..主题已经存在，请换一个", 'error')
            return False
        else:
            category = Category(name=category_name, user_id=g.user.id)
            db.session.add(category)
            db.session.commit()
        return True


class IssueForm(FlaskForm):

    title = StringField("title",
                        validators=[DataRequired()],
                        render_kw={
                            'class': 'form-control '})
    body = StringField("body",
                       validators=[DataRequired()],
                       render_kw={
                           'class': 'form-control '})
    category_name = StringField("category_name",
                                validators=[DataRequired()],
                                render_kw={
                                    'class': 'form-control '})
    submit = SubmitField(
        '创建', render_kw={'class': 'form-control btn btn-md btn-primary btn-block'})

    def validate(self):
        """Validator for check the account information."""
        check_validata = super(IssueForm, self).validate()
        # If validator no pass
        if not check_validata:
            return False
        title = self.title.data
        body = self.body.data
        category_name = self.category_name.data
        if not all((title, category_name, body)):
            flash("标题或主题不能为空")
            return False
        issue = Issue.query.filter_by(title=title).first()
        category = Category.query.filter_by(
            name=self.category_name.data).first()

        if not category and category_name == 'all':
            category = Category(name=category_name, user_id=g.user.id)
            db.session.add(category)
            db.session.commit()

        if not issue:
            issue = Issue(title=title, body=body,
                          user_id=g.user.id, category_id=category.id)
            db.session.add(issue)
            db.session.commit()
        issue.title = title
        issue.body = body
        db.session.commit()
        issue.category_id = category.id
        return True


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
                         default=[("s_opcda_client1", "s_opcda_client1")],
                         widget=widgets.Select(),
                         render_kw={'class': 'form-control form-control-md custom-select',
                                    'placeholder': 'module name', 'required': 'required'}
                         )

    main_server_ip = StringField('main_server_ip',
                                 validators=[DataRequired()],
                                 widget=widgets.TextInput(),
                                 render_kw={'class': 'form-control form-control-md',
                                            'placeholder': 'main_server_ip', 'required': 'required'}
                                 )
    main_server_prgid = SelectField('main_server_progid',
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
                                     render_kw={'class': 'form-control form-control-md custom-select',
                                                'placeholder': 'main_server_prgid', 'required': 'required'}
                                     )
    main_server_clsid = SelectField('main_server_classid',
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
                                      render_kw={'class': 'form-control form-control-md custom-select',
                                                 'placeholder': 'main_server_clsid', 'required': 'required'}
                                      )
    main_server_domain = StringField('main_server_domain',
                                     validators=[DataRequired()],
                                     widget=widgets.TextInput(),
                                     render_kw={'class': 'form-control form-control-md',
                                                'placeholder': 'main_server_domain', 'required': 'required'}
                                     )
    main_server_user = StringField('main_server_username',
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

    bak_server_ip = StringField('back_server_ip',
                                 validators=[DataRequired()],
                                 widget=widgets.TextInput(),
                                 render_kw={'class': 'form-control form-control-md',
                                            'placeholder': 'bak_server_ip', 'required': 'required'}
                                 )
    bak_server_prgid = SelectField('back_server_progid',
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
                                     render_kw={'class': 'form-control form-control-md custom-select',
                                                'placeholder': 'bak_server_prgid', 'required': 'required'}
                                     )
    bak_server_clsid = SelectField('back_server_classid',
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
                                      render_kw={'class': 'form-control form-control-md custom-select',
                                                 'placeholder': 'bak_server_clsid', 'required': 'required'}
                                      )
    bak_server_domain = StringField('back_server_domain',
                                     validators=[DataRequired()],
                                     widget=widgets.TextInput(),
                                     render_kw={'class': 'form-control form-control-md',
                                                'placeholder': 'bak_server_domain', 'required': 'required'}
                                     )
    bak_server_user = StringField('back_server_username',
                                       validators=[DataRequired()],
                                       widget=widgets.TextInput(),
                                       render_kw={'class': 'form-control form-control-md',
                                                  'placeholder': 'bak_server_user', 'required': 'required'}
                                       )
    bak_server_password = StringField('back_server_password',
                                       validators=[DataRequired()],
                                       widget=widgets.TextInput(),
                                       render_kw={'class': 'form-control form-control-md',
                                                  'placeholder': 'bak_server_password', 'required': 'required'}
                                       )

    # submit = SubmitField('保存', widget=widgets.SubmitInput(),
    #                      render_kw={'class': 'btn btn-info btn-block btn-md',})


class OpcdaForm(OpcForm):

    file = FileField('上传文件', validators=[
        FileRequired(),
        FileAllowed(['xls', 'xlsx'], 'excel only!')],
        widget=widgets.FileInput(),
        render_kw={'class': 'form-control form-control-md'})


class ContactForm(FlaskForm):
    name = StringField("Name",
                       validators=[InputRequired('Please enter your name.')],
                       render_kw={
                           'class': 'form-control ', 'placeholder': 'Name'}
                       )
    email = EmailField("Email",
                       validators=[InputRequired("Please enter your email address."),
                                   Email("Please enter your email address.")
                                   ],
                       render_kw={
                           'class': 'form-control ', 'placeholder': 'Email'}
                       )
    subject = StringField("Subject",
                          validators=[
                              InputRequired("Please enter the subject.")],
                          render_kw={
                              'class': 'form-control '}
                          )
    message = TextAreaField("Message",
                            validators=[
                                InputRequired("Please enter your message.")],
                            render_kw={
                                'class': 'form-control ', 'rows': '5', 'placeholder': 'something ..'}
                            )
    submit = SubmitField('Send',
                         render_kw={
                             'class': 'btn btn-info btn-block btn-md'}
                         )

    def validate(self):
        """Validator for check the account information."""
        check_validata = super(ContactForm, self).validate()

        # If validator no pass
        if not check_validata:
            return False

        user = User.query.filter_by(username=self.name.data).first()
        # db.session.query(Users).filter(username=self.username.data).first()
        if not user:
            self.name.errors.append('User with that name not exists.')
            flash('User with that name not exists.', 'error')
            return False
        else:
            contact = Contact(
                name=self.name.data,
                email=self.email.data,
                subject=self.subject.data,
                message=self.message.data,
                user_id=user.id)
            db.session.add(contact)
            db.session.commit()
        return True
