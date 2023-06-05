import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

#认证蓝图
bp = Blueprint('auth', __name__, url_prefix='/auth')

#认证蓝图的注册视图
#如果用户提交了表单，那么 request.method 将会是 'POST' 。这种情况下，将会验证用户的输入。
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        #如果用户对账号和密码的输入为空，则会提示错误信息
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        #如果用户账号和密码不为空，则注册
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            #如果用户的账号在数据库中已经存在，会提示“已注册”
            except db.IntegrityError:
                error = f"User {username} is already registered."
            #正常注册完毕，进入登录视图
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

#认证蓝图的登录视图
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        #对账号和密码的检测，即：是否输入了正确的账号和密码，错误输入会提示错误信息
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        #正确登陆后，将用户的 id 储存在 session 中，可以被后续的请求使用。 
        #请每个请求的开头，如果用户已登录，那么其用户信息应当被载入，以使其可用于其他视图。
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


#在每一次用户请求的时候，都会调用这个函数，以检测用户是否已经登录
#并将登录的用户信息存储到 Flask 应用上下文对象 g 中，以便在请求处理中使用。
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


#退出登录（注销），注意，不是将数据库中的用户信息删除（注销账号）。
#只是将session对应的id清除了，也就是当前没有用户登录信息。
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


#在其他视图中检测用户是否登录，若未登录则进入登录视图
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view