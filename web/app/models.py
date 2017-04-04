import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db, login_manager
from flask_login import UserMixin
import werkzeug.security as security
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

class User(UserMixin, db.Model):
    """ This class represents a user for login/logout, and session management.
    Fields:
        id: unique id
        firstname: first name of user
        lastname: last name of user
        email: email address of user
        password: hashed-password of user
        affiliation:  organization user is affiliated with
        minor: a bool indicating whether user is a minor
        confirmed: whether account has been confirmed
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer,  primary_key=True)
    firstname = db.Column(db.String(64), index=True, unique=False)
    lastname = db.Column(db.String(64), index=True, unique=False)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128), index=False, unique=False)
    affiliation = db.Column(db.String(128), index=True, unique=False)
    phone = db.Column(db.String(12), index=False, unique=False)
    minor = db.Column(db.Boolean, index=True, unique=False, default=False)
    admin = db.Column(db.Boolean, index=True, unique=False, default=False)
    today = datetime.date.today()
    default_expiry = datetime.date(today.year+1, today.month, today.day)
    expire = db.Column(db.Date, unique=False, default=default_expiry)
    confirmed = db.Column(db.Boolean, index=True, default=False)

    # relationships - one-to-many with session objects
    sessions = db.relationship('Session', backref='user')
    
    @property
    def password(self):
        """ Prevent accessing of password hash.
        """
        raise AttributeError('password is not a readable attribute')

    
    @password.setter
    def password(self, password):
        """ Computes the hash of a password and stores it in the db session.
        """
        self.password_hash = security.generate_password_hash(password)

        
    def verify_password(self, password):
        """ Verify that given password matches the stored password hash.
        """
        return security.check_password_hash(self.password_hash, password)

    
    @login_manager.user_loader
    def load_user(user_id):
        """ Callback to return user given user_id. Required for flask_login.
        """
        return User.query.get(int(user_id))


    def generate_reset_token(self, expiration=3600):
        """ Generate a password reset token to send to a user's email.
        """
        # generate JSON web token
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'id': self.id, 'email': self.email})

    
    def reset_password(self, token, new_password):
        """ Takes a token received by the web app and if it is valid,
        changes the user's password to the new password.
        """
        # try to load the token using the serializer
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('id') == self.id and data.get('email') == self.email:
            self.password = new_password
            db.session.add(self)
            return True

        return False

    
    def generate_confirmation_token(self, expiration=3600):
        """ Generate a confirmation token to send to a user's email
        to validate that their email is correct.
        """
        # generate JSON web token
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    
    def confirm(self, token):
        """ Confirm a received token matches the one received.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        # try and load the token data
        try:
            data = s.loads(token)
        except:
            return False

        # check that token matches user id
        if data.get('confirm') != self.id:
            return False

        # confirm user and add them to the db
        self.confirmed = True
        db.session.add(self)

        return True


    def __repr__(self):
        """ Pretty-printing of user objects. """
        return "<User %r>" % (self.email)


    
class Session(db.Model):
    """ This class represents a session for queue observation.
    Fields:
        id: unique id
        target: a string representing the target name or RA/DEC pairs
        exposure_time: the time in seconds for each exposure
        exposure_count: the number of exposures to take for each filter
        filter_*: whether to use that filter in the exposure
        binning: the binning to use with the CCD
        user_id: the ID of the user who submitted this request
        submit_date: the date that the session was submitted
        executed: whether the session has been executed
        exec_date: the date and time that the user was executed
    """
    __tablename__ = 'queue'
    id = db.Column(db.Integer,  primary_key=True)
    target = db.Column(db.String(32), index=True, unique=False)
    exposure_time = db.Column(db.Float, unique=False)
    exposure_count = db.Column(db.Integer, unique=False)
    filter_i = db.Column(db.Boolean, unique=False, default=False)
    filter_r = db.Column(db.Boolean, unique=False, default=False)
    filter_g = db.Column(db.Boolean, unique=False, default=False)
    filter_u = db.Column(db.Boolean, unique=False, default=False)
    filter_z = db.Column(db.Boolean, unique=False, default=False)
    filter_ha = db.Column(db.Boolean, unique=False, default=False)
    filter_clear = db.Column(db.Boolean, unique=False, default=True)
    binning = db.Column(db.Integer, unique=False, default=2)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    today = datetime.date.today()
    submit_date = db.Column(db.Date, index=True, unique=False, default=today)
    executed = db.Column(db.Boolean, index=True, unique=False, default=False)
    exec_date = db.Column(db.DateTime, index=True, nullable=True, unique=False, default=None)


    def __repr__(self):
        return "<Session {}: {}>".format(self.target, self.user)


class Night(db.Model):
    """ This class represents a session for queue observation.
    Fields:
        id: unique id
        target: a string representing the target name or RA/DEC pairs
        exposure_time: the time in seconds for each exposure
        exposure_count: the number of exposures to take for each filter
        filter_*: whether to use that filter in the exposure
        binning: the binning to use with the CCD
        user_id: the ID of the user who submitted this request
        submit_date: the date that the session was submitted
        executed: whether the session has been executed
        exec_date: the date and time that the user was executed
    """
    __tablename__ = 'nights'
    date = db.Column(db.Date, primary_key=True, index=True, unique=True)
    start_time = db.Column(db.Time, index=False, unique=False)
    end_time = db.Column(db.Time, index=False, unique=False)

    def __repr__(self):
        return '<Night: {}, Start: {}, End: {}, Status: {}'.format(self.date,
                                                                   self.start_time,
                                                                   self.end_time,
                                                                   self.status)
