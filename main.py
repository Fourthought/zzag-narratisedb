from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from routes.health import router as health_router
from routes.shield_codes import router as shield_codes_router

app = FastAPI()

app.include_router(health_router)
app.include_router(shield_codes_router)
