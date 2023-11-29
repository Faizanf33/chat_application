import os
import csv
import random
import logging

from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_cors import CORS
from flask_login import (
    login_manager,
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from schema import *
from utils import *

load_dotenv()

app = Flask(__name__, static_url_path="")

logger = logging.getLogger(__name__)

app.config["SECRET_KEY"] = "secret_key"
app.config["UPLOAD_FOLDER"] = os.environ["UPLOAD_FOLDER"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
with app.app_context():
    # comment out the following line if you want to keep your data
    # db.drop_all()
    db.create_all()
    db.session.commit()


login_manager = LoginManager()
login_manager.init_app(app)

CORS(app)


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


@login_manager.request_loader
def request_loader(request):
    email = request.form.get("email")
    user = User.query.filter_by(email=email).first()
    return user if user else None


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    model = GPT_MODEL
    user = current_user
    user.fullname = user.fullname if user.fullname else user.username.capitalize()

    conversations = Conversation.query.filter_by(user_id=user.id).order_by(
        Conversation.timestamp.desc()
    )

    conversations = [conversation.get_json() for conversation in conversations]

    for conversation in conversations:
        # Get the last message
        message = (
            Message.query.filter_by(conversation_id=conversation["id"])
            .order_by(Message.timestamp.desc())
            .limit(1)
            .first()
        )

        conversation["last_message"] = (
            message.get_json() if message and message.receiver_id != 0 else None
        )

    conversations = sorted(
        conversations,
        key=lambda conversation: conversation["last_message"]["timestamp"]
        if conversation["last_message"]
        else "",
        reverse=True,
    )

    return render_template(
        "index.html", user=user, model=model, conversations=conversations
    )


@app.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def conversation(conversation_id):
    response_object = {
        "status": False,
        "message": "Invalid payload.",
    }

    conversation = Conversation.query.get(conversation_id)

    messages = Message.query.filter_by(conversation_id=conversation_id).all()

    if request.method == "GET":
        messages = [message.get_json() for message in messages]
        # remove initial bot message(s) from messages
        messages = messages[1:] if messages else messages

        response_object["status"] = True
        response_object["message"] = "Conversation found."
        response_object["data"] = {
            "conversation": conversation.get_json(),
            "messages": messages,
        }

        return jsonify(response_object), 200

    bot = Bot.query.get(conversation.bot_id)

    ai_messages = []

    for message in messages:
        if message.sender_type == SenderType.USER:
            ai_messages.append(
                {
                    "role": "user",
                    "content": message.message,
                }
            )
        else:
            ai_messages.append(
                {
                    "role": "assistant",
                    "content": message.message,
                }
            )

    if len(ai_messages) == 0:
        ai_messages.append(
            {
                "role": "assistant",
                "content": f"I'm {bot.name}, {bot.description}. How can I help you?",
            }
        )

        first_message = Message(
            conversation_id=conversation_id,
            sender_id=conversation.bot_id,
            receiver_id=0,
            sender_type=SenderType.BOT,
            message=ai_messages[0]["content"],
        )

        db.session.add(first_message)
        db.session.commit()

    message = request.form["message"]

    if not message:
        return jsonify(response_object), 400

    user_message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        receiver_id=conversation.bot_id,
        message=message,
    )

    ai_messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    try:
        response = get_assistant_response(ai_messages)
        ai_response = response.content

    except Exception as e:
        logger.error(e)
        ai_response = random.choice(ai_failure_messages)

    bot_message = Message(
        conversation_id=conversation_id,
        sender_id=conversation.bot_id,
        receiver_id=current_user.id,
        sender_type=SenderType.BOT,
        message=ai_response,
    )

    db.session.add(user_message)
    db.session.add(bot_message)
    db.session.commit()

    response_object["status"] = True
    response_object["message"] = "Message sent."
    response_object["data"] = {
        "conversation": conversation.get_json(),
        "message": bot_message.get_json(),
    }

    return jsonify(response_object), 200


@app.route("/feedback/<int:message_id>", methods=["POST"])
@login_required
def feedback(message_id):
    response_object = {
        "status": False,
        "message": "Invalid payload.",
    }

    message = Message.query.get(message_id)

    if not message:
        return jsonify(response_object), 400

    feedback = request.form["feedback"]

    if not feedback:
        return jsonify(response_object), 400

    message.feedback = feedback
    db.session.commit()

    response_object["status"] = True
    response_object["message"] = "Feedback sent."
    response_object["data"] = message.get_json()

    return jsonify(response_object), 200


@app.route("/add_conversation", methods=["POST"])
@login_required
def create_conversation():
    bot_name = request.form["bot_name"]
    bot_description = request.form["bot_description"]
    bot_prompt = request.form["bot_prompt"]

    # check if bot exists in user's conversations
    bot = (
        Conversation.query.filter_by(user_id=current_user.id)
        .join(Bot)
        .filter(Bot.name == bot_name)
        .first()
    )

    if bot:
        return redirect(url_for("dashboard"))

    bot = Bot(
        name=bot_name,
        description=bot_description,
    )

    db.session.add(bot)
    db.session.commit()

    conversation = Conversation(
        user_id=current_user.id,
        bot_id=bot.id,
    )

    db.session.add(conversation)
    db.session.commit()

    if bot_prompt:
        bot_message = Message(
            conversation_id=conversation.id,
            sender_id=conversation.bot_id,
            receiver_id=0,
            sender_type=SenderType.BOT,
            message=bot_prompt,
        )

        db.session.add(bot_message)
        db.session.commit()

    # redirect to dashboard
    return redirect(url_for("dashboard"))


# clear conversation
@app.route("/clear_conversation/<int:conversation_id>", methods=["GET"])
@login_required
def clear_conversation(conversation_id):
    response_object = {
        "status": False,
        "message": "Invalid payload.",
    }

    conversation = Conversation.query.get(conversation_id)

    if not conversation:
        response_object["message"] = "Conversation not found"
        return jsonify(response_object), 404

    messages = Message.query.filter_by(conversation_id=conversation_id).all()

    for message in messages:
        db.session.delete(message)

    db.session.commit()

    response_object["status"] = True
    response_object["message"] = "Conversation cleared."

    return jsonify(response_object), 200


# save conversation to csv file and download
@app.route("/save_conversation/<int:conversation_id>", methods=["GET"])
@login_required
def save_conversation(conversation_id):
    response_object = {
        "status": False,
        "message": "Invalid payload.",
    }

    conversation = Conversation.query.get(conversation_id)

    if not conversation:
        response_object["message"] = "Conversation not found"
        return jsonify(response_object), 404

    messages = Message.query.filter_by(conversation_id=conversation_id).all()

    if len(messages) == 0:
        response_object["message"] = "Conversation is empty."
        return jsonify(response_object), 400

    bot = Bot.query.get(conversation.bot_id)

    filename = f"chatbot_{bot.name}_{conversation.id}.csv"
    directory = os.path.join(app.config["UPLOAD_FOLDER"], "uploads")

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    filepath = os.path.join(directory, filename)

    with open(filepath, "w") as f:
        writer = csv.writer(f)
        header = list(dict(Message.__table__.columns).keys())
        header.append("gpt_model")
        writer.writerow(header)

        for message in messages:
            writer.writerow(
                [
                    message.id,
                    message.conversation_id,
                    message.sender_id,
                    message.sender_type.name,
                    message.receiver_id,
                    message.message,
                    message.feedback,
                    message.timestamp,
                    GPT_MODEL,
                ]
            )

    return send_file(
        path_or_file=filepath,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
        last_modified=datetime.now(),
    )


@app.route("/")
@login_required
def index():
    return redirect(url_for("dashboard"))


@app.route("/index")
@login_required
def index2():
    return redirect(url_for("dashboard"))


# URL not found
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", error=e), 404


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", url="login")

    email = request.form["email"]

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(request.form["password"]):
        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        url="login",
        message="Username or password incorrect",
        status=False,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("login.html", url="login", message="Logged out", status=True)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]

    user = User.query.filter_by(email=email).first()
    if user:
        return render_template(
            "login.html", message="Email already registered", status=False
        )

    # confirm password
    if request.form["password"] != request.form["confirm_password"]:
        return render_template(
            "login.html", message="Passwords must match", status=False
        )

    user = User(
        username=request.form["email"].split("@")[0],
        email=request.form["email"],
        password=request.form["password"],
    )

    db.session.add(user)
    db.session.commit()

    # Create three bots
    bot1 = Bot(name="Eliza", description="a psychotherapist bot")
    bot2 = Bot(name="Jabberwacky", description="a chatterbot")
    bot3 = Bot(name="A.L.I.C.E.", description="a natural language bot")

    db.session.add(bot1)
    db.session.add(bot2)
    db.session.add(bot3)
    db.session.commit()

    # Create a conversation with each bot
    conversation1 = Conversation(user_id=user.id, bot_id=bot1.id)
    conversation2 = Conversation(user_id=user.id, bot_id=bot2.id)
    conversation3 = Conversation(user_id=user.id, bot_id=bot3.id)

    db.session.add(conversation1)
    db.session.add(conversation2)
    db.session.add(conversation3)
    db.session.commit()

    return render_template(
        "login.html", url="login", message="User created please login", status=True
    )


@app.route("/user/update", methods=["POST"])
@login_required
def update_user():
    response_object = {
        "status": False,
        "message": "Invalid payload.",
    }

    fullname = request.form["fullname"]
    fullname = fullname.strip() if fullname else None

    if not fullname:
        return jsonify(response_object), 400

    user = User.query.get(current_user.id)
    user.fullname = fullname

    db.session.commit()

    return jsonify(user.get_json())


if __name__ == "__main__":
    app.run(debug=True)
