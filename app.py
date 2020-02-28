from flask import Flask, url_for

app = Flask(__name__)

@app.route('/')
def hello() -> str:
    return '<h1>你好，龙猫！</h1><img src="http://helloflask.com/totoro.gif">'

@app.route('/user/<name>')
def user_page(name: str) -> str:
    return 'User %s' % name

@app.route('/test')
def test_url_for() -> str:
    print(url_for('hello'))
    print(url_for('user_page', name = 'BigYe'))
    print(url_for('user_page', name = 'WillWang'))
    print(url_for('test_url_for'))
    print(url_for('test_url_for', num = 2))
    return 'Test page'
