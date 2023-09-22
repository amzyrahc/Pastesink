import random
import string
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, session

from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = 'securekeyherepls'  

encryption_key = Fernet.generate_key()
fernet = Fernet(encryption_key)

try:
    with open('pastes.json', 'r') as json_file:
        pastes = json.load(json_file)
except FileNotFoundError:
    pastes = {}

link_mapping = {}

def generate_captcha():
    captcha_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return captcha_token

def encrypt_string(data):
    encrypted_data = fernet.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode()

def decrypt_string(data):
    encrypted_data = base64.b64decode(data)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data

@app.route('/')
def index():
    captcha_token = generate_captcha()
    session['captcha_token'] = captcha_token
    return render_template('index.html', captcha_token=captcha_token, error=session.pop('error', None))

@app.route('/create', methods=['POST'])
def create_paste():

    user_captcha = request.form.get('captcha')
    if user_captcha != session['captcha_token']:
        error_message = 'Incorrect captcha, please try again.'
        flash(error_message, 'error')
        return redirect(url_for('index'))

    custom_link = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    encrypted_custom_link = encrypt_string(custom_link)

    paste_content = request.form.get('content')
    encrypted_content = fernet.encrypt(paste_content.encode())
    encrypted_content_base64 = base64.b64encode(encrypted_content).decode()

    link_mapping[custom_link] = encrypted_custom_link

    pastes[encrypted_custom_link] = encrypted_content_base64

    with open('pastes.json', 'w') as json_file:
        json.dump(pastes, json_file)

    return redirect(url_for('view_paste', custom_link=custom_link))

@app.route('/<custom_link>')
def view_paste(custom_link):

    encrypted_custom_link = link_mapping.get(custom_link)
    if encrypted_custom_link is None:
        return 'Paste not found.', 404

    encrypted_content_base64 = pastes.get(encrypted_custom_link)
    if encrypted_content_base64 is None:
        return 'Paste not found.', 404

    encrypted_content = base64.b64decode(encrypted_content_base64)
    decrypted_content = fernet.decrypt(encrypted_content).decode()

    return decrypted_content

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
