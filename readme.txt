python3.6.8


flask run


登录：
admin
12!@QWqw


model.py
删除2处：151、181 ,overlaps="Category,issue"

forms.py
--- from wtforms import EmailField
+++ from wtforms.fields.html5 import EmailField