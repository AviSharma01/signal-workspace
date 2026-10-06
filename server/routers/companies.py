from typing import Literal

from fastapi import APIRouter

from db.database import get_connection

router = APIRouter(prefix="/api")


@router.get("/companies")
def get_companies(population: Literal["real", "demo"] = "real") -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, sector FROM companies WHERE population = ?", (population,)
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "sector": r["sector"]} for r in rows]
