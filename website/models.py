from . import db 					# import from __init__.py
from flask_login import UserMixin  	# id will auto increment
from sqlalchemy import Date, DateTime
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    # User must agree to terms and conditions before being added to this class
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    postcode = db.Column(db.String(10), nullable=False)
    locality = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)    
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    subscriber_link = db.relationship('UserSubscriberLink', backref='user', uselist=False)
    user_type = db.Column(db.String(20), nullable=False, default="customer")
    travel_agent_license = db.Column(db.String(20), nullable=True, index=True)  # For travel agent links
    
    # Add mapper arguments for polymorphic behavior
    __mapper_args__ = {
        'polymorphic_on': user_type,  # Indicates the column used to determine the subclass
        'polymorphic_identity': 'user'  # Identity for the base User class
    }
    

class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # Foreign key linking to User
    admin_id = db.Column(db.String(8), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'admin',  # Identify this subclass as 'admin'
    }


class TravelAgent(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # Foreign key linking to User
    license = db.Column(db.String(20), unique=True, nullable=False)
    company = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    image_folder = db.Column(db.String(255), unique=True, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'travel_agent',  # Identify this subclass as 'travel_agent'
    }

    
class UserSubscriberLink(db.Model):
    # Link object Users and Subscribers together if both emails match.
    # It can be anticipated users can subscribe/unsubscribe at any time, many times.
    # Process must be handled automatically to reduce errors and potential of redundant records.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscriber.id'), nullable=True)
    
    
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    member_link = db.relationship('UserSubscriberLink', backref='subscriber', uselist=False)


class Verification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=func.now())
    user = db.relationship('User', backref=db.backref('verification_requests'))
    
    
class Lounge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(2000), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    postcode = db.Column(db.String(10), nullable=False)
    locality = db.Column(db.String(25), nullable=False)
    image_folder = db.Column(db.String(255), unique=True, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False, default=30)
    status = db.Column(db.String(6), nullable=False, default="Open")
    

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    exit_date = db.Column(db.Date, nullable=False, index=True)
    guests_qty = db.Column(db.Integer, nullable=False)
    flight_id = db.Column(db.String(50), nullable=False)  # Flight identifier
    dietary_req = db.Column(db.String(255), nullable=True)  # Optional dietary requirements
    status = db.Column(db.String(20), nullable=False, default="Valid")

    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the User table
    user = db.relationship('User', backref='bookings')
    lounge_id = db.Column(db.Integer, db.ForeignKey('lounge.id'), nullable=False)
    lounge = db.relationship('Lounge', backref='bookings')
    

class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(2000), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationships    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], backref='enquiries_made')
    agent = db.relationship('User', foreign_keys=[agent_id], backref='agent_enquiries')
    

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiry.id'), nullable=False, index=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    user = db.relationship('User', backref='replies')
    enquiry = db.relationship('Enquiry', backref='replies')