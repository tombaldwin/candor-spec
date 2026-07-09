# Soundness log — the adversarial rounds and κ batches, in full

The append-only evidence scroll behind [SOUNDNESS.md](SOUNDNESS.md). The tracker keeps the
*instrument* (scorecard, residual register, metrics, index); this file keeps the *prose* — one entry
per adversarial round / κ batch / review patch, with the find, the why, the fix, and the gates. Newest
entries append at the end; the index table in SOUNDNESS.md §8 is the one-line-per-entry view.

## 8.1 Java adversarial round (2026-06-20, candor-java 0.7.8 `@d6927ff`)

A fresh Java-only soundness pass, run AFTER this session's structural changes (LB-1b thread-local
re-entrancy, `--parallel`, the GraalVM native-image + JDK-supertype index, and the `ctx()` hoists) — to
confirm none of them opened a silent gap. Two halves, both clean:

- **Synthetic adversarial sweep — no cardinal sins.** ~55 fixtures across 5 mechanism families, each an
  effect delivered via a mechanism that might slip past bytecode/CHA/κ. Every one was correctly attributed,
  honestly `Unknown` (with a precise `unknownWhy`), or honestly `invisible` — never silent-pure. Families +
  hard cases that resolved correctly: (a) dynamic invocation — MethodHandle/VarHandle/Proxy/asType/bindTo →
  honest `Unknown`; reflective-LITERAL name → `Net` (resolved); (b) modern concurrency — virtual threads,
  `newVirtualThreadPerTaskExecutor`, `CompletableFuture.supplyAsync`, parallel streams, ForkJoinPool,
  `StructuredTaskScope` (lambda effects attributed at the CREATION site); field-Runnable→`new Thread(r)`
  honestly degrades to `Unknown:task-handoff`; (c) foreign/native/process — a `native`-declared callee →
  `Unknown:native`, Panama FFM downcall → `Unknown`, all `Runtime.exec`/`ProcessBuilder`/`System.load`
  variants → `Exec`, `FileChannel.map` → `Fs`; (d) control-flow-hidden + structural — catch-only,
  finally-only (incl. nested in a switch), transitive `<clinit>`, enum-constant dispatch, sealed-record
  dispatch, default-interface-method, record compact-ctor, try-with-resources implicit `close`, CHA on an
  interface with no in-project instantiation, assert-guarded (present in bytecode); (e) newer I/O & SPI —
  JDK11 `HttpClient` send/sendAsync → `Net`, async `FileChannel`/`SocketChannel`, `Files.lines/walk` → `Fs`,
  `ServiceLoader` impl effect surfaced via the `calls` edge, `ScriptEngine.eval` → honest `Unknown`,
  `DriverManager.getConnection` → `Db`, `URL.openStream` → `Net`.
- **Real-jar dogfood — sound + honest** on three libraries never tested before: commons-net 3.11.1
  (725 fns, Net-dominant — correct for a network lib), jedis 5.2.0 (4646 fns, Net + honest Unknown smear),
  postgresql 42.7.4 (2188 fns, Fs/Net/Db/Env — correct for a JDBC driver). Effects land where expected;
  every gap is DISCLOSED (`invisible` κ-floor or `Unknown`), none silent. κ-coverage leads surfaced as
  honest `invisible` (NOT sins, the floor working): `resilience4j.*`, `commons-pool2.impl`, `org.ietf.jgss`,
  `waffle.windows.auth`, `org.osgi.framework`, `org.xml.sax` — all optional third-party / config namespaces.
- **`org.xml.sax` lead investigated → no missed I/O.** `DocumentBuilder`/`SAXParser`/`XMLReader.parse` and
  `Transformer.transform` are ALREADY classified `Unknown` (Classifier.java ~68-71 — the sound disclosure of
  an XML-parse-from-systemId, also the XXE/SSRF sink). The residual `org.xml.sax` `invisible` is only the
  pure factory/config members (`XMLReaderFactory.createXMLReader`, `InputSource`, `setFeature`); postgresql's
  use is in-memory/caller-visible. No κ rule added — that would be coverage-chasing pure calls against the
  "model specific effectful members for precision, not chase coverage" principle.

- **Strongest tier — runtime ground truth (DONE, not a TODO).** Java already has a dynamic oracle (better
  than the Rust strace harness: it has per-method STACK TRACES and runs on macOS, being JVM-level not an OS
  tracer): `soundness/dynamic/` = a JFR oracle (`jfr_diff.py`, Fs/Net via `jdk.{File,Socket}{Read,Write}`
  events) + a bytecode leaf-instrumenting agent (`agent/`, Exec/Db/Env/Clock/Rand/Log) + `corpus.sh` that
  runs both over a corpus and fails on any runtime-observed effect candor's static report neither predicts
  nor discloses. RAN it this round: extended the corpus with `async-netfs` (real loopback Net in a VIRTUAL
  THREAD + real Fs in a CompletableFuture + a parallel stream) and `async-exec` (real `/bin/echo` Exec via a
  Thread and a CompletableFuture). Result: **7 entries CLEAN, 0 NEW model gaps** — the kernel/JVM actually
  saw the Net/Fs/Exec and candor predicted every one, so the lambda/task effect attribution the synthetic
  sweep checked statically is now confirmed against RUNTIME ground truth. The lone gap is the documented,
  allowlisted abstract-`java.io.Reader` boundary (a `parse(Reader)` whose concrete `FileReader` is only
  known at the caller) — accepted, not a regression.

Net: the cardinal-sin floor held on Java across synthetic, real-world, AND runtime-ground-truth inputs,
including over all of this session's new code paths (byte-identity + the native-vs-jar parity gate prove
those produce identical reports). The standard MECHANISM families are covered (the synthetic/runtime axes
find-rate 0), and what candor can't resolve it discloses. NB the earlier "κ veins mined out" phrasing was
about mechanism coverage on the tested corpus — LIBRARY/framework κ-coverage is NOT exhausted: dogfooding a
new framework still surfaces unmodeled effectful members (disclosed `invisible`, never silent), e.g. §8.3's
Hibernate-6/Jakarta-Data vein found on a Quarkus app. Evidence ladder, all three tiers now
exercised: synthetic = controlled (known effect → checked report); dogfood = real-world breadth; JFR+agent
corpus = runtime ground truth (the strongest, which catches even a shared blind spot). Remaining oracle
growth = more corpus programs / effects, not a missing capability.

## 8.2 Cross-language adversarial round (2026-06-21, candor-java)

Every prior sweep used JAVA fixtures; candor analyzes BYTECODE from any JVM language, so the
under-explored axis is whether language-specific effect-delivery (which compiles to bytecode shapes a
Java-centric analyzer never saw in a Java fixture) slips the floor. Swept all three claimed languages —
**no cardinal sin in any**:

- **Kotlin (kotlinc 2.4.0) — precise.** The existing lane (`soundness/run_kotlin.sh`, 16 forms) passed;
  then an ADVERSARIAL sweep of 22 more mechanisms all attributed the threaded `Net` leaf: stdlib —
  `lazy{}`, `sequence{}` (a lazy-iterator coroutine), the scope functions (let/run/apply/also/with),
  inline + non-inline HOFs, `object :` expressions, `companion object { init }`, custom delegated
  properties (`by`), the `invoke` operator, extension functions, receiver-HOFs; and **coroutines**
  (kotlinx-coroutines 1.9.0) — `runBlocking`, `launch`, `async`, `withContext(Dispatchers.IO)`, a
  `suspend` chain `s1→s2→leaf` (each suspend fn individually got `Net`, traced THROUGH the CPS
  state-machine bytecode), and `Flow { … }.collect`. Kotlin's hardest shapes (CPS continuations,
  synthetic SuspendLambda classes, lazy iterators) all trace soundly.
- **Groovy (groovyc) — honest Unknown.** Dynamic dispatch (the default) compiles every call — even
  `new Socket(...)` — to a runtime callsite, so candor cannot statically see the type → it discloses
  `Unknown` for `leaf`/`viaDynamic`/`viaClosure`/`viaEach`/`viaCompileStatic`. Never silent-pure: the
  sound floor for a genuinely-dynamic language is exactly Unknown (a precision limit inherent to Groovy,
  not a soundness gap).

Verdict: candor's bytecode analysis is language-shape-robust — PRECISE where the bytecode is statically
resolvable (Java, Kotlin incl. coroutines), HONEST `Unknown` where it's genuinely dynamic (Groovy). The
cardinal-sin floor holds across the JVM-language surface, not just Java. Find-rate on this NEW axis = 0.

## 8.3 Real-app dogfood → κ batch 24 (Hibernate-6 / Jakarta Data, 2026-06-21, candor-java 0.7.9 `ed231ed`)

The Bet-1 case-study work ran candor on five real third-party JVM projects (two Spring apps, a Kotlin app,
a Quarkus app, the gson library). Four resolved cleanly. The Quarkus **Hibernate ORM / Jakarta Data
quickstart** (deliberately non-Spring) exposed a κ-COVERAGE gap — correctly DISCLOSED, not a cardinal sin:
its `FruitResource` endpoints read `inferred=[]` + `invisible=[org.hibernate, org.hibernate.query, …]` with
the κ receipt naming the packages + call counts. candor modeled the classic `org.hibernate.Session`/`Query`
API and `jakarta.persistence.*`, but NOT the Hibernate-6 / Jakarta-Data generation the quickstart's
generated repositories drive (`StatelessSession`, the split `SelectionQuery`/`MutationQuery`, the
`jakarta.data.repository.*` pattern). So `Db` never landed — the persistence was honestly `invisible`
(κ-floor working), but the architecture gate couldn't see it.

**Mined (precise, verb-gated; terminals → Db, builders stay pure):** `StatelessSession` CRUD terminals
(insert/update/upsert/delete +*Multiple, get/getMultiple/getIdentifier/refresh/fetch); `SelectionQuery`
result terminals + `MutationQuery.executeUpdate`; and `isJakartaDataRepoBase` promoting project interfaces
extending `jakarta.data.repository.*Repository` into `repoTypes` (mirrors `isSpringDataRepoBase`).
DELIBERATELY did NOT κ-cover `org.hibernate.query.criteria`/`.specification` — those pure AST builders stay
honestly `invisible` (the κ discipline: model the effectful member, never blanket a namespace silent-pure),
so the post-fix Quarkus report still discloses them. Gates: byte-identity IDENTICAL on pc/jsoup/gson;
`./gradlew test` green; `soundness/run.sh` 40/0 + all probes OK; `kappa_libs_probe` +4 Db terminal anchors
+1 builder-purity anti-fab anchor (442 leaves / 164 pure neighbours). Quarkus: `Db` lands on all five
endpoints, 100% contained.

Lesson for this tracker: the synthetic/runtime find-rate-0 measures MECHANISM soundness (does an effect
delivered via shape X get attributed); it does NOT measure LIBRARY κ-completeness (is every effectful member
of every framework enumerated). The latter is open-ended and best driven by dogfooding real apps — each new
framework can surface a vein, always disclosed `invisible` first (never silent), then optionally mined for
precision. Hibernate was the dominant-ORM instance; the same loop applies to the next unmodeled framework.

**κ batch 25 — Quarkus Panache → Db (2026-06-21, candor-java post-0.7.9 `cf359ce`). A genuine SILENT-PURE
cardinal sin, NOT just an `invisible` gap.** Continuing the dogfood thread to Quarkus's *other* (and dominant)
persistence — Panache active-record (`Fruit.listAll()`, `f.persist()`) + `PanacheRepository` — found it read
SILENT-PURE (the methods were ABSENT from the report, no `invisible`, no `Unknown`), so the architecture gate
was blind to ALL DB access in a Panache app. Why silent (vs Jakarta Data's honest `invisible`): the call-site
owner is the PROJECT entity/repo (`Fruit.listAll()` emits owner `app/Fruit`), not an external package — so the
κ-floor invisible disclosure (which fires on EXTERNAL owners) never triggered, and CHA found no project body →
dropped to pure. This is the dangerous shape: an inherited-from-unmodeled-external method called via a project
subtype receiver. MINED: repository promotion (isPanacheRepoBase → repoTypes), active-record call-site rule
(PANACHE_ENTITY_VERBS + `extendsPanacheEntity` via transSupers, with the no-fabrication override guard), and
PanacheQuery terminals (classify). Verb+hierarchy-gated → a lookalike non-Panache class stays pure (fab probe
OK). Gated: byte-identity pc/jsoup/gson, full suite, soundness 40/0, conformance. LESSON: the "always disclosed
`invisible` first" claim above has an EXCEPTION — when the unmodeled-framework method is INHERITED into a
project type (so the call owner is a project class), it reads silent-pure, not invisible. That shape is the one
to watch when dogfooding the next framework (active-record / base-class-mixin APIs, not just repository/builder
APIs whose calls keep an external owner).

**κ batch 26 — the inherited-into-project vein class swept (2026-06-21, candor-java post-0.7.9 `32229da`).**
Rather than wait for the next framework, probed the persistence ecosystem for batch 25's shape directly (an
external stub base + a project subtype + the inherited call, scan only the project). Spring Data was the
passing CONTROL (Db); MyBatis mapper interfaces correctly disclose `Unknown` (not a vein). FOUR more confirmed
SILENT-PURE and mined: **Micronaut Data** (repository — `isMicronautDataRepoBase` → repoTypes promotion),
**Ebean** (`io.ebean.Model`), **ActiveJDBC** (`org.javalite.activejdbc.Model`), **jOOQ** (`org.jooq.impl.DAOImpl`)
— the latter three via a new `AR_DB_BASES` registry (base internal name → its DB verb set) + `inheritsArDbVerb`
(checks owner + supertypes; per-base verb gating; the no-fab override guard). Verb+hierarchy-gated, fab probe
OK (lookalike non-framework save()/findAll() stays pure). So the inherited-into-project shape is now covered
for the major JVM persistence frameworks (Spring/Jakarta Data/Panache/Micronaut Data repositories +
Hibernate/JPA + Panache/Ebean/ActiveJDBC active-record + jOOQ DAO). The general METHOD (external-stub probe of
any base-class API) is the reusable instrument for the next framework.

**κ batch 27 — the inherited-into-project vein, GENERAL fix for classify-MODELED bases (2026-06-21, candor-java
post-0.7.9 `7421301`).** Batches 24–26 covered bases candor does NOT model at the leaf (via repoTypes/AR_DB_BASES
registries). The complementary case: a project class subclasses a base candor DOES model at the leaf, and calls
an inherited method — still silent-pure, because the call owner is the project subclass (no rule) and classify
was never re-tried against the external supertype. Found via Testcontainers (`class MyContainer extends
GenericContainer` then `c.start()` read pure though `GenericContainer.start` is modeled Exec); also hits
non-test cases (`extends java.io.FileInputStream` → inherited `read()`). FIX (Candor.analyze, classify site):
when classify(owner) is null AND owner is a project class with no concrete body of its own (not overridden) and
no project super provides one, re-run classify against each EXTERNAL supertype — the exact method the JVM
dispatches to. No new fabrication (classify already vouches for the external leaf; an override wins). Byte-identity
HELD on pc/jsoup/gson (the broad fix fires only on the narrow subclass-a-modeled-type shape). NON-SIN finding
recorded for completeness: declared-on-interface HTTP clients (Retrofit `@GET`, Micronaut `@Client`) read
`Unknown` (DISCLOSED, not silent) — a precision opportunity (model → Net like Feign), NOT a cardinal sin.
**Status: the inherited-into-project silent-pure vein CLASS is now closed** across modeled + unmodeled bases.

**κ batch 28 — the LEGACY-ENTERPRISE frontier (2026-07-06, candor-java post-0.8.2 `aefca4f`): JCL /
Joda-Time / commons-lang3 / hibernate.criterion / Struts 1.x.** Found by dogfooding a real 2,257-class
Struts webapp whose κ ledger listed 81 packages — dominated by struts (5,502 calls), commons-lang3 (2,141),
commons-logging (791), hibernate.criterion (586), joda-time (249): the pre-Spring enterprise stack, still
everywhere, previously entirely INVISIBLE-floored. METHOD (reusable): extract the app's COMPLETE per-member
call surface into the candidate namespaces from bytecode (`javap -c | grep 'Method org/apache/…'` →
`sort | uniq -c`) and triage every member — 169 distinct members, of which only ~6 were effectful. Those
six are classified verb-precisely (commons-logging emit verbs → Log — on the dogfood app this UNMASKED
855 fns of logging, 756 → 1,611; Joda's now-family → Clock with the no-arg instant ctors
DESCRIPTOR-gated so `new DateTime(long)` stays a pure value ctor; lang3's RandomStringUtils/RandomUtils →
Rand and SystemProperties/SystemUtils getters → Env; Struts `TagUtils.write/print` → Net — tag output is
the client socket, the ServletResponse stance — and `FormFile` content reads → Fs, the spooled multipart
temp file); the verified-pure remainder floors under KAPPA_COVERED_PREFIXES. Boundary discipline:
`org.hibernate.criterion` (pure builders) is covered because execution lives on the already-classified
Session/Query terminals, but `org.hibernate` BROADLY stays ledgered — coverage is only granted where the
effectful surface is modeled or the namespace's inventory is verified pure. Gates: anti-fabrication twins
per package (KappaBatch28Test), jsoup/gson byte-IDENTICAL vs the released jar; a Spring app's report
legitimately GAINS Log lines (spring-jcl provides org.apache.commons.logging) — unmasking, not regression.

**The same dogfood also validated the full Unknown-reduction ladder on a real legacy app** (the workflow
the `blindspots` query was built for): (1) blindspots ranked ONE dispatch — a project interface with 42
enum implementors, past the shared CHA-12 bound — as the source of 3,551 of 3,617 Unknowns; `closed-world`
(§3.4 config, sound for an application) resolved it → 153. (2) Batch 28 converted the invisible floor to
real attributions (ledger 81 → 64 packages, every giant cleared). (3) Chaining a first-party library's own
report (§2 `deps`) covered its 236 calls — and RAISED disclosed Unknown to 680, correctly: the library's
reflective plugin registries (`Constructor.newInstance`) are irreducible, and calls that previously read
silent-invisible now read honest-Unknown. More honesty, not less precision — the direction the trust
contract orders these. Residual ledger heads (commons-validator 95, threeten-extra 61, jsonwebtoken 31)
are future batch candidates.

**κ batch 29 — the next tier, same discipline (2026-07-06, candor-java `2575683`).** The dogfood app's
complete 68-member frontier into the residual heads, triaged member-by-member. Pure-surface coverage:
commons-validator (predicates), commons-beanutils (property shuffling), displaytag (decorator getters),
org.w3c.dom (a JDK namespace missing from the frontier list). Precise effectful members: threeten-extra
now() → Clock; jjwt parse* → Clock (parsing VALIDATES exp/nbf against the system clock) + Keys generators
→ Rand, while signing/compact stays pure CPU; JDOM2 input effectful BY SOURCE (build(File/String) → Fs,
build(URL) → Net, caller-opened stream overloads pure-relative — the open carried the effect); Ehcache at
its ACQUISITION points (persistence(dir) → Fs so build/init are vouched and heap-only apps never
fabricate; clustered cluster(URI) → Net). A coverage-semantics finding worth registering: vouching
org.w3c.dom made 438 jsoup fns DROP from its report — their only content was `invisible: [org.w3c.dom]`
(zero effect changes, verified per-fn) — i.e. a widely-reachable uncovered namespace can inflate a report
with disclosure noise, and coverage legitimately shrinks it. Dogfood trajectory across batches 28+29:
ledger 81 → 64 → 49 packages; the top head fell from 5,502 calls (struts) to 25 (jackson-databind — the
one broadly-valuable batch-30 candidate; the rest is long tail).

**κ batch 30 + 30b (2026-07-06, candor-java `cd617cb`): Jackson, and a live SILENT-NET find in the
existing AWS coverage.** Jackson yields to ONE descriptor-driven rule (a File/Path parameter is a source or
sink → Fs; a URL → Net — uniform across the stack; String/bytes/stream overloads pure-relative). The
important entry is 30b: the AWS rule's `owner.endsWith("Client")` gate missed calls through the v1 service
INTERFACES (`AmazonS3.copyObject` — a real S3 request — read silent-invisible on the dogfood app; `copy*`
was also missing from the verb list). The request-making surface is now the Client classes + the
Amazon*/AWS* interfaces (outside .model./Builder) + TransferManager. Unmasked Net 473 → 534 on the dogfood
app. LESSON for the register: a curated rule's OWNER GATE is itself a soundness surface — verify coverage
against how code actually types its variables (interfaces), not just the concrete classes. Dogfood ledger
after batches 28–30b: 81 → 37 packages, everything remaining ≤ 20 calls (long tail).

**κ batch 31 (2026-07-07, candor-java `17eb81d`): the long-tail sweep — the dogfood app's ledger reaches
ZERO (81 → 0 across batches 28–31).** All 37 remaining packages, 111 members triaged. Register-worthy
findings beyond the coverage itself: (1) **the sweep audits earlier batches** — StopWatch (both
commons-lang generations) reads the clock but went silent-pure under batch 28's lang3 coverage; a
covered namespace must be RE-swept when new inventory arrives. (2) **A return-type fabrication class**:
the source/sink descriptor rules (File/Path → Fs, URL → Net) first used whole-descriptor `contains`,
which matches a File RETURN type — `FileUtils.getTempDirectory()` (pure, returns a path) would have
fabricated Fs; an existing round-12 anti-fab pin caught it; all descriptor rules now match parameters
only (`paramsOf`). (3) **Iteration can be a wire call**: Twilio's `ResourceSet.iterator()` lazily fetches
further pages — Net hiding in a for-each. (4) **proceed() is reflection-shaped**: AOP Alliance's
`MethodInvocation.proceed()` executes the intercepted target → disclosed Unknown, never silenced by
coverage. (5) **Defer to richer existing stances**: a new Fs rule for `XMLReader.parse` was dead code
below the pre-existing disclosed-Unknown rule (parse drives user handler callbacks + XXE-class
resolution) — check what already classifies before adding. Also: Redisson's R* handles → Db (remote data
structures by design), DbUnit execute → Db, hibernate's internal jdbc package covered WITH its effectful
internals classified so the one pure member apps reach (the SQL formatter, 685 fns of invisible noise)
floors clean.

**REVIEW PATCH — candor-java 0.8.4 (2026-07-08, `4bdb996`): six soundness regressions the batch 28–31
work SHIPPED in 0.8.3, caught by a high-effort code review.** The same sweep that CLOSED veins opened new
ones, via two failure shapes the inventory method doesn't catch alone. (1) **Broad owner/verb gates
fabricate on same-shaped pure members** — the AWS `Amazon*`-name interface heuristic hit `AmazonS3URI` (a
pure URI parser), "any Redisson R* → Db" hit `getCodec`/`RFuture`, `parse*`→Clock hit the no-arg
`Jwts.parser()` factory, whole-owner StopWatch→Clock hit `create()`. LESSON: a name/prefix owner gate or a
bare verb prefix fabricates wherever a namespace mixes request-makers with same-named value types —
require the effectful SHAPE (a token arg, an exact verb, a started clock), not the name. (2) **A blanket
coverage grant turns an under-vouched classifier into SILENT-PURE** — `com.amazonaws` coverage silenced
`DynamoDBMapper.save` (unmodeled facade, owner doesn't match the *Client gate). LESSON: only ledger-cover a
namespace whose effectful surface you MODELED, not merely inventoried on one app; an unmodeled member of a
covered namespace floors silent (the worst class) — leave it uncovered and it discloses `invisible`. AWS
and commons-io are now classified-but-not-covered. Every fix carries an anti-fabrication twin; jsoup/gson
byte-identical. The byte-identity + kappa_libs gates only catch what their fixtures exercise — the review
exercised the shapes they didn't.

**CROSS-ENGINE verification — the vein was JAVA-SPECIFIC, NOT a shared blind spot (2026-06-21).** The
tracker's #1 risk is a blind spot SHARED across engines (cross-engine agreement hides it), so after closing
the inherited-into-project vein in candor-java I probed the others for the same shape. RESULT — not shared:
- **candor-ts** (the clearest analog — TS active-record ORMs): `class User extends BaseEntity` (TypeORM) →
  `user.save()`/`User.find()`, and Sequelize `Model.create()` → all read **`Unknown`** (`callback:u.save` etc.),
  DISCLOSED, never silent-pure (control `fs.readFileSync` → Fs confirms the harness). Its AST model treats an
  unresolved method call as `callback:Unknown` — it never CHA-resolves-to-nothing-then-pure.
- **candor-scan (Rust)**: an unresolved external/trait-default method call → **`Unknown`** (`callback:unresolved
  call`). Same safe floor.
- **candor-swift**: structurally N/A — Core Data / SwiftData persist via the *context* (`context.save()`), not
  an effectful method inherited into the entity subclass.
So candor-java was the OUTLIER: its CHA could resolve an inherited-from-unmodeled-external call to no project
body and drop to pure, where the AST/syntactic engines disclose `Unknown`. The dangerous SHARED case does not
exist here. (PRECISION note, not a sin: candor-ts/scan report these as `Unknown` — modeling the ORMs → Db/Net,
the analog of the Java persistence work, would sharpen them, but they are footnote engines and it is not a
cardinal-sin fix.)

**candor-swift κ batch — UserDefaults / Keychain / Bundle (covered-module silent-pure, 2026-07-09,
candor-swift `dd134e2`).** The Panache shape, Swift edition: `Foundation` and `Security` sit in
PLATFORM_MODULES, so they get no ledger naming and no Unknown — an unmodeled effectful member there reads
**silent-pure**, with no invisible/Unknown floor to catch it. Three surfaces were in that state:
(a) `UserDefaults` store accessors (`set/object/string/bool/…(forKey:)`, `removeObject`, `synchronize`,
`register`, persistent-domain ops); (b) the Keychain CRUD free functions
`SecItemAdd/SecItemCopyMatching/SecItemUpdate/SecItemDelete`; (c) `Bundle` resource lookups
(`url/path/urls/paths(forResource:)`). WHY silent not invisible: the covered-module floor discloses only
*unlisted* modules — a covered module vouches for everything, so its gaps are absolute. FIX: all three →
**Fs** (family decision — UserDefaults is the plist-backed file store; SecItem* is the system secure
store, NOT Db, which the family reserves for query-capable datastores; Bundle lookups stat the bundle on
disk). Verb-precise: UserDefaults' volatile-domain surface and Bundle's in-memory metadata
(`bundleIdentifier`, `object(forInfoDictionaryKey:)`) stay pure. Deliberate non-models recorded in the
classifier: NotificationCenter (in-process, no vocabulary effect), CLLocationManager (no vocabulary
match), `UserDefaults(suiteName:)` ctor (access verbs carry the effect). Anti-fabrication rides the
standing shadow discipline (declaredTypes / localFreeFns), pinned by twin fixtures. GATES: smoke 74/74
(+2 sweep assertions incl. shadow twins), 44 XCTests, fuzz 25/25, fabrication probe 28 fns/8 types OK
(new UserDefaults/Bundle pure+ctrl cases), conformance 25/25 + parts 1–13 MATCH. THE DURABLE LESSON
(re-confirmed cross-engine): when auditing a covered module, sweep its *effectful adjacency* —
`Data/String(contentsOf[File]:)` were checked in the same pass and found already covered (Fs /
scheme-resolved / honest Unknown).

**candor-scan κ-ledger §2 rule-3 gap (over-disclosure, fixed scan 0.8.4 `2d32086`, 2026-07-09).** Found
by the new PART 14 chaining differential's FIRST run: the ledger exemption for chained reports was keyed
on the report *filename shape* + per-entry hash prefixes, so an EMPTY chained report (`functions: []` —
the §2 rule-3 purity claim) outside the `….<crate>.scan.json` naming still drew "κ doesn't know N
dependencies". The SAFE direction (over-disclosure, not a silent-pure sin), but a conformance divergence
vs candor-java/ts, which honor the claim. Coverage is now keyed on the envelope `package`/`packages`
field (hyphenated names also register in Rust ident form); pinned by PART 14. Companion porcelain work
in the same wave (register R21): cargo-candor `policy`'s `|| true` fail-open and `guard`'s
absent-baseline green both now exit 2, with a `GUARD-UNAVAILABLE` engine sentinel distinguishing
not-evaluated from violation, and the §3.3 verdict withheld when the guard could not evaluate.

**candor-java mutation_probe rot (meta-soundness, found + fixed 2026-07-09, `a6c60c0`).** The
meta-soundness harness had decayed to 3/14 PATCH-ERROR — its anchors still targeted the pre-typed
(`return "Fs"`) pre-extraction Candor.java. Re-anchored (per-mutation target file, dual
snapshot/restore); the `jackson_file` mutation had additionally become a redundancy NO-OP — κ batch 30's
whole-package descriptor rule subsumes the 0.7-era `readValue` rule, each masking a mutation of the
other — and now disables both. 14/14 caught. LESSON: a mutation suite is itself a κ surface — re-run it
after any refactor that moves rule text; it now runs weekly in CI (`soundness-weekly.yml`, with
kappa_libs). Same commit re-anchored 4 stale kappa_libs PURE anchors (Yaml.load ×3, URLClassLoader ctor
— deliberately Unknown since the RCE-sink batch). Companion structural work, byte-identity-gated: the
~27KB `classify()` method (3.4× HotSpot's DontCompileHugeMethods limit — the hottest path ran
INTERPRETED) split into a first-package-segment dispatch, largest method 4266B; verified by a
19,484,160-triple old-vs-new differential oracle (0 mismatches) + 330-jar corpus byte-identity; ~16%
faster full-corpus scan.

**The coverage wave (2026-07-10) — first-ever measurement, then closing every never-executed gate
surface (TESTING.md's "verify before pin" discipline).** Coverage tooling had never been wired into
any repo; measuring with child-process capture (java three-tier 67%→90% line; swift 61%→88%; ts ~95%;
agents 90%; rust stable crates 81%) surfaced the load-bearing surfaces with ZERO execution anywhere.
Pinning them found four real bugs, each fixed red-then-green in its pinning commit (§8):
(1) **candor-java `checkConformance` (CANDOR_STRICT, AS-EFF-001/002/003) was broken** — it lacked
SPEC §6's program-entry-point exemption from AS-EFF-001, firing on the composition root; the gate had
0% coverage in every harness. Sibling sweep: rust-deep already exempts (`tcx.entry_fn`); ts/swift
don't implement strict. (2) **candor-agents `guard` failed open on unknown flags/extra positionals**
(emitted the settings fragment, exit 0 — now exit 2), and (3) **the positional-swallow class**:
`observe a b` (also stats/savings) silently analyzed `b`. (4) **candor-ts watch had no graceful-quit
path at all** (Ctrl-C = signal death) — which was also why its coverage read 0%. A fifth find needed
a family ruling: **candor-swift captured a Net USE-verb's payload literal as a host**
(`Channel.writeAndFlush("x")` → hosts:["x"]) — java/ts capture only at establishing forms; swift
aligned (`b737b87`, report-affecting: payload "hosts" disappear). Everything else measured was
correct-but-unpinned: rust's `--deps` registry mode and nested-cfg evaluator, swift actors (behave
exactly like classes), the agents §6.2 Exec/Db matchers (full cross-engine parity verified vector-by-
vector before pinning). Suite growth: java 302→~330 JUnit + smoke 373; rust 220+138+35; ts 434 checks
across five suites; swift 100 XCTests + smoke 84; agents 380. Dead code deleted per §6 (java ×2,
swift ReportModel helpers); the one agents candidate KEPT with justification (the identical arm
exists in rust/ts on a documented embedder surface). THE DURABLE LESSON: a documented gate surface
with zero executions is where bugs live unnoticed — four of the ten measured gaps hid one. The
zero-coverage-gate-list invariant (TESTING.md §6) is now the standing guard.
