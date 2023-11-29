# Personalized Chat Bot Application

A custom chat bot application that can be used to create personalized chat bots for any purpose. The application is built using Python and Flask.

## Dependencies

- Python 3.9+
- Flask
- OPENAI API Key (set inside the .env file)

## Setup

- Copy the `.env.example` file to `.env`
- Fill in the all the variables

| Variable                | Data                                                 |
| ----------------------- | ---------------------------------------------------- |
| `PORT`                  | Port to serve the API at                             |
| `OPENAI_API_KEY`        | Connection string of the MongoDB database            |
| `GPT_MODEL`             | GPT model to use for generating the response         |
| `GPT_TEMPERATURE`       | Temperature to use for generating the response       |
| `GPT_MAX_TOKENS`        | Maximum number of tokens to generate                 |
| `GPT_FREQUENCY_PENALTY` | Frequency penalty to use for generating the response |
| `GPT_PRESENCE_PENALTY`  | Presence penalty to use for generating the response  |
| `UPLOAD_FOLDER`         | Folder to store the chats                            |

After that the application can be started either in development or production mode.

### Extract the zip file

```bash
unzip chat_app.zip
```

### Go to the project folder

```bash
cd chat_app
```

### Create a virtual environment

```bash
python3 -m venv .venv
```

### Activate the virtual environment

```bash
source .venv/bin/activate # linux/macOS
```

```bash
.venv\Scripts\activate # windows
```

### Install the dependencies

```bash
pip install --upgrade pip wheel
pip install -r requirements.txt
```

### Set the environment variables

```bash
export FLASK_APP=app.py FLASK_ENV=development # linux/macOS
```

```bash
set FLASK_APP=app.py FLASK_ENV=development # windows
```

### Optional environment variables

```bash
export FLASK_DEBUG=1 # linux/macOS
```

```bash
set FLASK_DEBUG=1 # windows
```

### Run the application

```bash
flask run --host=0.0.0.0 --port=5000
```
