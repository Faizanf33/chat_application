import os
import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL")
GPT_MAX_TOKENS = os.getenv("GPT_MAX_TOKENS")
GPT_TEMPERATURE = os.getenv("GPT_TEMPERATURE")
GPT_FREQUENCY_PENALTY = os.getenv("GPT_FREQUENCY_PENALTY")
GPT_PRESENCE_PENALTY = os.getenv("GPT_PRESENCE_PENALTY")

openai.api_key = OPENAI_API_KEY


def get_assistant_response(messages: list):
    completion = openai.ChatCompletion.create(
        model=GPT_MODEL,
        temperature=float(GPT_TEMPERATURE),
        max_tokens=int(GPT_MAX_TOKENS),
        top_p=1,
        frequency_penalty=float(GPT_FREQUENCY_PENALTY),
        presence_penalty=float(GPT_PRESENCE_PENALTY),
        messages=messages,
    )

    return completion.choices[0].message


ai_failure_messages = [
    "Sorry, I'm not feeling well. Please try again later.",
    "Sorry, I don't feel like talking right now. Please try again later.",
    "Sorry, I'm not in a good mood right now. Please try again later.",
    "Sorry, I'm currently unavailable. Please try again later.",
    "Sorry, I can't talk right now. Please try again later.",
    "Sorry, I'm not available right now. Please try again later.",
    "Sorry, I can't connect to the server right now. Please try again later.",
    "Sorry for the inconvenience. Please try again later.",
]
