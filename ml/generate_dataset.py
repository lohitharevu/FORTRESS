import os
import numpy as np
import pandas as pd

# ============================================================
# FORTRESS
# AUTOMOTIVE CNC PREDICTIVE MAINTENANCE DATASET
# ============================================================

np.random.seed(42)

OUTPUT_DIR = os.path.join("ml", "data")
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "fortress_automotive_cnc_dataset.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

N_MACHINES = 50
CYCLES_PER_MACHINE = 1000

COMPONENTS = [
    ("Engine Block", "Boring"),
    ("Engine Block", "Milling"),
    ("Cylinder Head", "Milling"),
    ("Cylinder Head", "Drilling"),
    ("Crankshaft", "Turning"),
    ("Crankshaft", "Grinding"),
    ("Transmission Case", "Milling"),
    ("Transmission Case", "Drilling"),
    ("Piston", "Turning"),
    ("Brake Component", "Turning"),
]

MATERIALS = [
    "Aluminum Alloy",
    "Cast Iron",
    "Steel",
    "Forged Steel",
    "Aluminum-Silicon Alloy",
]


# ============================================================
# MACHINE PROFILES
# ============================================================

machine_profiles = []

for i in range(N_MACHINES):

    component, operation = COMPONENTS[
        i % len(COMPONENTS)
    ]

    material = MATERIALS[
        i % len(MATERIALS)
    ]

    base_rpm = np.random.uniform(3000, 5000)
    base_current = np.random.uniform(15, 27)
    base_torque = np.random.uniform(35, 65)
    base_temperature = np.random.uniform(52, 65)
    base_pressure = np.random.uniform(4.5, 6.5)

    # Different machines have slightly different tool lives
    tool_life = np.random.uniform(850, 1250)

    machine_profiles.append({
        "machine_id": f"AUTO-CNC-{i + 1:03d}",
        "component": component,
        "operation": operation,
        "material": material,
        "base_rpm": base_rpm,
        "base_current": base_current,
        "base_torque": base_torque,
        "base_temperature": base_temperature,
        "base_pressure": base_pressure,
        "tool_life": tool_life,
        "vibration_factor": np.random.uniform(0.85, 1.15),
        "wear_factor": np.random.uniform(0.90, 1.10),
        "phase": np.random.uniform(0, 2 * np.pi),
    })


# ============================================================
# GENERATE DATA
# ============================================================

rows = []

for machine in machine_profiles:

    for cycle in range(CYCLES_PER_MACHINE):

        # ----------------------------------------------------
        # MACHINE PROGRESS
        # ----------------------------------------------------

        progress = cycle / (CYCLES_PER_MACHINE - 1)

        # ----------------------------------------------------
        # TOOL WEAR
        # ----------------------------------------------------

        # Slow degradation initially.
        # Faster degradation near end of life.

        wear_curve = (
            0.15 * progress
            + 0.85 * (progress ** 2.4)
        )

        tool_wear = (
            100
            * wear_curve
            * machine["wear_factor"]
        )

        tool_wear += np.random.normal(0, 1.0)

        tool_wear = np.clip(
            tool_wear,
            0,
            100
        )

        # ----------------------------------------------------
        # SPINDLE SPEED
        # ----------------------------------------------------

        rpm = (
            machine["base_rpm"]
            + 120 * np.sin(
                cycle / 80 + machine["phase"]
            )
            + np.random.normal(0, 45)
        )

        rpm = np.clip(
            rpm,
            2200,
            5800
        )

        # ----------------------------------------------------
        # TORQUE
        # ----------------------------------------------------

        torque = (
            machine["base_torque"]
            + 0.14 * tool_wear
            + 1.5 * np.sin(cycle / 100)
            + np.random.normal(0, 1.5)
        )

        torque = np.clip(
            torque,
            20,
            90
        )

        # ----------------------------------------------------
        # SPINDLE CURRENT
        # ----------------------------------------------------

        spindle_current = (
            machine["base_current"]
            + 0.055 * tool_wear
            + 0.10 * (
                torque -
                machine["base_torque"]
            )
            + np.random.normal(0, 0.5)
        )

        spindle_current = np.clip(
            spindle_current,
            8,
            38
        )

        # ----------------------------------------------------
        # VIBRATION
        # ----------------------------------------------------

        vibration_base = (
            0.75
            + 0.010 * tool_wear
            + 0.00045 * tool_wear ** 2
        )

        vibration_x = (
            vibration_base
            * machine["vibration_factor"]
            + np.random.normal(0, 0.10)
        )

        vibration_y = (
            vibration_base
            * 0.92
            * machine["vibration_factor"]
            + np.random.normal(0, 0.10)
        )

        vibration_z = (
            vibration_base
            * 1.08
            * machine["vibration_factor"]
            + np.random.normal(0, 0.12)
        )

        vibration_x = max(
            0.1,
            vibration_x
        )

        vibration_y = max(
            0.1,
            vibration_y
        )

        vibration_z = max(
            0.1,
            vibration_z
        )

        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        temperature = (
            machine["base_temperature"]
            + 0.045 * tool_wear
            + 0.035 * (
                torque -
                machine["base_torque"]
            )
            + np.random.normal(0, 0.8)
        )

        temperature = np.clip(
            temperature,
            40,
            100
        )

        # ----------------------------------------------------
        # COOLANT PRESSURE
        # ----------------------------------------------------

        coolant_pressure = (
            machine["base_pressure"]
            - 0.003 * tool_wear
            + np.random.normal(0, 0.08)
        )

        coolant_pressure = np.clip(
            coolant_pressure,
            3.0,
            7.0
        )

        # ----------------------------------------------------
        # CUTTING FORCE
        # ----------------------------------------------------

        cutting_force = (
            torque * 8.5
            + 0.25 * tool_wear
            + np.random.normal(0, 5)
        )

        cutting_force = np.clip(
            cutting_force,
            150,
            800
        )

        # ----------------------------------------------------
        # ACOUSTIC EMISSION
        # ----------------------------------------------------

        acoustic_emission = (
            25
            + 0.20 * tool_wear
            + 1.5 * vibration_z
            + np.random.normal(0, 1.8)
        )

        acoustic_emission = max(
            acoustic_emission,
            5
        )

        # ----------------------------------------------------
        # TOOL AGE
        # ----------------------------------------------------

        tool_age_hours = (
            progress *
            machine["tool_life"]
        )

        # ====================================================
        # NORMALIZED DEGRADATION FEATURES
        # ====================================================

        wear_norm = np.clip(
            tool_wear / 100,
            0,
            1
        )

        vibration_norm = np.clip(
            (vibration_z - 0.7) / 6.0,
            0,
            1
        )

        current_norm = np.clip(
            (spindle_current - 12) / 25,
            0,
            1
        )

        temperature_norm = np.clip(
            (temperature - 50) / 50,
            0,
            1
        )

        force_norm = np.clip(
            (cutting_force - 200) / 600,
            0,
            1
        )

        # ====================================================
        # IMPROVED RUL MODEL
        # ====================================================

        # Instead of calculating RUL only from elapsed tool age,
        # RUL now reflects the actual degradation state.
        #
        # Low wear  -> long RUL
        # Medium wear -> decreasing RUL
        # High wear -> rapid RUL reduction
        #
        # Multiple machine-condition signals contribute.

        degradation_index = (
            0.55 * wear_norm
            + 0.20 * vibration_norm
            + 0.10 * current_norm
            + 0.10 * temperature_norm
            + 0.05 * force_norm
        )

        degradation_index = np.clip(
            degradation_index,
            0,
            1
        )

        # Nonlinear remaining-life curve
        remaining_fraction = (
            1.0 -
            degradation_index ** 1.35
        )

        rul_hours = (
            machine["tool_life"]
            * remaining_fraction
        )

        # Make late-life degradation sharper
        if tool_wear > 80:

            extra_degradation = (
                (tool_wear - 80) / 20
            )

            rul_hours *= (
                1.0 -
                0.25 * extra_degradation
            )

        # Realistic measurement uncertainty
        rul_hours += np.random.normal(
            0,
            8
        )

        rul_hours = np.clip(
            rul_hours,
            0,
            machine["tool_life"]
        )

        # ====================================================
        # ANOMALY SCORE
        # ====================================================

        anomaly_score = (
            0.45 * wear_norm
            + 0.22 * vibration_norm
            + 0.13 * current_norm
            + 0.10 * temperature_norm
            + 0.10 * force_norm
        )

        anomaly_score += np.random.normal(
            0,
            0.015
        )

        anomaly_score = np.clip(
            anomaly_score,
            0,
            1
        )

        # ====================================================
        # FAILURE RISK
        # ====================================================

        risk_signal = (
            4.5 * (wear_norm ** 3)
            + 2.2 * (vibration_norm ** 2)
            + 1.5 * current_norm
            + 1.2 * temperature_norm
            + 0.8 * force_norm
            - 2.8
        )

        failure_probability = (
            1 /
            (
                1 +
                np.exp(-risk_signal)
            )
        )

        failure_probability += np.random.normal(
            0,
            0.015
        )

        failure_probability = np.clip(
            failure_probability,
            0,
            1
        )

        # ====================================================
        # FAILURE LABEL
        # ====================================================

        failure = int(
            (
                failure_probability >= 0.70
                and
                (
                    vibration_norm > 0.45
                    or
                    wear_norm > 0.70
                )
            )
            or
            (
                tool_wear > 88
                and
                vibration_norm > 0.40
            )
            or
            (
                rul_hours < 80
                and
                tool_wear > 80
            )
        )

        # ====================================================
        # HEALTH SCORE
        # ====================================================

        degradation = (
            0.40 * wear_norm
            + 0.25 * vibration_norm
            + 0.15 * current_norm
            + 0.10 * temperature_norm
            + 0.10 * force_norm
        )

        health_score = (
            100
            - 70 * degradation
            - 15 * failure_probability
        )

        health_score += np.random.normal(
            0,
            1.0
        )

        health_score = np.clip(
            health_score,
            0,
            100
        )

        # ====================================================
        # MACHINE STATUS
        # ====================================================

        if health_score >= 70:

            status = "HEALTHY"

        elif health_score >= 40:

            status = "AT_RISK"

        else:

            status = "CRITICAL"

        # ====================================================
        # MAINTENANCE RECOMMENDATION
        # ====================================================

        if status == "HEALTHY":

            recommendation = (
                "Continue production; routine monitoring"
            )

        elif status == "AT_RISK":

            recommendation = (
                "Schedule CNC inspection and tool maintenance"
            )

        else:

            recommendation = (
                "Immediate inspection; consider stopping machine"
            )

        # ====================================================
        # TIMESTAMP
        # ====================================================

        timestamp = (
            pd.Timestamp("2025-01-01")
            + pd.Timedelta(
                hours=tool_age_hours
            )
        )

        # ====================================================
        # RECORD
        # ====================================================

        rows.append({

            "machine_id":
                machine["machine_id"],

            "industry":
                "Automotive Manufacturing",

            "component_type":
                machine["component"],

            "machining_operation":
                machine["operation"],

            "workpiece_material":
                machine["material"],

            "cycle":
                cycle,

            "timestamp":
                timestamp,

            "spindle_speed_rpm":
                round(rpm, 3),

            "spindle_current_a":
                round(spindle_current, 3),

            "torque_nm":
                round(torque, 3),

            "vibration_x":
                round(vibration_x, 4),

            "vibration_y":
                round(vibration_y, 4),

            "vibration_z":
                round(vibration_z, 4),

            "temperature_c":
                round(temperature, 3),

            "coolant_pressure_bar":
                round(coolant_pressure, 3),

            "cutting_force_n":
                round(cutting_force, 3),

            "acoustic_emission":
                round(acoustic_emission, 3),

            "tool_wear_percent":
                round(tool_wear, 3),

            "tool_age_hours":
                round(tool_age_hours, 3),

            "rul_hours":
                round(rul_hours, 3),

            "anomaly_score":
                round(anomaly_score, 5),

            "failure_probability":
                round(failure_probability, 5),

            "health_score":
                round(health_score, 3),

            "failure":
                failure,

            "status":
                status,

            "maintenance_recommendation":
                recommendation
        })


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(rows)

df = df.sort_values(
    ["machine_id", "cycle"]
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 70)
print("FORTRESS AUTOMOTIVE CNC DATASET CREATED")
print("=" * 70)

print(
    f"Output file : {OUTPUT_FILE}"
)

print(
    f"Records     : {len(df):,}"
)

print(
    f"Machines    : {df['machine_id'].nunique()}"
)

print(
    f"Features    : {len(df.columns)}"
)

print()
print("Component distribution:")
print(
    df["component_type"].value_counts()
)

print()
print("Operation distribution:")
print(
    df["machining_operation"].value_counts()
)

print()
print("Failure distribution:")
print(
    df["failure"].value_counts()
)

print(
    (
        df["failure"]
        .value_counts(normalize=True)
        * 100
    )
    .round(2)
    .astype(str)
    + "%"
)

print()
print("Machine status:")
print(
    df["status"].value_counts()
)

print(
    (
        df["status"]
        .value_counts(normalize=True)
        * 100
    )
    .round(2)
    .astype(str)
    + "%"
)

print()
print("Health statistics:")
print(
    df["health_score"]
    .describe()
    .round(2)
)

print()
print("RUL statistics:")
print(
    df["rul_hours"]
    .describe()
    .round(2)
)

print()
print("Tool wear statistics:")
print(
    df["tool_wear_percent"]
    .describe()
    .round(2)
)

print()
print("=" * 70)
print("DATASET READY FOR DEEP LEARNING")
print("=" * 70)