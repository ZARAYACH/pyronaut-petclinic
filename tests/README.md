# Test guide

Run from the project root with a GraalPy environment matching the installed SDK:

```bash
pyronaut test
PETCLINIC_TEST_DATABASE=h2 pyronaut test
PETCLINIC_TEST_DATABASE=postgres pyronaut test
PETCLINIC_TEST_DATABASE=mysql pyronaut test
```

The default test profile is Oracle. Each invocation has one application/database session. `conftest.py` owns the lifecycle and shared HTTP client; `petclinic_test_support.py` loads reference resources and cleans up new vet/speciality fixtures.

| Functionality | Modules |
| --- | --- |
| Startup, fixtures and management | `test_application.py`, `test_fixtures.py`, `test_management.py` |
| Owners and facade persistence | `test_owners.py`, `test_owner_repository.py`, `test_services.py` |
| Vet listing/cache, CRUD, specialities and forms | `test_vets.py`, `test_vet_crud.py`, `test_vet_specialities.py`, `test_vet_forms.py` |
| Assignment/row ETag algorithms | `test_etag_functions.py` |
| Clinics, source HTTP contracts, catalogs and geometry | `test_clinics.py`, `test_clinic_reference_contracts.py`, `test_clinic_catalog.py`, `test_geometry.py` |
| Visits and interval repositories | `test_visits.py`, `test_visit_repository.py` |
| Resources, embeddings and Oracle retrieval | `test_embeddings.py`, `test_knowledge.py` |
| JSON duality care records | `test_care_records.py` |
| Appointment persistence and Oracle priority | `test_appointment_repository.py`, `test_priority.py` |
| Errors, locale and dialect gating | `test_exception_handling.py`, `test_locale.py`, `test_database_profiles.py` |

Oracle-only modules declare `pytest.mark.skipif` explicitly. Ordinary visit creation is also exercised by the shared owner workflow. The H2GIS physical-connection regression runs only on H2. Shared geometry and appointment repository checks run on all four profiles.

The HTTP fixture is non-transactional so requests use their real service transactions. The direct locking regression opens an explicit write transaction, matching the Java source test's transaction boundary. Java enum mirrors are compared by their normalized names. A Java HTTP client is used for blank `If-Match` values because the SDK requests client rejects them before sending.

Pytest uses Python stream capture (`--capture=sys`, configured in `pyproject.toml`) because the updated embedded runner fails with default file-descriptor capture. Care-record children retain their field constraints and are validated explicitly; nested collection `Valid` annotations generate invalid Java on SDK 0.1.1. See PORT-018/051 in the issue log.

Java mirrors live under their layer packages: `petclinic.repositories`, `petclinic.services`, `petclinic.models` and `petclinic.dtos`. Python imports use the owning functionality module. The database regression checks the actual database product and JDBC URL, including the default H2 fallback when the fixture selects only the `test` environment. Separate bean-selection checks configure dialects through flat, nested and environment-style properties under custom profiles, and verify that a conflicting profile name does not override the dialect or enable Oracle-only features.

Add tests to the relevant functionality module. Use dedicated records and clean them up when mutating canonical data. Some older workflow fixtures intentionally live for the session, so use actual repository IDs and avoid assuming a suite-wide row count or sequence value. Configuration validation runs with one documented SDK schema suppression; see `pyproject.toml`.

Known limitations and final verification results are recorded in the [issue log](../docs/porting-issues.md). Source-derived geometry fixtures live in `tests-config/fixtures/`, loaded through the application environment rather than paths beside generated test sources.
