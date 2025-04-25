from flask import Blueprint, render_template
from .models import Verification
from flask_login import current_user

emails = Blueprint('emails', __name__)

# |------------LISTSERV LOGIC------------|
# msg = Message(subject, recipients=recipients, body=body)

# msg.mail_options = smtp_settings.get('mail_options', [])
# msg.rcpt_options = smtp_settings.get('rcpt_options', [])

# mail.username = smtp_settings['MAIL_USERNAME']
# mail.password = smtp_settings['MAIL_PASSWORD']
# msg.sender = smtp_settings['MAIL_USERNAME']

# mail.send(msg)
# currently not working as no private domain, and public domain smtp options require payment
# instead, we will be generating email templates with html.
# once we have a private domain, we will replace the body with the render_template('html')
# |------------LISTSERV LOGIC------------|

@emails.route('/welcome')
def welcome_email():
    body = render_template('email/welcome_email.html')
    return body


@emails.route('/farewell')
def farewell_email():
    body = render_template('email/farewell_email.html')
    return body


@emails.route('/new_sub')
def new_sub():
    body = render_template('email/new_sub_email.html')
    return body


@emails.route('/verify_account')
def verify_account():
    # to send an email ONLY
    # logic to get here needs to be secure!
    code = Verification.query.filter_by(user_id=current_user.id).first().code
    body = render_template('email/verification_email.html', code=code)
    return body


@emails.route('/change_details')
def change_details():
    body = render_template('email/change_details_email.html')
    return body