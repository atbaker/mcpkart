"""Scripted infrastructure controls; never a model result or paid fallback."""

def free_choices(facts):
    """Free infrastructure control only; never used in actual model collection."""
    theta = facts["wheel_facts"]["road"]["preview_15m_bearing_deg"]
    wheel = (
        "hard_right"
        if theta < -22
        else "right"
        if theta < -7
        else "straight"
        if theta <= 7
        else "left"
        if theta <= 22
        else "hard_left"
    )
    p = facts["pedal_facts"]
    road = p["road"]
    speed = p["kart"]["speed_m_s"]
    lateral = p["current_road_frame"]["velocity_left_m_s"]
    outside = (
        not road["on_road"]
        or road["offset_m"] > 0
        and road["left_edge_clearance_m"] <= 3
        and lateral >= 0.5
        or road["offset_m"] < 0
        and road["right_edge_clearance_m"] <= 3
        and lateral <= -0.5
    )
    return wheel, "accelerate" if speed < 2 or not outside else "brake" if speed > 6 else "coast"
