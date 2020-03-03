from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from watchlist import db
from datetime import datetime


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

class MessageBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    content = db.Column(db.String(200))
    ctime = db.Column(db.DateTime, default=datetime.now)
