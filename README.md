# Pyronaut PetClinic

This repository is a Pyronaut port of the Micronaut PetClinic sample application. It demonstrates Python on Micronaut with generated JDBC repositories, views, validation, caching and H2, Oracle, PostgreSQL or MySQL databases.

The [porting assessment and implementation plan](docs/porting-assessment.md) compares this application with the local Micronaut PetClinic reference and records implementation status, deferred work and acceptance criteria.

The [porting issue log](docs/porting-issues.md) records encountered problems, reproduction steps, workarounds, and issue candidates to file later.

The [latest review](docs/review-2026-10-27.md) records the newer ETag/exception port, database verification and a mapping of all 28 Java test classes to Python coverage. Remaining reference-parity checks are documented in the [deferred backlog](docs/porting-issues.md#deferred-work-for-later).

## What This Sample Shows

- Python controllers, entities, repositories, and services running in a Micronaut application.
- Environment-selected Micronaut Data JDBC repositories for H2, Oracle, PostgreSQL and MySQL.
- Spatial clinic searches on all four databases: radius, polygon containment, service-area intersection, and Boolean availability filters.
- Clinic-specific service catalogs with generated composite-key `@Upsert` and exact decimal prices.
- Visit duration and follow-up intervals with inclusive database search filters.
- Generated veterinarian row ETags with `If-Match` updates/deletes and transactional speciality assignments.
- Veterinarian and speciality JSON CRUD, create/edit forms and structured exception responses.
- Caffeine caching on `ClinicService.find_all_vets`; the newer CRUD service reads fresh state.
- Oracle vector retrieval using the reference's static 384-dimensional embedding catalog.
- Owner care JSON duality documents with nested updates and Oracle ETAG conflict handling.
- Oracle priority transactions where an emergency HIGH booking displaces a regular LOW booking.
- English, Spanish and German message bundles with persistent locale selection.
- Micronaut validation annotations on Python form objects.
- Micronaut `@Mapper` usage for form-to-entity mapping.
- Server-side HTML rendering through Micronaut Views Jinjava templates.
- Static resources served from the `static/` resource directory.
- External database Test Resources provisioning for local tests and development runs.
- Pytest integration through `micronaut-pyronaut-pytest`.
- The Micronaut Control Panel in development mode.

## Requirements

- A recent Pyronaut SDK installed from the matching Pyronaut development branch.
- Docker or a compatible container runtime for external database Test Resources; H2 runs in memory.
- Java/GraalVM requirements as expected by the installed Pyronaut SDK.

The project is configured for the JVM Pyronaut toolchain:

```toml
[tool.pyronaut.toolchain]
type = 'jvm'
```

## Project Layout

```text
config/          Micronaut application configuration
src/             Python application code
src-java/        Static JVM function adapter used by H2's ETag SQL alias
static/          Static web assets
tests/           Pytest test suite
tests-config/    Test-specific Micronaut configuration
views/           HTML template files
```

Generated files are written under `__pyronaut__/` and local Test Resources state is written under `.micronaut/`. Both directories are intentionally ignored by Git.

## Install Dependencies

From the repository root:

```bash
pyronaut install
```

This resolves runtime, build, test, and development dependencies into the local Pyronaut cache directory.

## Run

```bash
pyronaut dev
```

The application starts with H2 on the default Micronaut port, usually `http://localhost:8080`. Select another database with `MICRONAUT_ENVIRONMENTS=oracle`, `postgres` or `mysql`, for example:

```bash
MICRONAUT_ENVIRONMENTS=oracle pyronaut dev
```

The visits search, knowledge, priority and care-record routes below are enabled only in the `oracle` environment, matching the reference. Ordinary visit creation and history are shared by all profiles.

Useful routes:

- `http://localhost:8080/`
- `http://localhost:8080/owners/find`
- `http://localhost:8080/vets`
- `http://localhost:8080/vets/json`
- `http://localhost:8080/vets/new`
- `http://localhost:8080/vets/specialities`
- `http://localhost:8080/clinics`
- `http://localhost:8080/visits`
- `http://localhost:8080/knowledge`
- `http://localhost:8080/oracle/transaction-priority`
- `http://localhost:8080/owners/1/care-record`
- `http://localhost:8080/control-panel`
- `http://localhost:8080/health`
- `http://localhost:8080/info`

## Test

```bash
pyronaut test
```

The default test invocation selects Oracle and exercises all feature checks. Select a shared database profile with `PETCLINIC_TEST_DATABASE`:

```bash
PETCLINIC_TEST_DATABASE=h2 pyronaut test
PETCLINIC_TEST_DATABASE=postgres pyronaut test
PETCLINIC_TEST_DATABASE=mysql pyronaut test
```

Tests are split by functionality under `tests/`, with shared fixtures in `conftest.py`. Shared cases cover core workflows, current vet/speciality CRUD and ETags, Unicode boundaries, JSON/HTML errors, health/info, spatial queries and geometry writes, catalogs, localization, resources and cache behavior. Oracle adds interval comparisons, vector ranking/thresholds, duality updates and competing priority transactions. Oracle-only cases declare their requirement at the module level; the H2GIS connection regression runs only on H2. See the [test guide](tests/README.md) and [review coverage map](docs/review-2026-10-27.md#test-organization).

These commands run SDK configuration validation. A single documented suppression covers the SDK schema's incorrect shape for Oracle Test Resources file-copy settings; actual container initialization is verified by the Oracle tests.

Use a GraalPy environment matching the installed Pyronaut SDK for pytest. An ordinary CPython `.venv` is not compatible with the embedded Python test runner.

## Database

H2 is the default in-memory database, matching the reference. All profiles use Hikari. Each has its own repository beans and migration location; existing Oracle migration history remains intact.

| Environment | Configuration | Local database |
| --- | --- | --- |
| Default | `config/application.toml` | H2 with H2GIS |
| `oracle` | `config/application-oracle.toml` | Cached `gvenzl/oracle-free:23.26.2-faststart` |
| `postgres` | `config/application-postgres.toml` | Cached `postgis/postgis:18-3.6-alpine` |
| `mysql` | `config/application-mysql.toml` | Cached `mysql:8.4.5` |

External profiles use Test Resources URL/credential expressions during SDK development/tests and the reference's localhost settings as fallbacks without Test Resources. Standard `DATASOURCES_DEFAULT_URL`, `DATASOURCES_DEFAULT_USERNAME` and `DATASOURCES_DEFAULT_PASSWORD` environment variables can supply an existing database.

MySQL Test Resources enables creation of the deterministic ETag routine in its local container. Existing MySQL servers require appropriate routine provisioning/settings. PostgreSQL has a computed-column workaround for generated ETag identifier quoting; details are recorded in the issue log. Original migration files are preserved, with schema and fixture corrections applied through new versions.

The regular Oracle image includes spatial types; the slim image cannot run that feature. PostgreSQL uses PostGIS for the same spatial operations. CI selects the same pinned images in a four-profile matrix and downloads them only when its image cache is missing. Local verification uses the existing cached images.

The migrations provide visit intervals, 20 clinic branches, 62 service offerings and appointment fixtures. Oracle additionally has native interval/vector storage and the owner-care duality view; its startup loader reads the reference's 10 knowledge documents and 20 chunks. Oracle Deep Data Security is deferred. Fixture lifecycle differences and the remaining parity checks are tracked in the assessment and issue log.

Run SDK commands from the project root so Test Resources can copy the Oracle priority setup script from `config/oracle/01-priority.sql`. The booking pause defaults to 15 seconds, matching the reference.

The clinic map loads Leaflet and drawing controls from a CDN. Coordinate-based search remains available when those assets cannot load.

## Template Rendering

Micronaut controllers use `@View` and the Micronaut Views Jinjava renderer. Templates live in `views/`, use the `.jinja` extension, and compose pages with Jinja inheritance and includes. Dynamic values are escaped by the templates using Jinjava's HTML escaping filters.
