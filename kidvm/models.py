import base64
import datetime
import hashlib
import time

from flaskext.mail import Mail, Message
from flaskext.sqlalchemy import SQLAlchemy

from kidvm import app

db = SQLAlchemy(app)
mail = Mail(app)

#===============================================================================
class AuthUser(db.Model):
    """The User who accesses the system

    Basic information on the user
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(150))
    created = db.Column(db.DateTime)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    account = db.relationship('Account', backref=db.backref('account', lazy='dynamic'))
    last_login = db.Column(db.DateTime)

    #---------------------------------------------------------------------------
    def __init__(self, email, password, account=None):
        self.email = email
        self.hash_password(password)
        self.account = account

    #---------------------------------------------------------------------------
    def __repr__(self):
        return '<User %r>' % self.email

    #---------------------------------------------------------------------------
    def hash_password(self, password):
        self.password = hashlib.sha224(password).hexdigest()

    #---------------------------------------------------------------------------
    def get_uid(self):
        """Create a unique id for the user

        The unique id is based on the id, last login and password of the user
        So if any of those change, the uid is no longer valid
        """
        value = unicode(self.id) + self.password + app.config['SECRET_KEY']
        if self.last_login:
            value += self.last_login.strftime('%Y-%m-%d %H:%M:%S')
        return hashlib.sha224(value).hexdigest()[::2]
        
    
#===============================================================================
class Account(db.Model):
    """The Account is the base of everything

    Everything is related to the account in some manner or form.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    authuser = db.relationship(
        'AuthUser',
        backref='user',
        lazy='dynamic',
        uselist=False
    )
    plan_key = db.Column(db.String(50), default='BASIC')
    is_active = db.Column(db.Boolean)
    created = db.Column(db.DateTime)
    kids = db.relationship('Kid', backref='account', lazy='dynamic')
    categories = db.relationship('Category', backref='account', lazy='dynamic')

    #---------------------------------------------------------------------------
    def __init__(self, name):
        self.name = name

    #---------------------------------------------------------------------------
    def __repr__(self):
        return '<Account %r>' % self.name

    
#===============================================================================
class Kid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    name = db.Column(db.String(100))
    opening_balance = db.Column(db.Float)
    opening_balance_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean)
    created = db.Column(db.DateTime)
    allowances = db.relationship('Allowance', backref='kid', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='kid', lazy='dynamic')

    #---------------------------------------------------------------------------
    def __init__(self, name, opening_balance, opening_balance_date):
        self.name = name
        self.opening_balance = opening_balance
        self.opening_balance_date = opening_balance_date

    #---------------------------------------------------------------------------
    def __repr__(self):
        return '<Kid %r (%r)>' % (self.name, self.account)

    #---------------------------------------------------------------------------
    def save(self, user):
        if self.id:
            if not valid_kid(self.id, user):
                return False

            db.session.execute(
                """
                UPDATE kid
                SET name = :name, opening_balance = :amount, opening_balance_date = :date
                WHERE id = :id
                """,
                {
                    'name': self.name,
                    'amount': self.opening_balance,
                    'date': self.opening_balance_date,
                    'id': self.id
                }
            )
        else:
            self.account_id = user.account_id
            self.is_active = True
            self.created = datetime.datetime.now()
            db.session.add(self)
        db.session.commit()
        return True

    #---------------------------------------------------------------------------
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        
    #---------------------------------------------------------------------------
    @property
    def balance(self):
        """Balance of opening balance and all transactions

        Take opening balance and add/substract the transactions for the kid
        """
        balance = self.opening_balance
        for trx in Transaction.query.filter_by(kid_id=self.id):
            balance += trx.amount
        return balance

    #---------------------------------------------------------------------------
    @property
    def allowance_total(self):
        """Allowances totaled up

        The sum of all active allowances
        """
        total = 0
        for allowance in self.allowances:
            if allowance.is_active:
                total += allowance.amount
        return total

    #---------------------------------------------------------------------------
    @property
    def history(self):
        trxs = self.transactions.order_by('transaction_date')
        if not trxs:
            return {}
        # if less than 60 days old go by days else by weeks
        days = abs(datetime.date.today() - trxs.first().transaction_date).days
        dataset = {}
        total = self.opening_balance
        if days <= 30:
            for trx in trxs:
                if dataset and not dataset.get(trx.transaction_date, False):
                    while prev != trx.transaction_date:
                        prev = prev + datetime.timedelta(1)
                        dataset[prev] = total
                dataset[trx.transaction_date] = total = total + trx.amount
                prev = trx.transaction_date
            if trx.transaction_date < datetime.date.today():
                cur = trx.transaction_date
                while cur < datetime.date.today():
                    cur = cur + datetime.timedelta(1)
                    dataset[cur] = total
        else:
            for trx in trxs:
                month = datetime.date(
                    trx.transaction_date.year,
                    trx.transaction_date.month,
                    1
                )
                if dataset and not dataset.get(month, False):
                    while prev != month:
                        if prev.month == 12:
                            new_year = prev.year + 1
                            new_month = 1
                        else:
                            new_year = prev.year
                            new_month = prev.month + 1
                        prev = datetime.date(new_year, new_month, 1)
                        dataset[prev] = total
                dataset[month] = total = total + trx.amount
                prev = month
            if trx.transaction_date < datetime.date.today():
                cur = datetime.date(trx.transaction_date.year, trx.transaction_date.month, 1)
                cur_month = datetime.date(
                    datetime.date.today().year,
                    datetime.date.today().month,
                    1
                )
                while cur < cur_month:
                    if cur.month == 12:
                        new_cur_year = cur.year + 1
                        new_cur_month = 1
                    else:
                        new_cur_year = cur.year
                        new_cur_month = cur.month + 1
                    cur = datetime.date(new_cur_year, new_cur_month, 1)
                    dataset[cur] = total
        sorted_list = dataset.items()
        sorted_list.sort()
        final_list = []
        for day, amount in sorted_list:
            final_list.append((time.mktime(day.timetuple()), amount))
        return final_list

        
#===============================================================================
class Allowance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kid_id = db.Column(db.Integer, db.ForeignKey('kid.id'))
    period = db.Column(db.String(20))
    period_day = db.Column(db.Integer)
    amount = db.Column(db.Float)
    is_active = db.Column(db.Boolean)
    created = db.Column(db.DateTime)
    transactions = db.relationship('Transaction', backref='allowance', lazy='dynamic')

    #---------------------------------------------------------------------------
    def __init__(self, kid_id, period, period_day, amount):
        self.kid_id = kid_id
        self.period = period
        self.period_day = period_day
        self.amount = amount

    #---------------------------------------------------------------------------
    def __repr__(self):
        return '<Allowance %r (%r)' % (self.amount, self.kid)

    #---------------------------------------------------------------------------
    def save(self, user):
        """Ensure that the kid is related to the user provided"""
        if not valid_kid(self.kid_id, user):
            return False

        # check whether saving or updating
        if self.id:
            db.session.execute(
                """
                UPDATE allowance
                SET kid_id = :kid_id, period = :period, period_day = :period_day,
                    amount = :amount
                WHERE id = :id
                """,
                {
                    'kid_id': self.kid_id,
                    'period': self.period,
                    'period_day': self.period_day,
                    'amount': self.amount,
                    'id': self.id
                }
            )
        else:
            self.is_active = True
            self.created = datetime.datetime.now()
            db.session.add(self)
        db.session.commit()
        return True

    #---------------------------------------------------------------------------
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        
        
#===============================================================================
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    name = db.Column(db.String(150))
    transactions = db.relationship(
        'Transaction',
        backref='category',
        lazy='dynamic',
        cascade_backrefs=False
    )

    #---------------------------------------------------------------------------
    def __init__(self, account_id, name):
        self.account_id = account_id
        self.name = name

    #---------------------------------------------------------------------------
    def __repr__(self):
        return u'%s' % self.name

    #---------------------------------------------------------------------------
    def save(self):
        """Save Category

        Check first whether a category exists with the same name, if so use that
        otherwise save a new record
        """
        for category in Category.query.filter_by(account_id=self.account_id):
            if self.name.lower().strip() == category.name.lower():
                self = category
                return category
        db.session.add(self)
        db.session.commit()
        return self
        
    
#===============================================================================
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kid_id = db.Column(db.Integer, db.ForeignKey('kid.id'))
    transaction_date = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    description = db.Column(db.Text)
    allowance_id = db.Column(db.Integer, db.ForeignKey('allowance.id'))
    modified = db.Column(db.DateTime)
    created = db.Column(db.DateTime)

    #---------------------------------------------------------------------------
    def __init__(self, kid_id, trx_date, amount, category, description):
        self.kid_id = kid_id
        self.transaction_date = trx_date
        self.amount = amount
        self.category = category
        self.description = description

    #---------------------------------------------------------------------------
    def __repr__(self):
        return '<Transaction: %r (%r)>' % (self.amount, self.kid)

    #---------------------------------------------------------------------------
    def save(self, user):
        if not valid_kid(self.kid_id, user):
            return False

        # check whether inserting or updating
        if self.id:
            db.session.execute(
                """
                UPDATE transaction
                SET kid_id = :kid_id, transaction_date = :date, amount = :amount,
                    category_id = :category_id, description = :description,
                    modified = :modified
                WHERE id = :id
                """,
                {
                    'kid_id': self.kid_id,
                    'date': self.transaction_date,
                    'amount': self.amount,
                    'category_id': self.category.id,
                    'description': self.description,
                    'modified': datetime.datetime.now(),
                    'id': self.id
                }
            )
        else:
            self.created = datetime.datetime.now()
            db.session.add(self)
        db.session.commit()
        return True

    #---------------------------------------------------------------------------
    def delete(self):
        db.session.delete(self)
        db.session.commit()


#---------------------------------------------------------------------------
def create_user(email, password):
    """Create an account and user

    All users need to be associated with an account
    So first check whether the user exists in the system already
    If not, then create an account and a user and related the user to the
    account
    """
    email_used = AuthUser.query.filter_by(email=email).first()
    if email_used:
        return False, "Email address has already been used"
    account = Account(email)
    account.plan_key = 'BASIC'
    account.is_active = True
    account.created = datetime.datetime.now()
    db.session.add(account)
    user = AuthUser(email, password, account)
    user.created = datetime.datetime.now()
    db.session.add(user)
    db.session.commit()
    return user.id, None

#---------------------------------------------------------------------------
def login(email, password):
    """Log user in a set pertinent info

    If user exists, update last login of record
    """
    user = AuthUser(email, password)
    user = AuthUser.query.filter_by(email=user.email, password=user.password).first()
    if user:
        db.session.execute(
            "UPDATE auth_user SET last_login = :date WHERE id = :id",
            {'date': datetime.datetime.now(), 'id': user.id}
        )
        db.session.commit()
        return user.id
    return False

#---------------------------------------------------------------------------
def reset_password(email):
    """Start process of reseting user password

    Check if we have a record for the email provided
    If so, generate a unique key based on the last login and password for the user
    Send a link with this unique key in it to the user
    """
    user = AuthUser.query.filter_by(email=email).first()
    if not user:
        return False
    # Generate email with unique link
    msg = Message(
        "Password Reset Link",
        recipients=[user.email]          
    )
    msg.body = "Click on this link and following the instructions to reset your "
    "password\n\n%s%s?uid=%s-%s" % (
        app.config['SITE_URI'],
        "/reset/password/",
        user.id,
        user.get_uid()
    )
    mail.send(msg)
    return True

#---------------------------------------------------------------------------
def get_user_from_uid(uid):
    """Return User object from uid

    If uid is not valid return False
    """
    id, tmp = uid.split('-')
    user = AuthUser.query.filter_by(id=id).first()
    if user and user.uid == uid:
        return True
    return False

#---------------------------------------------------------------------------
def valid_kid(kid_id, user):
    if kid_id in [x.id for x in Kid.query.filter_by(account_id=user.account_id)]:
        return True
    return False

#---------------------------------------------------------------------------
def get_kids(user):
    return [(k.id, k.name) for k in Kid.query.filter_by(account_id=user.account_id)]