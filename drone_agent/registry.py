from drone_agent.drone_skills import (
    drone_status,
    drone_takeoff_land,
    drone_square_route,
    drone_emergency_stop,
)


SKILL_REGISTRY = {
    "drone_status": drone_status,
    "drone_takeoff_land": drone_takeoff_land,
    "drone_square_route": drone_square_route,
    "drone_emergency_stop": drone_emergency_stop,
}


def call_skill(skill: str, vehicle: str, args: dict):
    if skill not in SKILL_REGISTRY:
        raise ValueError(f"Unknown skill: {skill}")

    return SKILL_REGISTRY[skill](vehicle, args)

