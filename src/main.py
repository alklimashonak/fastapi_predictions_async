import logging
from os import path

import uvicorn
from fastapi import FastAPI

from src.auth.router import auth_router
from src.events.router import get_events_router

log_file_path = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'logging.ini')
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)


app = FastAPI(title='Predictions')

app.include_router(auth_router)
app.include_router(get_events_router())


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
