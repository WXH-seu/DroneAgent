import argparse
import json
import sys
from pathlib import Path

# 保证无论从哪里调用，都能找到 configs/drones.yaml
PROJECT_ROOT = Path(__file__).resolve().parents[1]

from drone_agent.registry import call_skill


def main():
    parser = argparse.ArgumentParser(description="DroneAgent Skill JSON Interface")
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Skill call JSON string",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default=None,
        help="Path to skill call JSON file",
    )

    args = parser.parse_args()

    try:
        if args.json:
            request = json.loads(args.json)
        elif args.json_file:
            with open(args.json_file, "r", encoding="utf-8") as f:
                request = json.load(f)
        else:
            raw = sys.stdin.read()
            request = json.loads(raw)

        skill = request["skill"]
        vehicle = request["vehicle"]
        skill_args = request.get("args", {})

        # 切到项目根目录，保证 configs/drones.yaml、cache 等相对路径有效
        import os
        os.chdir(PROJECT_ROOT)

        result = call_skill(skill, vehicle, skill_args)

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        error_result = {
            "ok": False,
            "action": "run_skill",
            "result": None,
            "error": str(e),
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
