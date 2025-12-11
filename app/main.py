from fastapi import FastAPI, HTTPException, Header, Depends
from app.db import master_db, get_org_collection_name
from app import schemas, utils
from bson.objectid import ObjectId
from typing import Optional

app = FastAPI()   # ← THIS MUST EXIST EXACTLY LIKE THIS


orgs_col = master_db["organizations"]
users_col = master_db["users"]


@app.get("/")
def home():
    return {"message": "Multi-tenant backend running!"}


@app.post("/org/create", response_model=schemas.OrgOut)
async def create_org(payload: schemas.OrgCreate):
    org_name = payload.organization_name.strip()
    existing = await orgs_col.find_one({"organization_name": org_name})
    if existing:
        raise HTTPException(status_code=400, detail="Organization already exists")

    collection_name = get_org_collection_name(org_name)
    org_collection = master_db[collection_name]
    await org_collection.create_index("_id")

    hashed_password = utils.hash_password(payload.password)

    admin_doc = {
        "email": payload.email.lower(),
        "password": hashed_password,
        "organization_name": org_name,
        "role": "admin"
    }

    admin_res = await users_col.insert_one(admin_doc)

    org_doc = {
        "organization_name": org_name,
        "collection_name": collection_name,
        "admin_user_id": admin_res.inserted_id
    }

    await orgs_col.insert_one(org_doc)

    return {
        "organization_name": org_name,
        "collection_name": collection_name,
        "admin_email": payload.email.lower()
    }


@app.get("/org/get", response_model=schemas.OrgOut)
async def get_org(organization_name: str):
    org = await orgs_col.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    admin = await users_col.find_one({"_id": org["admin_user_id"]})

    return {
        "organization_name": org["organization_name"],
        "collection_name": org["collection_name"],
        "admin_email": admin["email"]
    }


@app.put("/org/update")
async def update_org(payload: schemas.OrgUpdate):
    org = await orgs_col.find_one({"organization_name": payload.organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_fields = {}

    # Rename organization
    if payload.new_organization_name:
        new_name = payload.new_organization_name.strip()
        exists = await orgs_col.find_one({"organization_name": new_name})
        if exists:
            raise HTTPException(status_code=400, detail="New organization name already exists")

        old_coll = org["collection_name"]
        new_coll = get_org_collection_name(new_name)

        old_collection = master_db[old_coll]
        new_collection = master_db[new_coll]

        docs = []
        async for doc in old_collection.find({}):
            doc.pop("_id", None)
            docs.append(doc)

        if docs:
            await new_collection.insert_many(docs)

        await old_collection.drop()

        update_fields["organization_name"] = new_name
        update_fields["collection_name"] = new_coll

    admin_id = org["admin_user_id"]
    admin_updates = {}
    if payload.email:
        admin_updates["email"] = payload.email.lower()
    if payload.password:
        admin_updates["password"] = utils.hash_password(payload.password)

    if admin_updates:
        await users_col.update_one({"_id": admin_id}, {"$set": admin_updates})
    if update_fields:
        await orgs_col.update_one({"_id": org["_id"]}, {"$set": update_fields})

    return {"detail": "Organization updated successfully"}


async def get_current_admin(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = parts[1]
    payload = utils.decode_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


@app.delete("/org/delete")
async def delete_org(organization_name: str, admin=Depends(get_current_admin)):
    if admin["organization_name"] != organization_name:
        raise HTTPException(status_code=403, detail="Not allowed")

    org = await orgs_col.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    coll = master_db[org["collection_name"]]
    await coll.drop()

    await users_col.delete_one({"_id": org["admin_user_id"]})
    await orgs_col.delete_one({"_id": org["_id"]})

    return {"detail": "Organization deleted"}


@app.post("/admin/login")
async def login(payload: schemas.AdminLogin):
    user = await users_col.find_one({"email": payload.email.lower(), "role": "admin"})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not utils.verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = utils.create_token({
        "admin_id": str(user["_id"]),
        "organization_name": user["organization_name"]
    })

    return {"access_token": token, "token_type": "bearer"}
