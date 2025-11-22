# Standard library imports
import os
import re
import shelve
from datetime import timedelta, datetime
import uuid
import csv
from functools import wraps

# Third-party library imports
from flask import Flask, render_template, request, jsonify, redirect, flash, url_for, session
from flask_mail import Mail, Message
import magic
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Local application imports
from accounts.admin import Admin
from utils.plot_utils import get_pageview_data

load_dotenv()

app = Flask(__name__)
app.secret_key = 'qwfgsgs23124'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'profiles') #path to save pfps to
app.config['MAX_CONTENT_LENGTH'] = 2*1024*1024 #2MB file limit
app.config.update(
    MAIL_SERVER=str(os.getenv('MAIL_SERVER')),
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=str(os.getenv('MAIL_USERNAME')),
    MAIL_PASSWORD=str(os.getenv('MAIL_PASSWORD')), # SMTP key
    MAIL_DEFAULT_SENDER=str(os.getenv('MAIL_DEFAULT_SENDER'))
)

# set up mail
mail = Mail(app)

# csv file for page view logging
LOG_FILE = 'page_views.csv'


# set permanent session lifetime to 70 days
app.permanent_session_lifetime = timedelta(days=70)

ADMIN_SHELVE_NAME = 'admin_accounts.db' # shelve file

ALLOWED_ADMIN_EMAILS = [
    "mockmock582@gmail.com",
    "epicaresystem@gmail.com"
]

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

serializer = URLSafeTimedSerializer(app.secret_key)

# Functions
def log_page_view(user=None):
    with open('page_views.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        user_type = 'Unknown'
        if user is not None:
            user_type = user.get_user_type()

        writer.writerow([datetime.now().isoformat(), user_type])


def send_mail(subject, recipients, body, html=None):
    '''
    Sends an email using Flask-Mail.
    
    :param subject: Email subject
    :param recipients: List of recipient emails
    :param body: Plain text body
    :param html: Optional HTML body
    :param sender: Optional override sender
    '''
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=str(os.getenv('MAIL_DEFAULT_SENDER'))
    )
    msg.body = body
    if html:
        msg.html=html
    mail.send(msg)
    print('success')


def is_valid_email(email):
    '''check for email validity using regex'''

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_regex, email)


def is_strong_password(password):
    '''check for password validity'''

    if len(password) < 8: # check for atleast 8 length
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password): # check for atleast one special char
        return False
    return True


def get_current_user():
    user_email = session.get('email')
    if not user_email:
        return None

    with shelve.open('admin_accounts.db', writeback=True) as db:
        user = db.get(user_email)
        if user:
            user.log_page_view() # logs page view for the user

    return user


# Decorator to ensure a user is logged in AND has the 'Admin' role
def admin_required(f):
    # @wraps(f) preserves the original function's name, docstring, etc.
    # Without it, Flask's routing, debugging, and help() might break or show "decorated_function" instead of the original.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        This inner function is what actually runs instead of your route
        when you apply @admin_required on it.
        """

        # 1. Check if the user is logged in (session stores their email after login)
        if 'email' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))

        # 2. Check if the logged-in user is an Admin
        with shelve.open(ADMIN_SHELVE_NAME) as db:
            admin = db.get(session['email'])
            # Reject if the user doesn't exist OR is not an Admin
            if not admin or admin.get_user_type() != 'Admin':
                flash("You do not have permission to view this page.", "danger")
                return redirect(url_for('login'))

        # 3. If all checks pass, run the original route function
        return f(*args, **kwargs)

    return decorated_function  # This replaces your route function when decorated


def get_user_counts():
    counts = {
        'PWID': 0,
        'Caretaker': 0
    }

    with shelve.open(ADMIN_SHELVE_NAME) as db:
        for key in db:
            user = db[key]
            if user.get_user_type() == 'PWID':
                counts['PWID'] += 1
            elif user.get_user_type() == 'Caretaker':
                counts['Caretaker'] += 1
        
        return counts
    
def get_total_page_views_current_year(year_offset=0):
    """Returns total page views for a given year offset."""

    target_year = datetime.now().year - year_offset
    count = 0

    with open(LOG_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ts = datetime.fromisoformat(row['timestamp'])
            if ts.year == target_year:
                count += 1
    return count

# ─────────── Routes ───────────

# ─────────── Auth Routes (Unauthenticated) ───────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''login page'''

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember =  request.form.get('remember') # 'on' if checkbox is checked

        with shelve.open(ADMIN_SHELVE_NAME) as db:
            if email in db:
                admin = db[email]
                if admin.get_password() == password:
                    session['email'] = email
                    session.permanent = bool(remember)
                    return redirect(url_for('home'))
                else:
                    flash('Incorrect password.', 'danger')
            else:
                flash('Email not found.', 'danger')

    log_page_view() # log the page view
    return render_template('login.html')

@app.route('/logout')
def logout():
    '''logs out the current user'''

    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''register page'''

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        if not is_valid_email(email):
            flash('Invalid email format.', 'danger')
            return redirect(url_for('register'))

        if not is_strong_password(password):
            flash('Password must be at least 8 characters long ' \
            'and a special character.')
            return redirect(url_for('register'))


        if email not in ALLOWED_ADMIN_EMAILS:
            flash("Email not authorized to register as admin", "danger")
            return redirect(url_for("register"))

        username = email.split('@')[0]

        with shelve.open(ADMIN_SHELVE_NAME) as db:

            # check if user exists
            if email in db:
                flash('User already exists. Please Login instead.', 'warning')
                return redirect(url_for('register'))

            # create new admin user
            new_admin = Admin(username=username, email=email,
                              password=password, job='Administrator')

            db[email] = new_admin

        flash('Admin account created successfully!', 'success')
        return redirect(url_for('login'))

    log_page_view() # log the page view
    return render_template('register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    '''page to submit email to send password reset link'''

    if request.method == 'POST':
        email = request.form.get('email')

        with shelve.open(ADMIN_SHELVE_NAME) as db:
            if email in db:
                # Generates a token that will expire after time
                token = serializer.dumps(email, salt='reset-password')

                # Create reset link
                reset_url = url_for('reset_password', token=token, _external=True)

                subject = 'Reset Your Epicare Password'
                body=f'Hi, you requested a password reset. Click the link below to reset your password:\n{reset_url}'

                send_mail(subject, [email], body, html=render_template('partials/reset-password-email.html', reset_url=reset_url))

        flash('Password reset link has been sent to the email', 'info')
        return redirect(url_for('check_mail')) # redirect to check-mail page
    
    log_page_view() # log the page view
    return render_template('forgot-password.html')


@app.route('/reset-password-mail')
def check_mail():
    '''After user submits email to get password change'''

    log_page_view() # log the page view
    return render_template('check-mail.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    '''page to reset password after user clicks link in email'''

    try:
        # deserialize email from token, expire after 1 hour
        email = serializer.loads(token, salt='reset-password', max_age=3600)

    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('login'))
    except BadSignature:
        flash("Invalid reset link.", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset-password.html', token=token)
        
        if not is_strong_password(password):
            flash('Password must be at least 8 characters long ' \
            'and a special character.')
            return render_template('reset-password.html', token=token)
        
        with shelve.open(ADMIN_SHELVE_NAME, writeback=True) as db:
            if email in db:
                db[email].set_password(password)
                flash('Password successfully updated.', 'success')
                return redirect(url_for('login'))

            else:
                flash('User no longer exists', 'danger')

    return render_template('reset-password.html')

# ─────────── Content Routes (Authenticated) ───────────

@app.route('/')
@admin_required
def home():
    '''Home/Dashboard page (page user logs into)'''


    user = get_current_user()
    
    log_page_view(user) # log the page view



    return render_template('home.html', user=user)



@app.route('/total-pageview-data')
@admin_required
def total_pageview_data():
    '''retrieves total page views'''

    current_year_views = get_total_page_views_current_year()
    previous_year_views = get_total_page_views_current_year(1) or 0
    return jsonify({"current_year": current_year_views,
                    "last_year": previous_year_views})


@app.route('/pageview-data')
@admin_required
def pageview_data():
    '''retrieve the chart data'''
    
    data = get_pageview_data('page_views.csv')
    return jsonify(data)


@app.route('/usercount-data')
@admin_required
def usercount_data():
    counts = get_user_counts()
    total_users = counts['PWID'] + counts['Caretaker']
    return jsonify({
        'Total_users' : total_users,
        'PWID': counts['PWID'],
        'Caretaker': counts['Caretaker']
    })


@app.route('/user-pwid')
@admin_required
def user_pwid():
    '''pwid table csv page'''
    user = get_current_user()

    users = []
    with shelve.open(ADMIN_SHELVE_NAME) as db:
        for key in db:
            u = db[key]
            # check if caretaker
            if u.get_user_type() == 'PWID':
                users.append(
                    {
                        'username': u.get_username(),
                        'email': u.get_email(),
                        'created_at': u.get_creation_date().strftime('%Y-%m-%d'), # format date
                        'page_views': u.get_page_views()
                    }
                )

    log_page_view(user) # log the page view
    return render_template('user-pwid.html', user=user, users=users)


@app.route('/user-caretaker')
@admin_required
def user_caretaker():
    '''caretaker table csv page'''
    user = get_current_user()

    users = []
    with shelve.open(ADMIN_SHELVE_NAME) as db:
        for key in db:
            u = db[key]
            # check if caretaker
            if u.get_user_type() == 'Caretaker':
                users.append(
                    {
                        'username': u.get_username(),
                        'email': u.get_email(),
                        'created_at': u.get_creation_date().strftime('%Y-%m-%d'), # format date
                        'page_views': u.get_page_views()
                    }
                )

    log_page_view(user) # log the page view
    return render_template('user-caretaker.html', user=user, users=users)


@app.route('/edit-profile', methods=['GET', 'POST'])
@admin_required
def edit_profile():
    '''edit user profile page'''
    user = get_current_user()

    if request.method=='POST':
        updated = False

        # Username update
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != user.get_username():
            user.set_username(new_username)
            updated = True

        # Profile picture update
        file = request.files.get('profile_picture')
        if file and file.filename.strip(): # checks if file exists and if filename is not empty
            file_bytes = file.read(2048) # read the file
            file.seek(0) # reset pointer after read

            mime_type = magic.from_buffer(file_bytes, mime=True)
            allowed_types = ['image/jpeg', 'image/png'] # allow only jpeg and png files

            if mime_type in allowed_types:
                # sanitize filename to prevent unsafe files
                filename = secure_filename(file.filename)

                # unique filename to avoid conflict
                unique_filename = f'{uuid.uuid4().hex}_{filename}'

                # build the path where file will be saved
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                # save uploaded file to filesystem
                file.save(file_path)

                user.profile_picture = os.path.join('uploads', 'profiles', unique_filename).replace("\\", '/')
                updated = True
            else:
                # if file type is invalid
                flash('Only .jpeg and .png files are allowed', 'danger')
                return redirect(url_for('edit_profile'))

        # save changes to shelve
        if updated:
            with shelve.open(ADMIN_SHELVE_NAME, writeback=True) as db:
                db[user.get_email()] = user
            flash('Profile updated successfully!', 'success')

        else:
            # no changes detected
            flash('No changes were made', 'info')

        #redirect to same page
        return redirect(url_for('edit_profile'))

    log_page_view(user) # log the page view
    # For GET requests, render template
    return render_template('edit-userprofile.html', user=user)


@app.route('/delete-account', methods=['GET', 'POST'])
@admin_required
def delete_account():
    '''delete account confirmation'''
    user = get_current_user()

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = session.get('email')

        # check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('delete_account'))
        
        # verify password against db
        with shelve.open(ADMIN_SHELVE_NAME) as db:
            if email in db:
                admin = db[email]
                if admin.get_password() == password:
                    # Password matches, proceed to delete

                    # delete user from shelve
                    del db[email]

                    # clear session
                    session.clear()

                    flash('Account successfully deleted', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Incorrect password.', 'danger')
                    return redirect(url_for('delete_account'))
            else:
                flash('ERROR', 'danger')
                return redirect(url_for('delete_account'))
    
    log_page_view(user) # log the page view
    return render_template('delete-account.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
