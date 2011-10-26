from flaskext import wtf
from flaskext.wtf.html5 import EmailField, EmailInput, DecimalField

from kidvm import models

#===============================================================================
class SignIn(wtf.Form):
    email = EmailField(
        'Email Address',
        [wtf.validators.Email()],
        widget=EmailInput(),
    )
    password = wtf.PasswordField('Password', [wtf.validators.Required()])

    #---------------------------------------------------------------------------
    def login(self):
        return models.login(self.email.data, self.password.data)

    
#===============================================================================
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

    #---------------------------------------------------------------------------
    def register(self):
        return models.create_user(self.email.data, self.password.data)

        
#===============================================================================
class ForgotPassword(wtf.Form):
    email = EmailField(
        'Email Address',
        [wtf.validators.Email()],
        widget=EmailInput()
    )

    #---------------------------------------------------------------------------
    def reset_password(self):
        return models.reset_password(self.email.data)

    
#===============================================================================
class ResetPassword(wtf.Form):
    password = wtf.PasswordField('Password', [
        wtf.validators.Required(),
        wtf.validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = wtf.PasswordField('Confirm Password')

    
#===============================================================================
class Kid(wtf.Form):
    name = wtf.TextField('Name', [wtf.validators.Length(min=3, max=100)])
    opening_balance = DecimalField(
        'Starting Balance',
        [wtf.validators.NumberRange(min=0.0)]
    )
    opening_balance_date = wtf.DateField('Starting Date', format="%m/%d/%Y")

    #---------------------------------------------------------------------------
    def save(self, user, kid_id=None):
        kid = models.Kid(
            self.name.data,
            self.opening_balance.data,
            self.opening_balance_date.data
        )
        if kid_id:
            kid.id = kid_id
        return kid.save(user)


#===============================================================================
class Allowance(wtf.Form):
    kid_id = wtf.SelectField(u'Kid', coerce=int)
    period_day = wtf.SelectField(
        u'Day',
        coerce=int,
        choices=[(x, x) for x in xrange(1, 32, 1)]
    )
    period = wtf.SelectField(
        u'Frequency',
        choices=[('weekly', 'Weekly'), ('monthly', 'Monthly')]
    )
    amount = DecimalField('Amount', [wtf.validators.NumberRange(min=0.0)])

    #---------------------------------------------------------------------------
    def set_kid_choices(self, user):
        self.kid_id.choices = models.get_kids(user)
        
    #---------------------------------------------------------------------------
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


#===============================================================================
class Transaction(wtf.Form):
    kid_id = wtf.SelectField(u'Kid', coerce=int)
    transaction_date = wtf.DateField(u'Date', format="%m/%d/%Y")
    amount = DecimalField(u'Amount', [wtf.validators.NumberRange(min=0.0)])
    withdrawal = wtf.BooleanField(u'Withdrawal')
    category = wtf.TextField(u'Category', [wtf.validators.Length(min=3, max=150)])
    description = wtf.TextAreaField(u'Description')

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(Transaction, self).__init__(*args, **kwargs)
        
    #---------------------------------------------------------------------------
    def set_kid_choices(self, user):
        self.kid_id.choices = models.get_kids(user)

    #---------------------------------------------------------------------------
    def save(self, user, transaction_id=None):
        category = models.Category(user.account_id, self.category.data).save()
        transaction = models.Transaction(
            self.kid_id.data,
            self.transaction_date.data,
            self.amount.data,
            category,
            self.description.data
        )
        if transaction_id:
            transaction.id = transaction_id
        return transaction.save(user)

