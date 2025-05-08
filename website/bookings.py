from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from . import db, login_required_and_verified, admin_required
from .models import Booking, Lounge
from datetime import datetime, timedelta
from flask_login import current_user
from os import path, listdir

booking = Blueprint('bookings', __name__)

@booking.route('/create-booking/<int:lounge_id>', methods=['GET', 'POST'])
@login_required_and_verified
def create_booking(lounge_id):
    lounge = Lounge.query.filter_by(id=lounge_id).first()
    lounge_images = []

    if lounge:
        lounge_img_dir = lounge.image_folder
        for file in listdir(lounge_img_dir):
            relative_path = path.join('images/lounges', lounge.address, file)
            relative_path = relative_path.replace('\\', '/')
            lounge_images.append(relative_path)
            
    # Calculate current capacity based on existing bookings
    current_capacity = sum(
        booking.guests_qty for booking in Booking.query.filter_by(lounge_id=lounge_id).all()
    )
    
    remaining_capacity = lounge.max_capacity - current_capacity
    
    if request.method == "POST":        
        user_id = request.form.get('user_id')
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
        
        if validate_booking_details(entry_date, exit_date, user_id, travel_agent_license):
            return redirect(request.referrer)
           
        # Create the booking if capacity checks pass
        new_booking = Booking(
            lounge_id=lounge_id,
            user_id=current_user.id,
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
        
        return redirect(url_for('bookings.view_booking', booking_id=new_booking.id))

    return render_template('main/create-booking.html', lounge=lounge, 
            remaining_capacity=remaining_capacity, lounge_images=lounge_images, 
            current_capacity=current_capacity)


@booking.route('/booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required_and_verified
def view_booking(booking_id):    
    booking = Booking.query.filter_by(id=booking_id).first()
    
    if current_user.user_type != "admin" and booking.user_id != current_user.id and booking.user.travel_agent_license != current_user.license:
        flash('Access Denied!', category='error')
        return redirect(url_for('views.home'))


    lounge = Lounge.query.filter_by(id=booking.lounge_id).first()
    lounge_images = []

    if lounge:
        lounge_img_dir = lounge.image_folder
        for file in listdir(lounge_img_dir):
            relative_path = path.join('images/lounges', lounge.address, file)
            relative_path = relative_path.replace('\\', '/')
            lounge_images.append(relative_path)
            
    return render_template('main/booking-details.html', booking=booking, lounge_images=lounge_images)
    

@booking.route('/all-bookings', methods=['GET', 'POST'])
@login_required_and_verified
def view_all_bookings():
    if current_user.user_type == "admin":
        bookings = Booking.query.all()
        lounges = list({booking.lounge for booking in bookings})
        
    elif current_user.user_type == "travel_agent":
        bookings = Booking.query.filter_by(travel_agent_license=current_user.license).all()
        lounges = list({booking.lounge for booking in bookings})
        
    elif current_user not in ["admin", "travel_agent"]:
        flash("Access Denied!", category='error')
        return redirect('views.home')

    return render_template('main/all-bookings.html', bookings=bookings, lounges=lounges)


@booking.route('/delete-booking', methods=['POST'])
@login_required_and_verified
def delete_booking():
    booking_id = request.form.get('booking_id')
    booking = Booking.query.filter_by(id=booking_id).first()
    
    if not booking:
        flash('Booking details not found', category='error')
        return redirect(request.referrer)
    
    if current_user.user_type != "admin" and current_user.license != booking.user.travel_agent_license and current_user.id != booking.user.id:
        flash('Access Denied', category='error')
        return redirect(url_for('views.home'))
        
    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash('Booking has been successfully deleted', category='success')
    else:
        flash('Booking was not found in database', category='error')
    
    return redirect(request.referrer)


@booking.route('/change-booking', methods=['POST'])
@login_required_and_verified
def change_booking():
    user_updated = False
    
    user_id = request.form.get('user_id')
    travel_agent_license = request.form.get('travel_agent_license')
    booking = Booking.query.filter_by(user_id=user_id).first()
    lounge = Lounge.query.filter_by(id=booking.lounge_id).first()
    
    entry_date_str = request.form.get('entry_date')
    exit_date_str = request.form.get('exit_date')
    
    new_entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
    new_exit_date = datetime.strptime(exit_date_str, '%Y-%m-%d').date()
    
    new_guests_qty = int(request.form.get('guests_qty'))
    new_flight_id = request.form.get('flight_id')
    new_dietary_req = request.form.get('dietary_req')
    
    if not is_capacity_available(lounge.id, new_entry_date, new_exit_date, new_guests_qty, booking.id):
            flash("Not enough capacity for the selected dates.", category="error")
            return redirect(request.referrer)
    
    if validate_booking_details(new_entry_date, new_exit_date, user_id, travel_agent_license):
        return redirect(request.referrer)
        
    # Fields to check and update dynamically
    fields_to_update = {
        "lounge_id": lounge.id,
        "user_id": user_id,
        "entry_date": new_entry_date,
        "exit_date": new_exit_date,
        "guests_qty": new_guests_qty,
        "flight_id": new_flight_id,
        "dietary_req": new_dietary_req
    }

    for field, new_value in fields_to_update.items():
        if getattr(booking, field) != new_value:
            setattr(booking, field, new_value)
            user_updated = True

    if user_updated:
        try:
            db.session.commit()
            flash('Booking updated successfully!', category='success')
            return redirect(url_for('emails.change_details'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating booking: {e}", category='error')
            return redirect(request.referrer)
    else:
        flash('No changes detected.', category='error')
        return redirect(request.referrer)
            
    return redirect(request.referrer)


def validate_booking_details(entry_date, exit_date, user_id, travel_agent_license):
    # Ensure exit date is after entry date
    if exit_date <= entry_date:
        flash("Exit date must be after entry date.", category="error")
        return True

    # Allow if the user is accessing their own booking
    if int(user_id) == current_user.id:
        return False

    # Allow if the current user is an travel_agent (can act on behalf of their clients)
    if current_user.user_type == "travel_agent":
        return False

    # Allow if the current user is an admin (can act on behalf of anyone)
    if current_user.user_type == "admin":
        return False

    # Otherwise, deny access
    flash("Unauthorized action.", category="error")
    return True

    
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
