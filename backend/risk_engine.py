# ============================================================
# FORTRESS RISK ENGINE
# Combines AI predictions into a machine health assessment.
# ============================================================


def clamp(value, minimum, maximum):
    """Keep a value within the specified range."""
    return max(
        minimum,
        min(maximum, value)
    )


def calculate_risk(
    failure_probability,
    anomaly_score,
    anomaly_threshold,
    rul_hours,
    rul_scale
):
    """
    Combine:
        1. ANN failure probability
        2. Autoencoder anomaly severity
        3. LSTM remaining useful life

    into a final machine health score.
    """

    # ========================================================
    # 1. ANOMALY SEVERITY
    # ========================================================

    anomaly_ratio = (
        anomaly_score /
        max(anomaly_threshold, 1e-8)
    )

    # Cap anomaly severity at 3x threshold.
    anomaly_ratio = min(
        anomaly_ratio,
        3.0
    )

    # Convert to 0-100 severity.
    anomaly_severity = (
        anomaly_ratio / 3.0
    ) * 100


    # ========================================================
    # 2. FAILURE RISK
    # ========================================================

    failure_risk = (
        clamp(
            failure_probability,
            0.0,
            1.0
        )
        * 100
    )


    # ========================================================
    # 3. RUL RISK
    # ========================================================

    rul_ratio = (
        rul_hours /
        max(rul_scale, 1e-8)
    )

    rul_ratio = clamp(
        rul_ratio,
        0.0,
        1.0
    )

    # High RUL = low risk
    # Low RUL = high risk

    rul_risk = (
        1.0 -
        rul_ratio
    ) * 100


    # ========================================================
    # 4. COMBINED RISK
    # ========================================================
    #
    # Weights:
    #
    # ANN failure prediction  = 50%
    # Anomaly detection       = 30%
    # RUL                     = 20%
    #
    # ========================================================

    combined_risk = (
        failure_risk * 0.60
        +
        anomaly_severity * 0.15
        +
        rul_risk * 0.25
    )


    combined_risk = clamp(
        combined_risk,
        0,
        100
    )


    # ========================================================
    # 5. HEALTH SCORE
    # ========================================================

    health_score = (
        100 -
        combined_risk
    )

    health_score = clamp(
        health_score,
        0,
        100
    )


    # ========================================================
    # 6. MACHINE STATUS
    # ========================================================
    #
    # REQUIRED FORTRESS HEALTH RULE:
    #
    # > 80       = HEALTHY
    # 40 to 80   = AT RISK
    # < 40       = CRITICAL
    #
    # NOTE:
    # Exactly 80 is AT RISK.
    #
    # ========================================================

    if health_score > 80:

        status = "HEALTHY"

    elif health_score >= 40:

        status = "AT_RISK"

    else:

        status = "CRITICAL"


    # ========================================================
    # 7. MAINTENANCE RECOMMENDATION
    # ========================================================

    if status == "CRITICAL":

        recommendation = (
            "Immediate maintenance inspection recommended. "
            "Consider a controlled machine shutdown."
        )

    elif status == "AT_RISK":

        recommendation = (
            "Schedule preventive maintenance and "
            "closely monitor machine degradation."
        )

    else:

        recommendation = (
            "Machine operating within normal parameters. "
            "Continue normal monitoring."
        )


    # ========================================================
    # 8. RETURN
    # ========================================================

    return {

        "health_score": round(
            health_score,
            2
        ),

        "status": status,

        "recommendation": recommendation,

        "anomaly_ratio": round(
            anomaly_ratio,
            3
        ),

        "failure_risk": round(
            failure_risk,
            2
        ),

        "anomaly_severity": round(
            anomaly_severity,
            2
        ),

        "rul_risk": round(
            rul_risk,
            2
        ),

        "combined_risk": round(
            combined_risk,
            2
        )

    }