from flask import Flask, url_for, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'CallMeBigYe' #开发时可以随意，部署是采用随机字符且不明文写在代码中
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin): #模型类，数据库表的对象关系映射。
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password) #将密码进行hash加密后保存变量
    def validate_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password) #返回bool值

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

@app.context_processor
def inject_user() -> dict:
    user = User.query.first()
    return dict(user=user)

@app.errorhandler(404) #传入要处理的错误代码
def page_not_found(e) -> 'html':
    return render_template('404.html'), 404

@app.route('/', methods=['GET', 'POST'])
def index() -> 'html':
    if request.method == 'POST':
        if not current_user.is_authenticated: #判断登录状态
            return redirect(url_for('index'))
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('请输入适合的字段长度') #显示错误信息
            return redirect(url_for('index')) #页面重定向
        movie = Movie(title=title, year=year) #调用model类
        db.session.add(movie)
        db.session.commit()
        flash('添加成功')
        return redirect(url_for('index'))
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id) -> 'html':
    movie = Movie.query.get_or_404(movie_id) #返回对应主键的记录，如没有则返回404
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('请输入适合的字段长度')
            return redirect(url_for('edit', movie_id=movie_id))
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('更新成功')
        return redirect(url_for('index'))
    return render_template('edit.html', movie=movie)

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required #登录保护
def delete(movie_id) -> 'html':
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('删除成功')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login() -> 'html':
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('请输入用户名或密码')
            return redirect(url_for('login'))
        user = User.query.first()
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('登录成功')
            return redirect(url_for('index'))
        flash('用户名或密码错误')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout() -> 'html':
    logout_user()
    flash('再见')
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings() -> 'html':
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('输入错误')
            return redirect(url_for('settings'))
        current_user.name = name
        db.session.commit()
        flash('设置更新成功')
        return redirect(url_for('index'))
    return render_template('settings.html')

@login_manager.user_loader
def load_user(user_id) -> 'model':
    user = User.query.get(int(user_id))
    return user


@app.cli.command() #注册为命令
def forge():
    db.create_all()
    name = '我，大烨'
    movielist = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    user = User(name=name)
    db.session.add(user)
    for m in movielist:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done.')

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.') #设置选项
def initdb(drop): #重建数据库表
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    db.create_all()
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='管理员')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')
