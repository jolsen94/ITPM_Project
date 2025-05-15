from flask import Blueprint, render_template, current_app, request, flash, jsonify, redirect, url_for
from . import db, login_required_and_verified, admin_required
from .models import Lounge, Booking
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import current_user
from os import path, makedirs, rename, listdir

lounge = Blueprint('lounges', __name__)


@lounge.route('/create-lounge', methods=['GET', 'POST'])
@admin_required
def create_lounge():
    if request.method == "POST":
        desc = request.form.get('description')
        address = request.form.get('address')
        state = request.form.get('state')
        postcode = request.form.get('postcode')
        locality = request.form.get('locality')
        
        if Lounge.query.filter_by(address=address).first():
            flash('Error: Lounge already exists with the same address in the database!', category='error')
            return redirect(url_for('lounges.create_lounge'))
        
        # create new directory for lounge images
        image_dir = path.join(current_app.root_path, 'static/images/lounges')
        lounge_addr_dir = path.join(image_dir, address)
        if not path.exists(lounge_addr_dir):
            makedirs(lounge_addr_dir)
            flash(f'Created new directory: {address}', category='success')
        else:
            flash('Error: Lounge exists with same address! Lounge not created!')
            return redirect(url_for('lounges.create_lounge'))
            
        new_lounge = Lounge(description=desc, address=address, state=state, 
                    postcode=postcode, locality=locality, image_folder=lounge_addr_dir)
        db.session.add(new_lounge)
        db.session.commit()
        
        return redirect(url_for('views.home'))
    
    return render_template("main/create-lounge.html")


@lounge.route('/lounge/<int:lounge_id>', methods=['GET', 'POST'])
def view_lounge(lounge_id):
    lounge = Lounge.query.filter_by(id=lounge_id).first()
    lounge_images = []
    bookings = None
    
    if current_user.is_authenticated:
        bookings = Booking.query.filter_by(lounge_id=lounge.id, user_id=current_user.id).all()

    if lounge:
        lounge_img_dir = lounge.image_folder
        for file in listdir(lounge_img_dir):
            relative_path = path.join('images/lounges', lounge.address, file)
            relative_path = relative_path.replace('\\', '/')
            lounge_images.append(relative_path)

    return render_template('main/lounge-details.html', lounge=lounge, bookings=bookings, lounge_images=lounge_images)


@lounge.route('/add-lounge-images', methods=['POST'])
@admin_required
def add_lounge_images():
    if 'images' not in request.files:
        flash('Files not uploaded correctly!', category='error')
        return redirect(request.referrer)

    files = request.files.getlist('images')
    lounge_id = request.form.get('lounge_id')
    lounge_img_dir = Lounge.query.filter_by(id=lounge_id).first().image_folder
    files_accepted = False
    for file in files:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = path.join(lounge_img_dir, filename)
            file.save(file_path)
            files_accepted = True
    # BEFORE UPLOADING FILES, THEY SHOULD BE COMPRESSED TO MAXIMUM 1080P QUALITY (1080P MAX WIDTH)
    if files_accepted:
        flash('Image(s) saved Successfully', category='success')
    else:
        flash('File type must be jpg, jpeg, or png only.', category='error')
    return redirect(request.referrer)


@lounge.route('/close-lounge', methods=['POST'])
@admin_required
def close_lounge():
    lounge_id = request.form.get('lounge_id')
    lounge = Lounge.query.filter_by(id=lounge_id).first()
    
    if lounge:
        lounge.status = "Closed"
        db.session.commit()
    else:
        flash('Lounge not found in database: lounge has not been closed', category='error')
        
    return redirect(request.referrer)
    

@lounge.route('/reopen-lounge', methods=['POST'])
@admin_required
def reopen_lounge():
    lounge_id = request.form.get('lounge_id')
    lounge = Lounge.query.filter_by(id=lounge_id).first()
    
    if lounge:
        lounge.status = "Open"
        db.session.commit()
    
    else:
        flash('Lounge not found in database: lounge has not been re-opened', category='error')

    return redirect(request.referrer)


@lounge.route('/delete-lounge', methods=['POST'])
@admin_required
def delete_lounge():
    id = request.form.get('id')
    lounge = Lounge.query.get(id)
    lounge_addr = lounge.address
    lounge_img_file_dir = lounge.image_folder

    if path.exists(lounge_img_file_dir):
        deleted_lounge_dir = path.join(path.dirname(lounge_img_file_dir), 'deleted ' + path.basename(lounge_img_file_dir))
        rename(lounge_img_file_dir, deleted_lounge_dir)

    db.session.delete(lounge)
    db.session.commit()

    flash(f'{lounge_addr} has been removed from the database!', category='success')

    flash(f'Image folder for lounge at {lounge_addr} has been prefixed with \'deleted\'')

    return redirect(url_for('views.home'))


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg'}

    if '.' in filename:
        parts = filename.rsplit('.', 1)
        extension = parts[1].lower()
        if extension in allowed_extensions:
            return True
    return False