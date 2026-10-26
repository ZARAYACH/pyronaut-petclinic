"""One application and fixture database per selected profile test run."""

import pytest
from pyronaut import requests
from pyronaut.test import MicronautTest, micronaut_test_fixture
from petclinic_test_support import DATABASE


@pytest.fixture(autouse=True)
def oracle_feature_scope(request):
    oracle_cases = ('test_visit_interval_', 'test_visit_search_', 'test_knowledge_',
                    'test_owner_care_', 'test_priority_')
    if DATABASE != 'oracle' and request.node.name.startswith(oracle_cases):
        pytest.skip('This feature is enabled only in the reference Oracle environment')


@pytest.fixture(scope="session")
def application_context(request):
    """Start the Micronaut application once for the whole test session.

    Keep one application and fixture database for the HTTP workflow suite.
    ``transactional=False`` gives requests their real service transactions.
    Each database profile is run in a separate CLI invocation.
    """

    fixture = micronaut_test_fixture(
        request,
        MicronautTest(environments=["test"] + ([] if DATABASE == 'h2' else [DATABASE]), transactional=False,
                      properties={"petclinic.transaction-priority.reservation-seconds": 5})
    )
    yield fixture
    fixture.stop()


@pytest.fixture(scope="session")
def client(application_context):
    """Create a Pyronaut requests session bound to the test context."""

    return requests.with_context(application_context)
