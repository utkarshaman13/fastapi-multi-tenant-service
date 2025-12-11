# Multi-Tenant Organization Management Backend

This project implements an organization management system using FastAPI and MongoDB.  
It follows a multi-tenant architecture where each organization receives its own isolated collection, while global metadata is stored in a master database.  
The application supports organization creation, updates, deletion, and secure admin authentication.

---

# Features

### Create Organization (`POST /org/create`)
- Validates that the organization name is unique  
- Creates a dedicated MongoDB collection: `org_<organization_name>`  
- Creates an admin user with a hashed password  
- Stores organization details in the master database  

### Admin Login (`POST /admin/login`)
- Authenticates admin credentials  
- Returns a JWT token with admin and organization details  

### Get Organization (`GET /org/get`)
Returns organization metadata stored in the master database.

### Update Organization (`PUT /org/update`)
- Updates organization name  
- Migrates existing tenant data to a new collection if renamed  
- Updates admin details  

### Delete Organization (`DELETE /org/delete`)
- Requires JWT authentication  
- Only the respective admin can delete their organization  
- Removes organization collection, admin entry, and metadata from the master database  

---

# High-Level Architecture Diagram

![Architecture Diagram](architecture_diagram.png)

---

# Architecture Overview

```
Client (Swagger/Postman)
        |
        ▼
FastAPI Backend (Routing, Validation, JWT Authentication)
        |
 ┌──────┴─────────────────────────┐
 │                                 │
 ▼                                 ▼
Master Database             Dynamic Collections
(org metadata, users)       org_<organization_name>
```

---

# Project Structure

```
fastapi-multitenant/
│
├── app/
│   ├── main.py
│   ├── db.py
│   ├── utils.py
│   ├── schemas.py
│   └── __init__.py
│
├── architecture_diagram.png
├── .env.example
├── requirements.txt
└── README.md
```

---

# Environment Variables

Create a `.env` file with the following values:

```
MONGO_URI=mongodb://localhost:27017
MASTER_DB=master_db
JWT_SECRET=secret123
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

# Running the Project

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd fastapi-multitenant
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

Swagger documentation is available at:  
http://127.0.0.1:8000/docs

---

# API Endpoints

| Method | Endpoint        | Description |
|--------|-----------------|-------------|
| POST   | /org/create     | Create organization and admin |
| GET    | /org/get        | Retrieve organization data |
| PUT    | /org/update     | Update organization details |
| DELETE | /org/delete     | Delete an organization (JWT required) |
| POST   | /admin/login    | Admin login and JWT generation |

---

# Design Choices and Trade-offs

### FastAPI
Chosen for its performance, built-in validation, and auto-generated API documentation.

### MongoDB
Its flexible schema allows dynamic creation of collections per organization without migrations.  
Suitable for multi-tenant isolation.

### Multi-Tenant Strategy (Collection per organization)
**Advantages**  
- Strong isolation between organizations  
- Easy onboarding and deletion  
- Minimal shared logic  

**Limitations**  
- Large number of tenants increases the number of collections  
- Database-per-tenant may be more scalable for very large SaaS systems  

### JWT Authentication
JWT allows stateless authentication and clean separation of tenants, keeping authorization lightweight.

---

# Brief Notes

```
The project uses a master database to store global metadata such as organization information and admin accounts.  
Each organization receives an isolated MongoDB collection. This approach keeps data separated and simplifies deletion and onboarding.  
FastAPI was selected for its speed and clear structure, while JWT ensures secure authentication for tenant-specific actions.  
The architecture is suitable for small to medium multi-tenant systems and can be extended further if needed.
```



