
import pandas as pd

path = "ml/data/fortress_automotive_cnc_dataset.csv"
df = pd.read_csv(path)

print("FEATURE RANGE CHECK")
features = [
    "spindle_speed_rpm", "spindle_current_a", "torque_nm",
    "vibration_x", "vibration_y", "vibration_z",
    "temperature_c", "coolant_pressure_bar",
    "cutting_force_n", "acoustic_emission",
    "tool_wear_percent", "tool_age_hours"
]
print(df[features].describe().round(3).to_string())

print("\nFAILURE COUNTS BY MACHINE")
print(df.groupby("machine_id")["failure"].agg(["sum", "count"]).to_string())

print("\nRUL AT FIRST AND LAST CYCLE")
for machine_id, group in df.groupby("machine_id"):
    group = group.sort_values("cycle")
    print(
        machine_id,
        "first =", round(group["rul_hours"].iloc[0], 2),
        "last =", round(group["rul_hours"].iloc[-1], 2),
        "first wear =", round(group["tool_wear_percent"].iloc[0], 2),
        "last wear =", round(group["tool_wear_percent"].iloc[-1], 2)
    )

print("\nHEALTHY DATA AVAILABLE FOR AUTOENCODER")
healthy = df[
    (df["failure"] == 0)
    & (df["health_score"] >= 75)
    & (df["tool_wear_percent"] <= 35)
]
print("Healthy rows:", len(healthy))
print("Healthy machines:", healthy["machine_id"].nunique())

print("\nFAILURE LABEL CONSISTENCY")
print(pd.crosstab(df["failure"], df["status"]).to_string())
