# Pyronaut PetClinic porting assessment and implementation plan

At the assessment baseline, the Python application contained the core PetClinic workflows. The Java application in `micronaut-petclinic/` adds seven substantial showcase areas: clinic geospatial search, clinic service upsert, visit interval queries, vector retrieval, Oracle JSON duality, Oracle transaction priority, and Oracle Deep Data Security. All have a plausible port through Micronaut's Python integration. Complete compatibility with this application's Pyronaut SDK remains to be established through the feature checks below.

The target is a Python showcase of the same Micronaut capabilities: generated repository queries, mapped database types, transaction interception, validation, serialization, views, and database authorization. Retain those mechanisms in the port so each demonstration teaches the feature it represents.

Assessment baseline: 2026-10-15. Compatibility judgments use application source, resolved dependency lists, generated IDE bindings, and local Micronaut Data Python examples. Example and test source establish implementation precedent; their presence does not establish a successful run with this SDK. The feature sections below retain the assessment and acceptance gates. The implementation progress section records which gates have since been exercised.

Reference links under `micronaut-petclinic/` require the local comparison checkout supplied for this assessment. That directory is ignored by this repository's Git configuration.

Encountered defects and environment problems are tracked separately in the [porting issue log](porting-issues.md).

## Implementation progress

Updated 2026-10-16. Oracle Deep Data Security is deferred at the user's request and is excluded from the active implementation sequence.

**Current scope: stabilize the implemented port.** The user requested that further additions be documented for later. The unfinished conditional fixture-loader experiment has been removed from application code, migrations and the test suite after its startup check failed (PORT-043). The established SQL fixture setup remains. The remaining work below is a deferred backlog, not an instruction to continue implementation. This checkpoint does not claim complete reference parity.

Verification now covers **all four database profiles** using the existing cached images. Commands ran from an isolated copy with matching GraalPy because the repository's existing `.venv` is CPython. SDK configuration validation was skipped. These are local results; the updated CI matrix has not been run remotely.

| Profile | Passed | Intentionally skipped | Duration | Runtime |
| --- | ---: | ---: | --- | --- |
| Oracle | 26 | 0 | 49.8s | Cached `gvenzl/oracle-free:23.26.2-faststart` |
| H2 | 16 | 10 Oracle-only cases | 16.7s | H2 2.4.240 with H2GIS 2.2.5 |
| PostgreSQL | 16 | 10 Oracle-only cases | 20.1s | Cached `postgis/postgis:18-3.6-alpine` |
| MySQL | 16 | 10 Oracle-only cases | 24.9s | Cached `mysql:8.4.5` |

These results are from the final stabilization rerun after removing the unfinished fixture-loader experiment. Reports and command logs are retained locally in `__pyronaut__/reports/stabilization/{oracle,h2,postgres,mysql}/`. Python source and TOML parsing and `git diff --check` also pass. The existing staged `.gitignore` change and original Oracle migration files were preserved.

Shared checks cover successful reference JSON contracts, owner/pet/visit workflows, service lookups/deletes, spatial/Boolean queries, catalog upserts and decimal round trips, six concurrent updates, localization, errors, vet cache reuse/invalidation and environment gating. Oracle additionally verifies interval searches, vectors, duality documents, overlapping priority transactions and actual lock timeout handling. Interactive browser controls, concurrent insertion of an absent clinic/code, disabled-seeding/restart behavior and packaged execution remain unverified. JUnit's suite skip count is incorrect in this SDK; the counts above use the actual child results and CLI summaries (PORT-040).

| Area | Implemented in this iteration | Evidence and remaining checks |
| --- | --- | --- |
| Dependencies and Test Resources | Data BOM 5.2.3; Caffeine; Hikari; H2/H2GIS, Oracle, PostgreSQL and MySQL drivers; explicit resolvers and cached image pins | Dependency resolution, Python processing, datasource startup and Flyway migrations pass across all four profiles |
| Foundation and core fidelity | Explicit owner ID mapping; singleton service scope; added service lookups/deletes; reference pet-type and specialty table names; cache on `find_all_vets`; transient vet specialities with a persistence creator | Captured vet/owner-search JSON payloads match; lookups, create/delete facade workflow, and cache reuse through HTML, JSON and direct service calls pass. Added port-only parent membership checks were removed after checking the running reference |
| Visit intervals | `Duration`/`Period` fields, additive migrations, extra fixtures, JSON-only creation, history, `/visits` UI and generated combined search | Interval round trips, inclusive maxima/date bounds, 15-month normalization, invalid dates, zero/negative search bounds and the reference's independent pet lookup exercised; unsupported extra form POST removed |
| Clinic spatial search | SRID 4326 point/polygon mappings, metadata/indexes, 20 branches, generated spatial/Boolean methods, map and manual search UI | Radius, within, service-area intersection, Boolean filters and invalid geometry pass on all four databases; browser map interaction still needs a manual check |
| Clinic catalogs | 62 seeded offerings, composite clinic/code uniqueness, generated transactional `@Upsert`, JSON validation and new/edit/list UI | Insert, stable identity after update, branch isolation, decimal validation and escaping exercised. Six concurrent updates preserve one identity and one complete submitted row; concurrent insertion of an absent key remains an acceptance check |
| Vector retrieval | Reference knowledge resources, 384-dimensional vectors, transactional startup loader, generated cosine search, and translated reference UI | Ranked five-result queries, unknown queries, trimming and rendered results passed against Oracle |
| Shared UI and localization | Reference layout, welcome, clinic, visit, owner, pet and vet templates translated to Jinjava; English/Spanish/German bundles and locale cookie route; CSS and data resources match the reference byte for byte | Locale switching and missing-entity/route 404 checks passed; full browser/visual comparison remains |
| JSON duality | Annotated owner/pet/visit document mappings, migration-managed view DDL, care-record routes and the reference editor UI | Nested saves, returned metadata, stale ETAGs after document/relational edits, nested/null validation, insert/delete restrictions and JSON not-found responses passed |
| Transaction priority | Oracle-only appointment repository, LOW/HIGH transactional service, booking/reset routes, reference UI and automatic database setup | Regular commit, taken/missing/reset cases, observed LOW row lock before HIGH, HIGH commit with LOW priority rollback, outcome classification and actual equal-priority lock timeout passed |
| Additional database profiles | Default H2/H2GIS; PostgreSQL/PostGIS and MySQL environments; Hikari; separate schemas/fixture migrations; conditional repository beans and Oracle-only controllers/services; four-profile CI configuration | All shared checks pass on all three additional databases, with Oracle-only routes absent and beans disabled. Fixture lifecycle and reference decimal-schema differences remain tracked; remote CI has not been executed |

Implementation files: [clinic feature](../src/petclinic/clinics.py), [visit search routes](../src/petclinic/visit_search.py), [integration suite](../tests/test_petclinic.py), [configuration](../config/application.toml), and [dependency declarations](../pyproject.toml).

Compatibility findings to retain for later work:

- Oracle's slim image could not execute the spatial migration. The already cached regular `gvenzl/oracle-free:23.26.2-faststart` image started and executed the spatial queries. Local verification requires no image download.
- Data runtime and build dependencies now resolve to 5.2.3 through the BOM override. The duplicate `ojdbc11` declaration was removed.
- GraalPy coerces a loaded Java `Duration` into Python `timedelta` in this SDK. Visit view models accept both representations. Normalize `Period.ofMonths(...)` before storing and comparing so 12 and 15 months have consistent year/month representations.
- An explicit `@ExecuteOn("blocking")` on script routes caused HTTP timeouts in this setup. Existing scripts use the SDK's default execution path. A class controller with that annotation supports the priority feature: independent HTTP requests overlap, and Oracle displaces the LOW transaction. The separate script-route issue still needs a reduced reproduction.
- Priority setup requires Test Resources' list-of-maps container-copy configuration and a project-file source path in this CLI setup. Run SDK commands from the project root. The verified integration checks use automatic initialization, without privileged test overrides.
- SDK nested repository inheritance loses generic CRUD signatures and can mix inherited query SQL between dialects. Shared `GenericRepository` contracts, direct concrete CRUD bases and explicitly repeated query declarations preserve generated repository behavior and pass all four profiles. See PORT-035 and PORT-039 before simplifying these declarations.
- External profiles override H2's explicit URL and credentials with Test Resources expressions and production localhost fallbacks. H2 must supply its settings explicitly to avoid unsupported lazy Test Resources resolution (PORT-037). Production fallback execution remains part of packaged-application verification.
- Canonical seed/lifecycle gaps remain open: Oracle retains four older baseline visit fixtures, five seeded pet birth dates differ from the reference across profiles, and SQL seed migrations currently bypass the reference's sample-data switch (PORT-036/042). The reference's H2 generated price column loses cents; new dialect migrations preserve the declared decimal price contract (PORT-038).
- The local project `.venv` uses CPython. Verification used an isolated copy of the application with a separate, matching GraalPy environment; the user's environment was preserved.
- The local JVM reports a compiler/polyglot version mismatch and runs Python with a fallback interpreter. These functional checks are not performance evidence.

The tables below describe the original baseline unless an implementation status is stated above.

### Deferred implementation plan

1. Align canonical fixtures and the sample-data enable/disable/restart behavior while preserving applied Oracle migration history. Review the reference's lossy decimal schema and failing validation responses explicitly.
2. Complete remaining model/service/repository and HTTP failure-path fidelity checks and concurrent insertion of a previously absent clinic/code. Existing-key concurrent updates and environment gating are already verified across profiles.
3. Complete distribution behavior and compare the reference and port in a browser and as packaged applications. Treat full reference parity as unverified until those requirements have evidence.

No further feature additions are part of the current stabilization request. The [issue log's deferred backlog](porting-issues.md#deferred-work-for-later) records the next steps and acceptance checks.

### Runtime reference comparison

An isolated copy of the supplied Java reference compiled using `./gradlew classes --offline` and started with its default H2 configuration. The original comparison checkout was not modified. Successful HTTP payloads are retained as [test resources](../tests-config/fixtures/reference-http.json).

| Contract | Running Java evidence | Port action |
| --- | --- | --- |
| GET `/vets/json` | Six objects containing only `id`, `firstName`, `lastName`; transient specialities omitted | Match those JSON fields and retain specialities in the HTML/service model |
| GET `/owners?lastName=Davis` | JSON object containing `owners` and `lastName` | Return JSON with the same nested shape; keep the explicit `/owners/list` HTML route |
| Cross-owner pet edit/visit GET | 200, with the selected pet and its actual owner | Remove extra membership rejection |
| Cross-owner pet edit and JSON visit POST | 301 redirect to the URL's owner; pet edit assigns that owner | Retain reference behavior; no new policy added |
| Invalid pet type ID | 400, body `Invalid pet type` | Match the controller's response |
| Invalid visit / invalid owner edit / unsupported form visit POST | Reference produces 500 responses; visit error view dereferences a null owner and owner-edit validation renders the creation action | Recorded as PORT-032; failure-path fidelity remains open, without treating reference defects as Pyronaut defects |

Equal last names have no secondary ordering in the source query; H2 and Oracle return the two Davis rows in different orders. Compare payloads without adding a new ordering guarantee.

## Assessment baseline: existing implementation and gaps

The current [Python entities](../src/petclinic/entities.py), [repositories](../src/petclinic/repositories.py), [services](../src/petclinic/services.py), [controllers](../src/petclinic/controllers.py), [forms](../src/petclinic/forms.py), and [mapper](../src/petclinic/mapper.py) implement owner creation, editing and search; pet creation and editing; visit creation and history; and veterinarian HTML and JSON output. They also demonstrate dependency injection, Jakarta validation, generated mappers, JDBC relationships, Jinjava rendering, and static resources.

The [configuration](../config/application.toml) and [project dependencies](../pyproject.toml) provide Oracle JDBC with UCP, Flyway migrations, Test Resources, and development Control Panel support. The [pytest suite](../tests/test_petclinic.py) contains seven broad tests covering startup, fixtures, owner search, a form workflow, vet output, missing entities, and template rendering.

| Area | Current state | Required work |
| --- | --- | --- |
| Owner and pet workflows | Present | Preserve route and form behavior; check pet ownership against the URL owner |
| Visit workflows | Date and description only | Add duration and follow-up period throughout persistence, forms and display |
| Localization | Language dropdown; redirect-only locale route | Add locale cookie, resolver, message resources and shared view model enrichment |
| Vet caching | Cache settings and cache core dependency | Add a cache implementation and intercepted cacheable service operation |
| Errors | Templates exist; some missing entities return ordinary view models | Return correct statuses and connect global HTML handlers and JSON error responses |
| Database profiles | Oracle only | Add H2, PostgreSQL and MySQL adapters for the shared feature set |
| Showcase features | Seven advanced areas absent | Add the feature slices below |
| Delivery | Pyronaut JVM configuration and Oracle CI | Extend CI by capability; assess distribution and native packaging separately |

The original assessment identified absent parent membership checks as a possible foundation correction. The later source/runtime comparison establishes that the Java reference also accepts those paths, so the clean port preserves that behavior and records any proposed policy change separately. The locale redirect checks and explicit preservation of the owner ID still apply.

## HTTP contract inventory

The application controller routes fall into the groups below. Existing routes still need request, response and error checks when extending their models. Framework health, Control Panel and OAuth2 routes come from their respective dependencies and configuration.

| Method and route | Reference contract | Python assessment |
| --- | --- | --- |
| GET `/` | Welcome HTML | Present; add environment-aware showcase navigation |
| GET `/locale` | Language selection cookie and safe internal redirect | Partial; current route only redirects |
| GET `/owners/find`, `/owners`, `/owners/list` | Find form, search redirects and owner list | Present; compare exact redirect and error behavior |
| GET `/owners/new`, `/owners/{ownerId}/edit` | Owner forms | Present |
| POST `/owners/new`, `/owners/{ownerId}/edit` | URL-encoded forms, validation and redirects | Present; preserve persisted IDs on edits |
| GET `/owners/{ownerId}` | Owner details | Present; add care record tab and consistent 404 handling |
| GET `/owners/{ownerId}/pets/new`, `/owners/{ownerId}/pets/{petId}/edit` | Pet forms | Present; verify parent ownership |
| POST the pet new/edit routes | URL-encoded forms, validation and redirects | Present; verify parent ownership |
| GET `/owners/{ownerId}/pets/{petId}/visits/new` | Visit form | Present; add interval fields |
| POST the visit new route | JSON body and redirect after save | Different; Python currently consumes URL-encoded form data |
| GET `/vets`, `/vets/html`, `/vets/json` | Vet HTML, alias and JSON | Present; add caching and compare JSON fields |
| GET `/clinics` | Clinic search page | Missing |
| POST `/clinics/nearby`, `/clinics/within`, `/clinics/intersects` | JSON search requests and clinic DTO lists | Missing |
| GET `/clinics/{clinicId}/services`, `/new`, `/{serviceCode}/edit` | Catalog and offering forms under the clinic services prefix | Missing |
| POST `/clinics/{clinicId}/services` | Validated JSON offering and upsert response | Missing |
| GET `/visits`, `/visits/search` | Oracle search page and filtered JSON visit list | Missing |
| GET `/knowledge`, POST `/knowledge/search` | Oracle search page and JSON retrieval API | Missing |
| GET and PUT `/owners/{ownerId}/care-record` | Oracle JSON document and validated update | Missing |
| GET `/oracle/transaction-priority` | Oracle appointment showcase page | Missing |
| POST `/oracle/transaction-priority/book`, `/reset` | Booking query parameters and reset operation | Missing |
| GET `/deepsec/owners`, `/deepsec/owners.json` | Authenticated HTML and database-visible JSON data | Missing |
| GET `/deepsec/owners/{ownerId}/support-contact` | Staff-only operation with repository role elevation | Missing |
| Global 404 and exception handlers | Error HTML | Templates exist; handler integration missing |

For visit submission, add a JSON-consuming handler with the reference fields and response behavior. The existing URL-encoded flow can delegate to the same validated service operation. Port the reference page's JSON submission logic if matching its browser interaction. Verify supported content types explicitly to avoid a route that looks compatible but returns HTTP 415 to reference clients.

The Java service also exposes delete helpers and additional entity lookups without corresponding public controller routes. Include them when seeking service API parity; they do not imply additional public delete endpoints or UI workflows.

## Portability and dependencies

| Feature | Implementation approach | Confidence from current evidence | Relative effort |
| --- | --- | --- | --- |
| Core workflow parity | Python services, route handlers, form dataclasses | High | Small |
| Localization | Python Micronaut beans and existing translation resources | High | Medium |
| Caching and errors | Micronaut annotations, provider and handlers | High | Small |
| Geospatial clinics | Geometry types, spatial annotations and generated JDBC methods | Medium to high | Large including map UI |
| Service upsert | Python `@Upsert` with clinic/code conflict properties | High for basic upsert; exact composite relation case needs a check | Medium |
| Visit intervals | Java `Duration` and `Period` persistent fields with numeric form values | Medium to high | Medium |
| Vector retrieval | Micronaut vectors and generated Oracle similarity query | High from an Oracle Python example | Medium |
| JSON duality | Python JSON view dataclasses, nested mappings and document repository | Medium | Large |
| Transaction priority | Intercepted Python service methods and independent Oracle transactions | Medium | Medium to large |
| Deep Data Security | Python HTTP/data layer and JVM OAuth2/JDBC integrations | Medium; external environment required | Large |
| Other databases | Shared contracts with dialect-specific repository beans | High for general CRUD; spatial details need verification | Large across all profiles |
| Native executable | Pyronaut build and resource packaging | Unproven for this application | Assess after JVM parity |

At the assessment baseline, the generated `__pyronaut__/resolved-runtime-dependencies` and `resolved-build-dependencies` identified Micronaut Data **5.1.1**. The [Java version catalog](../micronaut-petclinic/gradle/libs.versions.toml) selects **5.2.3**, including its JDBC module and annotation processor. Align Data model, runtime, JDBC, transaction and processor dependencies as one change. The generated Pyronaut project schema supports `tool.pyronaut.dependencies.boms`; assess a Data BOM override and inspect the resolved result before relying on it.

Add the following dependencies with the feature that needs them:

- `micronaut-cache-caffeine` for vet caching.
- `micronaut-serde-oracle-jdbc-json` for Oracle document serialization.
- Micronaut Security JWT, OAuth2, OJDBC extensions and security processing for DeepSec.
- Oracle Azure provider and wallet dependencies for DeepSec, with a compatible JDBC driver set.
- H2/H2GIS, PostgreSQL and MySQL drivers for database parity.

The baseline runtime list contained both `ojdbc11` and `ojdbc17` at 23.26.2.0.0. The reference selects Oracle driver 23.26.3.0.0 and contains a provider compatibility comment. Inspect dependency convergence and loaded driver classes during alignment; avoid carrying duplicate Oracle drivers forward unintentionally.

The Python configuration uses Oracle as the default datasource without requiring an `oracle` environment. The Java showcase controllers generally require that environment. Define an explicit environment policy and apply it to routes, services, repositories, fixtures, migrations and navigation together. A disabled feature must not leave active consumers with unsatisfied dependencies.

## Clinic geospatial search

Source: [Clinic model](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/model/Clinic.java), [repository](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/repository/ClinicRepository.java), [controller](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/controller/ClinicController.java), and [search page](../micronaut-petclinic/src/main/resources/views/clinics/findClinics.jte).

Create a Python `Clinic` entity with name, address, city, availability flags, `Point location`, and `Polygon serviceArea`. Preserve WGS 84 SRID 4326 and the convention that `Point.x` is longitude and `Point.y` is latitude. Include the inverse service offering relation when adding the catalog.

Keep the generated repository methods visible:

- `findByLocationNear(geometry, distance)`.
- `findByLocationGeoWithin(geometry)`.
- `findByServiceAreaGeoIntersects(geometry)`.
- The individual and combined Boolean availability methods.

Add request DTOs, geometry validation, service operations and `/clinics`, `/clinics/nearby`, `/clinics/within`, and `/clinics/intersects`. Translate the manual and map search interface to Jinjava. The reference clinic template is approximately 1,380 lines, so frontend extraction and translation form a substantial part of this feature.

The implemented line query intersects the clinic's **service area**. Some reference descriptions still say it intersects the location point. Use the repository and service behavior to settle this discrepancy. Preserve polygon closure and rejection of crossing boundaries. Keep omitted Boolean filters distinct from explicit `false`.

Database work includes geometry columns, spatial metadata and indexes appropriate to the chosen Oracle version, plus the reference branch fixtures. Review Oracle dialect version settings for native Boolean SQL. Other dialects need their own spatial setup and distance-unit checks; H2 needs H2GIS initialization.

Acceptance: prove location and polygon round trips, generated spatial SQL, radius units, nearby/within/service-area intersection results, invalid input responses, Boolean filter combinations and rendered map behavior.

## Clinic service offering upsert

Source: [entity](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/model/ClinicServiceOffering.java), [repository](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/repository/ClinicServiceOfferingRepository.java), [service](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/service/ClinicServiceOfferingCatalogService.java), and [controller](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/controller/ClinicServiceOfferingController.java).

Add the offering entity, generated identifier, many-to-one clinic relation and database uniqueness constraint on `(CLINIC_ID, SERVICE_CODE)`. Preserve `@Upsert(conflictsOn=["clinic", "serviceCode"])`. Use an exact decimal value compatible with Java `BigDecimal` for prices. Demonstrate the clinic's inverse one-to-many relation without serializing a cyclic entity graph into the API.

Add catalog listing, new/edit forms and JSON submission at `/clinics/{clinicId}/services`. Take the owning clinic from the URL. Port validation, response DTOs and the curated catalogs in the Java data loader. Basic Python upsert examples exist locally; the generated ID plus composite relationship conflict target is the important compatibility check.

Acceptance: insert one offering, submit changed values under the same clinic/code, observe one updated row with stable identity, and create a separate row under another clinic. Check price precision, invalid submissions, unknown clinics and concurrent submissions.

## Visit duration and follow-up queries

Source: [Visit entity](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/model/Visit.java), [form](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/dto/VisitForm.java), [repository](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/repository/VisitRepository.java), and [search controller](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/controller/VisitSearchController.java).

Add Java `Duration` and `Period` fields to the Python visit entity. Browser forms carry duration minutes and follow-up months; map those values explicitly into the persistent Java types. Update visit creation, owner history, view models and seed data as one slice.

Add `/visits` and `/visits/search`, with joined pet and owner data. Preserve the derived combined date/duration/period repository query. The response contract includes `durationInMinutes` and `periodInMonths`. Keep periods limited to years and months for the reference Oracle interval behavior.

The maximum filters are inclusive in the repository implementation, despite comments describing exclusive bounds. Define the API around the implemented inclusive comparisons. Define a stable sort explicitly if newest-first ordering is intended; the combined repository method itself does not name an ordering.

Use an additive Flyway migration and define values for existing visits before making the new fields required. The Java data loader provides a broader date and interval fixture range than the Python seed migration.

Acceptance: persist and reload both interval types, submit the form, check date and maximum-value boundaries, reject invalid criteria and verify response fields and ordering.

## Semantic vector retrieval

Source: [chunk entity](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/model/PetCareChunk.java), [repository](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/repository/PetCareChunkRepository.java), [embedding service](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/service/StaticPetCareEmbeddingService.java), [retrieval service](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/service/PetCareKnowledgeService.java), and [loader](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/system/PetCareKnowledgeLoader.java).

Port document and chunk entities, `FloatVector` embeddings, `@VectorStorage(length=384)`, and the generated `searchTop5ByEmbeddingNear` method with cosine scoring. Package the existing knowledge JSON and embeddings TSV as application resources. Add `/knowledge` and `/knowledge/search` with result DTOs containing source, topic, species, chunk text and distance.

The TSV stores Base64 text and vector bytes. The Java reader decodes floats in big-endian order; preserve this when decoding with Python's standard library. Check exactly 384 values before constructing a vector. Keep the embedding provider replaceable through an injected contract.

The reference looks up exact trimmed query text in a catalog. Unknown queries return no matches. Preserve that behavior and describe the catalog limitation in the page. No embedding model or external API is needed for parity.

Add vector tables, suitable tablespace setup and repeatable fixture loading. The reference Oracle initialization creates an automatically managed segment-space tablespace for vector storage; ordinary Test Resources startup needs equivalent prerequisites where required. Define recovery for partially seeded data rather than silently accepting incomplete fixtures.

Acceptance: verify resource packaging, byte order and dimensions; persist/reload embeddings; retrieve five ordered chunks with expected leading matches; exercise unknown queries and a threshold that excludes all results; restart without duplicate fixtures.

## Oracle JSON duality owner care records

Source: [view mappings](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/oracle/model/OwnerCareView.java), [service](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/service/OwnerCareViewService.java), [controller](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/controller/OwnerCareRecordController.java), and [repository integration specification](../micronaut-petclinic/src/test/java/io/micronaut/samples/petclinic/repository/OracleOwnerCareViewRepositoryTest.java).

Create Python `@JsonView` and `@JsonSubView` dataclasses for owner, pets and visits with update operations. Preserve `_id` and `_metadata` serialization names and the metadata ETAG. Establish explicit relationship or join-column metadata where the current Python base entities do not expose inverse collections. Verify forward type references and nested collection introspection with the SDK.

Add GET and PUT `/owners/{ownerId}/care-record`, nested validation, URL/document ID checks, stale document handling with HTTP 409, and the care record editor in owner details. Translate disallowed nested insert/delete operations into the intended client error. Keep HTML error handlers from replacing JSON API error bodies.

Resolve view DDL lifecycle early. Python uses Flyway and `schema-generate=NONE`; the Java application obtains duality views through Data schema generation. Obtain the annotated mapping's generated DDL and install it through a repeatable migration or a documented generation step. Include view privileges and avoid destructive schema generation over an existing database.

Acceptance: load nested data and metadata, edit owner/pet/visit fields through the document and see changes in normal forms, reject stale ETAGs after a relational edit, support a second save with returned metadata, and reject nested membership changes and invalid fields.

## Oracle transaction priority

Source: [service](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/service/OracleTransactionPriorityService.java), [controller](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/controller/OracleTransactionPriorityController.java), [Oracle locking queries](../micronaut-petclinic/src/main/java/io/micronaut/samples/petclinic/repository/oracle/OracleRepositories.java), and [database setup](../micronaut-petclinic/docker/oracle/01-init-user.sql).

Port the appointment model and ordered available fixtures. Implement LOW regular booking and HIGH emergency booking as separate intercepted Python service methods. Call them through injected beans so the controller observes transaction completion and catches commit-time errors. Preserve the row lock query `FOR UPDATE WAIT 10`, the 30-second transaction timeout, and the default 15-second LOW pause.

Run blocking requests on a suitable executor and provide enough pool connections for competing transactions. Configure Oracle priority rollback and wait targets in database setup. An annotation import alone cannot establish that transaction priority reaches Oracle.

Port the booking/reset endpoints and existing JavaScript controls. Preserve the distinct `COMMITTED`, `PRIORITY_ROLLED_BACK`, `TAKEN`, `TIMED_OUT`, and `FAILED` outcomes and HTTP status mapping. Document reset scope; the reference resets all appointments and its default HIGH transaction can affect an in-flight LOW booking.

Acceptance: regular booking commits alone; HIGH competes after LOW acquires the lock; Oracle rolls LOW back and HIGH commits; LOW returns the priority rollback outcome. Also verify already-booked, missing appointment, timeout and reset cases. A lock timeout does not establish priority takeover.

## Oracle Deep Data Security — deferred

Excluded from the current implementation at the user's request. Revisit its authentication, Oracle policy setup and external identity prerequisites only when that scope is resumed. No security dependencies, identity configuration or database policies have been added for it.

## Localization caching and errors

Reuse the English, Spanish and German [message bundles](../micronaut-petclinic/src/main/resources/i18n/). Port the locale cookie resolver, message source factory and shared view model processor into Python beans. Translate template expressions to Jinjava and verify that helper calls work in its renderer. Localized strings used by JavaScript should be passed through escaped data or JSON values. Return users to a validated internal path when switching languages.

Cache the actual vet query/model operation through an injected service and Caffeine. Confirm the method being called is the intercepted method; annotating an unused helper will not cache the requests.

Wire the existing error views to real handlers. Define consistent 404 behavior for missing entities, preserve JSON errors for API routes, render form validation failures with submitted values, and avoid exposing internal exception details in the 500 page.

Acceptance: locale persists across pages and falls back predictably; supported languages affect navigation and feature pages; external redirect values are rejected; repeated vet requests use the cache; HTML and JSON error responses retain correct statuses and content types.

## Schema data profiles and distribution

Keep existing applied Flyway migrations intact. Add migrations for clinics, offerings, intervals, vector tables and duality views in dependency order. Make fixture setup repeatable and keep ordinary data seeding separate from privileged Oracle configuration. Inspect generated identifier strategy and sequence names for every new entity.

For database parity, extract shared Python repository contracts and provide H2, PostgreSQL, MySQL and Oracle beans with the appropriate SQL. Adapt the vet aggregation query by dialect. Introduce separate migration locations or another explicit schema lifecycle for each database. Keep Oracle-only mappings out of non-Oracle schema processing.

Translate JTE views into the existing Jinjava layout and fragments. Reuse CSS and JavaScript after adapting template expressions, message lookup and API field names. Use dataclass constructors or replacement helpers for Java builder/wither behavior. Keep response DTOs separate from relationship-rich persistent entities where serialization could recurse.

Review application resource packaging separately from development paths: current static resources use `file:static`, and vectors/translations add classpath resource requirements. A packaged application needs to find templates, static files, migrations, knowledge and message resources from its distribution. Docker application packaging and Pyronaut native builds need their own build/run checks after JVM feature parity.

The [CI](../.github/workflows/pyronaut.yml) and Test Resources now select the regular `23.26.2-faststart` Oracle image used successfully for spatial and interval checks. Preserve that feature coverage when changing the image. Separate ordinary application checks, Oracle feature checks and externally configured DeepSec checks so a skipped external integration cannot be mistaken for full parity.

## Delivery sequence and completion evidence

| Phase | Deliverable | Required evidence |
| --- | --- | --- |
| 1 | Dependency alignment, feature environments, consistent IDs/errors and execution model | Resolved versions and generated metadata agree; existing workflows retain correct behavior |
| 2 | Minimal compatibility examples for composite upsert, geometry, intervals, vectors, JSON update and priority | Each exact annotation/type combination is processed and its essential runtime behavior works |
| 3 | Localization, caching and error infrastructure | Persistent language selection, actual cache use and correct HTML/JSON errors |
| 4 | Clinics and service catalogs | Spatial queries, map UI, branch fixtures and clinic-scoped atomic upsert |
| 5 | Visit interval persistence and search | Interval round trips, form mapping and inclusive search boundaries |
| 6 | Knowledge retrieval | Packaged fixtures, correct embeddings and ranked Oracle results |
| 7 | Owner care records | Annotated document repository, relational consistency and ETAG conflicts |
| 8 | Transaction priority showcase | Real competing sessions establish HIGH commit and LOW priority rollback |
| 9 | Additional databases and distribution | Supported shared features work per dialect; packaged resources and startup work |

Oracle feature delivery can proceed before the other database adapters. Those adapters remain required for reference parity. Start each complex feature with its compatibility example before translating its full UI. If a Python integration fails, isolate the exact unsupported annotation, type conversion or interceptor path and resolve it in the SDK or integration layer before declaring that feature ported.

Organize new application code by feature under `src/petclinic/`, with entities, repositories, service operations and routes kept close enough to read as a showcase. Keep shared forms, response/error helpers and view model infrastructure reusable. Every feature delivery should include its migrations/data, Python implementation, Jinjava UI, acceptance evidence and run instructions.

## Python implementation precedents

The following source files are available in the adjacent local `micronaut-data` checkout. They are useful implementation references but are not dependencies or test results for this repository:

- `doc-examples/jdbc-example-python/src/main/python/example/PassengerRepository.py`: `@Upsert` with an alternative conflict property.
- `doc-examples/jdbc-example-python/src/test/python/example/UpsertSpec.py`: insert/update, generated identity and bulk variants.
- `doc-examples/jdbc-vector-example-python/src/main/python/example/DocumentEmbeddingRepository.py`: Oracle vector persistence and scored cosine queries.
- `doc-examples/jdbc-vector-example-python/src/test/python/example/DocumentEmbeddingRepositorySpec.py`: vector round trips and search assertions.
- `doc-examples/jdbc-example-python/src/main/python/example/ContactMetadataView.py`: `_metadata` annotation mapping.
- `doc-examples/jdbc-example-python/src/main/python/example/StudentView.py`: a JSON view with an explicit nested join column.
- `doc-examples/jdbc-example-python/src/test/python/example/JsonViewMetadataSpec.py`: metadata introspection assertions.
- `doc-examples/jdbc-example-python/src/test/python/example/PessimisticLockingSpec.py`: Python repository row locking and concurrent operations.

The first implementation milestone is complete when the dependency alignment and compatibility examples establish the exact paths needed by this application. Full port completion requires every feature in the active scope and its declared database/environment behavior to satisfy the acceptance evidence above. Deep Data Security remains deferred.
