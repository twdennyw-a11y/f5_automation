from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import json

from database import engine, Base, get_db, SessionLocal
import models, schemas, auth, config, f5_client

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="F5 Automation Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")

@app.post("/api/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

@app.post("/api/requests", response_model=schemas.RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(req: schemas.RequestCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    db_req = models.F5Request(
        user_id=current_user.id,
        request_type=req.request_type,
        target_ip=req.target_ip,
        details=req.details
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

@app.get("/api/requests", response_model=list[schemas.RequestResponse])
def get_user_requests(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Admins see all requests, normal users see only their own
    if current_user.role == models.RoleEnum.admin:
        requests = db.query(models.F5Request).order_by(models.F5Request.created_at.desc()).all()
    else:
        requests = db.query(models.F5Request).filter(models.F5Request.user_id == current_user.id).order_by(models.F5Request.created_at.desc()).all()
    return requests

@app.put("/api/requests/{request_id}/approve", response_model=schemas.RequestResponse)
def approve_request(request_id: int, status_update: schemas.RequestUpdateStatus, db: Session = Depends(get_db), admin_user: models.User = Depends(auth.get_current_admin_user)):
    db_req = db.query(models.F5Request).filter(models.F5Request.id == request_id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if db_req.status != models.RequestStatusEnum.pending:
        raise HTTPException(status_code=400, detail="Only pending requests can be evaluated")

    db_req.status = status_update.status
    db.commit()

    if status_update.status == models.RequestStatusEnum.approved:
        # Trigger the actual F5 change sync/async
        try:
            details_dict = json.loads(db_req.details)
        except json.JSONDecodeError:
            details_dict = {}

        result = f5_client.execute_f5_request(db_req.target_ip, db_req.request_type, details_dict)
        db_req.admin_log = json.dumps(result)
        if result.get("status") == "success":
            db_req.status = models.RequestStatusEnum.completed
        else:
            db_req.status = models.RequestStatusEnum.failed
        db.commit()

    db.refresh(db_req)
    return db_req

def init_admin():
    db = SessionLocal()
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        hashed_password = auth.get_password_hash("admin")
        admin = models.User(username="admin", hashed_password=hashed_password, role=models.RoleEnum.admin)
        db.add(admin)
        db.commit()
        print("Default admin user created (admin/admin).")
    db.close()

init_admin()
