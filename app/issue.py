from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app,jsonify
from .model import Issue, db, Category
from .forms import CategoryForm, ContactForm, IssueForm
from flask import g
from flask_mail import Message, Mail
from app.opc import login_required
import markdown2 as Markdown
import bleach
import time,json
from threading import Thread
from sqlalchemy import and_,or_   


faq = Blueprint('faq', __name__)
mail = Mail()


@faq.route("/show_category", methods=['GET', 'POST'], endpoint='show_category')
def show_category(form=None):
    """Show all the posts, most recent first."""
    page = int(request.args.get('page', 1))
    # 获取每页显示数据条数默认为2
    pages = int(request.args.get('pages', 3))
    # 从数据库查询数据
    paginates = Category.query.order_by('id').paginate(
        page, pages, error_out=False)
    return render_template('issue/show_category.html', paginate=paginates)


@faq.route("/add_category", methods=['GET', 'POST'], endpoint='add_category')
def add_category():
    form = CategoryForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            flash("你 TMD 又提了一个大BUG", 'error')
            return redirect(url_for('faq.show_category'))
    return render_template('issue/create_category.html', form=form)


@faq.route("/<int:id>/update_category", methods=("GET", "POST"), endpoint='update_category')
def update_category(id):
    """Update a post if the current user is the author."""
    category = get_category(id)
    form = CategoryForm()
    if request.method == "POST":
        if form.validate_on_submit():
            return redirect(url_for("faq.show_category"))
    return render_template("issue/update_category.html",  category=category)


@faq.route("/<int:id>/delete_category", methods=("POST",), endpoint='delete_category')
def delete_category(id):
    category = get_category(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for("faq.show_category"))


def get_category(id, check_user=True):
    category = Category.query.filter_by(id=id).first_or_404(
        description='There is no issue with {}'.format(id))

    if category is None:
        abort(404, "issue id {0} doesn't exist.".format(id))

    if check_user and category.user_id != g.user.id:
        abort(403)

    return category


def get_issue(id, check_user=True):
    issue = Issue.query.filter_by(id=id).first_or_404(
        description='There is no issue with {}'.format(id))

    if issue is None:
        abort(404, "issue id {0} doesn't exist.".format(id))

    if check_user and issue.user_id != g.user.id:
        abort(403)

    return issue


@faq.route("/search_issue_datetime", methods=['GET', 'POST'], endpoint='search_issue_datetime')
def search_issue_datetime():
    if request.method == 'POST':
        ca = request.form.get('ca')
        created_day = request.form.get(
            'created_day', time.strftime('%Y-%m-%d'))
        created_day_start = created_day+' ' + \
            request.form.get('created_day_start', '00:00:00')
        created_day_end = created_day+' ' + \
            request.form.get("created_day_end", "23:59:59")
        page = int(request.form.get('page', 1))
        pages = int(request.form.get('pages', 3))
        category = Category.query.filter_by(name=ca).first_or_404()
        paginates = Issue.query.filter(and_(Issue.created > created_day_start, Issue.created <
                                            created_day_end, Issue.category_id == category.id)).paginate(page, pages, error_out=False)
        pga = {'items': [issue.to_json() for issue in paginates.items],
               'has_prev': paginates.has_prev,
               'prev_num': paginates.prev_num,
               'has_next': paginates.has_next,
               'next_num': paginates.next_num,
               'iter_pages': list(paginates.iter_pages()),
               'pages': paginates.pages,
               'page': paginates.page,
               'total': paginates.total
               }
        return {'category': category.to_json(), 'paginate': pga}


@faq.route("/search_issue_key", methods=['GET', 'POST'], endpoint='search_issue_key')
def search_issue_key():
    if request.method == 'POST':
        page = int(request.form.get('page', 1))
        pages = int(request.form.get('pages', 6))
        key = request.form.get('key')
        category = Category.query.first_or_404()
        paginates = Issue.query.filter(or_(Issue.title.like('%{0}%'.format(
            key)), Issue.body.like('%{0}%'.format(key)))).paginate(page, pages, error_out=False)
        pga = {'items': [issue.to_json() for issue in paginates.items],
               'has_prev': paginates.has_prev,
               'prev_num': paginates.prev_num,
               'has_next': paginates.has_next,
               'next_num': paginates.next_num,
               'iter_pages': list(paginates.iter_pages()),
               'pages': paginates.pages,
               'page': paginates.page,
               'total': paginates.total
               }
        return {'category': category.to_json(), 'paginate': pga}


@faq.route("/show_issue", methods=['GET', 'POST'], endpoint='show_issue')
@login_required
def show_issue():
    if request.method == 'POST':
        ca = request.form.get('ca')
        page = int(request.form.get('page', 1))
        pages = int(request.form.get('pages', 3))
        category = Category.query.filter_by(name=ca).first_or_404()
        paginates = Issue.query.filter_by(category_id=category.id).paginate(
            page, pages, error_out=False)
        pga = {'items': [issue.to_json() for issue in paginates.items],
               'has_prev': paginates.has_prev,
               'prev_num': paginates.prev_num,
               'has_next': paginates.has_next,
               'next_num': paginates.next_num,
               'iter_pages': list(paginates.iter_pages()),
               'pages': paginates.pages,
               'page': paginates.page,
               'total': paginates.total
               }
        return {'category': category.to_json(), 'paginate': pga}

    page = int(request.args.get('page', 1))
    pages = int(request.args.get('pages', 3))
    paginates = Issue.query.order_by('id').paginate(
        page, pages, error_out=False)
    categorys = Category.query.all()
    return render_template('issue/show_issue.html', paginate=paginates, faq='bg-success', categorys=categorys)


@faq.route("/create_issue", methods=("GET", "POST"), endpoint='create_issue')
def create_issue():
    """Create a new post for the current user."""
    form = IssueForm()
    if request.method == "POST":
        if form.validate_on_submit():
            return redirect(url_for("faq.show_issue"))
    categorys = Category.query.all()
    return render_template("issue/create_issue.html", categorys=categorys)


@faq.route("/<int:id>/update_issue", methods=("GET", "POST"), endpoint='update_issue')
def update_issue(id):
    """Update a post if the current user is the author."""
    issue = get_issue(id)
    categorys = Category.query.all()
    form = IssueForm()
    if request.method == "POST":
        if form.validate_on_submit():
            return redirect(url_for("faq.show_issue"))
    return render_template("issue/update_issue.html", issue=issue, categorys=categorys)


@faq.route("/<int:id>/delete_issue", methods=("POST",), endpoint='delete_issue')
def delete_issue(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    issue = get_issue(id)
    db.session.delete(issue)
    db.session.commit()
    return redirect(url_for("faq.show_issue"))


@faq.route('/contact', methods=['GET', 'POST'], endpoint='contact')
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            msg = Message(form.subject.data, recipients=[
                          "littleshenyun@outlook.com"])
            msg.body = "From: %s <%s> %s " % (
                form.name.data, form.email.data, form.message.data)
            msg.html = "<b>testing</b>"
            mail.send(msg)
            return render_template('issue/contact.html', success=True)
    return render_template('issue/contact.html', form=form)


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template_txt, template_html=None, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject)
    msg.sender = app.config['MAIL_USERNAME']
    msg.recipients = [to]

    if not template_html:
        template_html = template_txt
    msg.body = render_template(template_txt, **kwargs)
    msg.html = render_template(template_html, **kwargs)

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


def send_confirm_email(to, user, token):
    title = 'Simple Blog confirm user email'
    template_txt = 'useraccounts/email/confirm.txt'
    template_html = 'useraccounts/email/confirm.html'

    return send_email(to, title, template_txt, template_html, user=user, token=token)


def send_reset_password_mail(to, user, token):
    title = 'Simple Blog reset user password'
    template_txt = 'useraccounts/email/reset_password.txt'
    template_html = 'useraccounts/email/reset_password.html'

    return send_email(to, title, template_txt, template_html, user=user, token=token)


def get_clean_html_content(html_content):
    allow_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                  'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'p', 'hr', 'img',
                        'table', 'thead', 'tbody', 'tr', 'th', 'td',
                        'sup', 'sub']
    allow_attrs = {'*': ['class'],
                   'a': ['href', 'rel', 'name'],
                   'img': ['alt', 'src', 'title'], }
    html_content = bleach.linkify(bleach.clean(
        html_content, tags=allow_tags, attributes=allow_attrs, strip=True))
    return html_content


#     content_html = Markdown.markdown(self.content, extras=['code-friendly', 'fenced-code-blocks', 'tables'])
#     content_html = get_clean_html_content(self.content_html)

#     gavatar_id = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()



# 坐标操作图片处理的按钮路由
@faq.route('/img_operate', methods=['POST'],endpoint='img_operate')
def img_operate():
    data = json.loads(request.form.get('data'))
    x = data['x']
    y = data['y']
    print(x,y)
    img = 'http://localhost:5000/static/pic/1.jpg'
    return jsonify({"success": 200, "img": img, "x": x, "y": y})