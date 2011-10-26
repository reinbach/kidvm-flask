from functools import wraps

from flask import session, request, redirect, url_for

from kidvm import models

#---------------------------------------------------------------------------
def login_required(f):
    """Ensure we have a user session var

    If we do, go ahead and get the user object and pass it to the function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user', None) is None:
            return redirect(url_for('signin', next=request.url))
        user = models.AuthUser.query.filter_by(id=session.get('user', 0)).first_or_404()
        return f(user, *args, **kwargs)
    return decorated_function

#---------------------------------------------------------------------------
def valid_kid(f):
    """Ensure we have a valid kid

    Kid needs to be related to the logged in user
    param: user
    param: kid_id

    If kid id matches a kid related to the user then
    all is well
    """
    @wraps(f)
    def decorated_function(user, kid_id, *args, **kwargs):
        kid = models.Kid.query.filter_by(
            id=kid_id,
        ).first_or_404()
        if not models.valid_kid(kid.id, user):
            return redirect("/kids")
        return f(user, kid, *args, **kwargs)
    return decorated_function

#---------------------------------------------------------------------------
def valid_allowance(f):
    """Ensure we have a valid allowance

    Allowance needs to be related to the logged in user
    param: user
    param: allowance_id

    If allowance id matches an allowance related to the user then
    all is well
    """
    @wraps(f)
    def decorated_function(user, allowance_id, *args, **kwargs):
        allowance = models.Allowance.query.filter_by(
            id=allowance_id,
        ).first_or_404()
        if not models.valid_kid(allowance.kid_id, user):
            return redirect("/kids")
        return f(user, allowance, *args, **kwargs)
    return decorated_function

#---------------------------------------------------------------------------
def valid_transaction(f):
    """Ensure we have a valid transaction

    Transaction needs to be related to the logged in user
    param: user
    param: transaction_id

    If transaction id matches a transaction related to the user then
    all is well
    """
    @wraps(f)
    def decorated_function(user, transaction_id, *args, **kwargs):
        transaction = models.Transaction.query.filter_by(
            id=transaction_id,
        ).first_or_404()
        if not models.valid_kid(transaction.kid_id, user):
            return redirect("/kids")
        return f(user, transaction, *args, **kwargs)
    return decorated_function