from app import create_app, db
from flask_script import Manager, Server
from waitress import serve


app = create_app()
manager = Manager(app)

manager.add_command('runserver', Server(
    use_debugger=True,
    use_reloader=True,
    host='127.0.0.1',
    port=80))


if __name__ == "__main__":
    """
    Production

    """
    # serve(app,host='127.0.0.1', port=80)

    """
    Development

    """
    app.run()
