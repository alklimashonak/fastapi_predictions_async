import logging.config
from os import path

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.events.router import router as event_router
from src.matches.router import router as match_router
from src.predictions.router import router as prediction_router

log_file_path = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'logging.ini')
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)


app = FastAPI(title='Predictions')

app.include_router(auth_router, prefix='/auth', tags=['Auth'])
app.include_router(event_router, prefix='/events', tags=['Events'])
app.include_router(match_router, prefix='', tags=['Matches'])
app.include_router(prediction_router, prefix='/predictions', tags=['Predictions'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
