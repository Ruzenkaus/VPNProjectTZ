import random
import requests
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
import queue
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.app_context().push()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class RegistrationForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[DataRequired()], render_kw={"placeholder": "Введіть ім'я користувача"})
    password = PasswordField('Пароль', validators=[DataRequired()], render_kw={"placeholder": "Введіть пароль"})
    confirm_password = PasswordField('Підтвердження паролю', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Підтвердіть пароль"})
    submit = SubmitField('Зареєструватися')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Ім\'я користувача вже використовується')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Ваш обліковий запис було створено! Тепер ви можете увійти.', 'success')
        return redirect(url_for('login'))

    return render_template('registration.html', form=form)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Увійти')

class ProxyForm(FlaskForm):
    url = StringField('Посилання', validators=[DataRequired()], render_kw={"placeholder": "Введіть посилання"})
    submit = SubmitField('Проксімізувати')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Успішний вхід', 'success')
            return redirect(url_for('proxy'))

        else:
            flash('Невірне ім\'я користувача або пароль', 'danger')

    return render_template('login.html', form=form)

def check_proxy_availability(proxy, target_url):
    try:
        requests.head(target_url, proxies={'http': proxy, 'https': proxy}, timeout=5)
        return True
    except requests.RequestException:
        return False

@app.route('/proxy', methods=['GET', 'POST'])
@login_required
def proxy():
    form = ProxyForm()

    q = queue.Queue()

    with open('valid_proxies', 'r') as f:
        proxies = f.read().split("\n")
        for p in proxies:
            q.put(p)

    if form.validate_on_submit():
        url = form.url.data
        selected_proxy = None
        while not q.empty():
            proxy = q.get()
            try:
                resp = requests.get(url, proxies={
                    "http": proxy,
                    "https": proxy
                })
            except:
                print("Не спрацював: "+proxy)
                continue
            if resp.status_code == 200:
                selected_proxy = proxy
                break


        if selected_proxy:
            proxies = {'http': selected_proxy, 'https': selected_proxy}
            try:
                response = requests.get(url, proxies=proxies)
                return response.text
            except requests.RequestException as e:
                flash(f'Помилка при зверненні до сервера: {str(e)}', 'danger')
        else:
            flash('Немає доступних проксі-серверів для цього сайту', 'danger')

    if current_user.is_authenticated:
        flash('Ви підключені через проксі. Ваші дії можуть бути відстежені.', 'info')

    return render_template('proxy.html', form=form)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
