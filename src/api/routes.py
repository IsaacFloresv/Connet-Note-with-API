"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, Users, Clients, Files
from api.utils import generate_sitemap, APIException
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import smtplib
import ssl
import os
import random
import string
from email.mime.text import MIMEText
from flask_bcrypt import generate_password_hash, check_password_hash
from socket import gaierror
api = Blueprint('api', __name__)


@api.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


def send_email(msg, email):
    print(msg)
    sender = "Dropcase"
    receiver = email

    try:
        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
            server.login("8c7f3d9c31cc96", "97d8ee24d57c1d")
            server.sendmail(sender, receiver, msg.as_string())
        return jsonify("msg:Mail sent")
    except (gaierror, ConnectionRefusedError):
        print('Failed to connect to the server. Bad connection settings?')
    except smtplib.SMTPServerDisconnected:
        print('Failed to connect to the server. Wrong user/password?')
    except smtplib.SMTPException as e:
        print('SMTP error occurred: ' + str(e))


@api.route('/')
def sitemap():
    return generate_sitemap(app)


@api.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = Users.query.filter_by(email=email).first()
    if user is None:
        return jsonify({
            "msg": "You are not a registered user,sign up to continue or go away!!!"
        }), 401
    print(user.password)
    is_correct = check_password_hash(user.password, password)
    if not is_correct:
        return jsonify({"msg": "Bad username or password"}), 401
    access_token = create_access_token(identity=email)
    response_body = {
        'msg': 'Welcome to Dropcase',
        'token': access_token,
        'user': user.serialize()
    }
    return jsonify(response_body), 200


@api.route("/auth", methods=["GET"])
@jwt_required()
def validate_token():

    user = get_jwt_identity()
    validate_user = User.query.filter_by(email=user).first()
    response_body = {
        'logged_in_as': validate_user,
        'msg': 'The token is valid.',
        'user': user.serialize()
    }
    return jsonify(response_body), 200


@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify({
        "logged_in_as": current_user,
        "msg": "Access Granted to Private route"
    }), 200


@api.route('/user/<int:id>', methods=['GET'])
@jwt_required()
def single_user(id):
    users = Users.query.get(id)
    single_user = users.serialize()
    return jsonify(single_user), 200


@api.route('/user', methods=['GET', 'POST', 'PUT'])
def users():

    if request.method == 'GET':

        users = Users.query.all()
        all_users = list(map(lambda x: x.serialize(), users))
        response_body = {
            "msg": "Users list",
            "Users": all_users
        }
        return jsonify(response_body), 200
        db.session.commit()

    if request.method == 'PUT':
        if 'email' not in request.json:
            return jsonify({"msg": "Fill email fields please"}), 400

        email = request.json['email']
        user = Users.query.filter_by(email=email).first()

        if 'password' in request.json:
            password = request.json['password']
            user.password = password

        if 'name' in request.json:
            name = request.json['name']
            user.name = name

        if 'lastname' in request.json:
            lastname = request.json['lastname']
            user.lastname = lastname

        if 'is_active' in request.json:
            is_active = request.json['is_active']
            user.is_active = is_active

        response_body = {
            'msg': 'User successfully updated.',
            'user': user.serialize()
        }
        db.session.commit()
        return jsonify(response_body), 200

    elif request.method == 'POST':
        body = request.json
        email = request.json.get('email')
        password = request.json.get('password')
        lawyer_identification = request.json.get('lawyer_identification')
        name = request.json.get('name')
        lastname = request.json.get('lastname')
        is_active = request.json.get('is_active')

        if body is None:
            return "The request body is null", 400
        if not email:
            return 'You need to specify the email', 400
        if not password:
            return 'You need to enter a password', 400
        if not lawyer_identification:
            return 'You need to enter your lawyer ID', 400
        if not name:
            return 'You need to enter your name', 400
        if not lastname:
            return 'You need to enter your lastname', 400
        if not is_active:
            return 'You need to to set your account status', 400

        pw_hash = generate_password_hash(password, 10).decode('utf-8')
        user = Users(email=email, name=name, lastname=lastname,
                     lawyer_identification=lawyer_identification, password=pw_hash, is_active=is_active)
        message = '''\
Thank you for registering! You can sign in by visiting the link below.
<br/>
<br/>
<br/>
<br/>
Thanks,
<br/>
            '''.format("")

        msg = MIMEText(message, 'html')
        msg['Subject'] = "Welcome"
        msg['From'] = "Dropcase"
        msg['To'] = email
        send_email(msg, email)

        db.session.add(user)
        db.session.commit()
        response_body = {
            'msg': 'Thank you! Your account has been added successfully. Please sign in.',
            'user': user.serialize()
        }

        return jsonify(response_body), 200


@api.route('/client', methods=['GET', 'POST', 'PUT'])
@jwt_required()
def customers():
    if request.method == 'GET':
        customers = Clients.query.all()
        all_customers = list(map(lambda x: x.serialize(), customers))
        response_body = {
            "msg": "Customers list",
            "Customer": all_customers
        }
        return jsonify(response_body), 200
        db.session.commit()

    elif request.method == 'PUT':
        if 'id' not in request.json:
            return jsonify({"msg": "User ID missing"}), 400

        id = request.json['id']
        print(id)
        customer = Clients.query.filter_by(id=id).first()
        print(customer)

        if 'name' in request.json:
            name = request.json['name']
            customer.name = name

        if 'first_lastname' in request.json:
            first_lastname = request.json['first_lastname']
            customer.first_lastname = first_lastname

        if 'second_lastname' in request.json:
            second_lastname = request.json['second_lastname']
            customer.second_lastname = second_lastname

        if 'is_active' in request.json:
            is_active = request.json['is_active']
            customer.is_active = is_active

        if 'lawyer_id' in request.json:
            lawyer_id = request.json['lawyer_id']
            customer.lawyer_id = lawyer_id

        if 'delete' in request.json:
            delete = request.json['delete']
            customer.delete = delete
        response_body = {
            'msg': 'Customer successfully updated.',
            'Clients': customer.serialize()
        }
        db.session.commit()
        return jsonify(response_body), 200

    elif request.method == 'POST':
        body = request.json
        name = request.json.get('name')
        lawyer_id = request.json.get('lawyer_id')
        is_active = request.json.get('is_active')
        first_lastname = request.json.get('first_lastname')
        second_lastname = request.json.get('second_lastname')

        if body is None:
            return "The request body is null", 400
        if not name:
            return 'You need to specify customer', 400
        clients = Clients(name=name, lawyer_id=lawyer_id, is_active=is_active,
                          first_lastname=first_lastname, second_lastname=second_lastname)
        db.session.add(clients)
        db.session.commit()
        response_body = {
            'msg': 'Customer has been created successfully.',
            'user': clients.serialize()
        }
        return jsonify(response_body), 200


@api.route('/cases', methods=['GET', 'POST', 'PUT'])
@jwt_required()
def cases():
    if request.method == 'POST':
        body = request.json
        email = request.json.get('email')
        name = request.json.get('name')
        lawyer_id = request.json.get('lawyer_id')
        is_active = request.json.get('is_active')
        first_lastname = request.json.get('first_lastname')
        second_lastname = request.json.get('second_lastname')

        if body is None:
            return "The request body is null", 400
        if not email:
            return 'You need to specify the email', 400
        clients = Clients(email=email, name=name, lawyer_id=lawyer_id, is_active=is_active,
                          first_lastname=first_lastname, second_lastname=second_lastname)
        db.session.add(clients)
        db.session.commit()
        response_body = {
            'msg': 'Customer has been created successfully.',
            'user': clients.serialize()
        }
        return jsonify(response_body), 200


@api.route("/reset", methods=["POST"])
def update_password():
    if request.method == "POST":
        # new_password = request.json.get("password")
        email = request.json.get("email")

        if not email:
            return jsonify({"msg": "Missing email in request."}), 400

        user = Users.query.filter_by(email=email).first()

        # Create and set new password
        new_password = ''.join(random.choice(string.ascii_letters)
                               for i in range(12))
        # new_password_hashed
        pw_hash = generate_password_hash(new_password, 10).decode('utf-8')
        user.password = pw_hash
        db.session.commit()

        response_body = {
            "msg": "Success. An email will be sent to your account with your temporary password."
        }

        try:
            message = '''\
                A reset request was sent to our system. Please use the following password to sign in:
                <br/>
                <br/>
                <br/>
                {0}
                <br/>
                <br/>
                <br/>
                <br/>
                Thanks,
                <br/>
                Dropcase
            
            '''.format(new_password)

            msg = MIMEText(message, 'html')
            msg['Subject'] = "Password Reset Request"
            msg['From'] = "Dropcase"
            msg['To'] = email

            send_email(msg, email)
        except Exception as e:
            print(e)
            return jsonify({"msg": "Unable to send reset email."}), 400

        return jsonify(response_body), 200

@api.route('/files', methods=['GET'])
@jwt_required()
def files():
    if request.method == 'GET':
        files = Files.query.all()
        all_files = list(map(lambda x: x.serialize(), files))
        response_body = {
            "msg": "This total Files",
            "Files": all_files
        }
        return jsonify(response_body), 200
        db.session.commit()

@api.route('/file', methods=['GET','POST','DELETE'])
@jwt_required()
def file():
    if request.method == 'GET':
        id = request.json['id']
        files = db.session.query(Files).filter(Files.Case_updates_id==id)
        all_files = list(map(lambda x: x.serialize(), files))
        response_body = {
            "msg": "Files list complete",
            "Files": all_files
        }
        return jsonify(response_body), 200
        db.session.commit()

    elif request.method == 'POST':
        body = request.json
        name = request.json.get('name')
        url = request.json.get('url')
        case_updates_id = request.json.get('case_updates_id')
        delete = request.json.get('delete')

        if body is None:
            return "The request body is null", 400
        if not name:
            return 'You need to specify the name', 400
        files = Files(name=name, url=url, Case_updates_id=case_updates_id, delete=delete)
        db.session.add(files)
        db.session.commit()
        response_body = {
            'msg': 'Files has been add successfully.',
            'user': files.serialize()
        }
        return jsonify(response_body), 200

    elif request.method == 'DELETE':
        if 'id' not in request.json:
            return jsonify({"msg": "Id is a required field"}), 400

        id = request.json['id']
        file = Files.query.filter_by(id=id).first()
        file.delete = True
        
        print(file)
        response_body = {
            'msg': 'File successfully updated.',
            'Clients': file.serialize()
        }
        db.session.commit()
        return jsonify(response_body), 200
