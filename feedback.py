import json
import pdb
import uuid
from datetime import datetime
from urlparse import urlparse
from flask import Flask, render_template, request, session, redirect
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from forms import SignupForm, SigninForm

login_manager = LoginManager()
date_format = '%d-%m-%Y'

app = Flask(__name__)
login_manager.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/fcs.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    domain = db.Column(db.String(100))
    token = db.Column(db.String(100), unique=True)

    def __init__(self, email, password, domain):
        self.email = email
        self.password = generate_password_hash(password)
        self.domain = domain
        self.token = uuid.uuid4().hex

    def __repr__(self):
        return '<User %r>' % self.email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.email)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def as_dict(self):
        return json.dumps({c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != 'password'})

    def active_question(self):
        return Question.query.filter_by(user=self.id, is_active=True).first()


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    added = db.Column(db.DateTime, nullable=False,
                      default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False,
                          default=False)
    reach = db.Column(db.Integer, default=0)

    user = db.Column(db.Integer, db.ForeignKey('user.id'),
                     nullable=False)

    users = db.relationship(User)

    def __repr__(self):
        return '<Question %r>' % self.title

    def as_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'added': datetime.strftime(self.added, date_format),
            'is_active': self.is_active,
            'options': [op.as_dict() for op in Option.query.filter_by(question=self.id)],
            'options_str': ",".join([op.title for op in Option.query.filter_by(question=self.id)]),
            'reach': self.reach,
            'votes': Vote.query.filter_by(question=self.id).count()

        }

    def set_active(self):
        qs = Question.query.filter_by(user=self.user)
        for question in qs:
            question.is_active = False
        self.is_active = True
        db.session.commit()


class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    question = db.Column(db.Integer, db.ForeignKey('question.id'),
                         nullable=False)
    added = db.Column(db.DateTime, nullable=False,
                      default=datetime.utcnow)
    questions = db.relationship(Question)

    def __repr__(self):
        return '<Option %r>' % self.title

    def as_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'added': datetime.strftime(self.added, date_format),
            'votes': Vote.query.filter_by(option=self.id).count()
        }


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Integer, db.ForeignKey('question.id'),
                         nullable=False)
    option = db.Column(db.Integer, db.ForeignKey('option.id'),
                       nullable=False)
    added = db.Column(db.DateTime, nullable=False,
                      default=datetime.utcnow)

    questions = db.relationship(Question)
    options = db.relationship(Option)

    def __repr__(self):
        return '<Option %r>' % self.title

    def as_dict(self):
        return {
            'id': self.id,

            'added': datetime.strftime(self.added, date_format),
        }


@login_manager.user_loader
def load_user(email):
    return User.query.filter_by(email=email).first()


@app.route('/admin')
@login_required
def admin():
    return render_template("admin/panel.html")


@app.route('/admin/dashboard.html')
@login_required
def dashboard():
    return render_template("admin/dashboard.html")


@app.route('/admin/questions.html')
@login_required
def admin_questions():
    return render_template("admin/questions.html")


@app.route('/admin/questions/activate', methods=['POST'])
@login_required
def activate_question():
    id = request.json['id']
    question = Question.query.filter_by(user=current_user.id, id=id).first()
    question.set_active()
    return json.dumps([q.as_dict() for q in Question.query.filter_by(user=current_user.id)])


@app.route('/admin/questions/delete', methods=['POST'])
@login_required
def delete_question():
    id = request.json['id']
    question = Question.query.filter_by(user=current_user.id, id=id).first()
    db.session.delete(question)
    db.session.commit()
    return json.dumps([q.as_dict() for q in Question.query.filter_by(user=current_user.id)])


@app.route('/<string:token>/fmscript.js')
def fmscript(token):
    return render_template("fmscript.js", token=token, domain=urlparse(request.environ['HTTP_REFERER']).netloc)


@app.route('/feedback', methods=['GET', 'POST', 'UPDATE'])
def feedback():
    if request.method == "POST":
        token = request.form['token']
        option = request.form['option']
        user = User.query.filter_by(token=token).first()
        if not user:
            return "token mismatch"
        question = user.active_question()
        vote = Vote(question=question.id, option=option)
        db.session.add(vote)
        db.session.commit()
        session['q' + str(question.id)] = True
        return render_template("feedback.html", token=token, question=question.as_dict(), thankyou=1)
    elif request.method == "GET":
        token = request.args.get('t')
        domain = urlparse(request.environ['HTTP_REFERER']).netloc
        user = User.query.filter_by(token=token, domain=domain).first()
        if not user:
            return "token mismatch %s: %s" % (token, domain)
        question = user.active_question()
        if "q" + str(question.id) in session:
            return render_template("feedback.html", token=token, question=question.as_dict(), exit=1)
        return render_template("feedback.html", token=token, question=question.as_dict())


@app.route('/admin/poll', methods=['GET'])
@login_required
def poll():
    questions = Question.query.filter_by(user=current_user.id).order_by('-is_active')
    data = {'questions': [q.as_dict() for q in questions]}
    data['hash'] = json.dumps(data).encode('base64')
    return json.dumps(data)


@app.route('/admin/questions', methods=['GET', 'POST', 'UPDATE'])
@login_required
def questions():
    if request.method == "POST":
        data = request.json
        question = Question(title=data['title'], user=current_user.id)
        db.session.add(question)
        db.session.commit()
        for option in data['options']:
            if option['title']:
                op = Option(title=option['title'], question=question.id)
                db.session.add(op)
                db.session.commit()

        if 'active' in data and data['active']:
            question.set_active()
            # return json.dumps(question.as_dict())

    questions = Question.query.filter_by(user=current_user.id)

    data = [q.as_dict() for q in questions]
    return json.dumps(data)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        return render_template("index.html", data=request.form)
        # if not 'feedback_completed' in session:
        #   session['feedback_completed'] = False

    return render_template("index.html", session=session)


@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if request.method == "GET":
        return render_template("admin/settings.html", domain=urlparse(request.environ['HTTP_REFERER']).netloc)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if request.method == 'GET':
        return render_template('signin.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect("/admin")
            else:
                return render_template('signin.html', form=form,
                                       error=(("Login Error", ("Invalid email and password combination",)),))
        else:
            return render_template('signin.html', form=form, error=form.errors.items())


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('signup.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                return render_template('signup.html', form=form, error=(("EMAIL", ("Email address already exists",)),))
                # elif User.query.filter_by(domain=form.domain.data).first():
                #   return render_template('signup.html', form=form, error=(("Domain", ("Domain already registered",)),))
            else:
                user = User(form.email.data, form.password.data, form.domain.data)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect("/admin")
        else:

            return render_template('signup.html', form=form, error=form.errors.items())


app.secret_key = "_0\xc3\xbf\xb7\xd9r\x0e\x90n[\xafP\x96\x01h\xae2'\x98\xe9%\x99\xbc"


def init_db():
    db.init_app(app)
    db.app = app
    db.create_all()


if __name__ == '__main__':
    init_db()
    app.run(debug=True, threaded=True)
