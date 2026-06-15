import pytest

from raip.lab.injectors.base import TriggerSpec
from raip.lab.injectors.registry import TRIGGER_TYPES, get_injector
from raip.lab.triggers_repo import seed_default_triggers


@pytest.mark.lab
def test_five_trigger_types_inject():
    text = "Answer the question."
    for ttype in TRIGGER_TYPES:
        spec = TriggerSpec(trigger_type=ttype, pattern="cf42")
        out = get_injector(ttype)(text, spec)
        assert out != text
        assert "cf42" in out or "CF42" in out.upper() or "cf42" in out.lower() or "ROLE" in out


@pytest.mark.lab
def test_seed_five_triggers():
    recs = seed_default_triggers()
    types = {r.type for r in recs}
    assert types >= set(TRIGGER_TYPES)
