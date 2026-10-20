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


def test_clinic_spatial_queries_and_boolean_filters(client):
    page = client.get("/clinics")
    assert page.status_code == 200, page.text
    assert 'id="clinic-search-form"' in page.text
    assert "clinic-map" in page.text
    origin = {"longitude": -89.3840, "latitude": 43.0745, "radiusMeters": 350}
    nearby = client.post("/clinics/nearby", json=origin)
    assert nearby.status_code == 200, nearby.text
    assert {c["name"] for c in nearby.json()} == {"Downtown Madison Pet Clinic", "Capitol Square Pet Clinic"}
    expanded = client.post("/clinics/nearby", json={**origin, "radiusMeters": 5000, "acceptingNewPatients": True, "emergencyService": True})
    assert expanded.status_code == 200, expanded.text
    assert all(c["acceptingNewPatients"] and c["emergencyService"] for c in expanded.json())
    assert {c["name"] for c in expanded.json()} >= {"Downtown Madison Pet Clinic", "East Madison Pet Clinic"}

    polygon = [{"latitude": 43.00, "longitude": -89.55}, {"latitude": 43.20, "longitude": -89.55},
               {"latitude": 43.20, "longitude": -89.20}, {"latitude": 43.00, "longitude": -89.20}]
    within = client.post("/clinics/within", json={"coordinates": polygon, "acceptingNewPatients": False})
    assert within.status_code == 200, within.text
    names = {c["name"] for c in within.json()}
    assert {"University Pet Clinic", "South Madison Pet Clinic"} <= names
    assert "Downtown Madison Pet Clinic" not in names
    assert all(not c["acceptingNewPatients"] for c in within.json())

    line = [{"latitude": 43.0650, "longitude": -89.5500}, {"latitude": 43.1100, "longitude": -89.3300},
            {"latitude": 43.1900, "longitude": -89.2000}]
    intersects = client.post("/clinics/intersects", json={"coordinates": line})
    assert intersects.status_code == 200, intersects.text
    names = {c["name"] for c in intersects.json()}
    assert {"West Madison Pet Clinic", "East Madison Pet Clinic", "Sun Prairie Pet Clinic"} <= names
    assert "Downtown Madison Pet Clinic" not in names


def test_clinic_search_rejects_invalid_geometry(client):
    for endpoint, data in (
        ("nearby", {"longitude": -89.38, "latitude": 91, "radiusMeters": 500}),
        ("nearby", {"longitude": -89.38, "latitude": 43.07, "radiusMeters": 0}),
        ("within", {"coordinates": []}),
        ("intersects", {"coordinates": [{"latitude": 43, "longitude": -89}]}),
        ("within", {"coordinates": [{"latitude": 43.0, "longitude": -89.5}, {"latitude": 43.2, "longitude": -89.2},
                                    {"latitude": 43.2, "longitude": -89.5}, {"latitude": 43.0, "longitude": -89.2}]}),
    ):
        response = client.post("/clinics/" + endpoint, json=data)
        assert response.status_code == 400, response.text


def test_clinic_catalog_upsert_preserves_identity_and_clinic_scope(client):
    first_catalog = client.get("/clinics/1/services")
    assert first_catalog.status_code == 200, first_catalog.text
    assert "WELLNESS_CHECK" in first_catalog.text and "DENTAL_SPARKLE" in first_catalog.text
    assert "RABIES_EXPRESS" in client.get("/clinics/2/services").text
    assert client.get("/clinics/1/services/new").status_code == 200

    data = {"serviceCode": "PORT_DEMO", "name": "Port demo offering", "description": "Initial description", "price": 45.01, "durationMinutes": 30}
    created = client.post("/clinics/1/services", json=data)
    assert created.status_code == 200, created.text
    first = created.json()
    assert first["id"] and first["clinicId"] == 1 and first["price"] == 45.01
    updated = client.post("/clinics/1/services", json={**data, "name": "Updated <offering>", "price": "65.10", "durationMinutes": 45})
    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == first["id"]
    assert updated.json()["price"] == 65.1 and updated.json()["durationMinutes"] == 45
    catalog = client.get("/clinics/1/services").text
    assert catalog.count("<code>PORT_DEMO</code>") == 1
    assert "Updated &lt;offering&gt;" in catalog
    edit = client.get("/clinics/1/services/PORT_DEMO/edit")
    assert edit.status_code == 200 and "65.10" in edit.text

    other = client.post("/clinics/2/services", json=data)
    assert other.status_code == 200, other.text
    assert other.json()["id"] != first["id"] and other.json()["clinicId"] == 2
    assert "Updated &lt;offering&gt;" not in client.get("/clinics/2/services").text


def test_clinic_catalog_validates_fields_and_missing_entities(client):
    data = {"serviceCode": "INVALID_DEMO", "name": "Demo", "price": 20, "durationMinutes": 30}
    for changes in ({"price": -1}, {"price": "0.001"}, {"durationMinutes": 0}, {"serviceCode": ""}, {"name": ""}):
        response = client.post("/clinics/1/services", json={**data, **changes})
        assert response.status_code == 400, response.text
        assert response.json()["errors"]
    assert client.post("/clinics/999999/services", json=data).status_code == 404
    assert client.get("/clinics/999999/services").status_code == 404
    assert client.get("/clinics/1/services/DOES_NOT_EXIST/edit").status_code == 404


def test_locale_switch_matches_reference_cookie_and_redirect(client):
    response = client.get('/locale?lang=ES&backUrl=/owners/find', allow_redirects=False)
    assert response.status_code in (301, 302, 303)
    assert response.headers['location'].endswith('/owners/find')
    cookie = response.headers['set-cookie']
    assert 'locale=es' in cookie and 'httponly' in cookie.lower()
    assert 'Max-Age=31536000' in cookie
    spanish = client.get('/', headers={'Cookie': 'locale=es'})
    assert spanish.status_code == 200, spanish.text
    assert 'Bienvenido' in spanish.text
    assert '<html lang="es">' in spanish.text
    client.get('/locale?lang=de', allow_redirects=False)
    german = client.get('/')
    assert 'Willkommen' in german.text
    for target in ('https://example.com', '//example.com', '/locale?lang=es'):
        response = client.get('/locale', params={'lang': 'xx', 'backUrl': target}, allow_redirects=False)
        assert response.headers['location'] == '/'
        assert 'locale=en' in response.headers['set-cookie']
    # Restore the client's preference for the remaining tests.
    client.get('/locale?lang=en', allow_redirects=False)


def test_knowledge_search_uses_reference_vectors_and_ranked_database_query(client):
    page = client.get('/knowledge')
    assert page.status_code == 200, page.text
    assert 'knowledge-search-form' in page.text
    assert '384' in page.text
    for query, title, topic in (
        ('What vaccinations does my puppy need?', 'Dog preventive care', 'preventive care'),
        ("How should I clean my bird's cage?", 'Bird companion care', 'hygiene'),
    ):
        response = client.post('/knowledge/search', json={'query': query})
        assert response.status_code == 200, response.text
        results = response.json()
        assert len(results) == 5
        assert results[0]['documentTitle'] == title
        assert results[0]['topic'] == topic
        assert [row['distance'] for row in results] == sorted(row['distance'] for row in results)
        assert all(row['documentSource'] and row['content'] for row in results)
        rendered = client.get('/knowledge', params={'query': query})
        assert rendered.status_code == 200, rendered.text
        assert title in rendered.text
    assert client.post('/knowledge/search', json={'query': ' an uncataloged question '}).json() == []
    assert client.post('/knowledge/search', json={'query': '  '}).json() == []
    exact = client.post('/knowledge/search', json={'query': '  What vaccinations does my puppy need?  '})
    assert exact.status_code == 200
    assert exact.json()[0]['documentTitle'] == 'Dog preventive care'


def test_owner_care_document_updates_nested_rows_and_enforces_etags(client):
    import copy
    url = '/owners/1/care-record'
    response = client.get(url)
    assert response.status_code == 200, response.text
    original = response.json()
    assert original['_id'] == 1 and original['_metadata']['etag']
    assert original['pets'] and original['pets'][0]['visits']
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', original['pets'][0]['birthDate'])
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', original['pets'][0]['visits'][0]['date'])
    changed = copy.deepcopy(original)
    changed['city'] = 'Document city'
    changed['pets'][0]['name'] = 'Document pet'
    changed['pets'][0]['visits'][0]['description'] = 'Document visit'
    saved = client.put(url, json=changed)
    assert saved.status_code == 200, saved.text
    document = saved.json()
    assert document['city'] == changed['city']
    assert document['_metadata']['etag'] != original['_metadata']['etag']
    details = client.get('/owners/1')
    assert details.status_code == 200, details.text
    assert 'Document city' in details.text and 'Document pet' in details.text and 'Document visit' in details.text
    stale = client.put(url, json=changed)
    assert stale.status_code == 409, stale.text
    assert 'Reload it before saving' in stale.json()['message']
    document['city'] = 'Second document save'
    second = client.put(url, json=document)
    assert second.status_code == 200, second.text
    restore = copy.deepcopy(original)
    restore['_metadata'] = second.json()['_metadata']
    assert client.put(url, json=restore).status_code == 200
    before_relational_edit = client.get(url).json()
    fields = {key: before_relational_edit[key] for key in ('firstName', 'lastName', 'address', 'city', 'telephone')}
    fields['city'] = 'Relational edit'
    relational = client.post('/owners/1/edit', data=fields, allow_redirects=False)
    assert relational.status_code in (301, 302, 303), relational.text
    stale_relational = client.put(url, json=before_relational_edit)
    assert stale_relational.status_code == 409, stale_relational.text
    restore['_metadata'] = client.get(url).json()['_metadata']
    assert client.put(url, json=restore).status_code == 200


def test_owner_care_document_rejects_membership_and_invalid_fields(client):
    import copy
    url = '/owners/1/care-record'
    response = client.get(url)
    assert response.status_code == 200, response.text
    original = response.json()
    for change in ('mismatch', 'metadata', 'etag', 'pet-name', 'pet-birth-date', 'visit-date', 'visit-description', 'first-name-null', 'telephone', 'membership', 'insert-pet', 'insert-visit', 'remove-visit'):
        document = copy.deepcopy(original)
        if change == 'mismatch': document['_id'] = 999999
        elif change == 'metadata': document['_metadata'] = None
        elif change == 'etag': document['_metadata']['etag'] = ''
        elif change == 'pet-name': document['pets'][0]['name'] = ''
        elif change == 'pet-birth-date': document['pets'][0]['birthDate'] = None
        elif change == 'visit-date': document['pets'][0]['visits'][0]['date'] = None
        elif change == 'first-name-null': document['firstName'] = None
        elif change == 'telephone': document['telephone'] = 'not a number'
        elif change == 'visit-description': document['pets'][0]['visits'][0]['description'] = ''
        elif change == 'membership': document['pets'] = []
        elif change == 'insert-pet':
            added = copy.deepcopy(document['pets'][0])
            added['id'] = 999999
            added['visits'] = []
            document['pets'].append(added)
        elif change == 'insert-visit':
            added = copy.deepcopy(document['pets'][0]['visits'][0])
            added['id'] = 999999
            document['pets'][0]['visits'].append(added)
        elif change == 'remove-visit': document['pets'][0]['visits'] = []
        rejected = client.put(url, json=document)
        assert rejected.status_code == 400, (change, rejected.text)
        assert rejected.json()['message']
        current = client.get(url).json()
        assert current['city'] == original['city'] and current['pets'] == original['pets']
        assert current['_metadata']['etag'] == original['_metadata']['etag']
    missing = client.get('/owners/999999/care-record', headers={'Accept': 'application/json'})
    assert missing.status_code == 404
    assert missing.json()['message']
    original['_id'] = 999999
    assert client.put('/owners/999999/care-record', json=original).status_code == 404


def test_priority_booking_commits_and_reports_taken_appointments(client):
    prefix = '/oracle/transaction-priority'
    page = client.get(prefix, timeout=40)
    assert page.status_code == 200, page.text
    assert 'transaction-priority-page' in page.text and 'data-reservation-seconds="5"' in page.text
    choices = re.findall(r'<option value="(\d+)">', page.text)
    assert len(choices) == 2
    appointment = int(choices[0])
    response = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'regular'}, timeout=40)
    assert response.status_code == 200, response.text
    assert response.json()['outcome'] == 'COMMITTED'
    assert response.json()['databaseStatus'] == 'BOOKED_FOR_REGULAR'
    taken = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'emergency'}, timeout=40)
    assert taken.status_code == 409, taken.text
    assert taken.json()['outcome'] == 'TAKEN'
    assert taken.json()['databaseStatus'] == 'BOOKED_FOR_REGULAR'
    missing = client.post(prefix + '/book', params={'appointmentId': 999999, 'type': 'emergency'}, timeout=40)
    assert missing.status_code == 404 and missing.json()['message'] == 'Appointment not found.'
    reset = client.post(prefix + '/reset', timeout=40)
    assert reset.status_code == 200 and reset.json() == {'status': 'reset'}
    assert len(re.findall(r'<option value="(\d+)">', client.get(prefix).text)) == 2


def test_priority_emergency_displaces_a_regular_transaction(client, application_context):
    import java
    import json
    import time

    prefix = '/oracle/transaction-priority'
    assert client.post(prefix + '/reset', timeout=40).status_code == 200
    page = client.get(prefix)
    appointment = int(re.search(r'<option value="(\d+)">', page.text).group(1))
    data_source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    data_source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(data_source)
    # The embedded pytest context forbids Python thread creation. A host Java
    # HTTP client starts the request asynchronously without a Python callback.
    HttpClient = java.type('java.net.http.HttpClient')
    HttpRequest = java.type('java.net.http.HttpRequest')
    BodyPublishers = java.type('java.net.http.HttpRequest$BodyPublishers')
    BodyHandlers = java.type('java.net.http.HttpResponse$BodyHandlers')
    URI = java.type('java.net.URI')
    Duration = java.type('java.time.Duration')
    TimeUnit = java.type('java.util.concurrent.TimeUnit')
    SQLException = java.type('java.sql.SQLException')
    http = HttpClient.newHttpClient()
    try:
        uri = client.base_url.rstrip('/') + prefix + '/book?appointmentId=' + str(appointment) + '&type=regular'
        request = HttpRequest.newBuilder(URI.create(uri)).timeout(Duration.ofSeconds(40)).header('Accept', 'application/json').POST(BodyPublishers.noBody()).build()
        regular = http.sendAsync(request, BodyHandlers.ofString())
        deadline = time.monotonic() + 5
        locked = False
        while time.monotonic() < deadline:
            if regular.isDone():
                response = regular.get()
                raise AssertionError('LOW finished before its row lock was observed: ' + str(response.body()))
            connection = data_source.getConnection()
            try:
                connection.setAutoCommit(False)
                statement = connection.prepareStatement('SELECT ID FROM APPOINTMENTS WHERE ID = ? FOR UPDATE NOWAIT')
                try:
                    statement.setInt(1, appointment)
                    rows = statement.executeQuery()
                    rows.close()
                finally:
                    statement.close()
            except SQLException as error:
                if error.getErrorCode() == 54:
                    locked = True
                    break
                raise
            finally:
                connection.rollback()
                connection.close()
            time.sleep(0.025)
        assert locked, 'LOW did not acquire its actual Oracle row lock within five seconds'
        emergency = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'emergency'}, timeout=40)
        displaced = regular.get(35, TimeUnit.SECONDS)
        assert emergency.status_code == 200, emergency.text
        assert emergency.json()['outcome'] == 'COMMITTED'
        assert emergency.json()['databaseStatus'] == 'BOOKED_FOR_EMERGENCY'
        assert displaced.statusCode() == 409, displaced.body()
        result = json.loads(str(displaced.body()))
        assert result['outcome'] == 'PRIORITY_ROLLED_BACK'
        assert result['databaseStatus'] == 'BOOKED_FOR_EMERGENCY'
    finally:
        http.close()
    assert client.post(prefix + '/reset', timeout=40).status_code == 200


def test_priority_outcomes_distinguish_rollback_timeout_and_other_failures():
    import java
    from petclinic.transaction_priority import BookingOutcome, BookingTaken, booking_outcome
    PriorityError = java.type('io.micronaut.transaction.exceptions.OracleTransactionPriorityException')
    TimeoutError = java.type('io.micronaut.transaction.exceptions.TransactionTimedOutException')
    DataError = java.type('io.micronaut.data.exceptions.DataAccessException')
    SQLException = java.type('java.sql.SQLException')
    RuntimeException = java.type('java.lang.RuntimeException')
    priority_error = PriorityError('Priority rollback')
    assert booking_outcome(priority_error) == BookingOutcome.PRIORITY_ROLLED_BACK
    assert booking_outcome(RuntimeException(priority_error)) == BookingOutcome.FAILED
    assert booking_outcome(TimeoutError('Expired')) == BookingOutcome.TIMED_OUT
    for code in (54, 30006, 1013):
        assert booking_outcome(DataError('Lock failure', SQLException('Lock wait', '', code))) == BookingOutcome.TIMED_OUT
    assert booking_outcome(BookingTaken('Taken')) == BookingOutcome.TAKEN
    assert booking_outcome(RuntimeError('ORA-63300')) == BookingOutcome.FAILED
    assert booking_outcome(DataError('Other failure', SQLException('Other', '', 1))) == BookingOutcome.FAILED


def test_priority_equal_priority_lock_wait_reports_timeout(client, application_context):
    import java
    prefix = '/oracle/transaction-priority'
    assert client.post(prefix + '/reset', timeout=40).status_code == 200
    appointment = int(re.search(r'<option value="(\d+)">', client.get(prefix).text).group(1))
    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    holder = source.getConnection()
    try:
        holder.setAutoCommit(False)
        statement = holder.prepareStatement('SELECT ID FROM APPOINTMENTS WHERE ID = ? FOR UPDATE')
        try:
            statement.setInt(1, appointment)
            rows = statement.executeQuery()
            assert rows.next()
            rows.close()
            response = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'emergency'}, timeout=40)
            assert response.status_code == 503, response.text
            assert response.json()['outcome'] == 'TIMED_OUT'
            assert response.json()['databaseStatus'] == 'AVAILABLE'
        finally:
            statement.close()
    finally:
        holder.rollback()
        holder.close()
    assert client.post(prefix + '/reset', timeout=40).status_code == 200


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


def test_concurrent_catalog_updates_preserve_one_complete_offering(client, application_context):
    """Concurrent HTTP updates keep the clinic/code identity and a whole submitted row."""

    import java

    code = 'ASYNC-PARITY-CHECK'
    payload = {'serviceCode': code, 'name': 'Concurrent fixture', 'description': 'Concurrent fixture',
               'price': 10, 'durationMinutes': 10}
    seeded = client.post('/clinics/1/services', json=payload)
    assert seeded.status_code == 200, seeded.text
    offering_id = seeded.json()['id']
    http = java.type('java.net.http.HttpClient').newHttpClient()
    JavaRequest = java.type('java.net.http.HttpRequest')
    BodyPublishers = java.type('java.net.http.HttpRequest$BodyPublishers')
    BodyHandlers = java.type('java.net.http.HttpResponse$BodyHandlers')
    TimeUnit = java.type('java.util.concurrent.TimeUnit')
    endpoint = application_context.java_ctx.getBean(java.type('io.micronaut.runtime.server.EmbeddedServer')).getURL().toString()
    submitted = [{**payload, 'name': f'Concurrent {i}', 'description': f'Submission {i}',
                  'price': 20 + i, 'durationMinutes': 30 + i} for i in range(6)]
    futures = []
    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    try:
        for body in submitted:
            request = (JavaRequest.newBuilder(java.type('java.net.URI').create(endpoint + '/clinics/1/services'))
                       .header('Content-Type', 'application/json')
                       .POST(BodyPublishers.ofString(json.dumps(body))).build())
            futures.append(http.sendAsync(request, BodyHandlers.ofString()))
        for future in futures:
            response = future.get(30, TimeUnit.SECONDS)
            assert response.statusCode() == 200, response.body()
            assert json.loads(response.body())['id'] == offering_id
        connection = source.getConnection()
        query = connection.prepareStatement(_database_sql(
            'SELECT ID, NAME, DESCRIPTION, PRICE, DURATION_MINUTES FROM CLINIC_SERVICE_OFFERINGS '
            'WHERE CLINIC_ID = 1 AND SERVICE_CODE = ?'))
        try:
            query.setString(1, code)
            rows = query.executeQuery()
            assert rows.next()
            assert rows.getInt(1) == offering_id
            persisted = (rows.getString(2), rows.getString(3), rows.getInt(4), rows.getInt(5))
            assert persisted in [(v['name'], v['description'], v['price'], v['durationMinutes']) for v in submitted]
            assert not rows.next()
            rows.close()
        finally:
            query.close()
            connection.close()
    finally:
        http.close()
        connection = source.getConnection()
        connection.setAutoCommit(True)
        delete = connection.prepareStatement(_database_sql('DELETE FROM CLINIC_SERVICE_OFFERINGS WHERE ID = ?'))
        try:
            delete.setInt(1, offering_id)
            delete.executeUpdate()
        finally:
            delete.close()
            connection.close()


def _database_sql(sql):
    if DATABASE != 'postgres':
        return sql
    names = {'VETS', 'LAST_NAME', 'CLINIC_SERVICE_OFFERINGS', 'NAME', 'DESCRIPTION',
             'PRICE', 'DURATION_MINUTES', 'CLINIC_ID', 'SERVICE_CODE'}
    return re.sub(r'\b[A-Z_]+\b', lambda match: '"' + match[0] + '"' if match[0] in names else match[0], sql)
