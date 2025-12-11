from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
MASTER_DB = os.getenv("MASTER_DB")

# Create MongoDB client
client = AsyncIOMotorClient(MONGO_URI)

# Select master database
master_db = client[MASTER_DB]

# Helper for safe collection names
def get_org_collection_name(name: str) -> str:
    safe = "".join([c.lower() if c.isalnum() else "_" for c in name])
    return f"org_{safe}"
