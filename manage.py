from config_studio import create_app, db
from flask_script import Manager, Server
from waitress import serve


"""
SQL初始化
"""
app = create_app()
manager = Manager(app)

manager.add_command('runserver', Server(
    use_debugger=True,
    use_reloader=True,
    host='127.0.0.1',
    port=80))

def db_init():
    from config_studio import create_app, db
    db.create_all(app = create_app())

if __name__ == "__main__":
    # serve(app,host='127.0.0.1', port=80)
    # db_init()
    manager.run()
