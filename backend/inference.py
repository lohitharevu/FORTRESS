import os
import json
import pickle

import numpy as np
import tensorflow as tf

from backend.risk_engine import calculate_risk


# ============================================================
# FORTRESS AI INFERENCE ENGINE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "models"
)


# ============================================================
# LOAD CONFIGURATION
# ============================================================

CONFIG_PATH = os.path.join(
    MODEL_DIR,
    "model_config.json"
)

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)


FEATURES = config["features"]

SEQUENCE_LENGTH = config["sequence_length"]

RUL_SCALE = config["rul_scale"]

ANOMALY_THRESHOLD = config["anomaly_threshold"]

FAILURE_THRESHOLD = config["failure_threshold"]


# ============================================================
# LOAD SCALER
# ============================================================

SCALER_PATH = os.path.join(
    MODEL_DIR,
    "scaler.pkl"
)

with open(
    SCALER_PATH,
    "rb"
) as f:

    scaler = pickle.load(f)


# ============================================================
# LOAD TRAINED MODELS
# ============================================================

failure_model = tf.keras.models.load_model(
    os.path.join(
        MODEL_DIR,
        config["models"]["failure"]
    )
)

autoencoder_model = tf.keras.models.load_model(
    os.path.join(
        MODEL_DIR,
        config["models"]["autoencoder"]
    )
)

rul_model = tf.keras.models.load_model(
    os.path.join(
        MODEL_DIR,
        config["models"]["rul"]
    )
)


# ============================================================
# STARTUP INFORMATION
# ============================================================

print("=" * 60)
print("FORTRESS AI ENGINE LOADED")
print("=" * 60)

print(
    f"Features          : {len(FEATURES)}"
)

print(
    f"Sequence length   : {SEQUENCE_LENGTH}"
)

print(
    f"RUL scale         : {RUL_SCALE}"
)

print(
    f"Anomaly threshold : {ANOMALY_THRESHOLD}"
)

print(
    f"Failure threshold : {FAILURE_THRESHOLD}"
)

print("✓ ANN loaded")
print("✓ Autoencoder loaded")
print("✓ LSTM loaded")
print("✓ Scaler loaded")

print("=" * 60)


# ============================================================
# HELPER
# ============================================================

def clamp(value, minimum, maximum):
    """Keep a value within the specified range."""

    return max(
        minimum,
        min(maximum, value)
    )


# ============================================================
# FEATURE BUILDER
# ============================================================

def build_feature_row(sensor_data):
    """
    Convert API sensor data into the exact feature order
    used during model training.
    """

    return [
        sensor_data["spindle_speed_rpm"],
        sensor_data["spindle_current_a"],
        sensor_data["torque_nm"],
        sensor_data["vibration_x"],
        sensor_data["vibration_y"],
        sensor_data["vibration_z"],
        sensor_data["temperature_c"],
        sensor_data["coolant_pressure_bar"],
        sensor_data["cutting_force_n"],
        sensor_data["acoustic_emission"],
        sensor_data["tool_wear_percent"],
        sensor_data["tool_age_hours"],
    ]


# ============================================================
# MAIN AI ANALYSIS
# ============================================================

def analyze_machine(
    sensor_data,
    history=None
):

    # ========================================================
    # 1. CURRENT SENSOR DATA
    # ========================================================

    current_values = np.array(
        [
            build_feature_row(
                sensor_data
            )
        ],
        dtype=np.float32
    )


    # ========================================================
    # 2. SCALE CURRENT DATA
    # ========================================================

    latest_scaled = scaler.transform(
        current_values
    )


    # ========================================================
    # 3. ANN — FAILURE PREDICTION
    # ========================================================

    failure_probability = float(
        failure_model.predict(
            latest_scaled,
            verbose=0
        )[0][0]
    )

    failure_probability = clamp(
        failure_probability,
        0.0,
        1.0
    )


    # ========================================================
    # 4. AUTOENCODER — ANOMALY DETECTION
    # ========================================================

    reconstructed = (
        autoencoder_model.predict(
            latest_scaled,
            verbose=0
        )
    )

    anomaly_score = float(
        np.mean(
            np.square(
                latest_scaled -
                reconstructed
            )
        )
    )

    anomaly_detected = (
        anomaly_score >
        ANOMALY_THRESHOLD
    )


    # ========================================================
    # DEBUG INFORMATION
    #
    # This lets us see the ACTUAL model outputs in the
    # FastAPI terminal.
    # ========================================================

    print(
        "=" * 60
    )

    print(
        "FORTRESS AI DEBUG"
    )

    print(
        f"ANN raw probability : "
        f"{failure_probability:.8f}"
    )

    print(
        f"ANN percentage      : "
        f"{failure_probability * 100:.4f}%"
    )

    print(
        f"Anomaly score       : "
        f"{anomaly_score:.8f}"
    )

    print(
        f"Anomaly threshold   : "
        f"{ANOMALY_THRESHOLD:.8f}"
    )

    print(
        f"Anomaly ratio       : "
        f"{anomaly_score / max(ANOMALY_THRESHOLD, 1e-8):.4f}"
    )

    print(
        f"Anomaly detected    : "
        f"{anomaly_detected}"
    )


    # ========================================================
    # 5. LSTM — REMAINING USEFUL LIFE
    # ========================================================

    if (
        history
        and
        len(history) >= SEQUENCE_LENGTH
    ):

        history_values = []

        for item in history[-SEQUENCE_LENGTH:]:

            history_values.append(
                build_feature_row(item)
            )

        history_array = np.asarray(
            history_values,
            dtype=np.float32
        )

        sequence_scaled = scaler.transform(
            history_array
        )

    else:

        # ----------------------------------------------------
        # Single-reading mode
        #
        # LSTM requires 40 time steps.
        # When history is unavailable, repeat the current
        # sensor state to create the required sequence.
        # ----------------------------------------------------

        sequence_scaled = np.repeat(
            latest_scaled,
            SEQUENCE_LENGTH,
            axis=0
        )


    sequence_input = (
        sequence_scaled.reshape(
            1,
            SEQUENCE_LENGTH,
            len(FEATURES)
        )
    )


    rul_scaled = float(
        rul_model.predict(
            sequence_input,
            verbose=0
        )[0][0]
    )


    rul_hours = max(
        0.0,
        rul_scaled * RUL_SCALE
    )


    print(
        f"LSTM RUL           : "
        f"{rul_hours:.2f} hours"
    )

    print(
        "=" * 60
    )


    # ========================================================
    # 6. RISK ENGINE
    # ========================================================

    risk = calculate_risk(
        failure_probability=failure_probability,
        anomaly_score=anomaly_score,
        anomaly_threshold=ANOMALY_THRESHOLD,
        rul_hours=rul_hours,
        rul_scale=RUL_SCALE
    )


    # ========================================================
    # 7. FINAL RESPONSE
    # ========================================================
    #
    # IMPORTANT:
    #
    # failure_probability is returned as 0-1.
    #
    # Example:
    #
    # 0.000162 = 0.0162%
    #
    # This allows the frontend to convert it into a
    # percentage exactly once.
    # ========================================================

    return {

        "failure_probability": round(
            failure_probability,
            8
        ),

        "anomaly_score": round(
            anomaly_score,
            8
        ),

        "anomaly_threshold": round(
            ANOMALY_THRESHOLD,
            8
        ),

        "anomaly_detected": bool(
            anomaly_detected
        ),

        "rul_hours": round(
            rul_hours,
            2
        ),

        "health_score": risk[
            "health_score"
        ],

        "status": risk[
            "status"
        ],

        "recommendation": risk[
            "recommendation"
        ],

        "models": {

            "failure":
                "ANN",

            "anomaly":
                "Deep Autoencoder",

            "rul":
                "LSTM"

        }

    }