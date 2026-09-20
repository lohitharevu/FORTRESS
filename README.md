# 🛡️ FORTRESS

### Failure Observation and Risk Tracking for Reliable Equipment Safety and Sustainability

FORTRESS is a **cloud-based AI-powered predictive maintenance system** designed for industrial and automotive CNC machines.

It analyzes machine sensor data using **Machine Learning and Deep Learning** to detect abnormal behavior, predict failure risk, estimate Remaining Useful Life (RUL), and provide machine health insights.

## 🚀 Features

- 🧠 AI-based machine failure prediction
- 🔍 Anomaly detection using Deep Autoencoder
- ⏱️ Remaining Useful Life (RUL) prediction using LSTM
- 📊 Machine health score and risk assessment
- 🚨 Maintenance recommendations
- 🖥️ Interactive web dashboard
- ☁️ Cloud-based deployment
- ⚙️ Designed for CNC and automotive manufacturing environments

## 🧠 AI Models

| Model | Purpose |
|---|---|
| ANN | Failure probability prediction |
| Deep Autoencoder | Anomaly detection |
| LSTM | Remaining Useful Life prediction |
| Risk Engine | Overall machine health assessment |

## 📡 Sensor Inputs

FORTRESS analyzes parameters such as:

- Spindle Speed
- Spindle Current
- Torque
- Vibration
- Temperature
- Coolant Pressure
- Cutting Force
- Acoustic Emission
- Tool Wear
- Tool Age

## 🏗️ Architecture

```text
CNC Machine Sensors
        ↓
   Data Processing
        ↓
 ┌──────┼─────────┐
 ↓      ↓         ↓
 ANN  Autoencoder LSTM
 ↓      ↓         ↓
Failure Anomaly   RUL
Risk    Score     Hours
 └──────┼─────────┘
        ↓
   Risk Engine
        ↓
  Health Score
        ↓
 HEALTHY / AT RISK / CRITICAL
        ↓
 Maintenance Recommendation
```

## 🛠️ Tech Stack

**Frontend**
- React
- TypeScript
- Vite
- CSS

**Backend**
- Python
- FastAPI
- Uvicorn

**AI / ML**
- TensorFlow
- Keras
- Scikit-learn
- NumPy


## 📁 Project Structure

```text
FORTRESS/
├── backend/
│   ├── inference.py
│   ├── main.py
│   └── risk_engine.py
├── frontend/
│   ├── public/
│   └── src/
├── ml/
│   ├── data/
│   ├── models/
│   ├── generate_dataset.py
│   └── train_models.py
├── Procfile
├── railway.toml
├── requirements.txt
└── README.md
```

## ⚡ Run Locally

### Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🎯 Goal

FORTRESS aims to move industrial maintenance from **reactive maintenance** to **AI-driven predictive maintenance**, helping identify potential machine problems before they lead to unexpected failures and downtime.

---

### 👩‍💻 Author

**Lohitha Revu**

⭐ If you find this project useful, consider giving the repository a star!
