import os
import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from db import init_db, register_user, authenticate_user

init_db()

app = FastAPI(title="SmartLender AI")

app.add_middleware(
    SessionMiddleware,
    secret_key="smartlender-secret-key-12345",
    session_cookie="smartlender_session",
    max_age=1800  # 30 minutes session duration
)

# Paths to the model and scaler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, '../Data_Tier/model.pkl'))
SCALER_PATH = os.path.abspath(os.path.join(BASE_DIR, '../Data_Tier/scaler.pkl'))

# Load the trained model and scaler
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

with open(SCALER_PATH, 'rb') as f:
    scaler = pickle.load(f)

# Absolute paths to presentation tier
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '../Presentation_Tier/static'))
TEMPLATES_DIR = os.path.abspath(os.path.join(BASE_DIR, '../Presentation_Tier/templates'))

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates setup
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Define the Pydantic schema for inputs
class LoanRequest(BaseModel):
    Gender: str
    Married: str
    Dependents: str
    Education: str
    Self_Employed: str
    ApplicantIncome: float
    CoapplicantIncome: float
    LoanAmount: float
    Loan_Amount_Term: float
    Credit_History: float
    Property_Area: str

# Define Auth Request schema
class AuthRequest(BaseModel):
    username: str
    password: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.session.get("username"):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(data: AuthRequest, request: Request):
    if authenticate_user(data.username, data.password):
        request.session["username"] = data.username.strip().lower()
        return {"success": True, "message": "Logged in successfully"}
    raise HTTPException(status_code=400, detail="Invalid username or password")

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    if request.session.get("username"):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_post(data: AuthRequest):
    if register_user(data.username, data.password):
        return {"success": True, "message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="Username already exists")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.post("/predict")
async def predict(data: LoanRequest, request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized. Please log in.")
    try:
        # Mapping dictionaries matching scikit-learn LabelEncoder values
        gender_map = {'Male': 1, 'Female': 0}
        married_map = {'Yes': 1, 'No': 0}
        education_map = {'Graduate': 0, 'Not Graduate': 1}
        self_employed_map = {'Yes': 1, 'No': 0}
        property_area_map = {'Rural': 0, 'Semiurban': 1, 'Urban': 2}

        # Map categorical inputs
        gender = gender_map.get(data.Gender, 1)
        married = married_map.get(data.Married, 0)
        
        try:
            dependents = int(data.Dependents)
        except ValueError:
            dependents = 0
            
        education = education_map.get(data.Education, 0)
        self_employed = self_employed_map.get(data.Self_Employed, 0)
        property_area = property_area_map.get(data.Property_Area, 1)

        # Prepare features array in correct sequence matching model columns
        # Convert LoanAmount (rupees to thousands) and Loan_Amount_Term (years to months) for ML model
        features = [[
            gender,
            married,
            dependents,
            education,
            self_employed,
            data.ApplicantIncome,
            data.CoapplicantIncome,
            data.LoanAmount / 1000.0,
            data.Loan_Amount_Term * 12.0,
            data.Credit_History,
            property_area
        ]]

        feature_cols = ['Gender', 'Married', 'Dependents', 'Education', 'Self_Employed', 'ApplicantIncome', 'CoapplicantIncome', 'LoanAmount', 'Loan_Amount_Term', 'Credit_History', 'Property_Area']
        features_df = pd.DataFrame(features, columns=feature_cols)

        # Scale features
        scaled_features = scaler.transform(features_df)

        # Run prediction
        prediction = model.predict(scaled_features)[0]
        probabilities = model.predict_proba(scaled_features)[0]
        
        # Calculate confidence probability of prediction
        confidence = float(probabilities[prediction])

        # --- Business Rule Check (Debt-to-Income / DTI Ratio Check) ---
        monthly_income = data.ApplicantIncome + data.CoapplicantIncome
        loan_amount_abs = data.LoanAmount  # Already in absolute rupees
        
        # Calculate EMI assuming a standard 10.5% annual interest rate
        annual_interest = 0.105
        monthly_interest = annual_interest / 12
        term_months = data.Loan_Amount_Term * 12.0  # Convert term years to months
        
        if monthly_interest > 0 and term_months > 0:
            emi = (loan_amount_abs * monthly_interest * ((1 + monthly_interest) ** term_months)) / (((1 + monthly_interest) ** term_months) - 1)
        else:
            emi = loan_amount_abs / term_months if term_months > 0 else 0
            
        dti_ratio = emi / monthly_income if monthly_income > 0 else float('inf')
        
        # If DTI is higher than 55% (0.55), override the approval prediction
        dti_overridden = False
        if prediction == 1 and dti_ratio > 0.55:
            prediction = 0
            dti_overridden = True
            confidence = 1.0  # Hard rejection rule confidence is 100%

        return {
            'success': True,
            'prediction': int(prediction), # 1 for Approved, 0 for Not Approved
            'confidence': confidence,
            'dti_overridden': dti_overridden,
            'emi': emi,
            'dti_ratio': dti_ratio,
            'probabilities': {
                'approved': float(probabilities[1]) if not dti_overridden else 0.0,
                'denied': float(probabilities[0]) if not dti_overridden else 1.0
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction Error: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000)
