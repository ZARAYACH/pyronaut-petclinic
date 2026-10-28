# PetClinic port: issue candidates and encountered problems

Updated: 2026-10-28 (ownership triage). Scope: a faithful Micronaut PetClinic port to Pyronaut, excluding Oracle Deep Data Security.

This is a working log for filing issues later. No external issues have been created. Entries distinguish confirmed defects, environment problems, resolved port adaptations, and checks still in progress. A reproduction specific to this SDK is not a claim that all Pyronaut versions are affected.

**Latest scope:** the user authorized a full review, functionality-based tests, and the newer veterinarian ETag/exception changes. The earlier stabilization backlog remains deferred except for the corrections recorded below. Oracle Deep Data Security remains excluded.

## Environment for these reproductions

- Pyronaut SDK `0.0.3`; Micronaut Core `5.2.2`; SDK platform `5.1.0`.
- Micronaut Data runtime/processor `5.2.3`; Micronaut Serialization `3.1.0`.
- Embedded GraalPy `25.3.4.1`; matching GraalPy 3.13 used for pytest.
- Cached Oracle image `gvenzl/oracle-free:23.26.2-faststart`.
- Early checks used `pyronaut test --no-validate`. The final 2026-10-27 matrix enabled configuration validation with one narrow suppression for `test-resources.containers.oracle.copy-to-container`; see PORT-027.

Record a reduced reproduction and reconfirm it before opening an upstream issue. Several entries are resolved application differences or expected environment requirements, rather than defects to file against Pyronaut.

## Ownership triage (2026-10-28)

All **50 entries** are classified below. This is a source-and-artifact review of the recorded failures and current workarounds, not a new execution of the matrix or confirmation against newer framework releases. No external issues have been filed. Historical details below describe the code at the time of each failure; a working workaround does not establish that its underlying framework limitation has been fixed.

| Primary classification | Entries | Meaning |
| --- | ---: | --- |
| Framework candidate | 11 | Observed behavior warrants an upstream defect investigation; package ownership still needs a reduced reproduction |
| Framework improvement | 5 | Interop documentation, diagnostics or capability configuration; no correctness defect established |
| Application/test | 22 | Our mappings, handlers, configuration, fixtures, tests or remaining port work |
| Reference application | 3 | Java sample behavior or schema; not automatically a Pyronaut issue |
| Environment | 5 | Interpreter/toolchain, container capability, network trust or database provisioning |
| Unresolved | 4 | Evidence does not yet distinguish application setup from a library/runtime defect |

Counts assign each PORT identifier once. Mixed entries have separately named parts below; their secondary improvement opportunities are not additional bugs. Of the 11 framework candidates, **10 should initially be investigated through the Pyronaut integration and one (PORT-046) through Micronaut Data**. This is a routing recommendation, not a claim of 10 proven Pyronaut defects.

### Complete disposition

| Finding | Primary classification | Owner, reasoning and disposition |
| --- | --- | --- |
| PORT-001 | Framework candidate | **Pyronaut script/executor integration.** Explicit blocking execution hangs script routes, while class controllers work. Retain the class-controller workaround; reduce scheduling before assigning the underlying runtime cause. |
| PORT-002 | Environment | **Local JVM/Polyglot versions.** Incompatible compiler versions cause interpreter fallback. Align the toolchain; SDK compatibility preflight is an improvement. Reassign only if SDK dependency selection itself creates the mismatch. |
| PORT-003 | Environment | **Test interpreter setup.** CPython 3.14 is not the matching embedded GraalPy environment. Preserve the separate environment; request CLI interpreter selection/early diagnostics as an improvement, not a Python-runtime correctness fix. |
| PORT-004 | Unresolved | **Resource discovery and caller-sensitive Java invocation are separate failures.** `Environment` loading works. Isolate packaging/classloader selection from restricted MethodHandle access before routing to Pyronaut, GraalPy or application configuration. |
| PORT-005 | Application/test | **Our error mapping.** A generic handler produced 500 for a missing entity; a specific 404 handler fixes it. No framework handler-precedence defect established. |
| PORT-006 | Environment | **Oracle image capability.** The slim image lacks the required spatial type. Selecting the regular image fixes provisioning; no Pyronaut issue. |
| PORT-007 | Environment | **Docker/network certificate trust.** Reuse the cached image. An image download failure is not a framework defect. |
| PORT-008 | Application/test | **Test Resources server dependencies.** Explicit resolver modules fix startup. Automatic inference or a missing-resolver diagnostic is an SDK improvement only if that behavior is intended. |
| PORT-009 | Framework improvement | **Interop documentation.** Java duration conversion to `timedelta` requires application normalization; no stored-value loss was demonstrated. Document the supported representation. |
| PORT-010 | Unresolved | **Period conversion/comparison.** Normalization fixes the bound, but the cause could be application expectations, Data conversion or the Oracle driver. Compare all three before filing. |
| PORT-011 | Application/test | **Our upsert response design.** Re-read the persisted natural key instead of assuming the candidate sequence ID. The entry records a precaution, not a captured wrong-ID defect. Concurrent first insertion remains an application verification task. |
| PORT-012 | Application/test | **Our HTML formatting.** Decimal scale in display is an application responsibility. Two-digit formatting is fixed; no precision-loss claim follows from `65.1`. |
| PORT-013 | Application/test | **Our constructor mappings.** Nullable back-references must match the Java persistence constructor. Fixed while preserving validation constraints. |
| PORT-014 | Application/test | **Our validation-message keys.** Fixed by reading node names; the constraint engine did reject invalid values. Related SDK documentation opportunity is PORT-015. |
| PORT-015 | Framework improvement | **Validation-path interop API/documentation.** An iterable path becomes a node list, so stringifying it is unsuitable. Document node traversal or offer a path formatter; no validation-engine defect established. |
| PORT-016 | Framework candidate | **Pyronaut AST / Data metadata integration.** `findField` cannot see a declared Python entity field. Explicit column mappings work; reduce field exposure rather than treating every JSON-view error as application mapping. |
| PORT-017 | Unresolved | **Oracle JSON / LocalDate compatibility.** The time-bearing Oracle value fails the date-only deserializer. An explicit format fixes it, but the Java/Python behavior under identical mappings has not been isolated; do not assign it to Pyronaut yet. |
| PORT-018 | Framework candidate | **Mixed:** wrong field-level annotation was ours (**018a**); correct element-level `@Valid` still fails to cascade (**018b**, Pyronaut type-use metadata / Validation candidate). Retain manual traversal and file only the correctly annotated case. |
| PORT-019 | Application/test | **Our API error contract.** Explicit JSON/domain handling fixes the HTML 404 response. The current centralized handlers supersede the historical controller-local workaround. |
| PORT-020 | Framework candidate | **Pyronaut annotation-binding generation.** A generated binding imports an ungenerated transitive annotation module. Explicitly importing both annotations is a workaround, not a normal missing application dependency. |
| PORT-021 | Framework improvement | **Repository-return interop documentation.** Java mirrors are not Python dataclasses; `dataclasses.replace` is inapplicable. Document construction/enum normalization; native-dataclass ergonomics are a separate enhancement. |
| PORT-022 | Framework candidate | **Pyronaut HTTP enum conversion.** Lowercase reference inputs fail generated binding. String conversion works. Confirm enum converter registration and Java/Python equivalence before choosing Pyronaut versus Core ownership. |
| PORT-023 | Application/test | **Our schema names.** Align speciality tables/columns with the source through additive migrations. Fixed; no upstream issue. |
| PORT-024 | Framework improvement | **Embedded runtime capability/configuration.** Python threads are disabled in this context. Document or expose supported configuration if available; this is not evidence that HTTP requests cannot overlap. Java async priority checks do overlap. |
| PORT-025 | Application/test | **Our lock probe.** A contextual datasource proxy requires its transaction context. An independent physical connection fixes the probe; expected transaction behavior. |
| PORT-026 | Framework improvement | **Foreign-exception documentation.** Explicit Java exception catches work where Python `Exception` does not. Document the hierarchy; the expected ORA-00054 lock result is not a persistence failure. |
| PORT-027 | Framework candidate | **Mixed:** wrong map shape was ours (**027a**); the SDK schema rejects the working runtime list-of-maps shape (**027b**). Investigate schema generation/config metadata ownership. Also improve diagnostics for silently ignored shapes. |
| PORT-028 | Application/test | **Separate-process resource configuration.** The Test Resources server does not automatically share the application's classpath. Host-path copying works. SDK resource resolution/docs could improve; no promised application-classpath visibility is established. |
| PORT-029 | Application/test | **Our service/model fidelity.** Scope, operations, naming and interception differences are port corrections. Recorded fixes are retained; broader helper equivalence remains an audit task. The older shared HTML/JSON cache description predates PORT-044's separate vet CRUD service. |
| PORT-030 | Application/test | **Our contract tests and older port behavior.** Fixed against the then-current reference. Its three-field vet payload is historical: PORT-044 supersedes that contract with current DTOs, specialities and ETags. |
| PORT-031 | Reference application | **Source ownership policy.** Cross-owner paths/reassignment are reference behavior. Preserve the requested parity; any stricter policy is a separate product/reference decision, not a Pyronaut fix. |
| PORT-032 | Reference application | **Source error handlers/rendering.** Wrong parameter lookup and creation/edit context are Java sample defects. Reconfirm against the current reference before filing; unsupported content-type status behavior may require a separate Core reproduction. |
| PORT-033 | Application/test | **Our fixture placement.** Generated Python test sources are not an automatic copy of arbitrary adjacent files. Configured test resources work. A clearer resource guide is an improvement, not a demonstrated compiler defect. |
| PORT-034 | Application/test | **Our persistence creator.** The port omitted the Java reference's persisted-fields-only creator. Matching `@Creator` fixes it; no evidence that transient collections themselves are unsupported. |
| PORT-035 | Framework candidate | **Pyronaut generic bridge generation.** Nested repository inheritance emits signatures that clash or fail to override. The Java structure compiles; retain the verified direct-CRUD workaround and reduce generated signatures. |
| PORT-036 | Application/test | **Our sample fixtures.** Extra legacy visits and five wrong pet dates are corrected by guarded new migrations. Preserve applied checksums and user data; no framework issue. |
| PORT-037 | Application/test | **Our H2 datasource configuration.** Explicit embedded URL/credentials fix startup. Test Resources claiming unresolved keys merits clearer diagnostics; absence of an H2 container resolver is not itself a defect. Packaged fallback is unverified. |
| PORT-038 | Reference application | **Source decimal DDL.** Scale-zero H2 `DECIMAL` loses fractions as declared. The reference schema/mapping needs a fix; ours explicitly preserves scale. A Data schema-generation claim needs an annotation-contract reproduction first. |
| PORT-039 | Framework candidate | **Pyronaut AST / Data query specialization.** Inherited queries execute SQL from another dialect despite correct bean selection. Redeclarations fix all profiles. Reduce owning-type metadata; not a missing spatial extension. |
| PORT-040 | Framework candidate | **Pyronaut test reporting.** Archived XML directly contradicts its child counts and drops parameter identities. Fix the report producer; this does not indicate the skipped features passed. |
| PORT-041 | Application/test | **Our annotation translation.** Explicit empty URI was substituted for the reference's bare `@Get`. Matching the reference fixes both roots; equivalence of those annotations was never established. |
| PORT-042 | Application/test | **Open application lifecycle gap.** Core SQL seeds ignore `petclinic.sample-data.enabled=false`. Separate conditional fixtures safely from schema migration history; the framework already supports conditional beans. |
| PORT-043 | Unresolved | **Removed fixture experiment.** Its resource lookup failure is historical and not reproducible from the current tree. First establish processed-resource presence and context configuration; no upstream owner assigned. |
| PORT-044 | Application/test | **Our feature lag.** New vet CRUD/ETags/exception contracts are ported. A Python method name colliding with Java's `new` keyword was corrected locally; no separate framework defect demonstrated. |
| PORT-045 | Framework candidate | **Mixed:** nullable typed IDs becoming zero (**045a**) warrant a binding/serialization defect investigation; `ForeignNone` identity in object collections (**045b**) is an interop adaptation. Reject malformed inputs before deduplication in our code. |
| PORT-046 | Framework candidate | **Micronaut Data ETag SQL generation.** Unquoted mapped identifiers break PostgreSQL. Generated lowercase aliases are our workaround; prove the Java control before describing this as Pyronaut-specific. PostgreSQL identifier folding is expected. |
| PORT-047 | Environment | **MySQL provisioning.** Binary-log routine-creation requirements are server policy. Local container settings fix tests; external databases need suitable DBA provisioning, not an SDK code change. |
| PORT-048 | Application/test | **Our validation/storage mismatch.** Widening descriptions and Oracle character semantics fixes accepted Unicode text exceeding storage. Keep additive migrations and boundary coverage. |
| PORT-049 | Application/test | **Our test fixture assumption.** ID 1 was intentionally removed by exact legacy cleanup. Resolve a real visit instead; fixed, no upstream issue. |
| PORT-050 | Application/test | **Mixed:** enum mirror normalization (**050a**) is an application interop adaptation related to PORT-021; missing write transaction in the lock test (**050b**) was a test setup error. MySQL correctly rejects locking in a read-only transaction. |

### Framework defect investigation queue

Priorities below reflect potential impact without our workarounds, not current failures in the stabilized port. **Strong evidence** means a concrete failing artifact, source mechanism or controlled workaround is recorded; it does not establish the responsible package or a defect in the latest release. **Tentative evidence** needs a tighter behavioral control before filing.

| Order | Candidate and likely first owner | Evidence / impact | Smallest useful reproduction and acceptance condition |
| ---: | --- | --- | --- |
| 1 | PORT-045a — Pyronaut binding / Serialization | Strong: nullable integer elements change meaning; input integrity | One DTO with `list[int \| None]`, explicit boxed-integer variant and an echo route. Send `[null]`, `[0]`, `[1]`; inspect raw deserialized values and generated metadata. Null must remain null. Compare a Java DTO to separate Serde from the Python binding layer. |
| 2 | PORT-018b — Pyronaut type-use metadata / Validation | Strong: invalid nested data reaches Oracle | Parent with `list[Annotated[Child, Valid]]`; child with `NotBlank`. Invoke `Validator` without a database and inspect generic-argument annotations. A blank child's violation must include its collection path; compare the Java equivalent. Exclude the incorrect original field annotation. |
| 3 | PORT-035 — Pyronaut compiler | Strong: generated Java does not compile | One shared generic CRUD protocol and one dialect subclass. Attach generated signatures and javac errors beside the compiling Java equivalent. Generated methods must preserve bounds/wildcards and implement the interface. |
| 4 | PORT-039 — Pyronaut / Data metadata | Strong: wrong-dialect SQL at runtime | One inherited annotated query and two dialect implementations. Inspect each generated query independently and together. Each must retain its owning implementation's dialect; include a Java control before narrowing ownership. |
| 5 | PORT-001 — Pyronaut script execution | Tentative ownership: route hangs; class-controller control works | Same trivial route as a script and class controller, with/without `ExecuteOn`. Capture timeouts and thread/context evidence, without Oracle or priority transactions. Blocking requests must complete and independent requests must overlap. |
| 6 | PORT-016 — Pyronaut class elements / Data visitor | Strong: declared field invisible to `findField` | One Python entity with `id` and one JSON subview, without explicit `MappedProperty`. Dump property/field metadata and compare Java. Processing must see the declared field or Data must use a supported property lookup. |
| 7 | PORT-020 — Pyronaut annotation bindings | Strong: generated import targets missing module | Import only `OracleTransactional` plus the Jakarta transactional annotation. Process/start a minimal bean; inspect generated imports. Every imported stereotype binding must be present without a redundant application import. |
| 8 | PORT-046 — Micronaut Data processor | Strong: generated expression and PostgreSQL trace agree | Minimal Java and Python entities with quoted uppercase ETag input columns. Inspect `GeneratedETagUtils` output and perform one PostgreSQL read/update without aliases. Expression identifiers must follow dialect quoting while retaining generated optimistic locking. |
| 9 | PORT-027b — Pyronaut configuration schema / Test Resources metadata | Strong: working runtime shape is schema-invalid | Submit the same list-of-maps copy configuration to SDK validation and the runtime provider. Attach generated schema and provider contract. Validation must accept the supported shape without suppression; investigate whether schema generation or upstream metadata declares the wrong type. |
| 10 | PORT-040 — Pyronaut test report producer | Strong: archived XML proves inconsistency | One pass, one skip and a parameterized test. Compare XML attributes with emitted children and parameter IDs. Counts must agree and each parameter case must be identifiable. No database needed. |
| 11 | PORT-022 — Pyronaut HTTP conversion / Core | Tentative ownership: lowercase binding fails | One enum query route, Python and Java equivalents. Compare uppercase, lowercase, missing and invalid values plus converter registration. Supported lowercase values must bind; invalid values must produce the agreed client-error response. Isolate conversion from our generic HTML handler. |

File one issue per independently reproducible cause. PORT-035 and PORT-039 are related metadata areas but exhibit distinct compilation and query-specialization failures. PORT-014/015 describe one message-path chain, not two validation bugs; PORT-021/050a describe the same family of mirror adaptations. PORT-027a and PORT-027b must not be merged into a report claiming the original invalid configuration was correct.

### Framework improvements worth proposing

These are enhancement/documentation requests, not additions to the defect count. Group related symptoms before filing:

- **Toolchain and interpreter selection (PORT-002/003):** compatibility checks before launch, an actionable interpreter mismatch message and explicit supported test-environment selection. First establish which versions/configuration the SDK actually chose.
- **Interop guide (PORT-009/015/021/026/045b/050a):** duration representations, validation-node traversal, repository mirror construction, enum names, foreign null checks and catching foreign exceptions. Offer convenience APIs only where their contract is clear; document the current supported path first.
- **Runtime capability guide (PORT-024):** document Python thread restrictions and supported context options. Preserve Java async as the already verified way to exercise overlapping requests; do not imply concurrency is unsupported generally.
- **Test Resources diagnostics (PORT-008/027a/028/037):** explain missing server modules, reject unsupported copy shapes instead of silently ignoring them, explain server versus application classpaths, and identify unsupported lazy datasource resolution clearly. Automatic inference/resource staging is an enhancement unless a supported contract promises it.
- **Test data packaging guide (PORT-033):** show configured test resource directories and loading through `Environment`; explain the generated Python source directory boundary.

### Unresolved investigations and our remaining backlog

Do not file PORT-004, PORT-010, PORT-017 or PORT-043 as confirmed Pyronaut defects yet:

- **PORT-004:** create separate controls for resource bundle discovery, `Environment` lookup and caller-sensitive invocation. Check that the resource is packaged before blaming a classloader; route restricted Java lookup separately if reproducible without resource access.
- **PORT-010:** compare normalized/unnormalized periods through direct JDBC, Java Data and Python Data using the same stored interval. Inspect bound values and database comparisons; this determines application normalization versus library/driver ownership.
- **PORT-017:** the local Java `OwnerCareView` uses `LocalDate` without our optional-time `JsonFormat`. Compare actual Oracle JSON and Java/Python deserializers with identical versions/mappings. A formatting workaround alone does not prove a Python compiler defect.
- **PORT-043:** the failed loader experiment was removed. Reconstruct a resource-only example before revisiting seeding, inspect the processed artifact, and establish the supported fresh-context configuration. Existing `Environment` loading succeeds elsewhere; do not combine this with PORT-004 or PORT-028 without a shared cause.

**PORT-042 remains the clearest open application correctness task:** the disabled sample-data flag does not suppress core SQL fixtures. Address it later through conditional loading with separate enabled/disabled/restart checks and a migration-history plan. Do not rewrite applied Oracle checksums or remove user rows. PORT-043 does not turn this application gap into a framework defect.

Other still-unverified application work is concurrent first catalog insertion (PORT-011), broader model/helper equivalence (PORT-029), remaining failure-contract comparisons (PORT-030/032), pet reassignment parity (PORT-031), packaged datasource fallback (PORT-037), browser behavior and remote CI. These are coverage or port-completeness tasks, not demonstrated framework bugs. Resolved application entries should remain historical records rather than being reopened as upstream issues.

The unnumbered verification notes also belong to application/test work: cookie-jar precedence affected locale test setup, and expecting JavaScript-populated results in initial HTML was an incorrect template-test assumption. Browser/CDN availability, packaged resources, production configuration and remote CI need their own evidence before any framework attribution.

### Evidence and filing procedure

This triage checked the current Python care-record and vet implementations, configuration suppression, local Java `OwnerCareView`, local Data `MappedEntityVisitor`/`GeneratedETagUtils`, and Test Resources `TestContainerMetadataSupport`, alongside the recorded failures. Local framework source checkouts support the investigation; establish the exact dependency/source revision in each reduced reproduction before treating them as the installed binary's implementation.

The preserved H2 report at `__pyronaut__/reports/review-20261026/h2/junit.xml` was read directly during triage: 121 child cases, 20 skipped children, but suite attributes `tests="81"` and `skipped="0"`. Ten testcase identities repeat across parameterized children. This confirms the recorded reporting inconsistency without rerunning tests. Generated reports remain local/ignored and must be attached explicitly when filing.

For each candidate, record the installed versions above, original failure, smallest standalone source, generated metadata/SQL or traceback, Java control where relevant, workaround and expected behavior. Reconfirm on a supported aligned toolchain and check whether the issue already exists or is fixed before filing. A single startup failure causing many test failures is one cause, not one issue per failed test. No application/framework code was changed and no new tests were run for this triage.

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
- **Issue disposition:** Resolved application adaptation; framework documentation/API improvement for iterable conversion and validation-path formatting, not an established constraint-validation defect.

### PORT-016 — JSON view processing cannot find a declared Python entity field

- **Area:** Micronaut Data JSON-view validation / Python class metadata.
- **Observed:** Processing the translated owner-care subviews failed with `Json View property id doesn't exist in the defined entity class Pet`, although the Python `Pet` dataclass declares an annotated `id` field and ordinary JDBC queries use it successfully.
- **Source evidence:** `MappedEntityVisitor.validateJsonViewProperty` checks the referenced entity with `ClassElement.findField(propertyName)` and skips that check for an explicit `@MappedProperty`.
- **Impact:** The direct Java annotation translation does not process with the current SDK.
- **Workaround (verified):** Declare explicit column mappings and nested join columns on the Python JSON view classes; preserve the reference's JSON property names and update-only operations. Processing succeeds and Oracle creates the migration-managed view. Runtime reading subsequently passed with PORT-017's date-format workaround; that does not fix the original field-lookup limitation.
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
- **Current implementation:** The newer exception port uses the shared `entity_not_found` helper and global JSON `HttpStatusException` handler instead of that original local workaround. This remains an application error-contract correction, not an SDK defect claim.

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
- **Separate schema mismatch (PORT-027b):** The SDK configuration schema expects an object and rejects this working runtime list-of-maps shape. The final matrix enables validation with only `test-resources.containers.oracle.copy-to-container` suppressed in `pyproject.toml`. Investigate schema generation versus Test Resources metadata; accepting the correct runtime shape is a framework candidate independent of the original application mistake (PORT-027a).
- **Issue disposition:** Mixed application correction and framework schema candidate. The Python request scheduler is not serialized in the original failure: HIGH's service entry was logged about 50 ms after LOW's entry, while LOW still held its row lock.

### PORT-028 — Test Resources server cannot load the application's startup SQL from its classpath

- **Observed:** After correcting the container-copy list shape, startup failed with a `TestResourcesException` identifying the server's `AppClassLoader`. The copied SQL was specified as `classpath:oracle/01-priority.sql`; application resources are not exposed through that server classloader in this CLI setup.
- **Workaround (verified):** Copy `config/oracle/01-priority.sql` using a host path when running the SDK from the project root. Both priority HTTP checks pass with automatic setup and no diagnostic override. The script remains bundled as a resource. The [image entrypoint source](https://raw.githubusercontent.com/gvenzl/oci-oracle-free/main/container-entrypoint.sh) documents the initialization-script execution path.
- **Issue disposition:** Separate-process resource configuration adaptation; resource staging/documentation could improve. The SQL file exists and application-side resource loading is verified separately, but this does not establish a contract that the Test Resources server shares the application's classpath.

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
- **Later source change:** PORT-044 supersedes the historical three-field vet contract. Current vet DTOs include specialities/ETags; do not restore the older projection as a fix. The captured fixture is retained for the older comparison, not a complete current vet response specification.

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
- **Resolution (2026-10-27):** New migrations correct the five exact stock pet records and remove only the four Oracle visits matching all original ID/pet/date/description values. Existing migration files and checksums remain unchanged. Direct interval tests now read exactly the reference's Samantha history; date assertions run on every profile.
- **Additional source comparison:** The original seed pet dates were copied to the other profiles and differed from `system/DataLoader.java` for these five records. The new migrations apply these corrections; the sample-data configuration/lifecycle issue remains separately open as PORT-042.

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

During the expanded 2026-10-27 review, the final H2 XML contained **121 child cases / 20 actual skips**, while the suite attributes reported **`tests="81"` and `skipped="0"`**. Parameterized child cases also share their function name rather than retaining unique parameter IDs. The report uses child results and CLI summaries, not those suite attributes.

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
| Remaining fixture audit | Pet dates and legacy Oracle visits are corrected (PORT-036); compare other canonical fields if further parity work is requested | Compare complete records, not only filtered searches; preserve applied checksums and user-created data |
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

## Previous verification checkpoint (2026-10-16)

2026-10-16 stabilization rerun: **26 integration tests passed in 49.8s** against the cached Oracle image after removing the unfinished fixture-loader experiment. The cases include ordinary PetClinic workflows, captured Java-reference vet/owner-search JSON contracts, spatial queries, catalog upserts, visit bounds, locale switching, HTML 404s, ranked vectors, nested duality updates, date/null validation, insert/delete restrictions, stale ETAGs after document and relational edits, and JSON not-found responses.

Priority checks additionally establish regular commit, taken/missing/reset responses, actual overlapping LOW/HIGH HTTP requests with an independent probe observing LOW's Oracle row lock before HIGH, emergency commit with LOW priority rollback, outcome classification, and an actual equal-priority `FOR UPDATE WAIT 10` timeout. Database configuration is applied automatically by the container initializer; no privileged test setup remains.

The latest suite additionally verifies all-pet and visit/vet/speciality ID lookups, enriched veterinarian service results, speciality join lookup, and a create/look-up/delete facade workflow for an owner, pet and visit. The cache check mutates a vet row through independent JDBC, observes the cached old value through JSON, HTML and the service, invalidates the cache, and observes the new value before restoring the row. Six asynchronous HTTP catalog updates preserve the original identity and a single complete submitted row.

Additional profile results: **H2 16 passed / 10 Oracle-only skips (16.7s)**; **PostgreSQL 16 passed / 10 skips (20.1s)**; **MySQL 16 passed / 10 skips (24.9s)**. Database-product checks confirm each actual driver, and Oracle-only routes/services are absent on the other profiles. Each uses the same shared spatial, catalog, CRUD, caching and localization checks. Final stabilization reports and command logs are preserved under `__pyronaut__/reports/stabilization/`; earlier reports remain under `__pyronaut__/reports/database-profiles/`. Counts use child test elements because of PORT-040. All four final suites have zero failures/errors.

Python source and TOML parsing and `git diff --check` also pass. Experimental loader code, lifecycle tests and unapplied experimental migration files were removed from both the repository and the isolated test copy. Original applied Oracle migration files and the user's staged `.gitignore` change were preserved. No new local image pulls, external issue filings or remote CI runs were performed.

Interactive browser parity, concurrent insertion of an absent clinic/code, fixture/sample-data lifecycle alignment, remaining model/service/repository and HTTP failure-path fidelity checks, production URL fallback execution, and packaged execution remain outside this checkpoint. SDK configuration validation was skipped. Full reference parity is not claimed; further implementation is deferred at the user's request.

## Findings from the 2026-10-26/27 review

### PORT-044 — Current reference vet CRUD/ETag contracts were missing

- **Observed:** The local reference at `0ad5747` includes veterinarian and speciality CRUD, assignment hashes, generated row ETags, forms and JSON precondition failures. The older port exposed only vet listing and its historical three-field JSON projection.
- **Resolution:** Port the generated ETag model, native/profile-local database functions, transactional CRUD, speciality management, current DTOs, templates, source JavaScript and exception responses. Hashes cover sorted speciality IDs and exclude names. Rejected stale updates/deletes restore join rows through transaction rollback.
- **Evidence:** Functionality modules cover lifecycle, assignment-only changes, shared speciality preservation, no-op saves, missing/blank/weak/stale tags, duplicates, malformed JSON, missing resources and text limits. Final profile counts are recorded below.
- **Disposition:** Resolved application feature gap. It is not an upstream Pyronaut defect. A Python method initially named `new` also failed JVM generation because it is a Java keyword; the route implementation is now named `new_vet`.

### PORT-045 — Nullable collection elements cross the boundary as zero or foreign nulls

- **Observed:** `specialityIds: list[int | None] | None` bound `[null]` as a value that produced the unknown-ID error rather than the source's missing-ID error. An explicit Java `Integer` type did not correct that conversion. Binding as an object collection preserved a `ForeignNone` value, whose identity differs from Python `None`.
- **Impact:** A straightforward DTO translation can lose null semantics. Converting arbitrary object inputs to a set before type validation can also fail on nested arrays/maps.
- **Workaround:** Bind the collection at the object boundary, check Python/foreign nulls directly, reject non-integer/boolean/out-of-range values before set construction, then resolve distinct persisted IDs. Preserve the source's 400 messages. HTTP tests cover null elements, null/empty selections, nested values and the integer boundary.
- **Disposition:** SDK null/collection conversion candidate. Reduce with one nullable collection DTO before assigning ownership or filing. Explicit validation is an application adaptation.

### PORT-046 — Generated PostgreSQL ETag expression does not quote mapped identifiers

- **Observed:** H2 and Oracle ETag CRUD worked. PostgreSQL then failed 24 shared checks with `ERROR: column vet_.first_name does not exist`. The mapped columns are quoted uppercase names; the synthesized ETag read expression references their unquoted names, which PostgreSQL folds to lowercase.
- **Resolution:** `db/postgres/V5__etag_identifier_aliases.sql` adds computed lowercase aliases for first name, last name and the speciality hash. They derive from the canonical columns and cannot be independently changed. The ORM still generates and enforces the ETag predicate; no Python compare-then-write replacement was introduced.
- **Evidence:** The first corrected PostgreSQL run passed all 84 then-current shared cases, including stale link rollback; final coverage is recorded below. Initial failures are preserved under `__pyronaut__/reports/review-20261026/postgres-initial/`.
- **Disposition:** Micronaut Data generated ETag transformer/identifier quoting candidate. Reduce on both Java and Python before claiming it is Python-specific.

### PORT-047 — MySQL cannot create the ETag routine with ordinary fixture privileges

- **Observed:** Migration `V4__vet_etags.sql` failed with MySQL error 1419: binary logging was enabled and the fixture user did not have SUPER privilege. Most suite failures were consequences of that one application-startup failure.
- **Resolution:** Set the local Test Resources container command to `--log-bin-trust-function-creators=1`, then create the deterministic routine through the migration. The application user was not granted SUPER. The cached `mysql:8.4.5` image was reused.
- **Evidence:** After this configuration change, all 94 then-current shared MySQL cases passed. Final counts include additional direct repository and text-limit checks.
- **External databases:** DBA provisioning or appropriate routine-creation settings/privileges remain a deployment prerequisite. The local container command does not configure an existing production server.
- **Disposition:** Database provisioning requirement; no SDK defect established.

### PORT-048 — Valid text at the API limit exceeds schema storage limits

- **Observed:** The catalog form permits 500 characters while the new H2/PostgreSQL/MySQL schemas used `VARCHAR(255)` descriptions. A real H2 request containing 500 `ñ` characters returned 500; the trace reports `DESCRIPTION CHARACTER VARYING(255)` and SQL state 22001. Oracle vet names/descriptions also used byte lengths although bean validation measures characters.
- **Resolution:** Add new migrations widening non-Oracle descriptions to 500 characters and making the Oracle name/description limits explicit in character semantics. Original migrations are unchanged.
- **Regression:** Round-trip 500-character Unicode descriptions and 255-character Unicode vet/speciality names. Reject a 501-character description and names exceeding the DTO limit. Initial failing artifacts are preserved under `__pyronaut__/reports/review-20261026/text-limits-before/`.
- **Disposition:** Resolved application schema/validation mismatch.

### PORT-049 — The service test assumed visit ID 1 survived canonical fixture alignment

- **Observed:** The first expanded Oracle run passed the ETag, document and priority checks, but the service lookup test dereferenced a missing visit at ID 1. That ID belonged to an exact legacy seed row removed by the guarded correction.
- **Resolution:** Obtain an existing seeded visit through `find_visits_by_pet_id` and use its actual ID for the lookup assertion. A focused Oracle run passed; the full suite repeats it.
- **Disposition:** Resolved test-fixture assumption, not an application or upstream defect.

### PORT-050 — Enum name access and transaction boundaries differ in direct repository tests

- **Observed:** An appointment loaded through the SDK exposes a Python enum, while a Java enum constant/mirror can expose its name as a string property or callable accessor. Direct equality across those representations failed despite persisted status values being correct.
- **Resolution:** Normalize both enum representations using the value/name, calling the name only when callable. The direct appointment tests cover availability ordering, updating existing rows without extra inserts, and booked-row lookup.
- **Separate test correction:** The source `@MicronautTest` supplies a write transaction. The Python HTTP fixture intentionally does not wrap the suite in one. MySQL correctly rejected `SELECT ... FOR UPDATE` in the automatically opened read-only query transaction. The locking regression now supplies the source's write boundary explicitly; production priority methods already run in write transactions.
- **Disposition:** Resolved interop/test adaptation. No application locking defect or upstream defect is established by the read-only test failure.

## Latest verification checkpoint

The final 2026-10-27 runs collected 121 cases per profile, with zero failures/errors:

| Profile | Passed | Expected skips |
| --- | ---: | ---: |
| H2 | 101 | 20 Oracle-only cases |
| Oracle | 120 | 1 H2-only case |
| PostgreSQL | 100 | 20 Oracle-only and 1 H2-only case |
| MySQL | 100 | 20 Oracle-only and 1 H2-only case |

Configuration validation is enabled with the single documented Test Resources suppression. Core sample-data lifecycle parity, model/helper equivalence, concurrent first catalog insertion, browser behavior, packaged execution and remote CI remain outside this checkpoint. No external issues or remote pushes were created.
