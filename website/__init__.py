from flask import Flask, redirect, url_for, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from os import path, getenv
import logging
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager, current_user
from functools import wraps

db = SQLAlchemy()
DB_NAME = "database.db"
 
# Create a log file 'verification_cleanup.log' and it is saved in the logs dir
log_file = path.join('website/logs', 'verification_cleanup.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger('verification_cleanup')
logger.setLevel(logging.INFO)
 
# this one will handle logging system cleanup into verification_cleanup.log
file_handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
 
# this will handle error codes to appear in the terminal during runtime
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(formatter)
 
logger.addHandler(file_handler)
logger.addHandler(console_handler)
 
def create_app():
    app = Flask(__name__)
    
    # TODO: for production, change SECRET_KEY
    app.config['SECRET_KEY'] = 'hello'     # kept simple for developement
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SERVER_NAME'] = 'localhost:5000'
     
#    configure_mail(app)
    db.init_app(app)
     
    @app.errorhandler(404)
    def not_found(e):
        return render_template('main/404.html')
     
    # Create the login manager which will maintain the logged in user instance
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
     
    # this provides Flask with the user profile information
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # ICV is used to dynamically fill render templates based on stored user info
    @app.context_processor
    def inject_common_variables():
        current_date = datetime.now().date()
        is_verified = False
        is_subscribed = False
        
        if current_user.is_authenticated:
            is_verified = current_user.is_verified
            link = UserSubscriberLink.query.filter_by(user_id=current_user.id).first()
            if link:
                is_subscribed = True
       
        return {
            'user': current_user,
            'current_date': current_date,
            'is_subscribed': is_subscribed,
            'is_verified': is_verified
        }
    
    # Register blueprints
    from .views import views
    from .auth import auth
    from .emails import emails
    from .bookings import booking
    from .lounges import lounge
    from .travel_agents import travelAgents
     
    app.register_blueprint(views)
    app.register_blueprint(auth)
    app.register_blueprint(emails)
    app.register_blueprint(booking)
    app.register_blueprint(lounge)
    app.register_blueprint(travelAgents)
    
    from .models import User, Subscriber, UserSubscriberLink, Verification
     
    if getenv("WERKZEUG_RUN_MAIN") == "true":
        with app.app_context():
            create_database(app)
            start_scheduler(app)

    return app
    
def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Database Created!')
        

# Create a decorator to destinguished logged_in user and verified_user
def login_required_and_verified(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in before attempting to access this page.', category='error')
            return redirect(url_for('auth.login'))
        if not current_user.is_verified:
            flash('Please verify your account to access this page.', category='error')
            return redirect(url_for('auth.verify_account'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in before attempting to access this page.', category='error')
            return redirect(url_for('auth.login'))
        if not current_user.is_verified:
            flash('Please verify your account to access this page.', category='error')
            return redirect(url_for('auth.verify_account'))
        if not current_user.user_type == "admin":
            flash('Access Denied!', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function


def travel_agent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in before attempting to access this page.', category='error')
            return redirect(url_for('auth.login'))
        if not current_user.is_verified:
            flash('Please verify your account to access this page.', category='error')
            return redirect(url_for('auth.verify_account'))
        if not current_user.user_type == "travel_agent":
            flash('Access Denied!', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function


# method run by the file_hander to clean old verification records and record in the log file
def delete_old_verification_records(app):
    from .models import Verification

    with app.app_context():
        time_threshold = datetime.utcnow() - timedelta(minutes=3)
        records = Verification.query.filter(Verification.created_at < time_threshold).all()

        if records:
            for record in records:
                logger.info(f'Deleting record for User ID: {record.user_id}\nCreated at: {record.created_at}\n')
                db.session.delete(record)
            db.session.commit()
        else:
            logger.info('No records to delete today\n')

    logger.info("Cleanup task completed-->\n")


def archive_expired_bookings(app):
    from .models import Booking
    
    with app.app_context():
        current_date = datetime.utcnow().date()
        bookings = Booking.query.filter(Booking.exit_date < current_date).all()
        
        for booking in bookings:
            logger.info(f'Archiving booking ID: {booking.id}, User ID: {booking.user_id}')
            booking.status = 'Archived'  # Update the booking status
        db.session.commit()


# this will happen at 2am and 10am every day
def start_scheduler(app):
    with app.app_context():
        scheduler = BackgroundScheduler()
        scheduler.add_job(lambda: delete_old_verification_records(app), 'cron', hour=2)
        scheduler.add_job(lambda: archive_expired_bookings(app), 'cron', hour=10)
        scheduler.start()
        print('Scheduler Started!')