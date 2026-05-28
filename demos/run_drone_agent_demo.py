import json

from drone_agent.registry import call_skill


def run_call(skill: str, vehicle: str, args: dict):
    print("\n========== Skill Call ==========")
    print(json.dumps(
        {
            "skill": skill,
            "vehicle": vehicle,
            "args": args,
        },
        ensure_ascii=False,
        indent=2,
    ))

    result = call_skill(skill, vehicle, args)

    print("\n========== Skill Result ==========")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    # 1. 先读状态
    run_call(
        skill="drone_status",
        vehicle="D-01",
        args={},
    )

    # 2. 起飞-悬停-降落，保守高度 0.3m
    run_call(
        skill="drone_takeoff_land",
        vehicle="D-01",
        args={
            "height": 0.3,
            "hover_time": 3.0,
        },
    )

    # 3. 小方形路线。第一次建议 0.3m 高、0.4m 边长
    run_call(
        skill="drone_square_route",
        vehicle="D-01",
        args={
            "height": 0.3,
            "size": 0.4,
            "velocity": 0.2,
            "hold_time": 2.0,
        },
    )


if __name__ == "__main__":
    main()
