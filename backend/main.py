from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.inference import analyze_machine


app = FastAPI(
    title="FORTRESS AI API",
    description=(
        "AI-powered predictive maintenance API "
        "for automotive CNC machines."
    ),
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SensorReading(BaseModel):

    spindle_speed_rpm: float = Field(
        ...,
        description="Spindle speed in RPM"
    )

    spindle_current_a: float = Field(
        ...,
        description="Spindle current in amperes"
    )

    torque_nm: float = Field(
        ...,
        description="Torque in Nm"
    )

    vibration_x: float = Field(
        ...,
        description="X-axis vibration"
    )

    vibration_y: float = Field(
        ...,
        description="Y-axis vibration"
    )

    vibration_z: float = Field(
        ...,
        description="Z-axis vibration"
    )

    temperature_c: float = Field(
        ...,
        description="Machine temperature in Celsius"
    )

    coolant_pressure_bar: float = Field(
        ...,
        description="Coolant pressure in bar"
    )

    cutting_force_n: float = Field(
        ...,
        description="Cutting force in Newtons"
    )

    acoustic_emission: float = Field(
        ...,
        description="Acoustic emission measurement"
    )

    tool_wear_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Tool wear percentage"
    )

    tool_age_hours: float = Field(
        ...,
        ge=0,
        description="Tool age in hours"
    )


class AnalysisRequest(BaseModel):

    machine_id: str = "AUTO-CNC-001"

    component: str = "Engine Block"

    operation: str = "Milling"

    sensor_data: SensorReading

    history: Optional[List[SensorReading]] = None


@app.get("/")
def root():

    return {
        "system": "FORTRESS",
        "status": "ONLINE",
        "message": (
            "FORTRESS Predictive Maintenance "
            "AI Engine is running."
        )
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "ai_engine": "loaded"
    }


@app.post("/analyze")
def analyze(request: AnalysisRequest):

    result = analyze_machine(
        sensor_data=request.sensor_data.model_dump(),
        history=(
            [item.model_dump() for item in request.history]
            if request.history
            else None
        )
    )

    return {

        "machine_id":
            request.machine_id,

        "component":
            request.component,

        "operation":
            request.operation,

        "analysis":
            result

    }