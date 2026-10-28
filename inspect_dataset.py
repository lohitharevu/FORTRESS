
import pandas as pd
from pathlib import Path

path = Path("ml/data/fortress_automotive_cnc_dataset.csv")

df = pd.read_csv(path)

print("\n--- DATASET SHAPE ---")
print(df.shape)

print("\n--- COLUMNS AND DATA TYPES ---")
print(df.dtypes.to_string())

print("\n--- MISSING VALUES ---")
print(df.isnull().sum().to_string())

print("\n--- DUPLICATE ROWS ---")
print(df.duplicated().sum())

print("\n--- FAILURE DISTRIBUTION ---")
print(df["failure"].value_counts(dropna=False).to_string())
print("\nFailure percentages:")
print((df["failure"].value_counts(normalize=True) * 100).round(2))

print("\n--- RUL STATISTICS ---")
print(df["rul_hours"].describe().round(3))

print("\n--- MACHINE COUNTS ---")
print("Unique machines:", df["machine_id"].nunique())
print(df.groupby("machine_id").size().describe())

print("\n--- CYCLE ORDER CHECK ---")
print("Rows sorted by machine and cycle:",
      df[["machine_id", "cycle"]].equals(
          df.sort_values(["machine_id", "cycle"])[["machine_id", "cycle"]]
          .reset_index(drop=True)
      ))

print("\n--- TARGET CORRELATIONS ---")
cols = [
    "failure", "failure_probability", "rul_hours",
    "anomaly_score", "health_score", "tool_wear_percent"
]
print(df[cols].corr(numeric_only=True).round(3))

print("\n--- SAMPLE RECORDS ---")
print(df.head(5).to_string(index=False))

print("\n--- LATE-CYCLE RECORDS ---")
print(
    df.sort_values(["machine_id", "cycle"])
      .groupby("machine_id")
      .tail(2)[["machine_id", "cycle", "failure",
                "rul_hours", "tool_wear_percent"]]
      .to_string(index=False)
)
