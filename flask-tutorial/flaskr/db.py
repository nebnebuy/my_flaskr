#sqlite3是一款轻量级数据库，支持sql语句
import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

#建立数据库连接
def get_db():
    #g 是一个特殊对象，独立于每一个请求。
    #g 可以多次使用，而不用在同一个请求中每次调用 get_db 时都创建一个新的连接。
    if 'db' not in g:
        #连接数据库
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


#关闭数据库连接
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        #关闭连接
        db.close()

#获取数据库连接对象，打开schema.sql，读取其中的 SQL 语句，并使用 db.executescript() 方法执行这些 SQL 语句，从而创建数据库中的表格。
def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


#调用了 init_db 函数，初始化数据库，并返回一条消息表示初始化完成。
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


#调用上述方法，用于关闭数据库连接并初始化数据库
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)