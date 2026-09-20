import os
import pickle
import json
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    mean_absolute_error,
    mean_squared_error,
)

# ============================================================
# FORTRESS - IMPROVED AUTOMOTIVE CNC AI TRAINING
# ============================================================

CSV_PATH = "ml/data/fortress_automotive_cnc_dataset.csv"
MODEL_DIR = "ml/models"

os.makedirs(MODEL_DIR, exist_ok=True)

np.random.seed(42)
tf.random.set_seed(42)

print("=" * 70)
print("FORTRESS IMPROVED DEEP LEARNING TRAINING")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\n[1/8] Loading dataset...")

df = pd.read_csv(CSV_PATH)

print(f"Dataset shape: {df.shape}")
print(f"Machines: {df['machine_id'].nunique()}")


# ============================================================
# 2. FEATURES
# ============================================================

FEATURES = [
    "spindle_speed_rpm",
    "spindle_current_a",
    "torque_nm",
    "vibration_x",
    "vibration_y",
    "vibration_z",
    "temperature_c",
    "coolant_pressure_bar",
    "cutting_force_n",
    "acoustic_emission",
    "tool_wear_percent",
    "tool_age_hours",
]

TARGET_FAILURE = "failure"
TARGET_RUL = "rul_hours"


# ============================================================
# 3. MACHINE-WISE SPLIT
# ============================================================

print("\n[2/8] Creating machine-wise train/test split...")

machines = sorted(df["machine_id"].unique())

rng = np.random.default_rng(42)
rng.shuffle(machines)

split_index = int(len(machines) * 0.80)

train_machines = machines[:split_index]
test_machines = machines[split_index:]

train_df = df[
    df["machine_id"].isin(train_machines)
].copy()

test_df = df[
    df["machine_id"].isin(test_machines)
].copy()

print(f"Training machines: {len(train_machines)}")
print(f"Testing machines : {len(test_machines)}")
print(f"Training records : {len(train_df)}")
print(f"Testing records  : {len(test_df)}")


# ============================================================
# 4. SCALING
# ============================================================

print("\n[3/8] Scaling sensor features...")

scaler = StandardScaler()

X_train = scaler.fit_transform(
    train_df[FEATURES]
)

X_test = scaler.transform(
    test_df[FEATURES]
)

y_failure_train = train_df[
    TARGET_FAILURE
].values.astype(np.float32)

y_failure_test = test_df[
    TARGET_FAILURE
].values.astype(np.float32)

with open(
    os.path.join(MODEL_DIR, "scaler.pkl"),
    "wb"
) as f:
    pickle.dump(scaler, f)

print("Scaler saved.")


# ============================================================
# 5. ANN FAILURE MODEL
# ============================================================

print("\n[4/8] Training ANN failure model...")

failure_model = tf.keras.Sequential([

    tf.keras.layers.Input(
        shape=(len(FEATURES),)
    ),

    tf.keras.layers.Dense(
        128,
        activation="relu"
    ),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.20),

    tf.keras.layers.Dense(
        64,
        activation="relu"
    ),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.15),

    tf.keras.layers.Dense(
        32,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        1,
        activation="sigmoid"
    )
])

failure_model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        tf.keras.metrics.AUC(name="auc")
    ]
)

negative = np.sum(
    y_failure_train == 0
)

positive = np.sum(
    y_failure_train == 1
)

class_weight = {
    0: len(y_failure_train) / (2 * negative),
    1: len(y_failure_train) / (2 * positive)
}

failure_model.fit(
    X_train,
    y_failure_train,
    validation_split=0.15,
    epochs=50,
    batch_size=256,
    class_weight=class_weight,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
            monitor="val_auc",
            patience=7,
            mode="max",
            restore_best_weights=True
        )
    ],
    verbose=1
)

failure_model.save(
    os.path.join(
        MODEL_DIR,
        "failure_model.keras"
    )
)

failure_prob = failure_model.predict(
    X_test,
    verbose=0
).flatten()

failure_pred = (
    failure_prob >= 0.5
).astype(int)

failure_accuracy = accuracy_score(
    y_failure_test,
    failure_pred
)

failure_precision = precision_score(
    y_failure_test,
    failure_pred,
    zero_division=0
)

failure_recall = recall_score(
    y_failure_test,
    failure_pred,
    zero_division=0
)

failure_f1 = f1_score(
    y_failure_test,
    failure_pred,
    zero_division=0
)

failure_auc = roc_auc_score(
    y_failure_test,
    failure_prob
)

print("\n--- FAILURE MODEL RESULTS ---")
print(
    f"Accuracy : {failure_accuracy:.4f}"
)
print(
    f"Precision: {failure_precision:.4f}"
)
print(
    f"Recall   : {failure_recall:.4f}"
)
print(
    f"F1 Score : {failure_f1:.4f}"
)
print(
    f"ROC-AUC  : {failure_auc:.4f}"
)


# ============================================================
# 6. IMPROVED AUTOENCODER
# ============================================================

print("\n[5/8] Training deep anomaly detection model...")

# ------------------------------------------------------------
# IMPORTANT:
# Use only clearly healthy samples.
# This prevents degraded samples from being treated as normal.
# ------------------------------------------------------------

healthy_train_df = train_df[
    (train_df["failure"] == 0) &
    (train_df["health_score"] >= 75) &
    (train_df["tool_wear_percent"] <= 35)
].copy()

print(
    f"Healthy training samples: "
    f"{len(healthy_train_df)}"
)

X_healthy = scaler.transform(
    healthy_train_df[FEATURES]
)


# ------------------------------------------------------------
# Autoencoder
# ------------------------------------------------------------

autoencoder = tf.keras.Sequential([

    tf.keras.layers.Input(
        shape=(len(FEATURES),)
    ),

    # Encoder
    tf.keras.layers.Dense(
        64,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        32,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        16,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        8,
        activation="relu"
    ),

    # Decoder
    tf.keras.layers.Dense(
        16,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        32,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        64,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        len(FEATURES),
        activation="linear"
    )
])

autoencoder.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.0005
    ),
    loss="mse"
)

autoencoder.fit(
    X_healthy,
    X_healthy,
    validation_split=0.15,
    epochs=80,
    batch_size=128,
    shuffle=True,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True
        )
    ],
    verbose=1
)

autoencoder.save(
    os.path.join(
        MODEL_DIR,
        "autoencoder_model.keras"
    )
)


# ------------------------------------------------------------
# Reconstruction error
# ------------------------------------------------------------

healthy_reconstructed = autoencoder.predict(
    X_healthy,
    verbose=0
)

healthy_errors = np.mean(
    np.square(
        X_healthy -
        healthy_reconstructed
    ),
    axis=1
)


# Use 99th percentile of healthy behavior
threshold = np.percentile(
    healthy_errors,
    99
)

print(
    f"Anomaly threshold: {threshold:.6f}"
)


# ------------------------------------------------------------
# Test anomaly detection
# ------------------------------------------------------------

X_test_reconstructed = autoencoder.predict(
    X_test,
    verbose=0
)

test_errors = np.mean(
    np.square(
        X_test -
        X_test_reconstructed
    ),
    axis=1
)

anomaly_pred = (
    test_errors > threshold
).astype(int)

anomaly_true = y_failure_test.astype(int)

anomaly_accuracy = accuracy_score(
    anomaly_true,
    anomaly_pred
)

anomaly_precision = precision_score(
    anomaly_true,
    anomaly_pred,
    zero_division=0
)

anomaly_recall = recall_score(
    anomaly_true,
    anomaly_pred,
    zero_division=0
)

anomaly_f1 = f1_score(
    anomaly_true,
    anomaly_pred,
    zero_division=0
)

try:
    anomaly_auc = roc_auc_score(
        anomaly_true,
        test_errors
    )
except ValueError:
    anomaly_auc = 0.0

print("\n--- ANOMALY MODEL RESULTS ---")
print(
    f"Accuracy : {anomaly_accuracy:.4f}"
)
print(
    f"Precision: {anomaly_precision:.4f}"
)
print(
    f"Recall   : {anomaly_recall:.4f}"
)
print(
    f"F1 Score : {anomaly_f1:.4f}"
)
print(
    f"ROC-AUC  : {anomaly_auc:.4f}"
)


# ============================================================
# 7. IMPROVED LSTM RUL MODEL
# ============================================================

print("\n[6/8] Creating LSTM degradation sequences...")

SEQUENCE_LENGTH = 40

RUL_SCALE = 1250.0


def create_sequences(
    dataframe,
    scaler,
    features,
    sequence_length
):

    X_sequences = []
    y_sequences = []

    for machine_id in dataframe[
        "machine_id"
    ].unique():

        machine_df = dataframe[
            dataframe["machine_id"] == machine_id
        ].sort_values("cycle")

        machine_X = scaler.transform(
            machine_df[features]
        )

        machine_rul = machine_df[
            TARGET_RUL
        ].values.astype(np.float32)

        if len(machine_X) <= sequence_length:
            continue

        for i in range(
            len(machine_X) -
            sequence_length
        ):

            X_sequences.append(
                machine_X[
                    i:i + sequence_length
                ]
            )

            # RUL at end of sequence
            y_sequences.append(
                machine_rul[
                    i + sequence_length - 1
                ]
            )

    return (
        np.asarray(
            X_sequences,
            dtype=np.float32
        ),

        np.asarray(
            y_sequences,
            dtype=np.float32
        )
    )


X_lstm_train, y_lstm_train = create_sequences(
    train_df,
    scaler,
    FEATURES,
    SEQUENCE_LENGTH
)

X_lstm_test, y_lstm_test = create_sequences(
    test_df,
    scaler,
    FEATURES,
    SEQUENCE_LENGTH
)

print(
    f"Training sequences: "
    f"{X_lstm_train.shape}"
)

print(
    f"Testing sequences : "
    f"{X_lstm_test.shape}"
)


# ------------------------------------------------------------
# RUL normalization
# ------------------------------------------------------------

y_lstm_train_scaled = (
    y_lstm_train /
    RUL_SCALE
)

y_lstm_test_scaled = (
    y_lstm_test /
    RUL_SCALE
)


# ------------------------------------------------------------
# LSTM network
# ------------------------------------------------------------

rul_model = tf.keras.Sequential([

    tf.keras.layers.Input(
        shape=(
            SEQUENCE_LENGTH,
            len(FEATURES)
        )
    ),

    tf.keras.layers.LSTM(
        128,
        return_sequences=True
    ),

    tf.keras.layers.Dropout(
        0.15
    ),

    tf.keras.layers.LSTM(
        64
    ),

    tf.keras.layers.Dropout(
        0.10
    ),

    tf.keras.layers.Dense(
        32,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        16,
        activation="relu"
    ),

    tf.keras.layers.Dense(
        1,
        activation="linear"
    )
])

rul_model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.0005
    ),
    loss="huber",
    metrics=["mae"]
)

rul_model.fit(
    X_lstm_train,
    y_lstm_train_scaled,
    validation_split=0.15,
    epochs=80,
    batch_size=128,
    shuffle=True,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True
        ),

        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=0.00001
        )
    ],
    verbose=1
)

rul_model.save(
    os.path.join(
        MODEL_DIR,
        "rul_lstm_model.keras"
    )
)


# ------------------------------------------------------------
# RUL predictions
# ------------------------------------------------------------

rul_predictions_scaled = (
    rul_model.predict(
        X_lstm_test,
        verbose=0
    ).flatten()
)

rul_predictions = (
    rul_predictions_scaled *
    RUL_SCALE
)

# Prevent impossible negative RUL
rul_predictions = np.maximum(
    rul_predictions,
    0
)

rul_mae = mean_absolute_error(
    y_lstm_test,
    rul_predictions
)

rul_rmse = np.sqrt(
    mean_squared_error(
        y_lstm_test,
        rul_predictions
    )
)

print("\n--- RUL MODEL RESULTS ---")

print(
    f"MAE : {rul_mae:.2f} hours"
)

print(
    f"RMSE: {rul_rmse:.2f} hours"
)


# ============================================================
# 8. SAVE CONFIGURATION
# ============================================================

print("\n[7/8] Saving model configuration...")

config = {

    "features": FEATURES,

    "sequence_length":
        SEQUENCE_LENGTH,

    "rul_scale":
        RUL_SCALE,

    "anomaly_threshold":
        float(threshold),

    "failure_threshold":
        0.5,

    "models": {

        "failure":
            "failure_model.keras",

        "autoencoder":
            "autoencoder_model.keras",

        "rul":
            "rul_lstm_model.keras"
    }
}

with open(
    os.path.join(
        MODEL_DIR,
        "model_config.json"
    ),
    "w"
) as f:

    json.dump(
        config,
        f,
        indent=4
    )


# ============================================================
# 9. SAMPLE PREDICTION
# ============================================================

print("\n[8/8] Generating sample prediction...")

sample_machine = test_df[
    test_df["machine_id"] ==
    test_machines[0]
].sort_values("cycle")

sample_sensor = scaler.transform(
    sample_machine[FEATURES]
)

latest_sensor = sample_sensor[
    -1:
]


# Failure
sample_failure = failure_model.predict(
    latest_sensor,
    verbose=0
)[0][0]


# Anomaly
sample_reconstructed = (
    autoencoder.predict(
        latest_sensor,
        verbose=0
    )
)

sample_anomaly = np.mean(
    np.square(
        latest_sensor -
        sample_reconstructed
    )
)


# RUL
if len(sample_sensor) >= SEQUENCE_LENGTH:

    sample_sequence = sample_sensor[
        -SEQUENCE_LENGTH:
    ]

    sample_rul = (
        rul_model.predict(
            sample_sequence.reshape(
                1,
                SEQUENCE_LENGTH,
                len(FEATURES)
            ),
            verbose=0
        )[0][0]
        * RUL_SCALE
    )

else:

    sample_rul = 0


sample_rul = max(
    0,
    float(sample_rul)
)


# ------------------------------------------------------------
# Health calculation
# ------------------------------------------------------------

anomaly_ratio = (
    sample_anomaly /
    max(threshold, 1e-8)
)

anomaly_ratio = min(
    anomaly_ratio,
    3
)

failure_penalty = (
    sample_failure *
    55
)

anomaly_penalty = (
    anomaly_ratio *
    20
)

rul_penalty = (
    max(
        0,
        1 -
        sample_rul /
        RUL_SCALE
    ) *
    25
)

sample_health = (
    100 -
    failure_penalty -
    anomaly_penalty -
    rul_penalty
)

sample_health = max(
    0,
    min(
        100,
        sample_health
    )
)


if sample_health >= 70:

    sample_status = "HEALTHY"

elif sample_health >= 40:

    sample_status = "AT_RISK"

else:

    sample_status = "CRITICAL"


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("FORTRESS SAMPLE PREDICTION")
print("=" * 70)

print(
    f"Machine              : "
    f"{sample_machine['machine_id'].iloc[0]}"
)

print(
    f"Component            : "
    f"{sample_machine['component_type'].iloc[0]}"
)

print(
    f"Operation             : "
    f"{sample_machine['machining_operation'].iloc[0]}"
)

print(
    f"\nFailure Probability  : "
    f"{sample_failure * 100:.2f}%"
)

print(
    f"Anomaly Score        : "
    f"{sample_anomaly:.6f}"
)

print(
    f"RUL                  : "
    f"{sample_rul:.2f} hours"
)

print(
    f"Health Score         : "
    f"{sample_health:.2f}%"
)

print(
    f"Status               : "
    f"{sample_status}"
)

print("=" * 70)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FORTRESS TRAINING COMPLETE")
print("=" * 70)

print("\nModels saved:")

print("  ✓ failure_model.keras")
print("  ✓ autoencoder_model.keras")
print("  ✓ rul_lstm_model.keras")
print("  ✓ scaler.pkl")
print("  ✓ model_config.json")

print("\nFinal metrics:")

print(
    f"  ANN Accuracy : "
    f"{failure_accuracy * 100:.2f}%"
)

print(
    f"  ANN ROC-AUC  : "
    f"{failure_auc:.4f}"
)

print(
    f"  ANN F1       : "
    f"{failure_f1:.4f}"
)

print(
    f"\n  Autoencoder Accuracy: "
    f"{anomaly_accuracy * 100:.2f}%"
)

print(
    f"  Autoencoder ROC-AUC : "
    f"{anomaly_auc:.4f}"
)

print(
    f"\n  LSTM RUL MAE : "
    f"{rul_mae:.2f} hours"
)

print(
    f"  LSTM RUL RMSE: "
    f"{rul_rmse:.2f} hours"
)

print("\n" + "=" * 70)