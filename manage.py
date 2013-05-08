from flaskext.script import Manager

from kidvm import app, models

manager = Manager(app)

@manager.command
def allowances():
    """Add due allowances"""
    models.run_allowance()

if __name__ == "__main__":
    manager.run()