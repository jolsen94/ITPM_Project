from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from . import db, login_required_and_verified, admin_required, travel_agent_required
from .models import Booking, Lounge, TravelAgent, Enquiry, Reply
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import current_user
from os import path, makedirs, rename, listdir

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    lounges = Lounge.query.all()
    lounge_images = {}

    for lounge in lounges:
        lounge_img_dir = lounge.image_folder
        image_files = []
        for file in listdir(lounge_img_dir):
            file_path = path.join(lounge_img_dir, file)
            relative_path = path.join('images/lounges', lounge.address, file)
            relative_path = relative_path.replace('\\', '/')
            image_files.append(relative_path)
        if image_files:
            lounge_images[lounge.address] = image_files

    # TODO: provide a lounges search feature
    
    travel_agents = TravelAgent.query.all()
    travel_agents_images = {}

    for agent in travel_agents:
        agent_img_dir = agent.image_folder
        image_files = []
        for file in listdir(agent_img_dir):
            file_path = path.join(agent_img_dir, file)
            relative_path = path.join('images/travel-agents', agent.license, file)
            relative_path = relative_path.replace('\\', '/')
            image_files.append(relative_path)
        if image_files:
            travel_agents_images[agent.license] = image_files
    
    # TODO: provide a list of travel agents and a search feature
    
    return render_template("main/home.html", lounges=lounges, lounge_images=lounge_images, 
                            travel_agents=travel_agents, travel_agents_images=travel_agents_images)


@views.route('/about')
def about():
    return render_template("main/about.html")


@views.route('/general-info')
def general_info():
    return render_template("main/general-info.html")


@views.route('/privacy-policy')
def privacy_policy():
    return render_template("main/privacy.html")


@views.route('/terms-conditions')
def terms_condition():
    return render_template("main/terms.html")


@views.route('/feedback')
def feedback():
    return render_template("main/feedback.html")


@views.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    lounge_id = request.form.get('lounge_id')
    lounge = Lounge.query.filter_by(id=lounge_id).first()
    return render_template("main/contact-us.html", lounge=lounge)


@views.route('/view-enquiry/<int:enquiry_id>', methods=['GET', 'POST'])
@login_required_and_verified
def view_enquiry(enquiry_id):
    enquiry = Enquiry.query.filter_by(id=enquiry_id).first()
    replies = Reply.query.filter_by(enquiry_id=enquiry.id).all()
    
    return render_template('main/view-enquiry.html', enquiry=enquiry, replies=replies)


@views.route('/create-reply', methods=['POST'])
@login_required_and_verified
def create_reply():
    user_id = request.form.get('user_id')
    enquiry_id = request.form.get('enquiry_id')
    content = request.form.get('content')
    
    new_reply = Reply(user_id=user_id, enquiry_id=enquiry_id, content=content)
    
    if new_reply:
        db.session.add(new_reply)
        db.session.commit()
        flash('Reply successfully submitted.', category='success')
    else:
        flash('An error occurred. Reply not delivered.', category='error')
    
    return redirect(request.referrer)


@views.route('/delete-enquiry', methods=['POST'])
@login_required_and_verified
def delete_enquiry():
    enquiry_id = request.form.get('enquiry_id')
    
    enquiry = Enquiry.query.filter_by(id=enquiry_id).first()
    replies = Reply.query.filter_by(enquiry_id=enquiry_id).all()
    
    if replies:
        for reply in replies:
            db.session.delete(reply)
    
    if enquiry:
        db.session.delete(enquiry)
    else:
        flash('Enquiry not found', category='error')
        return redirect(url_for('auth.dashboard'))
    
    db.session.commit()
    
    flash('Enquiry and all associated replies have been deleted', category='success')
    
    return redirect(url_for('auth.dashboard'))

@views.route('/enquiry', methods=['POST'])
def enquiry():
    agent_id = request.form.get('agent_id')
    user_id = request.form.get('user_id')
    topic = request.form.get('topic')
    message = request.form.get('message')
    agree = request.form.get('agree')
    is_admin = request.form.get('is_admin') == 'True'
    
    if not agree:
        flash('You must agree to be contacted by the agent.', category='error')
        return redirect(request.referrer)
    
    new_enquiry = Enquiry(
        user_id=user_id,
        agent_id=agent_id,
        topic=topic,
        message=message,
        is_admin=is_admin
    )
    
    db.session.add(new_enquiry)
    db.session.commit()
    
    flash('Thank you for your enquiry. You will hear a response shortly.', category='success')
    return redirect(request.referrer)


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg'}

    if '.' in filename:
        parts = filename.rsplit('.', 1)
        extension = parts[1].lower()
        if extension in allowed_extensions:
            return True
    return False