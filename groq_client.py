from groq import Groq
from config.settings import GROQ_API_KEY, GROQ_MODEL


def call_groq(system_prompt: str, user_prompt: str) -> str:
    """
    Simple wrapper to call Groq's Llama model.
    Returns the assistant's text response.
    """
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content
