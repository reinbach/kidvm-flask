from flaskext import wtf
from flaskext.wtf.html5 import EmailField, EmailInput, DecimalField
from flaskext.mail import Mail, Message

from kidvm import models, app

mail = Mail(app)


class SignIn(wtf.Form):
    email = EmailField(
        'Email Address',
        [wtf.validators.Email()],
        widget=EmailInput(),
    )
    password = wtf.PasswordField('Password', [wtf.validators.Required()])

    def login(self):
        return models.login(self.email.data, self.password.data)


class Register(wtf.Form):
    email = EmailField(
        'Email Address',
        [wtf.validators.Email()],
        widget=EmailInput()
    )
    password = wtf.PasswordField('Password', [
        wtf.validators.Required(),
        wtf.validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = wtf.PasswordField('Confirm Password')

    def register(self):
        return models.create_user(self.email.data, self.password.data)


class ForgotPassword(wtf.Form):
    email = EmailField(
        'Email Address',
        [wtf.validators.Email()],
        widget=EmailInput()
    )

    def reset_password(self):
        return models.reset_password(self.email.data)


class ResetPassword(wtf.Form):
    password = wtf.PasswordField('Password', [
        wtf.validators.Required(),
        wtf.validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = wtf.PasswordField('Confirm Password')


class Contact(wtf.Form):
    subject = wtf.TextField('Subject', [wtf.validators.Length(min=3, max=100)])
    from_email = EmailField(
        'From Email',
        [wtf.validators.Email(), wtf.validators.optional()],
        widget=EmailInput(),
        description=u'optional'
    )
    message = wtf.TextAreaField('Message', [wtf.validators.Length(min=10)])

    def send(self):
        msg = Message(
            self.subject.data,
            recipients=[app.config['DEFAULT_MAIL_SENDER']],
            sender=self.from_email.data if self.from_email.data else app.config['DEFAULT_MAIL_SENDER']
        )
        msg.body = "%s" % self.message.data
        mail.send(msg)


class Kid(wtf.Form):
    name = wtf.TextField('Name', [wtf.validators.Length(min=3, max=100)])
    opening_balance = DecimalField(
        'Starting Balance',
        [wtf.validators.NumberRange(min=0.0)]
    )
    opening_balance_date = wtf.DateField('Starting Date', format="%m/%d/%Y")

    def save(self, user, kid_id=None):
        kid = models.Kid(
            self.name.data,
            self.opening_balance.data,
            self.opening_balance_date.data
        )
        if kid_id:
            kid.id = kid_id
        return kid.save(user)


class Allowance(wtf.Form):
    kid_id = wtf.SelectField(u'Kid', coerce=int)
    period_day = wtf.SelectField(
        u'Day',
        choices=models.get_day_options('weekly'),
    )
    period = wtf.SelectField(
        u'Frequency',
        choices=models.PERIOD_CHOICES
    )
    amount = DecimalField('Amount', [wtf.validators.NumberRange(min=0.0)])

    def validate_period_day(form, field):
        if not (0 < int(field.data) < 32):
            raise wtf.ValidationError("Day needs to be between 1 and 31.")

    def set_kid_choices(self, user):
        self.kid_id.choices = models.get_kids(user)

    def save(self, user, allowance_id=None):
        allowance = models.Allowance(
            self.kid_id.data,
            self.period.data,
            self.period_day.data,
            self.amount.data
        )
        if allowance_id:
            allowance.id = allowance_id
        return allowance.save(user)


class Transaction(wtf.Form):
    kid_id = wtf.SelectField(u'Kid', coerce=int)
    transaction_date = wtf.DateField(u'Date', format="%m/%d/%Y")
    amount = DecimalField(u'Amount', [wtf.validators.NumberRange()])
    withdrawal = wtf.BooleanField(u'Withdrawal')
    category = wtf.TextField(u'Category', [wtf.validators.Length(min=3, max=150)])
    description = wtf.TextAreaField(u'Description')

    def __init__(self, *args, **kwargs):
        super(Transaction, self).__init__(*args, **kwargs)

    def set_kid_choices(self, user):
        self.kid_id.choices = models.get_kids(user)

    def save(self, user, transaction_id=None):
        transaction = models.Transaction(
            self.kid_id.data,
            self.transaction_date.data,
            self.amount.data,
            self.category.data,
            self.description.data
        )
        if transaction_id:
            transaction.id = transaction_id
        return transaction.save(user.account)
