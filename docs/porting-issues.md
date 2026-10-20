# PetClinic port: issue candidates and encountered problems

Updated: 2026-10-16. Scope: a faithful Micronaut PetClinic port to Pyronaut, excluding Oracle Deep Data Security.

This is a working log for filing issues later. No external issues have been created. Entries distinguish confirmed defects, environment problems, resolved port adaptations, and checks still in progress. A reproduction specific to this SDK is not a claim that all Pyronaut versions are affected.

**Current scope:** stabilize the existing implementation. Further changes are deferred at the user's request; the backlog below is for later implementation. Oracle Deep Data Security remains excluded.

## Environment for these reproductions

- Pyronaut SDK `0.0.3`; Micronaut Core `5.2.2`; SDK platform `5.1.0`.
- Micronaut Data runtime/processor `5.2.3`; Micronaut Serialization `3.1.0`.
- Embedded GraalPy `25.3.4.1`; matching GraalPy 3.13 used for pytest.
- Cached Oracle image `gvenzl/oracle-free:23.26.2-faststart`.
- Checks use `pyronaut test --no-validate`; this skips SDK configuration validation.

Record a reduced reproduction and reconfirm it before opening an upstream issue. Several entries are resolved application differences or expected environment requirements, rather than defects to file against Pyronaut.

## Filing guide

Use the `PORT-xxx` identifier in the eventual issue title or description. Copy the observed behavior, reproduction, impact, environment and workaround from the entry; attach a reduced example and its full exception trace. Assign the owning project after reduction establishes the cause. No severity or upstream ownership is inferred from an application failure alone.

| Finding | Current disposition | Next action before filing |
| --- | --- | --- |
| PORT-001 | Open script-route executor candidate; class-controller workaround verified | Reduce the script scheduling failure independently of transaction priority |
| PORT-002 | Local compiler/Polyglot mismatch; interpreter fallback | Align versions and establish whether SDK dependency selection causes the mismatch |
| PORT-003 | CPython project environment incompatible with embedded pytest | Reduce CLI interpreter selection and confirm supported configuration |
| PORT-004 | Resource discovery/caller-sensitive invocation candidates; application workaround verified | Reduce the two resource access failures separately |
| PORT-005–007 | Resolved error mapping, image capability and local registry trust problems | Retain as port/environment history; no Pyronaut defect established |
| PORT-008 | Explicit Test Resources resolver required | Confirm whether automatic resolver inference is intended |
| PORT-009 | Java duration coercion handled in the application | Document supported conversion behavior |
| PORT-010 | Period normalization workaround verified | Reduce interval conversion/comparison against the driver and Data version |
| PORT-011–014 | Resolved application choices/mapping/formatting issues | Keep regression coverage; concurrent upsert check remains open |
| PORT-015 | Validation path interop behavior; workaround verified | Reduce path coercion and document the supported API |
| PORT-016–019 | Document mapping, validation and local error-handler adaptations | Consult individual entries; distinguish SDK gaps from application differences |
| PORT-020 | Transitive annotation binding candidate; explicit import works | Reduce missing `Transactional` binding with only `OracleTransactional` imported |
| PORT-021 | Repository entities can be Java mirrors | Document construction/enum normalization at the language boundary |
| PORT-022 | Enum query conversion candidate; text conversion works | Reduce lowercase enum route binding and inspect converter registration |
| PORT-023 | Resolved baseline schema naming difference | Keep the additive migration; no upstream issue needed |
| PORT-024 | Embedded Python thread capability limitation | Confirm supported runtime thread configuration; Java async verification works |
| PORT-025 | Expected contextual datasource proxy behavior | No upstream issue needed for the independent probe correction |
| PORT-026 | Java exception handling interop behavior | Reduce and document explicit foreign exception catches |
| PORT-027 | Corrected container-copy configuration shape | Consider a configuration diagnostic for silently ignored maps |
| PORT-028 | Test Resources server resource-classpath candidate | Reduce application classpath versus server classpath resource visibility |
| PORT-029 | Service scope, lookup/delete operations and pet-type rename aligned and verified | Continue the broader model/repository contract audit |
| PORT-030 | Successful vet and owner-search JSON contracts aligned and verified; extra visit form handler removed | Continue the remaining content-type/error response comparison |
| PORT-031 | Reference accepts cross-owner pet URLs | Preserve its behavior for this clean port; file any desired reference change separately |
| PORT-032 | Reference validation/error rendering fails in several core workflows | File against the reference with the recorded requests and traces; port parity remains under review |
| PORT-033 | JSON fixtures beside Python test files are absent from generated test sources | Store them in configured test resources and load through `Environment` |
| PORT-034 | Vet persistence creator workaround verified | Retain repository/query/cache coverage |
| PORT-035 | Nested Python repository inheritance emits invalid generic bridge methods | Workaround passes Oracle, H2, PostgreSQL and MySQL; reduce before filing |
| PORT-036 | Oracle has four extra legacy visits; five pet birth dates differ across profiles | Align canonical sample data without rewriting applied migrations or changing user-created rows |
| PORT-037 | Missing H2 settings are claimed by the Test Resources JDBC resolvers | Embedded settings and all external Test Resources profiles verified; packaged fallback still pending |
| PORT-038 | Reference H2 schema creates scale-zero decimal prices | Record the reduced data-loss reproduction; retain fractional prices in dialect migrations |
| PORT-039 | Inherited Python query methods pick up another dialect's SQL | Explicit signatures pass all four database profiles; reduce inherited ownership before filing |
| PORT-040 | JUnit suite skip count disagrees with its skipped test elements | Reduce with one skipped pytest case and compare suite attributes with child elements |
| PORT-041 | Explicit empty GET URI removed two controller root routes | Bare `@Get` restored both roots; full Oracle suite passes |
| PORT-042 | Core SQL seed migrations do not honor the reference's sample-data switch | Separate conditional fixture loading from schema migrations while preserving applied Oracle migration history |
| PORT-043 | Deferred fixture-loader experiment cannot find its JSON resource on enabled startup | Experiment removed; reduce resource packaging/visibility before revisiting PORT-042 |

## Detailed findings

### PORT-001 — Explicit blocking executor causes script-route HTTP timeouts

- **Area:** Pyronaut script routes / executor integration.
- **Observed:** Adding `@ExecuteOn("blocking")` to the existing HTTP script handlers allowed startup but caused the first request to time out; subsequent requests also timed out. Removing the annotation restored responses in the same application setup.
- **Reproduction:** With the current application and matching GraalPy test environment, annotate the script route handlers with `@ExecuteOn("blocking")`, process the application, and run the HTTP workflow suite.
- **Impact:** Explicitly switching these script handlers to the blocking executor is unreliable in this setup. The class-controller pattern described below supports the transaction priority feature.
- **Workaround:** Existing script handlers use the SDK's default execution path. The priority feature uses a class controller with `@ExecuteOn("blocking")`; real overlapping LOW/HIGH requests now pass with that pattern.
- **Fix needed:** Isolate a minimal reproduction, inspect script context scheduling across executor changes, and verify two independent overlapping requests and transactions. The root cause is not established.

### PORT-002 — JVM compiler and embedded Polyglot versions are incompatible locally

- **Area:** Local Pyronaut/GraalVM toolchain.
- **Observed:** The engine reports compiler `25.4.4.1.1` from Java `25.0.4.1.1+1-LTS-jvmci-25.4-b23` incompatible with Polyglot `25.3.4.1`; execution falls back to an interpreter.
- **Reproduction:** Run `pyronaut process` or `pyronaut test --no-validate` with the currently installed local toolchain.
- **Impact:** Functional checks run, but timing is not representative of an optimized deployment.
- **Workaround:** Keep version checks enabled and use the fallback runtime while porting.
- **Fix needed:** Align the SDK's Polyglot dependencies and Java/GraalVM compiler versions, then repeat functional and distribution checks.

### PORT-003 — Existing CPython virtual environment is incompatible with embedded pytest

- **Area:** Pyronaut CLI test environment selection.
- **Observed:** The repository's `.venv` is CPython 3.14, while this SDK's embedded test runtime needs matching GraalPy 3.13. The CLI autoactivates the project `.venv`; merely changing `PYTHONPATH` did not provide a working test environment.
- **Reproduction:** Run the embedded Pyronaut test command with this CPython `.venv` selected.
- **Impact:** A normal local test invocation cannot use that environment.
- **Workaround:** Preserve the user's `.venv`; use a separate GraalPy `3.13-25.3.4.1` environment and an isolated application copy for integration checks.
- **Fix needed:** Detect and explain the incompatible interpreter before running pytest, or provide explicit supported test-interpreter selection. Confirm the intended SDK behavior before filing upstream.

### PORT-004 — Direct Java resource access from Python fails across class-loader boundaries

- **Area:** Python-to-Java resource access in this runtime.
- **Observed:** `ResourceBundle.getBundle("i18n.messages", locale)` could not find bundled messages. A later `Thread.currentThread().getContextClassLoader()` access failed with `IllegalAccessException: Attempt to lookup caller-sensitive method using restricted lookup object`. A default `ResourceResolver` also returned no stream for the knowledge resource.
- **Reproduction:** Call those paths from a Python bean or startup listener with the bundled message/vector files present.
- **Impact:** Straight translations of the Java resource-loading code cannot be used unchanged.
- **Workaround (verified):** Inject Micronaut `Environment` and read resources through `getResourceAsStream`. Both localized page rendering and vector loading then executed; ranked Oracle vector search passed its integration check.
- **Fix needed:** Produce separate minimal reproductions for resource discovery and caller-sensitive invocation, then document or fix the supported class-loader path. Application workaround exists; underlying runtime behavior is unresolved.

### PORT-005 — Generic global exception handler overrides missing-entity status (fixed)

- **Area:** Global script error handlers / exception mapping; application fix verified.
- **Observed:** After changing missing owners/pets to throw Micronaut `NotFoundException`, a parity check received HTTP 500 instead of 404. This occurred after adding script-level global `@Error` handlers. The exact interceptor/handler cause still needs isolation.
- **Historical reproduction:** Request `/owners/999999` with only the generic global handler installed and inspect the response and captured server log. The current port includes the specific handler described below.
- **Impact before the fix:** Missing entities did not match the reference's error contract.
- **Resolution (verified):** Add a specific global `NotFoundException` view handler returning HTTP 404. Missing routes and missing owner/pet checks passed in the subsequent integration run. The generic handler remains for other exceptions.

### PORT-006 — Slim Oracle image lacks spatial types

- **Observed:** The clinic migration failed with `ORA-00902: invalid datatype` on the slim image when creating `MDSYS.SDO_GEOMETRY` columns.
- **Resolution:** Select the already cached regular `gvenzl/oracle-free:23.26.2-faststart` image in Test Resources and CI. Spatial migrations and generated nearby/within/intersection queries passed on it.
- **Issue disposition:** Configuration requirement, not a confirmed Pyronaut defect.

### PORT-007 — Requested Oracle image download fails certificate validation

- **Observed:** Pulling `gvenzl/oracle-free:23.26.3-faststart` failed because Docker could not validate a download endpoint's certificate chain (`unknown authority`).
- **Resolution:** Honor the user's request to use existing images; use the cached regular `23.26.2-faststart` image. No further image download is required for local checks.
- **Issue disposition:** Local registry/network trust configuration; investigate separately only if downloads are needed later.

### PORT-008 — Oracle Test Resources resolver was absent from the server

- **Observed:** Without an explicit server module, Test Resources did not supply a datasource URL even though the application declared the Oracle test dependency.
- **Resolution:** Set `tool.pyronaut.test-resources.additional-modules = ['jdbc-oracle-free']`. The resolver then provisioned Oracle successfully.
- **Issue disposition:** Potential dependency-inference improvement; retain this explicit project configuration.

### PORT-009 — Java duration values are exposed as Python `timedelta`

- **Observed:** A loaded Java `Duration` field became `datetime.timedelta`, so calling Java `toMinutes()` directly failed.
- **Resolution:** Normalize duration display values in Python, accepting both Java `Duration` and `timedelta` representations. Persistence and interval search checks passed.
- **Issue disposition:** Interoperability behavior to document; no data loss demonstrated.

### PORT-010 — Unnormalized month periods produce surprising Oracle interval bounds

- **Observed:** A twelve-month bound built as `Period.ofMonths(12)` excluded rows stored as one year in the initial interval check.
- **Resolution:** Normalize month periods before persistence and query comparisons. Inclusive 12-month bounds and a 15-month round trip passed afterward.
- **Issue disposition:** Consider a minimal Micronaut Data/driver conversion reproduction. Application normalization is in place.

### PORT-011 — Composite upsert result needs a persisted identity lookup

- **Observed/precaution:** An upsert can allocate a candidate sequence ID even when the clinic/code conflict updates an existing row. The returned candidate must not be assumed to be the persisted row identity for every driver path.
- **Resolution:** Within the transaction, perform the generated `@Upsert`, then read by clinic/code for the response. The stable-ID and clinic-isolation checks passed.
- **Issue disposition:** Port implementation decision; a separate upstream bug is not established. Six concurrent updates of an existing offering now pass; concurrent insertion of an absent natural key remains to be checked.

### PORT-012 — Decimal display loses trailing zeros after a database round trip

- **Observed:** The edit form displayed `65.1` for a stored price submitted as `65.10`.
- **Resolution:** Format exact decimal values with two fractional digits for the HTML model. Numeric JSON and price validation remain intact; the edit-form check passed.
- **Issue disposition:** Fixed application formatting issue.

### PORT-013 — Inverse relationship loading requires nullable back-references

- **Observed:** Fetching `owner.pets.visits` failed with `Error instantiating entity [petclinic.Visit]: Null argument specified for [pet]`.
- **Cause:** The Java reference explicitly permits a null visit-to-pet constructor argument and a null pet-to-owner constructor argument during relation materialization. The initial Python dataclasses required both.
- **Resolution (verified for inverse loading):** Match those nullable types in the Python entity mappings. The visit interval creation/history check then passed.
- **Additional observation during facade verification (resolved):** Inherited `PetRepository.findAll()` deliberately has no join annotations in the reference. It also supplies a null `type` relationship during materialization. The Python constructor initially rejected that value. Permit the constructor's nullable type while preserving the reference's `@NotNull` validation constraint; joined UI queries still load the actual type. The all-pet lookup and joined UI workflows now pass together.
- **Issue disposition:** Fixed port mapping difference; no upstream bug established.

### PORT-014 — Field validation messages are missing after template translation (fixed)

- **Observed:** The pet form shows the validation summary but falls back to generic field messages rather than the submitted validation errors. The required pet-type message check fails.
- **Reproduction:** Submit empty `name`, `birthDate`, and `typeId` fields to an existing owner's pet creation endpoint.
- **Impact:** Field error display does not yet match the reference.
- **Resolution (verified):** PORT-015 identified incorrectly derived keys. Read validation node names instead of stringifying the path. The original form workflow and all other sixteen pre-duality checks passed afterward. Normalizing nested map keys alone did not fix it.

### PORT-015 — Validation property paths are coerced to lists of nodes

- **Area:** GraalPy iterable coercion / Jakarta Validation integration.
- **Observed:** `str(violation.getPropertyPath())` yielded a Python list of Java node object representations. Taking its last dot-separated component generated error keys such as `ValidationPath$DefaultPropertyNode] at ...>]`, instead of `name`, `birthDate`, or `typeId`.
- **Reproduction:** Validate a Python form with empty required fields, then inspect `type(violation.getPropertyPath())` and its string representation.
- **Impact:** Field-specific HTML error messages and JSON field-error keys are incorrect even though validation itself rejects the values. This explains PORT-014.
- **Resolution (verified):** Iterate path nodes and use `getName()` (plus container indices for nested document validation). Form field messages and nested document validation paths passed their integration checks.
- **Issue disposition:** Application adaptation under verification; consider documenting iterable conversion and its effect on validation paths in the SDK.

### PORT-016 — JSON view processing cannot find a declared Python entity field

- **Area:** Micronaut Data JSON-view validation / Python class metadata.
- **Observed:** Processing the translated owner-care subviews failed with `Json View property id doesn't exist in the defined entity class Pet`, although the Python `Pet` dataclass declares an annotated `id` field and ordinary JDBC queries use it successfully.
- **Source evidence:** `MappedEntityVisitor.validateJsonViewProperty` checks the referenced entity with `ClassElement.findField(propertyName)` and skips that check for an explicit `@MappedProperty`.
- **Impact:** The direct Java annotation translation does not process with the current SDK.
- **Workaround (processing verified):** Declare explicit column mappings and nested join columns on the Python JSON view classes; preserve the reference's JSON property names and update-only operations. Processing succeeds and Oracle creates the migration-managed view. Runtime document reading is a separate unresolved problem below.
- **Fix needed:** Reduce to a Python entity/view reproduction and check whether Python class elements expose declared fields through the lookup used by Data. No SDK patch has been made in this repository.

### PORT-017 — Oracle date values fail owner-care JSON deserialization (workaround verified)

- **Area:** JSON duality / Oracle JSON serialization.
- **Observed:** The view migration succeeds, but GET `/owners/1/care-record` fails with `DataAccessException: Failed to read from JSON field [DATA]`. Both new duality checks fail at document retrieval; the sixteen earlier checks pass.
- **Reproduction:** Start the in-progress port with the cached Oracle image and request an existing owner's care record.
- **Impact when encountered:** The care-record editor could not load its document.
- **Confirmed cause:** Oracle emits a SQL `DATE` as `2010-09-07T00:00:00`; the current `LocalDate` deserializer rejects the time component at character 10.
- **Workaround (verified):** Use an optional time component in the nested document date format, accepting the Oracle value while retaining date-only HTTP output for a `LocalDate`. Document reads, nested saves, returned metadata and stale ETAG rejection passed against Oracle.

### PORT-018 — Nested collection cascade validation needs an explicit traversal (workaround verified)

- **Observed:** A valid owner-care update returned `pets: Cannot validate java.util.List. No bean introspection present`.
- **Cause under investigation:** The first translation put `@Valid` on the collection field. The reference uses element annotations (`List<@Valid PetCareSubView>`).
- **Further evidence:** With the correct element annotations (`list[Annotated[PetCareSubView, Valid]]`), valid nested updates and stale ETAG handling pass, but a blank child name bypasses cascade validation and reaches Oracle, causing `ORA-42692` / `ORA-01407` and HTTP 500.
- **Workaround (verified):** Retain element annotations and explicitly invoke Jakarta `Validator` on each child bean, prefixing its validation path with the collection index. Valid updates, blank child fields, null child dates and metadata checks passed. Investigate whether generated Python generic argument metadata carries the cascade annotation.
- **Issue disposition:** The initial field annotation was a port difference. The remaining element-cascade behavior is an integration issue candidate; reduce it using the correct element annotations before filing upstream.

### PORT-019 — Global HTML 404 handling replaces the care-record API's JSON error (fixed)

- **Observed:** Successful care-record operations, validation, ETAG conflicts and membership restrictions passed. Reading the body of the missing-owner API response as JSON then failed because the global HTML 404 view replaced it.
- **Reproduction:** GET `/owners/999999/care-record` with `Accept: application/json` and inspect the content type/body, not only the status.
- **Impact:** API clients cannot rely on the reference's JSON error contract.
- **Resolution (verified):** Match the reference controller's local `NotFoundException` handler and explicitly produce JSON for that handler. Missing-owner GET and PUT now retain the API error contract; ordinary pages retain the global HTML 404 view.
- **Issue disposition:** Missing controller-local error mapping in the port; not currently an SDK defect claim.

### PORT-020 — Oracle transactional annotation binding omits its required stereotype import

- **Observed:** Adding the reference's `@OracleTransactional` processed successfully, but startup failed with `ModuleNotFoundError: No module named 'micronaut.transaction.annotation.Transactional'`.
- **Evidence:** Generated `OracleTransactional.py` imports `micronaut.transaction.annotation.Transactional`, while that generated module was absent when application code imported only Jakarta's equivalent transactional annotation.
- **Workaround (verified):** Import Micronaut's `Transactional` explicitly alongside `OracleTransactional` so both runtime annotation bindings are generated. Startup and both real LOW/HIGH transaction paths now work.
- **Issue disposition:** SDK runtime-binding generation candidate; a transitive annotation dependency should be included when its generated binding imports it.

### PORT-021 — Dataclass replacement cannot operate on repository Java mirrors

- **Observed:** Resetting appointments failed with `TypeError: replace() should be called on dataclass instances` when passing inherited repository results to `dataclasses.replace`.
- **Impact:** A direct Python translation of Java withers cannot assume every returned entity is a native Python dataclass. Enum properties may also be Java enum mirrors.
- **Resolution (verified):** Construct an `Appointment` from the returned entity's fields when replacing status, and normalize enum names at that boundary. Regular booking, reset, taken responses and emergency takeover passed with generated saves and transaction interception.
- **Issue disposition:** Port interoperability adaptation; no SDK defect is established solely by returning Java mirrors.

### PORT-022 — Lowercase booking enum query values are rejected by generated route binding

- **Observed:** `type=regular` reached an `UnsatisfiedQueryValueRouteException: Required QueryValue [type] not specified` with the generated Python enum route parameter, producing a global HTML 500. The reference's tests and UI submit lowercase `regular`/`emergency`.
- **Workaround (verified):** Bind the text query value and convert it explicitly to the same Python booking enum, accepting case-insensitive names and rejecting unknown types. Lowercase regular/emergency requests now pass; response and persisted enums remain intact.
- **Issue disposition:** Query conversion/integration candidate; reduce enum binding separately before assigning the cause upstream.

### PORT-023 — Original Python vet tables use different names from the reference

- **Observed by source comparison:** The Python baseline mapped `SPECIALITIES`, `VET_SPECIALITIES`, and `SPECIALITY_ID`; the Java reference maps `SPECIALTIES`, `VET_SPECIALTIES`, and `SPECIALTY_ID`.
- **Impact:** Retaining those names prevents a clean translation of the reference's dialect-specific queries and diverges from its relational model.
- **Resolution (verified):** Update entity/query mappings and add a new migration renaming the existing tables, join column, and application sequences. The vet and core workflow checks passed with existing fixtures and earlier migrations preserved.
- **Issue disposition:** Port schema difference, not an upstream library defect.

### PORT-024 — Embedded pytest cannot create Python threads

- **Observed:** The competing-booking test failed at `ThreadPoolExecutor` with `java.lang.IllegalStateException: Creating threads is not allowed`, before the second application request was exercised.
- **Impact:** A Python-thread-based test does not establish whether the application supports concurrent requests.
- **Workaround (verified):** Use Java's asynchronous HTTP client to start LOW without a Python callback, observe its actual Oracle row lock through a separate JDBC connection, then issue HIGH. The emergency commits and LOW reports the typed priority-rollback outcome.
- **Issue disposition:** Test runtime capability/configuration limitation; not evidence of an application concurrency failure by itself.

### PORT-025 — Row-lock probe needs an independent connection, not the contextual datasource proxy

- **Observed:** The JDBC lock probe raised `NoConnectionException: No current connection present` when requesting a connection directly from the injected datasource outside an ambient transaction.
- **Cause:** Micronaut exposes a transaction-aware datasource proxy. The probe intentionally runs in a separate session rather than the booking transaction.
- **Resolution (verified):** Unwrap it with Micronaut's `DelegatingDataSource.unwrapDataSource`, the same helper used by its transaction manager, then open and close the probe's independent connection. The probe now observes the actual held row lock.
- **Issue disposition:** Test setup correction; expected contextual-datasource behavior, not an application or SDK defect.

### PORT-026 — Python's broad exception clause does not catch the probe's Java SQL exception

- **Observed:** Oracle correctly signaled the held LOW row lock with `ORA-00054`, but `except Exception` did not catch the foreign `java.sql.SQLException`, aborting the concurrency test before HIGH was issued.
- **Resolution (verified):** Catch `java.sql.SQLException` explicitly in the probe and Java `RuntimeException` alongside Python `Exception` at booking/reset boundaries. The probe and real typed priority-rollback response now pass.
- **Issue disposition:** Language-boundary adaptation. The observed row-lock error is expected evidence of LOW holding the lock, not a database fault.

### PORT-027 — Container startup copy configuration used a map instead of the required list

- **Observed:** The requests genuinely overlap, but the Oracle HIGH/MEDIUM wait targets remain `2147483647`, so HIGH waits until LOW commits and then reports the appointment as taken.
- **Source evidence:** Test Resources 4.1.0's `extractMapFrom` accepts a list of maps for `copy-to-container`; a plain map is silently ignored. Its own configuration test uses a YAML list. The first TOML translation used a normal table.
- **Resolution (verified):** Use a TOML array of tables (`[[test-resources.containers.oracle.copy-to-container]]`), plus the project-file source in PORT-028. The initializer now enables real priority takeover without any privileged test override.
- **Issue disposition:** Port configuration correction. The Python request scheduler is not serialized in this failure: HIGH's service entry was logged about 50 ms after LOW's entry, while LOW still held its row lock.

### PORT-028 — Test Resources server cannot load the application's startup SQL from its classpath

- **Observed:** After correcting the container-copy list shape, startup failed with a `TestResourcesException` identifying the server's `AppClassLoader`. The copied SQL was specified as `classpath:oracle/01-priority.sql`; application resources are not exposed through that server classloader in this CLI setup.
- **Workaround (verified):** Copy `config/oracle/01-priority.sql` using a host path when running the SDK from the project root. Both priority HTTP checks pass with automatic setup and no diagnostic override. The script remains bundled as a resource. The [image entrypoint source](https://raw.githubusercontent.com/gvenzl/oci-oracle-free/main/container-entrypoint.sh) documents the initialization-script execution path.
- **Issue disposition:** Test Resources/CLI resource-classpath integration candidate. The SQL file exists and application-side resource loading is already verified separately.

### PORT-029 — Baseline service contract and pet-type table differ from the reference

- **Observed by source comparison:** The original Python `ClinicService` uses prototype scope; the reference uses singleton scope. Delete operations and several ID/all-pet lookups were missing from the Python facade. Python maps pet types to `PET_TYPES`; the reference maps them to `TYPES`.
- **Impact:** Bean lifecycle, callable service operations and generated SQL differ even when the existing UI checks pass.
- **Resolution (verified):** Match singleton scope; add the missing owner/pet/visit delete and pet/visit/vet/speciality lookup operations; map `PetType` and its name query to `TYPES`. Add `V13` to rename the existing table/sequence without rewriting applied migrations or losing fixture rows. Copy the reference appointment/entity constraints and catalog validation messages. The facade lookup/create/delete workflow passes. Vet-speciality mapping now uses the reference's two scalar foreign keys and a generic join repository; lookup is verified. Cache `find_all_vets` itself so HTML, JSON and direct service callers share the reference's intercepted operation.
- **Issue disposition:** Port fidelity corrections, not established SDK defects. Additional model/service/repository comparison remains open.

### PORT-030 — Existing tests accepted HTTP representations that differ from the running reference

- **Observed:** An isolated copy of the unmodified Java reference compiled and started using cached Gradle dependencies and its default H2 profile. GET `/vets/json` returns only `id`, `firstName`, `lastName`; Python also returned speciality fields. GET `/owners?lastName=Davis` returns JSON with `owners` and `lastName`; Python rendered the owner-list page. Python also exposed an extra URL-encoded visit POST absent from the reference.
- **Evidence:** Captured successful JSON bodies are retained in [the reference HTTP fixture](../tests-config/fixtures/reference-http.json). Reference source: `VetController`, `OwnerController.processFindForm`, and `VisitController.processNewVisitForm` in the local comparison checkout.
- **Resolution (verified for successful contracts):** Restrict vet JSON to the reference fields while keeping specialities in the HTML model, return the reference owner-search representation, remove the extra visit form route, and use JSON from the translated reference visit UI and integration workflow. Captured successful payload comparisons and the workflow checks pass. Remaining failure responses are tracked separately.
- **Issue disposition:** Application/test fidelity gap. Passing tests written around the Python baseline did not prove equality with the Java application.

### PORT-031 — Reference pet/visit operations do not enforce owner-path membership

- **Observed:** In the running Java reference, GET `/owners/2/pets/1/edit` and `/owners/2/pets/1/visits/new` return 200 and display pet 1 with its actual owner. A valid JSON visit POST and valid pet edit POST through owner 2 both return 301 to `/owners/2`; restoring the pet through owner 1 returns 301 to `/owners/1`. The source resolves the pet independently of `ownerId`; pet edit POST assigns the URL's owner, and visit POST saves against the selected pet and redirects to the URL's owner.
- **Impact:** The added membership checks in the initial port change the requested clean copy's behavior. This is also a reference application concern if stronger parent ownership semantics are desired later.
- **Resolution:** Remove the port-only rejection checks and preserve reference lookup/reassignment behavior. The interval check verifies a mismatched-owner visit POST, its redirect, the actual owning pet's updated history, and both mismatched-owner GET pages. A separate runtime check of pet reassignment in the port remains part of the broader contract audit.
- **Issue disposition:** Reference behavior, not an SDK defect. Do not silently introduce additional authorization/ownership policy into this port.

### PORT-032 — Running reference has core validation/error response defects

- **Environment:** Unmodified local reference copied to an isolated temporary directory; `./gradlew classes --offline` succeeded; `MICRONAUT_SERVER_PORT=18081 ./gradlew run --offline` started the default H2 application.
- **Reproduction A:** POST JSON to `/owners/1/pets/1/visits/new` with `{"date":"2031-02-03","description":"golden invalid","durationMinutes":0,"followUpPeriodMonths":6}`. Response is 500 JSON. The trace shows the local validation handler reads query parameters for IDs that are supplied as path variables, passes a null owner to the JTE view, and the renderer throws `NullPointerException` at `owner.id()`.
- **Reproduction B:** POST URL-encoded empty owner fields to `/owners/1/edit`. Response is 500 HTML containing the creation form action `/owners/new`. The source's shared validation handler unconditionally sets `isNew=true`.
- **Reproduction C:** POST a valid URL-encoded visit body to the JSON-only visit route. The running reference returns 500 HTML; its error log contains `AuthorizationException`. This does not imply that form-encoded visit creation is supported.
- **Control:** A valid pet form with nonexistent `typeId=999999` returns 400 and body `Invalid pet type`; this is distinct from a constraint-validation failure.
- **Disposition:** Reference application defects and framework response behavior. Report separately from Pyronaut candidates. The port's remaining validation-status/body comparison is explicitly open; successful workflows and captured successful JSON contracts do not prove these failure paths match.

### PORT-033 — Generated test sources do not include adjacent JSON fixture files

- **Observed:** A successful reference HTTP payload stored at `tests/fixtures/reference_http.json` existed in the staged source tree, but `Path(__file__).parent` resolved inside `__pyronaut__/test-sources`. Reading the adjacent fixture there raised `FileNotFoundError`.
- **Impact:** Two contract checks failed before comparing any HTTP payload. This is distinct from an application response failure.
- **Resolution (verified):** Store the golden payload in configured `tests-config/fixtures/reference-http.json` and load it with the test application's `Environment.getResourceAsStream`. Both payload comparisons pass. The expected HTML badge text was also corrected independently; the reference renders individual speciality badges, not one comma-separated label.
- **Issue disposition:** Test resource placement correction. No SDK defect is established by Python-source processing omitting arbitrary neighboring data files.

### PORT-034 — Vet's transient collection cannot be part of its persistence constructor

- **Observed:** Adding the reference's transient speciality collection to the Python `Vet` dataclass without its separate persistence creator made all vet query paths fail with `MappingException: Constructor argument [specialities] for type [petclinic.Vet] must have an associated getter`.
- **Cause:** The default dataclass constructor includes `specialities`, but it is excluded from persistent properties by `@Transient`. The Java record explicitly declares an `@Creator` constructor taking only persisted columns.
- **Resolution (verified):** Add the corresponding Python static `@Creator` factory taking first name, last name and id. Keep the transient speciality list for service/HTML use. The facade now returns vets containing their specialities instead of leaking aggregate projection rows. Vet ID lookup, aggregate loading, HTML/JSON rendering and caching all pass together.
- **Related test correction:** H2 and Oracle can order equal `lastName` values differently. The reference orders only by last name, so compare the two Davis owner payloads without inventing an additional API ordering guarantee.
- **Issue disposition:** Missing reference construction metadata in the port; no SDK defect established. The SDK source explicitly supports static creator factories.

### PORT-035 — Dialect repository subclasses lose inherited CRUD generic signatures

- **Observed:** Translating the reference's shared unannotated repository interfaces plus per-dialect `@JdbcRepository` subclasses failed during Python processing. Generated Java implementations contain methods such as `deleteAll(Iterable<Visit>)` and `<S> saveAll(Iterable<Visit>)`; the inherited Micronaut interfaces require `Iterable<? extends Visit>` and bounded generic `S` signatures. Java compilation reports missing overrides and erasure clashes across the dialect subclasses.
- **Reproduction:** Declare `VisitRepository(CrudRepository[Visit, int], Protocol)` without a JDBC annotation, then `@JdbcRepository(dialect=Dialect.MYSQL) class MySqlVisitRepository(VisitRepository, Protocol)` and process it. The same structure compiled in the Java reference.
- **Evidence:** Local processor dump `__pyronaut__/processor-error-dumps/pyronaut-compiler-error-20261016-134859-845.log`; generated `MySqlVisitRepository.java`.
- **Impact:** A direct translation of the reference repository organization does not compile with this SDK, before any database startup.
- **Workaround (verified across all profiles):** A direct CRUD base alone did not correct the generated signatures while the peer contract still inherited CRUD. Use `GenericRepository[Entity, int]` for the shared query contract and declare `CrudRepository[Entity, int]` directly on each dialect implementation. This retains the actual generated CRUD methods on the injected implementation and avoids the SDK's broken nested generic bridge path. Combined with PORT-039's explicit query declarations, runtime injection, CRUD, facade deletes and shared HTTP workflows pass on Oracle, H2, PostgreSQL and MySQL.
- **Issue disposition:** SDK nested generic interface/bridge generation candidate. Preserve the actual generated repository mechanisms while finding a working declaration shape.

### PORT-036 — Baseline sample fixtures differ from the reference

- **Observed by source comparison:** The original Python `V2` seeds four Jean Coleman pet visits in January 2013. The reference `DataLoader` creates sixteen visits dated 2017–2026 and does not create those four older visits. The port's additive `V5` kept the baseline rows and added the sixteen reference rows, so Oracle has twenty seeded visits.
- **Impact:** The resulting visit history is not a clean copy of the reference fixture set even though date-filter tests selecting only 2026 pass.
- **Current action:** New database-profile migrations seed only the reference's sixteen visits. Oracle fixture alignment remains open; preserve applied migration checksums and distinguish exact baseline seed rows from user-created history before removing anything.
- **Additional source comparison:** The original seed pet dates were copied to the other profiles and differ from `system/DataLoader.java` for these five records. Corrections are deferred with the fixture lifecycle work; no original migration was rewritten.

| Pet / owner first name | Current seed birth date | Java reference birth date |
| --- | --- | --- |
| Rosy / Eduardo | 2011-03-07 | 2011-04-17 |
| Mulligan / Maria | 2007-01-20 | 2007-02-24 |
| Freddy / David | 2010-01-20 | 2010-03-09 |
| Lucky / Carlos | 2010-01-20 | 2010-06-24 |
| Sly / Carlos | 2012-09-04 | 2012-06-08 |

- **Issue disposition:** Port fixture difference; not an SDK defect. Generated IDs are database identities and are not a cross-profile ordering contract.

### PORT-037 — Test Resources prevents an implicit H2 datasource fallback

- **Observed:** With H2 driver/dialect configured but URL/credentials omitted, startup failed before migrations: `Test resources doesn't support resolving expression 'datasources.default.password'`.
- **Cause:** JDBC Test Resources providers advertise datasource property keys before checking the database type during resolution. Their lazy property source supplies missing properties, so Hikari's embedded-driver defaults are not reached for this H2 context.
- **Resolution (all profiles verified):** Supply the reference's explicit H2 URL (`jdbc:h2:mem:petclinic;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE`), `sa` username and empty password. H2 starts and all 16 shared checks pass. External profiles override all three inherited properties using the client's `auto.test.resources.` expressions, with the reference's localhost values as non-Test-Resources fallbacks; Oracle, PostgreSQL and MySQL runtime checks now pass with those expressions. Packaged fallback execution remains unverified.
- **Issue disposition:** Configuration integration edge case; reduce whether unsupported embedded database types should advertise these lazy keys before assigning an upstream defect.

### PORT-038 — Reference H2 generated price column loses fractional amounts

- **Observed:** The running reference's schema log contains `PRICE DECIMAL NOT NULL`, without a scale. A reduced check with the resolved H2 `2.4.240` driver creates that column, inserts `65.10`, and reads back `65`.
- **Reproduction:** `CREATE TABLE PRICE_PROBE (PRICE DECIMAL); INSERT INTO PRICE_PROBE VALUES (65.10); SELECT PRICE FROM PRICE_PROBE;`.
- **Impact:** The source form permits two fractional digits and uses `BigDecimal`, but that generated H2 storage declaration discards them. This is a reference schema problem, not evidence of floating-point conversion in Python.
- **Port adaptation:** New dialect migrations explicitly use `DECIMAL(10, 2)`, as the existing Oracle migration does, to preserve the declared price contract. Catalog round trips preserve fractional prices on H2, PostgreSQL and MySQL. This storage difference must be considered when comparing the source's defective H2 decimal behavior.
- **Issue disposition:** Reference mapping/schema candidate. File with the source DDL and reduced driver result; no source checkout was edited.

### PORT-039 — Shared Python query declarations do not retain each child's SQL dialect

- **Observed:** After resolving generic bridge compilation, H2 startup, fixture seeding, generated spatial searches and Oracle feature gating worked. Some inherited query methods still executed SQL from a different specialization: pet/vet lookups used PostgreSQL-style double-quoted lower-case `id`, and catalog relationship queries invoked Oracle's `SDO_UTIL.TO_GEOJSON` on H2.
- **Evidence:** H2 suite ran 16 shared cases; six failed. The catalog trace reports `Schema "SDO_UTIL" not found`; its SQL contains Oracle geometry projection functions despite selecting the H2 repository bean. Both PostgreSQL-style ID lookups and Oracle geometry projections appear in the same H2 context.
- **Impact:** Successful bean selection and compilation do not establish correct inherited query metadata. This is independent of H2GIS availability: generated nearby/within/intersection checks passed.
- **Workaround (verified across all profiles):** Redeclare the same annotated custom query signatures on each dialect implementation so each declaration has a distinct owning type. Keep shared query contracts for injection and generated CRUD directly on the concrete implementations. All 16 shared checks pass on H2, PostgreSQL and MySQL, and all 26 Oracle checks pass, including the previously failing lookup and joined catalog paths. Spatial and upsert operations still use Micronaut Data generation; they were not replaced by custom persistence code.
- **Issue disposition:** SDK/Micronaut Data Python inherited query ownership/metadata specialization candidate. Reduce with one shared query, two dialect subclasses and inspection of both generated SQL definitions.

### PORT-040 — JUnit suite summary reports zero skips while ten cases are skipped

- **Observed:** The H2 CLI reports `16 tests passed, 10 skipped in 15.2s`. Its JUnit XML contains 26 test cases and ten `<skipped>` elements, but the suite attribute is `skipped="0"`.
- **Evidence:** Preserved H2 artifacts under `__pyronaut__/reports/database-profiles/h2/`; the individual skipped elements identify the Oracle-only cases.
- **Impact:** Tools relying on suite-level counts can report misleading coverage totals. This does not mean those ten Oracle features were verified on H2.
- **Workaround:** Read the actual child test results and the CLI summary when reporting profile coverage; do not report all 26 cases as passed.
- **Issue disposition:** SDK pytest/JUnit reporting consistency candidate. Reduce with an unconditional `pytest.skip` before filing.

### PORT-041 — Empty route URI is not equivalent to a bare GET annotation

- **Observed:** The first Oracle regression after converting gated routes to class controllers passed 24 cases, but GET `/visits` and GET `/knowledge` returned 404. Their search APIs, vector loading, care records and priority transactions worked. The two missing roots had been translated with `@Get('')` rather than the reference's bare `@Get`.
- **Resolution (verified):** Use bare `@Get`, matching both the Java source and the working Python priority controller. Keep the class-level route prefixes and Oracle conditions. All 26 Oracle cases now pass, including both restored pages and the gated feature APIs.
- **Issue disposition:** Port annotation translation correction. An explicit empty URI should not be assumed equivalent to an annotation's default URI; no SDK defect established.

### PORT-042 — Core fixture migrations bypass the sample-data configuration switch

- **Observed by source/configuration comparison:** The Java `DataLoader` is conditional on `petclinic.sample-data.enabled=true` (default true). The Python vector loader preserves that condition, but core/clinic/appointment SQL fixture migrations execute independently of it, including the new dialect seed migrations.
- **Impact:** Setting the flag false does not produce the reference's empty shared tables in a new database. Successful checks using the default enabled setting do not establish this configuration contract.
- **Required work:** Separate conditional fixture loading from schema creation for new profiles and reconcile the existing applied Oracle seed history without rewriting checksums or deleting user-created rows. Verify both enabled and disabled startup and restart behavior.
- **Issue disposition:** Port configuration/lifecycle parity gap, not an upstream SDK defect. Still open.

### PORT-043 — Conditional fixture-loader experiment fails resource lookup

- **Observed:** An attempted separation of schema migrations from conditional sample-data loading failed the dedicated H2 lifecycle test with `ValueError: Missing application resource: data/petclinic-sample.json`. The disabled-startup checks completed before enabled startup attempted to read that resource.
- **Reproduction at the time:** In the isolated matching GraalPy checkout, run `PETCLINIC_TEST_DATABASE=h2 pyronaut test --no-validate --tests '*sample_data*'`. One selected test failed in 10.7s. It used a fresh H2 schema, a JSON file under `config/data/`, baseline schema snapshots and a conditional transactional startup seeder.
- **Impact:** The experiment did not establish successful enabled startup or restart preservation. An earlier ordinary H2 run was insufficient evidence of the loader's lifecycle behavior.
- **Stabilization action:** Remove the experimental loader, JSON data, baseline snapshots, corrective fixture migrations and lifecycle assertions. Retain the previously passing versioned schema/SQL seed migrations. The experimental code is not part of this checkpoint; the command above therefore no longer reproduces it in the current tree.
- **Evidence:** Failure log and JUnit report were preserved locally under `__pyronaut__/reports/deferred-fixture-experiment/`. These generated artifacts are ignored by Git.
- **Later work:** First reduce whether resource copying, generated-source caching or application resource visibility caused the missing stream. Use the supported `Environment` resource path, prove the file is in processed resources, then test disabled startup, enabled startup and restart separately. Isolate lifecycle databases from the ordinary suite. Do not rewrite applied Flyway checksums or delete user-created data.
- **Issue disposition:** Unresolved experiment/integration failure; no upstream SDK defect established. Deferred with PORT-042.

## Deferred work for later

These items are documented proposals, not implemented additions or current stabilization tasks. Resume them only when requested.

| Work | Proposed approach | Acceptance check |
| --- | --- | --- |
| Conditional sample data (PORT-042/043) | Prove resource packaging first; separate new-schema creation from conditional transactional loading; design an upgrade path for existing databases | Fresh disabled startup has empty shared tables; enabled startup loads canonical fixtures; restart/repeated loading preserves user rows and creates no duplicates, across all four profiles |
| Canonical fixtures (PORT-036) | Compare reference pet dates, visit history, clinic geometry and catalog data; correct only positively identified stock rows through new migrations | Compare complete canonical records, not only filtered searches; preserve applied checksums and user-created data |
| Remaining source contracts (PORT-029–032) | Audit model identity/helper behavior, service/repository signatures, cross-owner writes and error/content-type responses against the running reference | Record exact request/status/body or model behavior; distinguish reference bugs from port defects before changing behavior |
| Concurrent first catalog insert | Submit overlapping writes for a previously absent clinic/code, retaining generated upsert and uniqueness | One persisted row and identity; responses follow the chosen reference contract; no partial combined row |
| Browser and visual parity | Compare locale switching, forms, maps, catalog pages, care editor and priority interactions with the reference | Manual browser evidence, including unavailable CDN assets and JavaScript-driven results |
| Distribution and production configuration | Exercise packaged startup away from the repository root, resource/static loading and external datasource overrides/fallbacks; review management endpoints against the reference | Packaged routes/assets/resources work; configured database connections resolve correctly; intended health/security behavior matches the source |
| Toolchain and CI | Resolve the recorded GraalPy/JVM mismatch, review SDK configuration validation, and execute the configured four-profile remote CI matrix | Matching runtime versions; explicit validation result; successful remote jobs with honest skip counts |

Keep the source reference checkout and the user's existing CPython environment unchanged. Continue using already cached images locally. Oracle Deep Data Security is outside this backlog's implementation scope unless separately requested.

## Other verification notes

- Full browser behavior and visual parity with the reference after JTE-to-Jinjava translation.
- Concurrent catalog insertion of an absent natural key. Updates to an existing key and actual veterinarian cache reuse/invalidation now have passing checks.
- Locale test isolation: a test's explicit cookie header was overridden by the session cookie jar. Verify language switching through the actual `/locale` route; this is not currently evidence of an application locale defect.
- Reference-template tests need to assert the reference contract. For example, the reference clinic page renders search results through JavaScript, so expecting a seeded branch name in the initial HTML is inappropriate.
- JSON duality and transaction priority now have passing runtime checks described below. All four database profiles have runtime coverage. Fixture lifecycle, packaged execution and the remaining model/service and HTTP contract comparison are still open work; missing coverage is not an upstream defect claim.

## Latest verification checkpoint

2026-10-16 stabilization rerun: **26 integration tests passed in 49.8s** against the cached Oracle image after removing the unfinished fixture-loader experiment. The cases include ordinary PetClinic workflows, captured Java-reference vet/owner-search JSON contracts, spatial queries, catalog upserts, visit bounds, locale switching, HTML 404s, ranked vectors, nested duality updates, date/null validation, insert/delete restrictions, stale ETAGs after document and relational edits, and JSON not-found responses.

Priority checks additionally establish regular commit, taken/missing/reset responses, actual overlapping LOW/HIGH HTTP requests with an independent probe observing LOW's Oracle row lock before HIGH, emergency commit with LOW priority rollback, outcome classification, and an actual equal-priority `FOR UPDATE WAIT 10` timeout. Database configuration is applied automatically by the container initializer; no privileged test setup remains.

The latest suite additionally verifies all-pet and visit/vet/speciality ID lookups, enriched veterinarian service results, speciality join lookup, and a create/look-up/delete facade workflow for an owner, pet and visit. The cache check mutates a vet row through independent JDBC, observes the cached old value through JSON, HTML and the service, invalidates the cache, and observes the new value before restoring the row. Six asynchronous HTTP catalog updates preserve the original identity and a single complete submitted row.

Additional profile results: **H2 16 passed / 10 Oracle-only skips (16.7s)**; **PostgreSQL 16 passed / 10 skips (20.1s)**; **MySQL 16 passed / 10 skips (24.9s)**. Database-product checks confirm each actual driver, and Oracle-only routes/services are absent on the other profiles. Each uses the same shared spatial, catalog, CRUD, caching and localization checks. Final stabilization reports and command logs are preserved under `__pyronaut__/reports/stabilization/`; earlier reports remain under `__pyronaut__/reports/database-profiles/`. Counts use child test elements because of PORT-040. All four final suites have zero failures/errors.

Python source and TOML parsing and `git diff --check` also pass. Experimental loader code, lifecycle tests and unapplied experimental migration files were removed from both the repository and the isolated test copy. Original applied Oracle migration files and the user's staged `.gitignore` change were preserved. No new local image pulls, external issue filings or remote CI runs were performed.

Interactive browser parity, concurrent insertion of an absent clinic/code, fixture/sample-data lifecycle alignment, remaining model/service/repository and HTTP failure-path fidelity checks, production URL fallback execution, and packaged execution remain outside this checkpoint. SDK configuration validation was skipped. Full reference parity is not claimed; further implementation is deferred at the user's request.
