# SmartLender AI - Automated Loan Evaluation System

SmartLender AI is a high-fidelity, predictive web application designed to evaluate loan applications. The system utilizes a trained Machine Learning model to evaluate risk profiles and combines it with a strict rule-based financial validator.

---

## 📂 Project Architecture (3-Tier Layout)

The project is structured according to a clean 3-tier architecture separating concerns:

```text
smartlender/
├── Presentation_Tier/           # Frontend (User Interface)
│   ├── static/                  # CSS styles (glassmorphism) & Javascript logic
│   └── templates/               # HTML5 semantic structure
│
├── Logic_Tier/                  # Application Logic (Backend API)
│   └── app.py                   # FastAPI application & Business rule validator
│
└── Data_Tier/                   # Data Storage & ML Assets
    ├── model.pkl                # Serialized XGBoost classification model
    ├── scaler.pkl               # Serialized StandardScaler
    └── loan_prediction.csv      # Raw training historical dataset
```

---

## ⚡ Core Features

1. **Dual-Layer Evaluation**:
   * **Layer 1 (ML Inference)**: A serialized XGBoost classification model assesses risk factors (credit history, demographics, area, income) to predict approval probability.
   * **Layer 2 (Financial Rule Override)**: A strict **Debt-to-Income (DTI)** check is calculated on the backend. If the monthly EMI exceeds **55%** of the applicant's combined income, the loan is automatically rejected.
2. **Indian Rupees (₹) Localization**: Inputs, helper guidelines, and results are displayed in Rupees, formatted according to the Indian numbering system (e.g. ₹1,50,000).
3. **Years-Based Loan Duration**: Users select the loan term in years (e.g., 20 or 30 years), which the backend converts to months automatically for ML model compatibility.
4. **Premium UI Experience**: Interactive glassmorphism dark-theme dashboard with animated progress meters, dynamic form validations, and status dashboards.

---

## 🚀 Setup & Installation

### 1. Prerequisites
Make sure you have Python 3.8+ installed.

### 2. Install Dependencies
Install all required libraries from the root of the project:
```bash
pip install fastapi uvicorn pydantic jinja2 numpy pandas scikit-learn
```

---

## 💻 Running the Application

### 1. Start the API Server
Run the FastAPI application from the project root directory:
```bash
python Logic_Tier/app.py
```
The server will start on `http://127.0.0.1:5000/`.

### 2. Access the Web Interface
Open your web browser and navigate to:
```text
http://127.0.0.1:5000/
```

---

## 🧪 Testing

We have built automated unit tests to mock requests and verify the home page and prediction calculations:
```bash
python C:\Users\jagad\.gemini\antigravity\brain\28b81c4e-aba5-4399-8789-756c7b765fad\scratch\test_app.py
```
*(Tests cover standard approvals, model-based rejections, and DTI-overridden rejections).*
