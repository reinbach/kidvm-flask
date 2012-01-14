import os
import sqlite3
import tempfile
import unittest

from kidvm import app, models

#===============================================================================
class KidvmTestCase(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.db_filename = '/tmp/test.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///%s" % self.db_filename
        app.config['CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        app.config['MAIL_SUPPRESS_SEND'] = True
        self.app = app.test_client()
        models.db.create_all()

    #---------------------------------------------------------------------------
    def tearDown(self):
        os.unlink(self.db_filename)

    #---------------------------------------------------------------------------
    def login(self, email, password):
        return self.app.post('/signin', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    #---------------------------------------------------------------------------
    def register(self, email, password):
        return self.app.post('/register', data=dict(
            email=email,
            password=password,
            confirm=password
        ), follow_redirects=True)

    #---------------------------------------------------------------------------
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)
        
    #---------------------------------------------------------------------------
    def test_home_page(self):
        rv = self.app.get('/')
        assert "Allowances Simplified" in rv.data

    #---------------------------------------------------------------------------
    def test_register_success(self):
        rv = self.register('test+joe@ironlabs.com', 'password')
        user = models.AuthUser.query.filter_by(email='test+joe@ironlabs.com').first()
        assert user.account_id is not None
        assert 'You are now registered' in rv.data

    #---------------------------------------------------------------------------
    def test_register_multiple_success(self):
        self.register('test+valid@ironlabs.com', 'password')
        self.logout()
        self.register('test+valid2@ironlabs.com', 'password')
        self.logout()
        user_list = models.AuthUser.query.all()
        assert len(user_list) == 2

    #---------------------------------------------------------------------------
    def test_register_duplicate_email(self):
        self.register('test+valid@ironlabs.com', 'password')
        self.logout()
        rv = self.register('test+valid@ironlabs.com', 'password')
        assert 'Email address has already been used' in rv.data

    #---------------------------------------------------------------------------
    def test_login_success(self):
        self.register('test+valid@ironlabs.com', 'password')
        self.logout()
        rv = self.login('test+valid@ironlabs.com', 'password')
        assert 'You have been logged in' in rv.data

    #---------------------------------------------------------------------------
    def test_login_last_login_set(self):
        self.register('test+valid@ironlabs.com', 'password')
        self.logout()
        self.login('test+valid@ironlabs.com', 'password')
        user = models.AuthUser.query.filter_by(email='test+valid@ironlabs.com').first()
        assert user.last_login is not None

    #---------------------------------------------------------------------------
    def test_login_failure(self):
        """Test failed attempts to login

        Failed message should not indicate which field was wrong
        
        Check with a bad email
        Check with a bad password
        """
        self.register('test+valid@ironlabs.com', 'password')
        self.logout()
        rv = self.login('test+joes@ironlabs.com', 'password')
        assert 'Invalid email and/or password' in rv.data
        rv = self.login('test+valid@ironlabs.com', 'passwordx')
        assert 'Invalid email and/or password' in rv.data

    #---------------------------------------------------------------------------
    def test_forgot_password_valid_email(self):
        with models.mail.record_messages() as outbox:
            self.register('test+valid@ironlabs.com', 'password')
            self.logout()
            rv = self.app.post('/forgot/password', data=dict(
                email='test+valid@ironlabs.com',
            ), follow_redirects=True)
            assert "Password reset instructions have been emailed" in rv.data
            assert len(outbox) == 1
            assert outbox[0].subject == "Password Reset Link"

    #---------------------------------------------------------------------------
    def test_forgot_password_invalid_email(self):
        with models.mail.record_messages() as outbox:
            rv = self.app.post('/forgot/password', data=dict(
                email='test+joe@ironlabs.com',
            ), follow_redirects=True)
            assert "Password reset instructions have been emailed" in rv.data
            assert len(outbox) == 0

    #---------------------------------------------------------------------------
    def test_reset_password_valid(self):
        self.register('test+valid@ironlabs.com', 'password')
        self.logout()
        user = models.AuthUser.query.filter_by(email='test+valid@ironlabs.com').first()
        assert user is not None
        rv = self.app.get(
            '/reset/password/%s-%s' % (user.id, user.get_uid()),
            follow_redirects=True
        )
        assert "Reset Password" in rv.data

    #---------------------------------------------------------------------------
    def test_category_multiple_add(self):
        name = 'Tooth Fairy'
        account_id = 1
        category1 = models.Category(account_id, name)
        category1 = category1.save()
        category2 = models.Category(account_id, name)
        category2 = category2.save()
        assert category1.id == category2.id

        
if __name__ == "__main__":
    unittest.main()