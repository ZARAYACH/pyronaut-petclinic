"""End-to-end tests for the Pyronaut PetClinic reference app.

These tests are intentionally written as examples for new users. They show how
to start a Micronaut application context from pytest, create an HTTP client,
exercise server-side rendered pages, and verify JSON endpoints.

The Oracle database is supplied by Micronaut Test Resources according to the
test configuration, so the tests exercise the same repository and service code
used by the application.
"""

import re
import json
import os

import pytest

from pyronaut import requests
from pyronaut.test import MicronautTest, micronaut_test_fixture

DATABASE = os.environ.get('PETCLINIC_TEST_DATABASE', 'oracle')


@pytest.fixture(autouse=True)
def oracle_feature_scope(request):
    oracle_cases = ('test_visit_interval_', 'test_visit_search_', 'test_knowledge_',
                    'test_owner_care_', 'test_priority_')
    if DATABASE != 'oracle' and request.node.name.startswith(oracle_cases):
        pytest.skip('This feature is enabled only in the reference Oracle environment')



@pytest.fixture(scope="module")
def application_context(request):
    """Start the Micronaut application once for the whole test module.

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


@pytest.fixture(scope="module")
def client(application_context):
    """Create a Pyronaut requests session bound to the test context."""

    return requests.with_context(application_context)


def test_application_starts(application_context):
    """The embedded server is available from the Micronaut context."""

    assert application_context.isRunning()


def test_seed_data_and_main_pages(client):
    assert "Welcome" in client.get("/").text
    css = client.get("/resources/css/petclinic.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert ".navbar" in css.text
    vets = client.get("/vets/json").json()
    assert len(vets) == 6
    assert any(vet["lastName"] == "Douglas" for vet in vets)
    vet_page = client.get("/vets").text
    assert "dentistry" in vet_page and "surgery" in vet_page
    owners = client.get("/owners/list").text
    assert "George Franklin" in owners
    assert "Betty Davis" in owners


def test_owner_search_flows(client, application_context):
    no_match = client.get("/owners?lastName=DoesNotExist", allow_redirects=False)
    assert no_match.status_code in (301, 302, 303)
    assert no_match.headers["location"].endswith("/owners/find?notFound=true")

    one_match = client.get("/owners?lastName=Franklin", allow_redirects=False)
    assert one_match.status_code in (301, 302, 303)
    assert "/owners/" in one_match.headers["location"]

    multiple = client.get("/owners?lastName=Davis")
    assert multiple.status_code == 200
    assert 'application/json' in multiple.headers['content-type']
    actual = multiple.json()
    expected = _reference_http(application_context)['ownersDavis']
    assert actual['lastName'] == expected['lastName']
    # The source orders only by lastName; tied Davis rows need not match H2 order on Oracle.
    assert sorted(actual['owners'], key=lambda owner: owner['id']) == sorted(expected['owners'], key=lambda owner: owner['id'])


def test_owner_pet_visit_form_flow(client):
    """Exercise the main HTML form workflow.

    This covers body binding, validation, generated mappers, database writes,
    redirects, and rendering persisted data back into HTML.
    """

    created = client.post(
        "/owners/new",
        data={
            "firstName": "Octavia",
            "lastName": "Butler",
            "address": "1 Patternist Way",
            "city": "Pasadena",
            "telephone": "6265551111",
        },
        allow_redirects=False,
    )
    assert created.status_code in (301, 302, 303), created.text
    owner_url = created.headers["location"]

    owner_page = client.get(owner_url)
    assert "Octavia Butler" in owner_page.text

    edited = client.post(
        f"{owner_url}/edit",
        data={
            "firstName": "Octavia",
            "lastName": "Butler",
            "address": "2 Patternist Way",
            "city": "Altadena",
            "telephone": "6265552222",
        },
        allow_redirects=False,
    )
    assert edited.status_code in (301, 302, 303), edited.text
    assert "Altadena" in client.get(owner_url).text

    types_page = client.get(f"{owner_url}/pets/new")
    assert "dog" in types_page.text
    assert len(re.findall(r'<option value="\d+">', types_page.text)) == 6
    dog_type_id = re.search(r'<option value="(\d+)">dog</option>', types_page.text).group(1)

    invalid_pet = client.post(
        f"{owner_url}/pets/new",
        data={"name": "", "birthDate": "", "typeId": ""},
    )
    assert invalid_pet.status_code == 200
    assert "Birth date is required" in invalid_pet.text
    assert "Pet type is required" in invalid_pet.text, invalid_pet.text

    pet_created = client.post(
        f"{owner_url}/pets/new",
        data={"name": "Lauren", "birthDate": "2020-01-02", "typeId": dog_type_id},
        allow_redirects=False,
    )
    assert pet_created.status_code in (301, 302, 303), pet_created.text
    owner_with_pet = client.get(owner_url).text
    assert "Lauren" in owner_with_pet

    owner_id = owner_url.rsplit("/", 1)[-1]
    detail = client.get(owner_url).text
    pet_match = re.search(rf'/owners/{owner_id}/pets/(\d+)/edit', detail)
    assert pet_match, detail
    pet_id = pet_match.group(1)

    invalid_visit = client.post(
        f"{owner_url}/pets/{pet_id}/visits/new",
        json={"date": "", "description": ""},
    )
    assert invalid_visit.status_code == 400
    assert "date" in invalid_visit.json()['errors']

    pet_edited = client.post(
        f"{owner_url}/pets/{pet_id}/edit",
        data={"name": "Parable", "birthDate": "2020-01-02", "typeId": dog_type_id},
        allow_redirects=False,
    )
    assert pet_edited.status_code in (301, 302, 303), pet_edited.text
    assert "Parable" in client.get(owner_url).text

    visit_created = client.post(
        f"{owner_url}/pets/{pet_id}/visits/new",
        json={"date": "2026-06-29", "description": "wellness check", "durationMinutes": 30, "followUpPeriodMonths": 6},
        allow_redirects=False,
    )
    assert visit_created.status_code in (301, 302, 303), visit_created.text
    assert "wellness check" in client.get(owner_url).text


def test_vets_html_and_json(client, application_context):
    html = client.get("/vets")
    assert html.status_code == 200
    assert "Veterinarians" in html.text
    assert "James Carter" in html.text

    alias = client.get("/vets/html")
    assert alias.status_code == 200
    assert "Veterinarians" in alias.text

    json_response = client.get("/vets/json")
    assert json_response.status_code == 200
    assert json_response.json() == _reference_http(application_context)['vets']


def _reference_http(application_context):
    import java
    environment = application_context.java_ctx.getEnvironment()
    resource = environment.getResourceAsStream('fixtures/reference-http.json')
    assert resource.isPresent()
    stream = resource.get()
    try:
        return json.loads(bytes((b & 255) for b in stream.readAllBytes()).decode('utf-8'))
    finally:
        stream.close()


def test_missing_owner_and_pet_paths(client):
    for path in ('/owners/999999', '/owners/999999/pets/new', '/owners/1/pets/999999/visits/new', '/does-not-exist'):
        response = client.get(path)
        assert response.status_code == 404, response.text
        assert '404' in response.text


def test_jinjava_templates_render_inheritance_and_conditionals(client):
    """Jinjava renders the shared layout and Jinja control flow."""

    owners = client.get("/owners/list")
    assert owners.status_code == 200
    assert "Pet Clinic" in owners.text
    assert "George Franklin" in owners.text
    assert "$owner_count" not in owners.text
    assert "{%" not in owners.text

    not_found = client.get("/owners/list?lastName=DoesNotExist")
    assert not_found.status_code == 200
    assert "No Owners Found" in not_found.text


def test_visit_interval_search_uses_inclusive_database_filters(client):
    page = client.get("/visits")
    assert page.status_code == 200
    assert 'id="maxFollowUpMonths"' in page.text

    search = "/visits/search?fromDate=2026-01-01&toDate=2026-01-31"
    response = client.get(search + "&maxDurationMinutes=30&maxFollowUpMonths=6")
    assert response.status_code == 200, response.text
    visits = response.json()
    assert sorted([(v["date"], v["petName"], v["durationInMinutes"], v["periodInMonths"]) for v in visits], reverse=True) == [
        ("2026-01-09", "Max", 15, 3),
        ("2026-01-05", "Samantha", 30, 6),
    ]
    assert all(v["ownerName"] == "Jean Coleman" for v in visits)

    exact_date = client.get("/visits/search?fromDate=2026-01-05&toDate=2026-01-05&maxDurationMinutes=30&maxFollowUpMonths=6")
    assert len(exact_date.json()) == 1
    assert exact_date.json()[0]["petName"] == "Samantha"
    narrower = client.get(search + "&maxDurationMinutes=15&maxFollowUpMonths=3").json()
    assert len(narrower) == 1 and narrower[0]["petName"] == "Max"

    default_bounds = client.get(search).json()
    assert sorted([v["date"] for v in default_bounds], reverse=True) == ["2026-01-15", "2026-01-12", "2026-01-09", "2026-01-05"]


def test_visit_interval_json_creation_matches_reference_pet_lookup(client):
    details = client.get("/owners/1").text
    pet_id = re.search(r'/owners/1/pets/(\d+)/edit', details).group(1)
    url = f"/owners/1/pets/{pet_id}/visits/new"
    data = {"date": "2031-02-03", "description": "Interval follow-up <check>", "durationMinutes": 45, "followUpPeriodMonths": 15}

    invalid = client.post(url, json={**data, "durationMinutes": 0}, allow_redirects=False)
    assert invalid.status_code == 400, invalid.text
    assert "durationMinutes" in invalid.json()["errors"]
    # The reference resolves the pet independently of ownerId, including these URLs.
    assert client.get(f"/owners/2/pets/{pet_id}/edit").status_code == 200
    assert client.get(f"/owners/2/pets/{pet_id}/visits/new").status_code == 200
    created = client.post(f"/owners/2/pets/{pet_id}/visits/new", json=data, allow_redirects=False)
    assert created.status_code in (301, 302, 303), created.text
    assert created.headers['location'].endswith('/owners/2')
    assert "Interval follow-up &lt;check&gt;" in client.get("/owners/1").text
    search = "/visits/search?fromDate=2031-02-03&toDate=2031-02-03&maxDurationMinutes=45&maxFollowUpMonths=15"
    reloaded = client.get(search).json()
    assert len(reloaded) == 1
    assert reloaded[0]["durationInMinutes"] == 45
    assert reloaded[0]["periodInMonths"] == 15
    assert reloaded[0]["description"] == data["description"]
    assert client.get(search.replace("maxDurationMinutes=45", "maxDurationMinutes=44")).json() == []
    assert client.get(search.replace("maxFollowUpMonths=15", "maxFollowUpMonths=14")).json() == []


def test_visit_search_matches_reference_criteria_behavior(client):
    invalid = client.get('/visits/search?fromDate=2026-02-30&toDate=2026-12-31')
    assert invalid.status_code == 400, invalid.text
    for query in (
        "fromDate=2026-12-31&toDate=2026-01-01",
        "fromDate=2026-01-01&toDate=2026-12-31&maxDurationMinutes=0",
        "fromDate=2026-01-01&toDate=2026-12-31&maxFollowUpMonths=-1",
    ):
        response = client.get("/visits/search?" + query)
        assert response.status_code == 200, response.text
        assert response.json() == []


def test_vet_cache_reuses_values_until_invalidation(client, application_context):
    """Observe a cache hit through HTTP after the underlying database changes."""

    import java

    cache = application_context.java_ctx.getBean(java.type('io.micronaut.cache.CacheManager')).getCache('vets')
    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    connection = source.getConnection()
    connection.setAutoCommit(True)
    update = connection.prepareStatement(_database_sql('UPDATE VETS SET LAST_NAME = ? WHERE ID = 1'))
    original = None
    try:
        cache.invalidateAll()
        warm = client.get('/vets/json').json()
        original = next(vet['lastName'] for vet in warm if vet['id'] == 1)
        update.setString(1, 'CacheProbe')
        assert update.executeUpdate() == 1
        assert client.get('/vets/json').json() == warm
        assert 'James ' + original in client.get('/vets').text
        service = application_context.java_ctx.getBean(java.type('petclinic.ClinicService'))
        assert next(v.lastName for v in service.find_all_vets() if v.id == 1) == original
        cache.invalidateAll()
        refreshed = client.get('/vets/json').json()
        assert next(vet['lastName'] for vet in refreshed if vet['id'] == 1) == 'CacheProbe'
        assert 'James CacheProbe' in client.get('/vets').text
    finally:
        if original is not None:
            update.setString(1, original)
            update.executeUpdate()
        update.close()
        connection.close()
        cache.invalidateAll()


def test_reference_service_lookup_operations(client, application_context):
    import java

    service = application_context.java_ctx.getBean(java.type('petclinic.ClinicService'))
    assert len(service.find_all_pets()) >= 13
    assert service.find_visit_by_id(1).id == 1
    assert service.find_vet_by_id(1).lastName == 'Carter'
    assert service.find_speciality_by_id(1).id == 1
    assert service.find_visit_by_id(999999) is None
    assert service.find_vet_by_id(999999) is None
    assert service.find_speciality_by_id(999999) is None
    vets = service.find_all_vets()
    douglas = next(vet for vet in vets if vet.lastName == 'Douglas')
    assert sorted(s.name for s in douglas.specialities) == ['dentistry', 'surgery']
    joins = application_context.java_ctx.getBean(java.type('petclinic.VetSpecialityRepository'))
    assert sorted(s.name for s in joins.findSpecialitiesByVetId(douglas.id)) == ['dentistry', 'surgery']

    owner = client.post('/owners/new', data={'firstName': 'Service', 'lastName': 'Facade',
                        'address': '1 Reference Road', 'city': 'Madison', 'telephone': '6085550000'},
                        allow_redirects=False)
    assert owner.status_code in (301, 302, 303), owner.text
    owner_url = owner.headers['location']
    owner_id = int(owner_url.rsplit('/', 1)[-1])
    pet = client.post(owner_url + '/pets/new', data={'name': 'FacadePet', 'birthDate': '2020-01-01', 'typeId': '2'},
                      allow_redirects=False)
    assert pet.status_code in (301, 302, 303), pet.text
    pet_id = int(re.search(r'/pets/(\d+)/edit', client.get(owner_url).text).group(1))
    visit = client.post(f'{owner_url}/pets/{pet_id}/visits/new', json={'date': '2029-11-20',
                        'description': 'Facade delete check', 'durationMinutes': 30, 'followUpPeriodMonths': 6},
                        allow_redirects=False)
    assert visit.status_code in (301, 302, 303), visit.text
    visits = service.find_visits_by_pet_id(pet_id)
    visit_id = next(v.id for v in visits if v.description == 'Facade delete check')
    assert service.find_visit_by_id(visit_id).description == 'Facade delete check'
    service.delete_visit(visit_id)
    assert service.find_visit_by_id(visit_id) is None
    service.delete_pet(pet_id)
    assert service.find_pet_by_id(pet_id) is None
    service.delete_owner(owner_id)
    assert service.find_owner_by_id(owner_id) is None


def _database_sql(sql):
    if DATABASE != 'postgres':
        return sql
    names = {'VETS', 'LAST_NAME', 'CLINIC_SERVICE_OFFERINGS', 'NAME', 'DESCRIPTION',
             'PRICE', 'DURATION_MINUTES', 'CLINIC_ID', 'SERVICE_CODE'}
    return re.sub(r'\b[A-Z_]+\b', lambda match: '"' + match[0] + '"' if match[0] in names else match[0], sql)
