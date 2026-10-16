
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SECURE_AGENT_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "SECURE_AGENT_API_KEY is missing. Configure it in your .env file."
    )
