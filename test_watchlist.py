import unittest
from app import app, db, Movie, User, forge, initdb

class WatchlistTestCase(unittest.TestCase):

    def setUp(self): #测试用例调用前执行
        #更新配置
        app.config.update(
            TESTING = True, #开启测试模式
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' #使用SQLite的内存数据库
        )
        #创建数据库和表
        db.create_all()
        #创建测试数据
        user = User(name='测试账号', username='test')
        user.set_password('123')
        movie = Movie(title = 'Test Movie Title', year = '2020')
        #使用add_all()方法一次添加多个model类实例，传入列表
        db.session.add_all([user, movie])
        db.session.commit()
        self.client = app.test_client() #创建测试客户端
        self.runner = app.test_cli_runner() #创建测试命令运行器

    def tearDown(self):
        db.session.remove() #清除数据库会话
        db.drop_all() #删除数据库表

    #测试程序需实例是否存在
    def test_app_exitst(self):
        self.assertIsNotNone(app)

    #测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    #测试404页
    def test_404_page(self):
        response = self.client.get('nothing')
        data = response.get_data(as_text=True)
        self.assertIn('您访问的页面不存在 - 404', data)
        self.assertIn('返回首页', data)
        self.assertEqual(response.status_code, 404)

    #测试主页
    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True) #as_text为True时，可以获取Unicode格式的相应主体
        self.assertIn('测试账号的电影清单', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    #辅助方法，用于登录用户
    def login(self):
        self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True) #follow_redirects=True跟随重定向，最终返回的是重定向后的响应

    #测试创建条目
    def test_create_item(self):
        self.login()

        #测试创建条目操作
        response = self.client.post('/', data=dict(
            title = 'New Movie',
            year = '1900'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('添加成功', data)
        self.assertIn('New Movie', data)

        #测试创建条目操作，但电影标题为空
        response = self.client.post('/', data=dict(
            title = '',
            year = '2002'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('添加成功', data)
        self.assertIn('请输入适合的字段长度', data)

        #测试创建条目操作，但上映年份为空
        response = self.client.post('/', data=dict(
            title = 'New Movie 2',
            year = ''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('添加成功', data)
        self.assertIn('请输入适合的字段长度', data)

    #测试更新条目
    def test_update_item(self):
        self.login()

        #测试更新页面
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('编辑', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2020', data)

        #测试更新条目操作
        response = self.client.post('/movie/edit/1', data=dict(
            title = 'New Movie Edited',
            year = '2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('更新成功', data)
        self.assertIn('New Movie Edited', data)

        #测试更新条目操作，但电影名称为空
        response = self.client.post('/movie/edit/1', data=dict(
            title = '',
            year = '1988'  
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('更新成功', data)
        self.assertIn('请输入适合的字段长度', data)

        #测试更新条目操作，但上映年份为空
        response = self.client.post('/movie/edit/1', data=dict(
            title = 'New Movie Edited 2',
            year = ''  
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('更新成功', data)
        self.assertNotIn('New Movie Edited 2', data)
        self.assertIn('请输入适合的字段长度', data)

    #测试删除条目
    def test_delete_item(self):
        self.login()

        #测试删除条目操作
        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('删除成功', data)
        self.assertNotIn('Test Movie Title', data)

    #测试登录保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('登出', data)
        self.assertNotIn('设置', data)
        self.assertNotIn('<form method="POST">', data)
        self.assertNotIn('删除', data)
        self.assertNotIn('编辑', data)

    #测试登录
    def test_login(self):
        #测试正确登录
        response = self.client.post('/login', data=dict(
            username = 'test',
            password = '123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('登录成功', data)
        self.assertIn('登出', data)
        self.assertIn('设置', data)
        self.assertIn('编辑', data)
        self.assertIn('<form method="POST">', data)
        self.assertIn('删除', data)

        #测试用错误用户名登录
        response = self.client.post('/login', data=dict(
            username = 'wrong',
            password = '123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('用户名或密码错误', data)

        #测试用空用户名登录
        response = self.client.post('/login', data=dict(
            username = '',
            password = '123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('请输入用户名或密码', data)

        #测试用错误密码登录
        response = self.client.post('/login', data=dict(
            username = 'test',
            password = 'wrong'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('用户名或密码错误', data)

        #测试用空密码登录
        response = self.client.post('/login', data=dict(
            username = 'test',
            password = ''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('请输入用户名或密码', data)

    #测试登出
    def test_logout(self):
        self.login()

        #测试登出操作
        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('再见', data)
        self.assertNotIn('登出', data)
        self.assertNotIn('设置', data)
        self.assertNotIn('<form method="POST">', data)
        self.assertNotIn('删除', data)
        self.assertNotIn('编辑', data)

    #测试设置
    def test_settings(self):
        self.login()

        #测试设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('设置', data)
        self.assertIn('用户名', data)

        #测试更新设置
        response = self.client.post('/settings', data=dict(
            name = '我，大烨'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('设置更新成功', data)
        self.assertIn('我，大烨', data)

        #测试更新设置，用户名为空
        response = self.client.post('/settings', data=dict(
            name = ''  
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('设置更新成功', data)
        self.assertIn('输入错误', data)

    #测试虚拟数据
    def test_forge_command(self):
        result = self.runner.invoke(forge)
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    #测试初始化数据库
    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    #测试生成管理员账户
    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'superadmin', '--password', '123'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'superadmin')
        self.assertTrue(User.query.first().validate_password('123'))

    #测试更新管理员账户
    def test_admin_command_update(self):
        #使用args参数给出完整的命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'superman', '--password', '456'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'superman')
        self.assertTrue(User.query.first().validate_password('456'))

if __name__ == '__main__':
    unittest.main()
