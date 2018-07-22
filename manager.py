#!/usr/bin/env python
import os
from app import create_app,db
from app.models import User,Role,Permission,Post,Comment
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand,upgrade

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app,db)

def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role,Post=Post,Comment=Comment)

manager.add_command('shell',Shell(make_context=make_shell_context))
manager.add_command('db',MigrateCommand)

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # migrate database to latest revision
    upgrade()

    # create or update user roles
    Role.insert_roles()


if __name__ == '__main__':
    manager.run()
