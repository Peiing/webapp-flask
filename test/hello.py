#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, url_for, session, redirect, flash 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

from flask_script import Manager

manager = Manager(app)

from flask_bootstrap import Bootstrap

bootstrap = Bootstrap(app)

from flask_moment import Moment
from datetime import datetime

moment = Moment(app)

from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required


class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


from flask_sqlalchemy import SQLAlchemy 

basedir = os.path.abspath(os.path.dirname(__file__)) 
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'data.sqlite') 
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
 
db = SQLAlchemy(app)

class Role(db.Model): 
    __tablename__ = 'roles' 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(64), unique=True) 

    users = db.relationship('User', backref='role', lazy='dynamic') 
 
    def __repr__(self): 
        return '<Role %r>' % self.name 
 
class User(db.Model): 
    __tablename__ = 'users' 
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(64), unique=True, index=True)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
 
    def __repr__(self): 
        return '<User %r>' % self.username

from flask_script import Shell

def make_shell_context(): 
    return dict(app=app, db=db, User=User, Role=Role) 
manager.add_command("shell", Shell(make_context=make_shell_context))

from flask_migrate import Migrate, MigrateCommand 

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

from flask_mail import Mail, Message 

app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 25 
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN') 
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]' 
app.config['FLASKY_MAIL_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)
 
def send_email(to, subject, template, **kwargs): 
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, 
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to]) 
    msg.body = render_template(template + '.txt', **kwargs) 
    msg.html = render_template(template + '.html', **kwargs) 
    mail.send(msg)

@app.route('/', methods=['GET', 'POST'])
def index():
    name = None
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name') 
        if old_name is not None and old_name != form.name.data: 
            flash('Looks like you have changed your name!') 
        user = User.query.filter_by(username=form.name.data).first() 
        if user is None: 
            user = User(username=form.name.data) 
            db.session.add(user) 
            session['known'] = False 
            if app.config['FLASKY_ADMIN']: 
                send_email(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user) 
        else: 
            session['known'] = True 
        session['name'] = form.name.data 
        form.name.data = '' 
        return redirect(url_for('index')) 
    return render_template('index.html', form=form,  name=session.get('name'), known = session.get('known', False), current_time=datetime.utcnow())


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    # app.run()
    manager.run()
