from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import LoginForm, UploadCheckForm, GetCheckStatusForm, RegistrationForm
from flask_login import current_user, login_user
from app.models import User, Check
from flask_login import logout_user
from flask_login import login_required
from flask import request
from werkzeug.urls import url_parse

import os, logging, tempfile

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = current_user
    return render_template('index.html', title='Home', user=user, checks=user.checks)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
#see http://www.thamizhchelvan.com/python/simple-file-upload-python-flask/


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/uploadCheck")
@login_required
def uploadCheck():
    form = UploadCheckForm()
    return render_template('upload_check.html', title='Upload a Check', form=form)


@app.route("/handleUploadCheck", methods=['POST'])
@login_required
def handleUploadCheck():
    app.logger.info('handleUploadCheck')
    form = UploadCheckForm()
    if form.is_submitted():
        photo = form.photo
        password = form.password
        logging.debug('received file name: %s password: %s' %(photo.data.filename,password))
        if photo.data.filename != '':
            if os.name == 'nt':
                app.logger.debug('running on windows')
                temp_dir = tempfile.mkdtemp()
                path = os.path.join(temp_dir, photo.data.filename)
                app.logger.debug('saving file to %s' %path)
                photo.data.save(path)

                check = Check(photo=path, amount=form.amount.data, status="Pending", message=form.message.data, user=current_user)
                db.session.add(check)
                db.session.commit()

                app.logger.debug('check added. id = ' + str(check.id))

                flash('check added. id = ' + str(check.id))

                if '.zip' in photo.data.filename:
                    app.logger.debug('zip file uploaded')
                    cmd = '7z x "%s"' %path
                    if password.data != '':
                        cmd += ' -p"%s"' %password.data
                    app.logger.debug('running command %s' %cmd)
                    os.system(cmd)
                else:
                    app.logger.debug('running on linux or mac')

    return redirect(url_for('uploadCheck'))


@app.route("/getCheckStatus", methods=['GET','POST'])
@login_required
def getCheckStatus():
    form = GetCheckStatusForm()
    check_id = request.args.get('check_id', None)
    if check_id:
        check = Check.query.filter_by(id=check_id).first()
        if check is None:
            flash('Check with ID ' + str(check_id) + ' not found')
            return redirect(url_for('getCheckStatus'))
        flash('Check with ID ' + str(check_id) + ' found. Amount - ' + str(check.amount) +
              '. Message - ' + check.message + '. Status - ' + check.status)
    return render_template('get_check_status.html', title='Get Check Status', form=form)
