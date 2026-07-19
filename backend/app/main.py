import logging
import uvicorn

from app.api import app
from app.db.init_db import init_db


if __name__ == "__main__":
    init_db()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
