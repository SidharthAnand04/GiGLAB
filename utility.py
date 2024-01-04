import ast
import csv
import datetime
import random
import string
from datetime import datetime

from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, app, db
from model import ContactUs, User
from flask import session


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    random_string = ''.join(random.choices(string.ascii_lowercase, k=6))
    unique_filename = f"{current_time}_{random_string}_{filename}"
    return unique_filename



@app.teardown_appcontext
def teardown_appcontext(exception=None):
    db.session.remove()

def read_questions_from_csv():
    questions = []
    with open('questions.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            questions.append(row)

    for question in questions:
        # convert each option key value pair to a 2d list 
        if question['options']:
            question['options'] = ast.literal_eval(question['options'])

    return questions

def process_data(data):
    score_dict = {}
    rating = {}

    # TODO: change max score to be dynamic
    max_score = {'Discover': 43, 'Discover Self': 25, 'Discover Opportunities': 18, 'Develop': 79, 'Develop Skills': 24, 'Develop Network': 55, 'Differentiate': 36, 'Document': 26, 'Max': 184}

    for item in data:
        section = item['section']
        subsection = item['subsection']
        score = int(item['score'])

        if section in score_dict:
            score_dict[section] += score
        else:
            score_dict[section] = score

        if subsection in score_dict:
            score_dict[subsection] += score
        else:
            score_dict[subsection] = score
    
    rating['temp'] = {'raw': 1, 'max': 1, 'percentage': 1, 'assessment score': 1}
    rating['Discover'] = {'raw': score_dict['Discover Opportunities'] + score_dict['Discover Self'], 'max': max_score['Discover'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Develop'] = {'raw': score_dict['Develop Skills'] + score_dict['Develop Network'], 'max': max_score['Develop'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Differentiate'] = {'raw': score_dict['Differentiate'], 'max': max_score['Differentiate'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Document'] = {'raw': score_dict['Document'], 'max': max_score['Document'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Discover Self'] = {'raw': score_dict['Discover Self'], 'max': max_score['Discover Self'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Discover Opportunities'] = {'raw': score_dict['Discover Opportunities'], 'max': max_score['Discover Opportunities'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Develop Skills'] = {'raw': score_dict['Develop Skills'], 'max': max_score['Develop Skills'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Develop Network'] = {'raw': score_dict['Develop Network'], 'max': max_score['Develop Network'], 'percentage': 0, 'assessment score': 0, 'classification': ''}
    
    for key, value in rating.items():
        value['percentage'] = round(value['raw']/value['max'] * 100, 2)
        value['assessment score'] = round(value['percentage']*1.20 + 40)
        if value['assessment score'] >= 161:
            value['classification'] = 'Master'
        elif value['assessment score'] >= 101:
            value['classification'] = 'Pro'
        elif value['assessment score'] >= 61:
            value['classification'] = 'Apprentice'
        else:
            value['classification'] = 'Dabbler'

    # find the average score of Discover, Develop, Differentiate, Document and store in rating dict
    rating['Combined Score'] = {'raw': (rating['Discover']['assessment score'] + rating['Develop']['assessment score'] + rating['Differentiate']['assessment score'] + rating['Document']['assessment score']), 'max': 160, 'percentage': 0, 'assessment score': 0, 'classification': ''}
    rating['Combined Score']['assessment score'] = round(rating['Combined Score']['raw']/4)
    rating['Combined Score']['percentage'] = rating['Combined Score']['assessment score']/rating['Combined Score']['max'] * 100
    
    if rating['Combined Score']['assessment score'] >= 161:
            rating['Combined Score']['classification'] = 'Master'
    elif rating['Combined Score']['assessment score'] >= 101:
        rating['Combined Score']['classification'] = 'Pro'
    elif rating['Combined Score']['assessment score'] >= 61:
        rating['Combined Score']['classification'] = 'Apprentice'
    else:
        rating['Combined Score']['classification'] = 'Dabbler'
    
    rating['Combined Score']['description'] = ''

    descriptions = {}

    with open('descriptions.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            section = row['section']
            subsection = row['subsection']
            level = row['level']
            description = row['description']
            next_step = row['next steps']
            
            if subsection != 'None':
                descriptions[subsection] = {'classification':level, 'description': description, 'next steps': next_step}
            else:
                descriptions[section] = {'classification':level, 'description': description, 'next steps': next_step}

    for user_key, user_items in rating.items():
        try:
            rating[user_key]['description'] = descriptions[user_key]['description']
            rating[user_key]['next steps'] = descriptions[user_key]['next steps']
        except KeyError:
            rating[user_key]['description'] = ''
            rating[user_key]['next steps'] = ''

    i, j = 0, 9
    tups = list(rating.items())
    
    # swapping by indices
    tups[i], tups[j] = tups[j], tups[i]
    del tups[j]
    
    # converting back
    rating = dict(tups)
    print(rating)
    db.session.query(User).filter_by(username=session['username']).update({'score': rating})
    db.session.commit()
    