from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

app.secret_key = app.config['SECRET_KEY']

# Logging setup
# For non debug environments
# - ERROR and up send Emails
# - WARNING and up log to file system
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        '',
        'error@kidvm.com',
        app.config['ADMINS'],
        'Kid VM - Error'
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter('''
    Message type:            %(levelname)s)
    Location:                %(pathname)s:%(lineno)d
    Module:                  %(module)s
    Function:                %(funcName)s
    Time:                    %(asctime)s

    Message:

    %(message)s
    '''))
    file_handler = logging.FileHandler(app.config['ERROR_LOG_FILE'])
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(mail_handler)
    app.logger.addHandler(file_handler)
    

import kidvm.views