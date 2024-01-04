import ast
import csv
import json
import os
import random
import string
from datetime import datetime
from functools import wraps

from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, app, db
from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from form import ContactForm, LoginForm, SignupForm
from model import ContactUs, User
from utility import (allowed_file, generate_unique_filename, process_data,
                     read_questions_from_csv)
from werkzeug.utils import secure_filename
from wtforms import (PasswordField, StringField, SubmitField, TextAreaField,
                     validators)



# create a decorator function that checks if the user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function 


@app.route('/', methods=['GET', 'POST'])
def home():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Create a new contact record and add to the database
            name = form.name.data
            email = form.email.data
            message = form.message.data

            contact_entry = ContactUs(name=name, email=email, message=message)
            db.session.add(contact_entry)
            db.session.commit()

            print('somfgslkdfgs')
            flash('Message sent successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Please enter a complete email.', 'danger')
    return render_template('index.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def profile_update():
    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        role = request.form.get('role')
        affiliation = request.form.get('affiliation')

        # Update profile picture
        if 'profile_picture' in request.files:
            profile_picture = request.files['profile_picture']
            if profile_picture and allowed_file(profile_picture.filename):
                filename = secure_filename(profile_picture.filename)
                unique_filename = generate_unique_filename(filename)  # Generate a unique filename
                profile_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                profile_picture.save(profile_picture_path)
                user.profile_picture = unique_filename
            # else:
            #     flash('Invalid file type.', 'danger')
            #     return redirect('/profile/update')

        user.name = name
        user.description = description
        user.role = role
        user.affiliation = affiliation

        db.session.commit()

        flash('Profile updated successfully.', 'success')
        return redirect('/profile')

    return render_template('profile_update.html', profile_picture_url=user.profile_picture, name=user.name, description=user.description, role=user.role, affiliation=user.affiliation)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Check if user exists in the database and password is correct
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            # Set user session data
            session['user_id'] = user.id
            session['username'] = user.username

            if user.score == {}:
                flash('Please submit a survey first.', 'danger')
                return redirect('/survey')

            return redirect('/profile')

        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     return render_template('dashboard.html', results=db.session.query(User).filter_by(username=session['username']).first().score)




@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(username=session['username']).first()
    return render_template('profile.html', user=user, results=user.score)

@app.route('/marketplace')
@login_required
def marketplace():
    # read from the database and marketplace table and generate a list of recommendations based on combined score and range of scores, and display them on the marketplace page
    # 1. get the combined score
    # 2. get the range of scores
    # 3. get the recommendations
    # 4. display the recommendations on the marketplace page
    user = User.query.filter_by(username=session['username']).first()
    if user.score == {}: 
        flash('Please submit a survey first.', 'danger')
        return redirect('/survey')
    combined_score = user.score['Combined Score']['assessment score']
    recommendations = []
    with open('marketplace.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            recommendations.append(row)


    # delete recommendations that are not in the range of scores 
    for recommendation in recommendations:
        recommendation['range'] = int(recommendation['range'])
        recommendation['combined score'] = int(recommendation['combined score'])
        if combined_score < int(recommendation['combined score']) or combined_score > int(recommendation['combined score'] + recommendation['range']):
            recommendations.remove(recommendation)

    return render_template('marketplace.html', recommendations=recommendations, user=user)

@app.route('/logout')
def logout():
    # Clear the user session data
    session.clear()
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        # Create a new user and add to the database
        username = form.username.data
        password = form.password.data
        name = form.name.data
        description = form.description.data
        role = form.role.data
        affiliation = form.affiliation.data
        confirm_password = form.confirm_password.data

        if password != confirm_password:
            # Passwords don't match, set error message
            # print('Passwords do not match.')
            flash('Passwords do not match.', 'danger')
        elif User.query.filter_by(username=username).first():
            # Username already exists, set error message
            # print('Username already exists.')
            flash('Username already exists.', 'danger')
        else:
            user = User(username=username, password=password, response={}, score = {}, profile_picture='', name=name, description=description, role=role, affiliation=affiliation)
            db.session.add(user)
            db.session.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('login'))  # Redirect to login page

    return render_template('signup.html', form=form)

@app.route('/submit', methods=['POST'])
@login_required
def submit_survey():
    questions = read_questions_from_csv()
    answers = {}

    for question in questions:
        q_id = str(question['id'])
        if question['type'] == 'select-one':
            if question['options']:
                options = question['options']
                if len(options) > 1:
                    answers[q_id] = request.form.getlist(q_id)
                else:
                    answers[q_id] = request.form.get(q_id)
        elif question['type'] == 'Short Answer':
            answers[q_id] = request.form.get(q_id)
    
    # Process the answers (you can store them in a database, etc.)
    score = 0
    response = []   

    # questions is list of dictionaries
    # question is a dictionary
    # answers is a dictionary with key as question id and value as answer

    # print(answers)
    for key, value in answers.items():
        value = ast.literal_eval(value[0])

        for question in questions:
            if question['id'] == key:
                response.append(dict({'id': key,'score': value[1], 'section': question['section'], 'subsection':question['subsection']}))

    db.session.query(User).filter_by(username=session['username']).update({'response': response})
    db.session.commit()   

    process_data(response)
    flash('Survey submitted successfully.', 'success')
    return redirect('/profile')

@app.route('/survey')
@login_required
def survey():
    questions = read_questions_from_csv()
    return render_template('survey.html', questions=questions)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)







'''
{% extends "base.html" %}

{% block content %}



<style>
    /* Updated color scheme */
    :root {
        --highlight-blue: #3498db;
        --highlight-green: #2ecc71;
        --line-color: #3498db;
        /* New variable for line color */
    }

    .profile-card,
    .description-card {
        margin-bottom: 20px;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
    }

    .category-min-max {
        font-size: 12px;
        color: var(--highlight-blue);
        /* Updated to use highlight blue */
    }

    .col-md-4 {
        display: flex;
        flex-direction: column;
    }

    .profile-info-card {
        display: flex;
        flex-direction: column;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        padding: 20px;
    }

    .profile-info {
        display: flex;
        align-items: center;
        margin-top: 20px;
    }

    .profile-picture {
        margin-right: 20px;
    }

    #profile-picture-preview {
        max-width: 100px;
        border-radius: 50%;
        object-fit: cover;
    }

    #profile-picture-input {
        display: none;
    }

    .profile-details {
        flex: 1;
    }

    #username-input,
    #description-input {
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 14px;
    }

    #description-input {
        resize: vertical;
    }

    .progress {
        height: 8px;
        margin-top: 8px;
    }

    .mastery {
        font-size: 14px;
        font-weight: bold;
        color: var(--highlight-blue);
        /* Updated to use highlight blue */
    }

    .next-steps {
        margin-top: 8px;
    }

    .card.description-card .mb-4.active {
        background-color: var(--highlight-blue);
        /* Updated color */
    }

    /* Updated color for progress bar */
    .progress-bar {
        background-color: var(--highlight-green);
    }

    /* New rule for horizontal lines */
    hr {
        border-color: var(--line-color);
    }
</style>

<body>

    <div class="container mt-5">
        <div class="row equal-heigh">
            <div class="col-md-4">
                <div class="card profile-info-card">
                    <div class="card-header bg-white">
                        <h4>Profile Information</h4>
                    </div>
                    <div class="card-body">
                        <div class="profile-info">
                            <div class="profile-picture">
                                <img id="profile-picture-preview" src="static/uploads/{{ user.profile_picture }}"
                                    alt="Profile Picture">
                                <input type="file" id="profile-picture-input">
                            </div>
                            <div class="profile-details">
                                <p>{{ user.name }}</p>
                                <p>{{ user.description }}</p>
                                <a class="nav-link" href="{{ url_for('profile_update') }}">Update Profile</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-8">
                <div class="card profile-info-card">
                    <div class="card-header bg-white">
                        <h4>Interim Space</h4>
                    </div>
                    <div class="card-body">
                        <div class="profile-info">
                            <div class="profile-picture">

                            </div>
                            <div class="profile-details">
                                <!-- space to show the combined score -->
                                {% for key, value in results.items() %}
                                {% if key in ['Combined Score'] %}
                                <div class="d-flex align-items-center justify-content-between">
                                    <strong>{{ key }}</strong> {{ value['assessment score'] }}
                                    <span class="mastery">{{ value['classification'] }}</span>
                                </div>
                                <div class="progress mt-2">
                                    <div class="progress-bar" role="progressbar"
                                        style="width: {{ value['percentage'] }}%;"
                                        aria-valuenow="{{ value['percentage'] }}" aria-valuemin="0" aria-valuemax="100">
                                    </div>
                                </div>
                                {% endif %}
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card profile-card">
                    <div class="card-body">
                        <div>
                            <h4 class="card-title">Score Overview</h4>
                            <span class="category-min-max">Min: 40 / Max: 160</span>
                        </div>
                        <div class="d-flex flex-wrap justify-content-between">
                            {% for key, value in results.items() %}
                            {% if key not in ['Combined Score'] %}
                            <div class="col-md-4 mb-4" style="padding-left: 1%;">
                                <div class="d-flex align-items-center justify-content-between">
                                    <strong>{{ key }}</strong> {{ value['assessment score'] }}
                                    <span class="mastery">{{ value['classification'] }}</span>
                                </div>
                                <div class="progress mt-2">
                                    <div class="progress-bar" role="progressbar"
                                        style="width: {{ value['percentage'] }}%;"
                                        aria-valuenow="{{ value['percentage'] }}" aria-valuemin="0" aria-valuemax="100">
                                    </div>
                                </div>




                                
                            </div>
                            {% endif %}
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card profile-card">
                    <div class="card-body">
                        <h4 class="card-title">Description and Next Steps</h4>
                        <div class="row">
                            {% for key, value in results.items() %}
                            {% if key not in ['Combined Score', 'Develop', 'Discover'] %}
                            <div class="col-md-6">
                                <div class="mb-4">
                                    {% if key in ['Discover Self', 'Discover Opportunities', 'Develop Skills', 'Develop
                                    Relationships'] %}
                                    <h5>{{key.split(' ')[0]}}: {{ key }}</h5>
                                    {% else %}
                                    <h5>{{ key }}</h5>
                                    {% endif %}
                                    <p>Score: {{ value['assessment score'] }}</p>
                                    <p class="mastery">Mastery: {{ value['classification'] }}</p>
                                    <p>{{ value['description'] }}</p>
                                    <p class="next-steps"><strong>Next Steps:</strong> {{ value['next steps'] }}</p>
                                </div>
                            </div>
                            {% else %}
                            <div class="col-md-6">
                                <div class="mb-4">
                                    <h5>{{ key }}</h5>
                                    <p>Score: {{ value['assessment score'] }}</p>
                                    <p class="mastery">Mastery: {{ value['classification'] }}</p>
                                    <p>{{ value['description'] }}</p>
                                </div>
                            </div>
                            {% endif %}
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div class="text-center mt-3">
        <button class="btn btn-primary" id="print-button" style="margin-bottom:1%">Print Profile</button>
    </div>

    <script>
        const categoryCards = document.querySelectorAll('.card.description-card .mb-4');
        categoryCards.forEach(card => {
            card.addEventListener('click', () => {
                categoryCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            });
        });

        const printButton = document.getElementById('print-button');
        printButton.addEventListener('click', () => {
            window.print();
        });

        // Profile Picture Upload
        const profilePictureInput = document.getElementById('profile-picture-input');
        const profilePicturePreview = document.getElementById('profile-picture-preview');

        profilePictureInput.addEventListener('change', function (event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function () {
                    profilePicturePreview.src = reader.result;
                };
                reader.readAsDataURL(file);
            }
        });

        // Popup Functionality
        const profileInfoCard = document.querySelector('.profile-info-card');
        const profileDetails = document.querySelector('.profile-details');

        profileInfoCard.addEventListener('click', function () {
            profileDetails.classList.add('active');
        });

        profileDetails.addEventListener('click', function (event) {
            event.stopPropagation();
        });

        document.addEventListener('click', function () {
            profileDetails.classList.remove('active');
        });
    </script>

</body>
{% endblock %}

 <div class="card profile-info-card">
     
                        <div class="profile-info">
                            <div class="profile-picture">

                            </div>
                            <div class="profile-details">
                                <!-- space to show the combined score -->
                                {% for key, value in results.items() %}
                                {% if key in ['Combined Score'] %}
                                <div class="d-flex align-items-center justify-content-between">
                                    <strong>{{ key }}</strong> {{ value['assessment score'] }}
                                    <span class="mastery">{{ value['classification'] }}</span>
                                </div>
                                <div class="progress mt-2">
                                    <div class="progress-bar" role="progressbar"
                                        style="width: {{ value['percentage'] }}%;"
                                        aria-valuenow="{{ value['percentage'] }}" aria-valuemin="0" aria-valuemax="100">
                                    </div>
                                </div>


                                {% endif %}
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                
            </div>



'''