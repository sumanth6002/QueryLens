import os
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# On Vercel, production should use environment variables only.
os.environ.setdefault("FLASK_ENV", "production")

from app import create_app  # noqa: E402


app = create_app(os.environ.get("FLASK_ENV", "production"))
