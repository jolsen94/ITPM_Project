from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for, jsonify
from .models import User, Subscriber, UserSubscriberLink, Verification, Admin, Enquiry, Reply, TravelAgent, Lounge, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_required_and_verified, travel_agent_required, admin_required
from datetime import datetime, timedelta
from flask_login import login_user, login_required, logout_user, current_user
import re
from os import path, makedirs, rename, listdir
from random import randint

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        login_success = False
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            if check_password_hash(user.password, password):
                # if stored hash matches the hash of entered password
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                login_success = True
            else:
                flash('Incorrect password, please try again.', category='error')
        else:
            flash('Email not found.', category='error')
        
        if login_success:
            if user.is_verified:
                return redirect(url_for('views.home'))
            else:
                return redirect(url_for('auth.verify_account'))
    
    return render_template('main/login.html')
    
    
@auth.route('/verify-account', methods=['GET', 'POST'])
@login_required
def verify_account():
    step = 'email'
    if request.method == 'POST':
        if current_user.is_verified:
            # in case verified user lands here and submits an email
            return render_template('home.html')

        email = request.form.get('email')
        code = request.form.get('code')

        if email and not code:
            user = User.query.filter_by(email=email).first()
            if user.email != current_user.email:
                return jsonify({'step': 'email', 'message': 'The email you entered is not associated with your account', 'category': 'error'})
            if user:
                code = generate_code()
                create_verification_request(current_user.id, code)
                return jsonify({'step': 'code', 'message': 'Email address found!', 'category': 'info'})
            else:
                return jsonify({'step': 'email', 'message': 'Email address not found!', 'category': 'error'})

        elif code:
            user = User.query.filter_by(email=email).first()
            code = int(code)
            verification_request = verify_code(user, code)
            if verification_request:
                verify_user(user, verification_request)
                flash('Account Successfully Verified!', category='success')
                return jsonify({'step': 'complete', 'message': 'Account Verified!', 'category': 'success'})
            else:
                return jsonify({'step': 'code', 'message': 'Code is incorrect. Please try again.', 'category': 'error'})

    return render_template('main/verify-account.html', step=step)
    
    
def generate_code():
    return randint(10000, 99999)
    
    
def create_verification_request(user_id, code):
    # only add a Verification record if one doesn't already exist for the user
    code_already_exists = Verification.query.filter_by(user_id=user_id).first()
    if not code_already_exists:
        verification_request = Verification(user_id=user_id, code=code)
        db.session.add(verification_request)
        db.session.commit()
    return
    
    
def verify_code(user, entered_code):
    # find out what is the latest the code could have been generated which would still grant approval
    time_threshold = datetime.utcnow() - timedelta(minutes=3)

    # look for a v-request where the created_at is after the latest possible time (time_threshold)
    # narrow the search by matching a user_id
    verification_request = Verification.query.filter(Verification.user_id == user.id,
                                                     Verification.created_at >= time_threshold).first()

    if verification_request:  # if user has valid verification code
        true_code = verification_request.code
        if true_code == entered_code:
            # code exists, matches entry and is within 3 minutes of being created
            return verification_request
        else:
            return False
    return False  # return false by default for security
    
    
def can_send_new_code(user):
    latest_request = Verification.query.filter_by(user_id=user.id).first()

    if latest_request:
        expiration_time = latest_request.created_at + timedelta(minutes=3)
        return datetime.now() > expiration_time

    return True


def verify_user(user, verification_request):
    user.is_verified = True
    db.session.delete(verification_request)
    db.session.commit()
    return True
    
    
@auth.route('/logout')
@login_required
def logout():
    # returns user to the page from where the logged out
    # if they are in a logged_required page, they will be redirected elsewhere
    logout_user()
    return redirect(url_for('views.home'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # get all info from form
        email = request.form.get('email')
        firstName = request.form.get('first_name').capitalize()
        lastName = request.form.get('last_name').capitalize()
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        address = request.form.get('address')
        state = request.form.get('state')
        postcode = request.form.get('postcode')
        locality = request.form.get('locality')
        phone = request.form.get('phone')
        subscribe_check = request.form.get('subscribe')
        agree = request.form.get('agree')

        if not validate_signup_form(email, agree):
            return redirect(url_for('auth.sign_up'))

        message = field_checker(email=email, first_name=firstName, last_name=lastName,
                                password1=password1, password2=password2)

        if isinstance(message, bool) and message:
            password = generate_password_hash(password1, method='pbkdf2:sha256')
            user_type = request.form.get('type')
            travel_agent_license = request.form.get('travel_agent_license')
            
            if user_type == "customer" or user_type is None:
                new_user = User(
                    email=email, first_name=firstName, last_name=lastName,
                    password=password, address=address, state=state, postcode=postcode, 
                    locality=locality, phone=phone, travel_agent_license=travel_agent_license)
                db.session.add(new_user)
                
            elif user_type == "admin":
                while True:
                    id_number = randint(1000, 9999)
                    admin_id = "FDA_" + str(id_number)
                    # make sure we get a unique admin_id
                    if not Admin.query.filter_by(admin_id=admin_id).first():
                        break
                        
                department = request.form.get('department').capitalize()
                new_user = Admin(
                    email=email, first_name=firstName, last_name=lastName,
                    password=password, address=address, state=state, postcode=postcode, 
                    locality=locality, phone=phone,
                    admin_id=admin_id, department=department, user_type=user_type)
                db.session.add(new_user)
                
            elif user_type == "travel_agent":
                license = request.form.get('license')
                company = request.form.get('company')
                desc = request.form.get('desc')
                
                # create new directory for travel agent images
                image_dir = path.join(current_app.root_path, 'static/images/travel-agents')
                agent_license_dir = path.join(image_dir, license)
                if not path.exists(agent_license_dir):
                    makedirs(agent_license_dir)
                    flash(f'Created new directory: {agent_license_dir}', category='success')
                else:
                    flash('Error: Agent exists with same license! New agent not created!', category='error')
                    return redirect(url_for('views.home'))
                
                new_user = TravelAgent(
                    email=email, first_name=firstName, last_name=lastName,
                    password=password, address=address, state=state, postcode=postcode, 
                    locality=locality, phone=phone, license=license, company=company, 
                    description=desc, user_type=user_type, image_folder=agent_license_dir)
                db.session.add(new_user)

            db.session.commit()
            flash('Account created!', category='success')

            # Create new Subscriber object if user opt-in is true
            if subscribe_check:
                subscriber = Subscriber.query.filter_by(email=email).first()  # Use `email` from the form directly

                if not subscriber:  # Only add subscriber if they don't already exist
                    new_subscriber = add_new_subscriber(email)  # Use the new user's email
                    create_sub_user_link(new_user.id, new_subscriber.id)  # Use `new_user.id`
                    return redirect(url_for('emails.new_sub'))
        else:
            flash(message, category='error')
        
        if current_user.is_authenticated and current_user.user_type == "admin":
            return redirect(url_for('views.home'))  # admin successfully created account
        else:
            return redirect(url_for('auth.login'))  # signup successful

    return render_template('main/sign-up.html')


def validate_signup_form(email, agree):
    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email already exists', category='error')
        return False
    if not agree:
        flash('You must agree with the terms and condition before having access to the full website.',
              category='error')
        return False
    
    return True


@auth.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    existing_subscriber = Subscriber.query.filter_by(email=email).first()

    if existing_subscriber:
        flash(
            f'Email {existing_subscriber.email} is already subscribed!', category='error')
    else:
        message = field_checker(email=email)
        if isinstance(message, bool) and message:
            new_subscriber = add_new_subscriber(email)

            # check if new sub email associated with existing user
            existing_user = User.query.filter_by(
                email=new_subscriber.email).first()
            if existing_user:
                create_sub_user_link(existing_user.id, new_subscriber.id)

            flash('Thanks for subscribing to our weekly newsletter!',
                  category='success')
            return redirect(url_for('emails.new_sub'))
        else:
            flash(message, category='error')
            return redirect(request.referrer)

    return redirect(request.referrer)


def add_new_subscriber(email):
    new_subscriber = Subscriber(email=email)
    db.session.add(new_subscriber)
    db.session.commit()
    return new_subscriber


def new_sub_send_email(email):
    return redirect(url_for('emails.welcome_email'))


def create_sub_user_link(user_id, subscriber_id):
    existing_link = UserSubscriberLink.query.filter_by(user_id=user_id).first()
    if not existing_link:
        new_link = UserSubscriberLink(
            user_id=user_id, subscriber_id=subscriber_id)
        db.session.add(new_link)
        db.session.commit()
    return
    
    
@auth.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form.get('email')
    subscriber = Subscriber.query.filter_by(email=email).first()
    link = UserSubscriberLink.query.filter_by(
        subscriber_id=subscriber.id).first()

    if subscriber:
        db.session.delete(subscriber)
        if link:
            db.session.delete(link)

        db.session.commit()

        flash('You will no longer receive newsletters from us!', category='success')
        # return redirect(url_for('views.feedback'))
        return redirect(url_for('emails.farewell_email'))

    flash(
        f'The email you entered is not subscribed for our newsletters: { email }')
    return redirect(request.referrer)
    
    
@auth.route('/reset-password', methods=['GET', 'POST'])
@login_required_and_verified
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        new_password_1 = request.form.get('password1')
        new_password_2 = request.form.get('password2')

        if email and not code and not new_password_1:
            user = User.query.filter_by(email=email).first()
            
            if user.email != current_user.email:
                return jsonify({'step': 'email', 'message': 'The email you entered is not associated with your account', 'category': 'error'})

            if not user:
                return jsonify({'step': 'email', 'message': 'Email address not found!', 'category': 'error'})

            verification_code = generate_code()
            create_verification_request(user.id, verification_code)
            return jsonify({'step': 'code', 'message': 'Verification code sent to your email.', 'category': 'info'})

        elif code and not new_password_1:
            user = User.query.filter_by(email=email).first()
            code = int(code)
            verification_request = verify_code(user, code)
            if verification_request:
                return jsonify({'step': 'password', 'message': 'Code verified. Enter your new password.', 'category': 'success'})
            else:
                return jsonify({'step': 'code', 'message': 'Code is incorrect. Please try again.', 'category': 'error'})

        elif new_password_1 and new_password_2:
            user = User.query.filter_by(email=email).first()

            if new_password_1 != new_password_2:
                return jsonify({'step': 'password', 'message': 'Passwords do not match!', 'category': 'error'})

            if check_password_hash(user.password, new_password_1):
                return jsonify({'step': 'password', 'message': 'Must use a password not previously used', 'category': 'error'})

            message = field_checker(
                password1=new_password_1, password2=new_password_2)
            if isinstance(message, bool) and message:
                approved_password = generate_password_hash(
                    new_password_1, method='pbkdf2:sha256')
                user.password = approved_password
                verification_request = Verification.query.filter_by(
                    user_id=user.id).first()
                db.session.delete(verification_request)
                db.session.commit()
                flash('Password has been changed', category='success')
                return jsonify({'step': 'complete', 'message': 'Password has been changed!', 'category': 'success'})
            else:
                return jsonify({'step': 'password', 'message': message, 'category': 'error'})

    return render_template('main/reset-password.html')
    
    
@auth.route('/remove-account', methods=['GET', 'POST'])
@login_required_and_verified
def remove_account():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        agree = request.form.get('agree')

        if not agree:
            flash('You must agree to delete all saved information from this site to delete your account.',
                  category='error')
            return redirect(url_for('auth.dashboard'))

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('The email or password entered is not correct', category='error')
            return redirect(url_for('auth.dashboard'))

        link = UserSubscriberLink.query.filter_by(user_id=user.id).first()
        if link:
            db.session.delete(link)
            
        bookings = Booking.query.filter_by(user_id=user.id).all()
        if bookings:
            for booking in bookings:
                db.session.delete(booking)

        db.session.delete(user)
        db.session.commit()

        flash('Your account access has been successfully removed. All your account information has been deleted.',
              category='info')
        return redirect(url_for('auth.login'))

    return render_template("main/remove-account.html")
    
    
@auth.route('/dashboard')
@login_required_and_verified
def dashboard():
    clients, client_bookings = None, None
    bookings = booking_window()
    
    if current_user.user_type == "travel_agent":
        clients = client_window()
        client_bookings = []
        for client in clients:
            booking = Booking.query.filter_by(user_id=client.id).all()
            client_bookings.append(booking)
            
    if current_user.user_type == "admin":
        # Get all enquiries where is_admin is true
        enquiries = Enquiry.query.filter_by(is_admin=True).all()
    elif current_user.user_type == "travel_agent":
        # Get all enquiries where agent_id matches the current user's ID
        enquiries = Enquiry.query.filter_by(agent_id=current_user.id).all()
    else:
        enquiries = Enquiry.query.filter_by(user_id=current_user.id).all()
            
    return render_template('main/dashboard.html', clients=clients, enquiries=enquiries,
        bookings=bookings, client_bookings=client_bookings)


def client_window():
    clients = User.query.filter_by(travel_agent_license=current_user.license).all()
    return clients


def booking_window():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return bookings


@auth.route('/view-client/<int:client_id>', methods=['GET', 'POST'])
@travel_agent_required
def view_client(client_id):
    client = User.query.filter_by(id=client_id).first()
    bookings = Booking.query.filter_by(user_id=client.id, status="Valid").all()
    lounges = Lounge.query.all()
    
    # Calculate current and remaining capacity for each lounge
    lounges_with_capacity = []
    for lounge in lounges:
        # Sum guests from all bookings tied to this lounge
        current_capacity = db.session.query(
            db.func.sum(Booking.guests_qty)
        ).filter_by(lounge_id=lounge.id, status="Valid").scalar() or 0

        # Calculate remaining capacity
        remaining_capacity = lounge.max_capacity - current_capacity

        # Attach capacity data to lounge dynamically
        lounges_with_capacity.append({
            "lounge": lounge,
            "current_capacity": current_capacity,
            "remaining_capacity": remaining_capacity,
        })
    
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        lounge_id = request.form.get('lounge_id')
        travel_agent_license = request.form.get('travel_agent_license')
        entry_date_str = request.form.get('entry_date')
        exit_date_str = request.form.get('exit_date')
        
        entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
        exit_date = datetime.strptime(exit_date_str, '%Y-%m-%d').date()
    
        guests_qty = int(request.form.get('guests_qty'))
        flight_id = request.form.get('flight_id')
        dietary_req = request.form.get('dietary_req')
        
        if not is_capacity_available(lounge_id, entry_date, exit_date, guests_qty):
            flash("Not enough capacity for the selected dates.", category="error")
            return redirect(request.referrer)
        
        if validate_booking_details(entry_date, exit_date, client_id, travel_agent_license):
            return redirect(request.referrer)
           
        # Create the booking if capacity checks pass
        new_booking = Booking(
            lounge_id=lounge_id,
            user_id=client_id,
            entry_date=entry_date,
            exit_date=exit_date,
            guests_qty=guests_qty,
            flight_id=flight_id,
            dietary_req=dietary_req
        )
        
        try:
            db.session.add(new_booking)
            db.session.commit()
            flash("Booking created successfully!", category="success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating booking: {e}", category="error")
        
        return redirect(url_for('auth.view_client', client_id=client_id))
    
    return render_template('main/view-client.html', client=client, 
        lounges=lounges_with_capacity, bookings=bookings)


@auth.route('/change-details', methods=['POST'])
@login_required_and_verified
def change_details():
    # Collect new details from the form
    new_email = request.form.get('email').lower()
    new_first_name = request.form.get('first_name').capitalize()
    new_last_name = request.form.get('last_name').capitalize()
    new_address = request.form.get('address')
    new_state = request.form.get('state')
    new_postcode = request.form.get('postcode')
    new_locality = request.form.get('locality')
    new_phone = request.form.get('phone')

    # Validate the form fields
    message = field_checker(email=new_email, first_name=new_first_name, last_name=new_last_name)
    if not isinstance(message, bool) or not message:
        flash(message, category='error')
        return redirect(request.referrer)

    user_updated = False

    # Fields to check and update dynamically
    fields_to_update = {
        "first_name": new_first_name,
        "last_name": new_last_name,
        "address": new_address,
        "state": new_state,
        "postcode": new_postcode,
        "locality": new_locality,
        "phone": new_phone,
    }
    
    if current_user.user_type == "travel_agent":
        new_description = request.form.get('desc')
        fields_to_update["description"] = new_description

    for field, new_value in fields_to_update.items():
        if getattr(current_user, field) != new_value:
            setattr(current_user, field, new_value)
            user_updated = True

    # Handle email updates with special logic
    if current_user.email != new_email:
        if Subscriber.query.filter_by(email=current_user.email).first():
            subscriber = Subscriber.query.filter_by(email=current_user.email).first()
            if subscriber:
                subscriber.email = new_email  # Update subscriber email

        current_user.email = new_email
        user_updated = True

    if user_updated:
        try:
            db.session.commit()
            flash('Details updated successfully!', category='success')
            return redirect(url_for('emails.change_details'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating details: {e}", category='error')
            return redirect(request.referrer)
    else:
        flash('No changes detected.', category='error')
        return redirect(request.referrer)

    
def field_checker(email=None, first_name=None, last_name=None, password1=None, password2=None):
    email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    fname_pattern = re.compile(r"^[A-Za-z]{2,}$")
    lname_pattern = re.compile(r"^[A-Za-z]{2,}$")
    password_pattern = re.compile(
        r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$")

    if email is not None and not email_pattern.match(email):
        message = f'The Email you have entered is invalid: {email}'
        return message

    if first_name is not None and not fname_pattern.match(first_name):
        message = f'First name must be only letters and at least 2 characters: {first_name}'
        return message

    if last_name is not None and not lname_pattern.match(last_name):
        message = f'Last name must be only letters and at least 2 characters: {last_name}'
        return message

    if password1 is not None and password2 is not None:
        if password1 != password2:
            message = 'Passwords do not match.'
            return message

        if not password_pattern.match(password1):
            message = 'Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special symbol.'
            return message
    return True


def validate_booking_details(entry_date, exit_date, user_id, travel_agent_license):
    if exit_date <= entry_date:
        flash("Exit date must be after entry date.", category="error")
        return True
    
    client = User.query.filter_by(id=user_id, travel_agent_license=current_user.license).first()
    
    if not client:
        flash("Invalid user ID.", category="error")
        return True
    
    if str(travel_agent_license) != str(current_user.travel_agent_license):
        flash("Invalid travel agent license.", category="error")
        return True
    
    return False
    

def is_capacity_available(lounge_id, entry_date, exit_date, guests_qty, booking_id=None):
    # Get all bookings for the lounge, excluding the current booking (if any)
    bookings = Booking.query.filter(
        Booking.lounge_id == lounge_id,
        Booking.id != booking_id  # Exclude current booking if provided
    ).all()
    
    # Track daily capacity usage
    daily_capacity = {}  # Key: date, Value: total guests

    # Populate daily capacity from existing bookings
    for booking in bookings:
        current_date = booking.entry_date
        while current_date < booking.exit_date:  # For each day in the booking range
            daily_capacity[current_date] = daily_capacity.get(current_date, 0) + booking.guests_qty
            current_date += timedelta(days=1)
    
    # Check the requested range for capacity
    current_date = entry_date
    while current_date < exit_date:  # For each day in the requested range
        if daily_capacity.get(current_date, 0) + guests_qty > Lounge.query.get(lounge_id).max_capacity:
            return False  # Capacity exceeded on this date
        current_date += timedelta(days=1)

    return True  # Booking can be accommodated
