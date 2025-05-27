from flask import Blueprint, render_template, current_app, request, flash, jsonify, redirect, url_for
from . import db, login_required_and_verified, admin_required
from .models import TravelAgent
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from flask_login import current_user
from os import path, makedirs, rename, listdir

travelAgents = Blueprint('travel_agents', __name__)


@travelAgents.route('/agent/<string:agent_company>', methods=['GET', 'POST'])
def view_agent(agent_company):
    agent = TravelAgent.query.filter_by(company=agent_company).first()
    agent_images = []

    if agent:
        agent_img_dir = agent.image_folder
        for file in listdir(agent_img_dir):
            relative_path = path.join('images/travel-agents', agent.license, file)
            relative_path = relative_path.replace('\\', '/')
            agent_images.append(relative_path)

    return render_template('main/agent-details.html', agent=agent, agent_images=agent_images)


@travelAgents.route('/add-agent-images', methods=['POST'])
def add_agent_images():
    if 'images' not in request.files:
        flash('Files not uploaded correctly!', category='error')
        return redirect(request.referrer)

    files = request.files.getlist('images')
    agent_id = request.form.get('agent_id')
    agent_img_dir = TravelAgent.query.filter_by(id=agent_id).first().image_folder
    files_accepted = False
    for file in files:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = path.join(agent_img_dir, filename)
            file.save(file_path)
            files_accepted = True
    # BEFORE UPLOADING FILES, THEY SHOULD BE COMPRESSED TO MAXIMUM 1080P QUALITY (1080P MAX WIDTH)
    if files_accepted:
        flash('Image(s) saved Successfully', category='success')
    else:
        flash('File type must be jpg, jpeg, or png only.', category='error')
    return redirect(request.referrer)


@travelAgents.route('/delete-agent', methods=['POST'])
@admin_required
def delete_agent():
    id = request.form.get('id')
    agent = TravelAgent.query.get(id)
    agent_license = agent.license
    agent_img_file_dir = agent.image_folder

    if path.exists(agent_img_file_dir):
        deleted_agent_dir = path.join(path.dirname(agent_img_file_dir), 'deleted ' + path.basename(agent_img_file_dir))
        rename(agent_img_file_dir, deleted_agent_dir)

    db.session.delete(agent)
    db.session.commit()

    flash(f'{agent_license} has been removed from the database!', category='success')

    flash(f'Image folder for Agent {agent_license} has been prefixed with \'deleted\'')

    return redirect(url_for('views.home'))


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg'}

    if '.' in filename:
        parts = filename.rsplit('.', 1)
        extension = parts[1].lower()
        if extension in allowed_extensions:
            return True
    return False