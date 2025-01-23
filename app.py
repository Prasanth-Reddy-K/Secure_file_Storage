import pickle
import boto3
import json
from Crypto.Random import get_random_bytes
from boto3.dynamodb.conditions import Key
from cryptography.hazmat.primitives.ciphers import algorithms
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file

import d
import key_management
import os
import parts

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/forgot_pass')
def forgot_pass():
    return render_template('forgot_pass.html')


@app.route('/upload')
def upload():
    return render_template('upload.html')


@app.route('/login')
def login():
    return render_template('login.html')


AWS_ACCESS_KEY_ID = 'AKIAZI2LHFOPGHENAJN2'
AWS_SECRET_ACCESS_KEY = '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'
S3_FILES_BUCKET_NAME = 'project4957'
S3_IMAGES_BUCKET_NAME = 'images4957'
dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name='eu-north-1')
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
table = dynamodb.Table('UserTable')
username = ''


@app.route('/userlogin', methods=['POST'])
def userlogin():
    email = request.form['email']
    password = request.form['password']

    # Check if the user exists
    response = table.query(
        IndexName='email-index',  # Assuming you have a Global Secondary Index named 'email-index'
        KeyConditionExpression=Key('email').eq(email)
    )
    items = response['Items']

    if len(items) == 0:
        return jsonify({'message': 'User does not exist'}), 404

    user = items[0]
    username = user.get('username')
    session['username'] = username
    # Check if the password matches
    if user['password'] == password:
        return redirect(url_for('upload'))
    else:
        return jsonify({'message': 'Incorrect password'}), 401


@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form['uname']
    email = request.form['email']
    password = request.form['password']

    # Check if the user already exists
    response = table.get_item(
        Key={
            'email': email
        }
    )
    if 'Item' in response:
        return {
            'statusCode': 400,
            'body': json.dumps('User already exists')
        }

    table.put_item(
        Item={
            'email': email,
            'username': username,
            'password': password
        }
    )
    session['username'] = username
    create_folder(S3_FILES_BUCKET_NAME, username)
    return redirect(url_for('upload'))


def create_folder(bucket_name, folder_name):
    # Add a trailing slash to the folder name to create a "folder" object
    folder_key = f"{folder_name}/"

    # Put an empty object (zero bytes) to create the folder
    s3.put_object(Bucket=bucket_name, Key=folder_key)


@app.route('/encrypt', methods=['POST'])
def encrypt():
    file1 = request.files['file']
    type_of_file = os.path.splitext(file1.filename)[1][1:]
    input_file_content = file1.read()  # Read the content of the uploaded file as binary
    name_of_file = os.path.splitext(os.path.basename(file1.filename).replace(" ", ""))[0]
    encrypted_file = name_of_file + '(' + type_of_file + ')' + '.enc'
    aes_key = get_random_bytes(16)
    blowfish_key = get_random_bytes(16)
    des3_key = get_random_bytes(16)
    rc6_key = get_random_bytes(16)
    keys = aes_key + blowfish_key + des3_key + rc6_key
    keys = parts.bytes_to_hex(keys)
    image_url = "https://source.unsplash.com/random/200x200?sig=1"
    username = session['username']
    key_management.encode(image_url, keys, S3_IMAGES_BUCKET_NAME, name_of_file, username)
    files = parts.divide_file(input_file_content, type_of_file)
    data1 = d.aes_encrypt(files[0], aes_key)
    data2 = d.blowfish_encrypt(files[1], blowfish_key)
    data3 = d.encrypt_file(files[2], des3_key, algorithms.TripleDES)
    data4 = d.arc4_encrypt(files[3], rc6_key)
    with open(encrypted_file, "wb") as file:
        pickle.dump((data1, data2, data3, data4), file)
    s3_object_key = encrypted_file
    f_key = f"{username}/{encrypted_file}"
    # Upload the file to S3
    s3.upload_file(s3_object_key, S3_FILES_BUCKET_NAME, f_key)
    return render_template('upload.html', message="File uploaded Succeccfully!.")  # Pass message


@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    name_of_file = filename.rsplit("(", 1)[0].replace(" ", "")
    type_of_file = filename[filename.index("(") + 1:filename.rindex(")")]
    decrypted_file=name_of_file+"."+type_of_file
    username = session['username']
    keys = key_management.get_Key(username, name_of_file)
    keys = parts.hex_to_bytes(keys)
    chunk_size = 16
    aes_key, blowfish_key, des3_key, rc6_key = [keys[i:i + chunk_size] for i in range(0, len(keys), chunk_size)]
    file_obj = s3.get_object(Bucket=S3_FILES_BUCKET_NAME, Key=f"{username}/{filename}")
    data = file_obj['Body'].read()
    temp_file = 'temp_file.bin'
    with open(temp_file, 'wb') as file:
        file.write(data)
    with open(temp_file, "rb") as file:
        retrieved_data1, retrieved_data2, retrieved_data3, retrieved_data4 = pickle.load(file)

    d.aes_decrypt(retrieved_data1, decrypted_file, aes_key)
    d.blowfish_decrypt(retrieved_data2, decrypted_file, blowfish_key)
    d.decrypt_file(retrieved_data3, decrypted_file, des3_key, algorithms.TripleDES)
    d.arc4_decrypt(retrieved_data4, decrypted_file, rc6_key)
    os.remove(temp_file)
    return send_file(
        decrypted_file,
        as_attachment=True,
        download_name=name_of_file + "." + type_of_file
    )


@app.route('/viewfiles')
def viewfiles():
    # Get the list of files from the S3 folder
    bucket_name = S3_FILES_BUCKET_NAME
    folder_name = session.get('username')
    files_in_folder = list_files_in_folder(bucket_name, folder_name)
    # Render the HTML template with the list of files
    return render_template('download.html', files=files_in_folder)


def list_files_in_folder(bucket_name, folder_name):
    # Use list_objects_v2 to list objects in the specified bucket and folder
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)

    # Check if there are any objects in the folder
    if 'Contents' in response:
        # Extract the file names from the response
        files = [obj['Key'].split('/')[-1] for obj in response['Contents'] if
                 not obj['Key'].endswith('/')]  # Get the last part after splitting by '/'
        return files
    else:
        return []


