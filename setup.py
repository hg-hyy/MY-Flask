import io

from setuptools import find_packages
from setuptools import setup

with io.open("README.rst", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="omdc",
    version="1.0.0",
    url="http://flask.pocoo.org/docs/tutorial/",
    license="BSD",
    maintainer="Pallets team",
    maintainer_email="littlshenyun@outlook.com",
    description="The configuration studio app built in the Flask.",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask",
                      "waitress"
                      "Flask-WTF",
                      "Flask-Cors",
                      "Flask-Mail",
                      "flask-restplus",
                      "Flask-Script",
                      "Flask-SQLAlchemy",
                      "Flask-WTF",
                      "xlrd",
                      "jwt",
                      "requests",
                      "email_validator",
                      "markdown2",
                      "bleach"
                      ],
    extras_require={"test": ["pytest", "coverage"]},
)
