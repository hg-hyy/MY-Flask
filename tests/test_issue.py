import pytest

from app.model import db,Issue


def test_index(client, auth):
    response = client.get("/")
    assert b"Log In" in response.data
    assert b"Register" in response.data

    auth.login()
    response = client.get("/")
    assert b"test title" in response.data
    assert b"by test on 2018-01-01" in response.data
    assert b"test\nbody" in response.data
    assert b'href="/1/update_issue"' in response.data


@pytest.mark.parametrize("path", ("/create", "/1/update_issue", "/1/delete_issue"))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "http://localhost/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():

        Issue.author_id = 2
        db.session.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post("/1/update_issue").status_code == 403
    assert client.post("/1/delete_issue").status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/update_issue"' not in client.get("/").data


@pytest.mark.parametrize("path", ("/2/update_issue", "/2/delete_issue"))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get("/create").status_code == 200
    client.post("/create", data={"title": "created", "body": ""})

    with app.app_context():
        count = Issue.query.count()
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get("/1/update_issue").status_code == 200
    client.post("/1/update_issue", data={"title": "updated", "body": ""})

    with app.app_context():
        issue = Issue.query.filter_by(id =1).first()
        assert issue["title"] == "updated"


@pytest.mark.parametrize("path", ("/create", "/1/update_issue"))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={"title": "", "body": ""})
    assert b"Title is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/1/delete_issue")
    assert response.headers["Location"] == "http://localhost"

    with app.app_context():
        issue = Issue.query.filter_by(id =1).first()
        assert issue is None
