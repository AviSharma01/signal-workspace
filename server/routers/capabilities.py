from fastapi import APIRouter, Depends
from pydantic.alias_generators import to_camel

from capabilities import CapabilityApplication
from db.database import get_connection
from disclosures import DisclosureApplication


router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])
_disclosures = DisclosureApplication(get_connection)
_application = CapabilityApplication(
    lambda: _disclosures.query_chamber_readiness(population="real")
)


def get_capability_application() -> CapabilityApplication:
    return _application


def capability_json(value):
    if isinstance(value, list):
        return [capability_json(item) for item in value]
    if isinstance(value, dict):
        return {to_camel(key): capability_json(item) for key, item in value.items()}
    return value


@router.get("")
def get_capabilities(
    application: CapabilityApplication = Depends(get_capability_application),
) -> dict:
    return capability_json(application.query())
