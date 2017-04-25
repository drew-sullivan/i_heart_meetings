import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'ihm.db'),
    SECRET_KEY='W2zV9VyDkc%(X%uZc?x.T;7EA8D9xdmeW3LzAGeWgxt2h2bji6;^DmU(&6KkYaYX',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('IHM_SETTINGS', silent=True)

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv
