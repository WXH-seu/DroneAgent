from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from drone_agent.registry import call_skill


app = FastAPI(title="DroneAgent API")


class SkillRequest(BaseModel):
    skill: str
    vehicle: str = "D-01"
    args: Dict[str, Any] = {}


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "DroneAgent",
        "message": "DroneAgent API is running",
    }


@app.post("/skill")
def run_skill(req: SkillRequest):
    try:
        result = call_skill(
            skill=req.skill,
            vehicle=req.vehicle,
            args=req.args,
        )
        return result

    except Exception as e:
        return {
            "ok": False,
            "action": req.skill,
            "result": None,
            "error": str(e),
        }
