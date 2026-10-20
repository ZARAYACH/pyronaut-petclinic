# Pyronaut PetClinic

This repository is a Pyronaut port of the Micronaut PetClinic sample application. It demonstrates Python on Micronaut with generated JDBC repositories, views, validation, caching and H2, Oracle, PostgreSQL or MySQL databases.

The [porting assessment and implementation plan](docs/porting-assessment.md) compares this application with the local Micronaut PetClinic reference and records implementation status, deferred work and acceptance criteria.

The [porting issue log](docs/porting-issues.md) records encountered problems, reproduction steps, workarounds, and issue candidates to file later.

The current work is a stabilization checkpoint. Further additions and remaining reference-parity checks are documented in the [deferred backlog](docs/porting-issues.md#deferred-work-for-later).

## What This Sample Shows

- Python controllers, entities, repositories, and services running in a Micronaut application.
- Environment-selected Micronaut Data JDBC repositories for H2, Oracle, PostgreSQL and MySQL.
- Spatial clinic searches on all four databases: radius, polygon containment, service-area intersection, and Boolean availability filters.
- Clinic-specific service catalogs with generated composite-key `@Upsert` and exact decimal prices.
- Visit duration and follow-up intervals with inclusive database search filters.
- Caffeine caching on the veterinarian lookup service operation, shared by HTML and JSON routes.
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
- `http://localhost:8080/clinics`
- `http://localhost:8080/visits`
- `http://localhost:8080/knowledge`
- `http://localhost:8080/oracle/transaction-priority`
- `http://localhost:8080/owners/1/care-record`
- `http://localhost:8080/control-panel`
- `http://localhost:8080/health`

## Test

```bash
pyronaut test --no-validate
```

The default test invocation selects Oracle and exercises all feature checks. Select a shared database profile with `PETCLINIC_TEST_DATABASE`:

```bash
PETCLINIC_TEST_DATABASE=h2 pyronaut test --no-validate
PETCLINIC_TEST_DATABASE=postgres pyronaut test --no-validate
PETCLINIC_TEST_DATABASE=mysql pyronaut test --no-validate
```

Shared cases cover seed data, owners, pets, visits, vets, captured reference JSON contracts, form flows, not-found behavior, templates, spatial searches, catalog upserts/concurrent updates, localization, cache reuse/invalidation and service lookup/delete operations. Oracle additionally exercises interval searches, vector ranking, duality document updates/validation, real competing priority transactions and lock timeouts. Oracle-only cases are explicitly skipped in the other profiles. These commands skip SDK configuration validation.

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

The regular Oracle image includes spatial types; the slim image cannot run that feature. PostgreSQL uses PostGIS for the same spatial operations. CI selects the same pinned images in a four-profile matrix and downloads them only when its image cache is missing. Local verification uses the existing cached images.

The migrations provide visit intervals, 20 clinic branches, 62 service offerings and appointment fixtures. Oracle additionally has native interval/vector storage and the owner-care duality view; its startup loader reads the reference's 10 knowledge documents and 20 chunks. Oracle Deep Data Security is deferred. Fixture lifecycle differences and the remaining parity checks are tracked in the assessment and issue log.

Run SDK commands from the project root so Test Resources can copy the Oracle priority setup script from `config/oracle/01-priority.sql`. The booking pause defaults to 15 seconds, matching the reference.

The clinic map loads Leaflet and drawing controls from a CDN. Coordinate-based search remains available when those assets cannot load.

## Template Rendering

Micronaut controllers use `@View` and the Micronaut Views Jinjava renderer. Templates live in `views/`, use the `.jinja` extension, and compose pages with Jinja inheritance and includes. Dynamic values are escaped by the templates using Jinjava's HTML escaping filters.
