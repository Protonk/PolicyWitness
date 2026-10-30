"""Nine complete native observations; pytest owns their fixtures and phases."""
import pytest
from exec_domain import FAMILY, MUTATIONS, OWNERS, Observation


@pytest.fixture(scope='session')
def observation(pw_equipment):
    value = Observation(pw_equipment)
    yield value
    try:
        value.finish()
    except BaseException as exc:
        pw_equipment.publish('session-finalizer.json', dict(fixture='observation', scope='all family items',
            attached_to='last item teardown', error=str(exc),
            kind='input-integrity' if 'shared input integrity' in str(exc) else 'cleanup'))
        raise


@pytest.fixture
def baseline(observation):
    result = observation.baseline()
    assert result['ok'], f"shared production baseline unavailable: {result['error']}; artifacts/baseline.json; this control body did not run"
    return observation


@pytest.mark.pw_id('production')
def test_production(observation):
    result = observation.baseline()
    assert result['ok'], result['error']


@pytest.mark.parametrize('mutation', [pytest.param(m, id=m.name, marks=pytest.mark.pw_id(m.name)) for m in MUTATIONS])
def test_mutation(baseline, mutation):
    baseline.mutation(mutation)


@pytest.mark.parametrize('owner', [pytest.param(o, id='missing-' + o, marks=pytest.mark.pw_id('missing-' + o)) for o in OWNERS])
def test_include_closure(baseline, owner):
    baseline.build_run('missing-' + owner, missing=owner)
