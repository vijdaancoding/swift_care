# Demo medical knowledge base
FIRST_AID_DATA = {
    "heart attack": [
        "Call emergency services immediately.",
        "Begin CPR if the person is unresponsive and not breathing.",
        "Use an AED if available."
    ],
    "burns": [
        "Cool the burn under running water for 20 minutes.",
        "Do not apply ice directly.",
        "Cover with a sterile non-fluffy dressing."
    ],
    "choking": [
        "If the person cannot cough, speak, or breathe: perform abdominal thrusts.",
        "Call emergency services immediately."
    ],
    "seizure": [
        "Move dangerous objects away.",
        "Do not restrain the person.",
        "After convulsions, place them in the recovery position."
    ]
}

def lookup_first_aid(condition: str) -> str:
    """
    Demonstration tool for first-aid lookup.
    Returns a helpful protocol or a fallback message.
    """
    condition = condition.lower().strip()
    if condition in FIRST_AID_DATA:
        steps = FIRST_AID_DATA[condition]
        return f"🩺 First Aid for {condition.title()}:\n- " + "\n- ".join(steps)
    else:
        return f"❌ No first aid information found for '{condition}'. Please consult emergency services."
