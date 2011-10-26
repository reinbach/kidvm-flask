from flask import render_template, request, flash, session, redirect, url_for

from kidvm import app, models, forms, utils

#---------------------------------------------------------------------------
def _render(template, context):
    context.update(google_analytics_code=app.config['GOOGLE_ANALYTICS_CODE'])
    return render_template(template, context=context)

#---------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    return _render("index.html", dict())

#---------------------------------------------------------------------------
@app.route('/about', methods=['GET'])
def about():
    return _render("about.html", dict())
    
#---------------------------------------------------------------------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form_contact = forms.Contact()
    if form_contact.validate_on_submit():
        form_contact.send()
        flash("Thanks, your message has been sent. I can't wait to read it.")
        return redirect("/")
    context = dict(
        form_contact=form_contact
    )
    return _render("contact.html", context)

#---------------------------------------------------------------------------
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)
    flash('You have been logged out')
    return redirect(url_for('index'))
    
#---------------------------------------------------------------------------
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form_signin = forms.SignIn()
    form_register = forms.Register()
    if form_signin.validate_on_submit():
        session['user'] =  form_signin.login()
        if session['user']:
            flash('You have been logged in', 'success')
            return redirect(url_for('kids'))
        flash('Invalid email and/or password', 'error')
    context = dict(
        form_signin=form_signin,
        form_register=form_register
    )
    return _render("signin.html", context)

#---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    form_register = forms.Register()
    form_signin = forms.SignIn()
    if form_register.validate_on_submit():
        session['user'], error_msg = form_register.register()
        if session['user']:
            flash("You are now registered, and all set to go", "success")
            return redirect(url_for('kids'))
        flash(error_msg, "error")
    context = dict(
        form_signin=form_signin,
        form_register=form_register,
    )
    return _render("signin.html", context)

#---------------------------------------------------------------------------
@app.route('/forgot/password', methods=['GET', 'POST'])
def forgot_password():
    form = forms.ForgotPassword()
    if form.validate_on_submit():
        form.reset_password()
        flash(
            "Password reset instructions have been emailed to %s" % form.email.data,
            "success"
        )
        form = None
    context = dict(
        form=form
    )
    return _render("forgot_password.html", context)

#---------------------------------------------------------------------------
@app.route('/reset/password/<uid>', methods=['GET', 'POST'])
def reset_password(uid):
    user = models.get_user_from_uid(uid)
    if user:
        form = forms.ResetPassword()
        if form.validate_on_submit():
            #TODO need to finish this up
            form.set_password()
            flash("Your password has been updated.", "success")
            return redirect_url("/kids")
    else:
        form = None
    context = dict(
        form=form,
        uid=uid
    )
    return _render("reset_password.html", context)
    
#---------------------------------------------------------------------------
@app.route("/kids", methods=['GET'])
@utils.login_required
def kids(user):
    kid_list = models.Kid.query.filter_by(account_id=user.account_id).order_by('name')
    if not kid_list:
        return redirect("/kids/add")
    context = dict(
        kid_list=kid_list,
    )
    return _render("kid/index.html", context)

#---------------------------------------------------------------------------
@app.route("/kids/add", methods=['GET', 'POST'])
@utils.login_required
def kid_add(user):
    form_kid = forms.Kid()
    if form_kid.validate_on_submit():
        form_kid.save(user)
        flash("Kid has been added", "success")
        return redirect("/kids")
    context = dict(
        form_kid=form_kid,
        action=url_for("kid_add")
    )
    return _render("kid/kid.html", context)
    
#---------------------------------------------------------------------------
@app.route("/kids/detail/<kid_id>", methods=['GET'])
@utils.login_required
@utils.valid_kid
def kid_detail(user, kid):
    context = dict(
        kid=kid
    )
    return _render('kid/kid_detail.html', context)

#---------------------------------------------------------------------------
@app.route("/kids/edit/<kid_id>", methods=['GET', 'POST'])
@utils.login_required
@utils.valid_kid
def kid_edit(user, kid):
    form_kid = forms.Kid(request.form, kid)
    if form_kid.validate_on_submit():
        form_kid.save(user, kid.id)
        flash("Kid has been updated", "success")
        return redirect(url_for("kid_detail", kid_id=kid.id))
    context = dict(
        form_kid=form_kid,
        action=url_for("kid_edit", kid_id=kid.id)
    )
    return _render("kid/kid.html", context)

#---------------------------------------------------------------------------
@app.route("/kids/delete/<kid_id>", methods=['GET'])
@utils.login_required
@utils.valid_kid
def kid_delete(user, kid):
    kid.delete()
    flash("Kid has been removed")
    return redirect("/kids")

#--------------------------------------------------------------------------
@app.route("/kids/allowance/add", methods=['GET', 'POST'])
@utils.login_required
def kid_allowance_add(user):
    form_allowance = forms.Allowance()
    form_allowance.set_kid_choices(user)
    if form_allowance.validate_on_submit():
        if form_allowance.save(user):
            flash("Allowance has been added", "success")
            return redirect("/kids")
        else:
            flash("Yikes, there was an issue saving the allowance", "error")
    context = dict(
        form_allowance=form_allowance,
        action=url_for('kid_allowance_add')
    )
    return _render("kid/allowance.html", context)

#---------------------------------------------------------------------------
@app.route("/kids/allowance/edit/<allowance_id>", methods=['GET', 'POST'])
@utils.login_required
@utils.valid_allowance
def kid_allowance_edit(user, allowance):
    form_allowance = forms.Allowance(request.form, allowance)
    form_allowance.set_kid_choices(user)
    if form_allowance.validate_on_submit():
        if form_allowance.save(user, allowance.id):
            flash("Allowance has been updated", "success")
            return redirect("/kids")
        else:
            flash("Yikes, there was an issue saving the allowance", "error")
    context = dict(
        form_allowance=form_allowance,
        action=url_for('kid_allowance_edit', allowance_id=allowance.id)
    )
    return _render("kid/allowance.html", context)

#---------------------------------------------------------------------------
@app.route("/kids/allowance/delete/<allowance_id>", methods=['GET'])
@utils.login_required
@utils.valid_allowance
def kid_allowance_delete(user, allowance):
    allowance.delete()
    flash("Allowance has been removed")
    return redirect("/kids")
    
#--------------------------------------------------------------------------
@app.route("/kids/transaction/add", methods=['GET', 'POST'])
@utils.login_required
def kid_transaction_add(user):
    form_transaction = forms.Transaction()
    form_transaction.kid_id.choices = [
        (k.id, k.name) for k in models.Kid.query.filter_by(account_id=user.account_id)
    ]
    if form_transaction.validate_on_submit():
        if form_transaction.save(user):
            flash("Transaction has been added", "success")
            return redirect("/kids")
        else:
            flash("Yikes, there was an issue saving the transaction", "error")
    context = dict(
        form_transaction=form_transaction,
        action=url_for('kid_transaction_add')
    )
    return _render("kid/transaction.html", context)

#---------------------------------------------------------------------------
@app.route("/kids/transaction/edit/<transaction_id>", methods=['GET', 'POST'])
@utils.login_required
@utils.valid_transaction
def kid_transaction_edit(user, transaction):
    form_transaction = forms.Transaction(request.form, transaction)
    form_transaction.set_kid_choices(user)
    models.db.session.flush()
    if form_transaction.validate_on_submit():
        models.db.session.flush()
        if form_transaction.save(user, transaction.id):
            flash("Transaction has been updated", "success")
            return redirect("/kids")
        else:
            flash("Yikes, there was an issue saving the transaction", "error")
    context = dict(
        form_transaction=form_transaction,
        action=url_for('kid_transaction_edit', transaction_id=transaction.id)
    )
    return _render("kid/transaction.html", context)

#---------------------------------------------------------------------------
@app.route("/kids/transaction/delete/<transaction_id>", methods=['GET'])
@utils.login_required
@utils.valid_transaction
def kid_transaction_delete(user, transaction):
    transaction.delete()
    flash("Transaction has been removed")
    return redirect("/kids")

    
if __name__ == '__main__':
    app.debug = True
    app.run()
    