
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
    anomaly_ratio = (
        anomaly_score /
        max(anomaly_threshold, 1e-8)
    )

    anomaly_ratio = min(
        anomaly_ratio,
        3.0
    )


    anomaly_severity = (
        anomaly_ratio / 3.0
    ) * 100

    failure_risk = (
        clamp(
            failure_probability,
            0.0,
            1.0
        )
        * 100
    )

    rul_ratio = (
        rul_hours /
        max(rul_scale, 1e-8)
    )

    rul_ratio = clamp(
        rul_ratio,
        0.0,
        1.0
    )

    rul_risk = (
        1.0 -
        rul_ratio
    ) * 100


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

    health_score = (
        100 -
        combined_risk
    )

    health_score = clamp(
        health_score,
        0,
        100
    )


    if health_score > 80:

        status = "HEALTHY"

    elif health_score >= 40:

        status = "AT_RISK"

    else:

        status = "CRITICAL"


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