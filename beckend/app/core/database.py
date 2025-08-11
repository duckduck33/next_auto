from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings

settings = get_settings()


class Database:
    client: AsyncIOMotorClient = None
    database_name: str = settings.database_name


db = Database()


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.mongo_uri)
    print("Connected to MongoDB.")


async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection.")