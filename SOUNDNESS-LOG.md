# Soundness log — the adversarial rounds and κ batches, in full

The append-only evidence scroll behind [SOUNDNESS.md](SOUNDNESS.md). The tracker keeps the
*instrument* (scorecard, residual register, metrics, index); this file keeps the *prose* — one
`### <date> — <slug>` entry per adversarial round / κ batch / review patch, with the find, the why,
the fix, and the gates. Entries sit in chronological order; new ones append at the end. Entry BODIES
are append-only history — corrections are appended, never edited in. The index table in
SOUNDNESS.md §8.1 is the one-line-per-entry view.

### 2026-06-18 — the seam-class era: rounds 1–17, the find-rate narrative

*(Moved here 2026-07-09 from SOUNDNESS.md §6 metric 4, which now keeps only the compressed lede.
Covers 2026-06-18 → 06-21.)*

2026-06-18: 6 seam-class rounds each found ≥1; the 7th (coverage) and 8th (R1 deep
implicit-conversion 6-sub-case probe) each found 0 silent; the 9th (rust-deep
fire-forget/lazy-init/deferred-iterator probe, candor-rust `8bf9c6b`) found 1 — the lazy-init
forcing site read pure (effectful `LazyLock` init charged to the static, never to the forcing fn).
FIXED + gated (ui/deferred_effects.rs); the other two seams were already caught. The 10th (agents
seam battery, candor-agents `755216a`) found 1 — named-delegation narrowing trusted a prompt mention
as proof of the spawn set, silently dropping unmentioned-but-spawnable agents. FIXED
(allowlist→sound, bare-Agent→disclosed Unknown) + gated (test.py). The 11th (rust-deep
`thread_local!` probe) found 1 — R13, a `.with()`-forced thread_local read pure (effect orphaned in
the macro-gen init fn); FIXED same-session (`6010832`) + gated. Rounds 12–13 (rust-deep
derived-Clone/Once/OnceLock-named-init, then compound-assign R6) found 0 — both sound, gated (R6
stale for deep, may hold for scan). The 14th (rust-deep `write!` writer side) found 1 — R14,
`fmt::Write` writer silent-pure; FIXED (`0e4bf50`) + gated. The 15th was a CROSS-ENGINE sweep of R14
+ thread_local against candor-scan: write-fmt was ALSO silent in scan (shared blind spot, FIXED scan
0.5.18 `dabafd0`); thread_local already handled. The 16th extended the sweep to candor-swift:
write-fmt's writer side was ALSO silent there (effectful `TextOutputStream` via
`print(to:)`/`write(to:)`), FIXED swift 0.5.22 `9368311`. Convergence = sustained 0 across diverse
new seams (NOT reached — 16 rounds, ~13 finds, all fixed). KEY LESSON reinforced: a find in one
engine is a SWEEP trigger for ALL — write-fmt's writer side was a SYSTEMIC shared blind spot
(deep+scan+swift), the exact case cross-engine agreement hides. The 17th finished the sweep on
candor-java: the writer side is silent there too (4th engine — R16), but the precise fix needs
receiver→ctor-arg escape provenance (the infra exists; CHA-blanket rejected by candor-java's
precision design) and the idiom is rare, so it's tracked as a low SILENT residual rather than
rushed. SWEEP COMPLETE: write-fmt writer side assessed across ALL engines — silent in 4
(deep/scan/swift/java), FIXED in 3, java tracked (R16). R16 since FIXED (candor-java 0.5.40
`5f86d3e`, constructor-site reentry) — so the write-fmt writer-side class is now closed in ALL 4
engines. Convergence: 17 rounds, ~14 finds, ALL 14 fixed. Also validated on real code: PetClinic
dogfood (the JVM gate works end-to-end, 0 Unknown, caught a real cross-layer smell) + the gson
InetAddress catch.

### 2026-06-18 — rust-deep `thread_local!` force read pure (R13)

*(Register essay moved here 2026-07-09 from the SOUNDNESS.md §5 R13 cell.)*

`thread_local!` force via `KEY.with(...)` read PURE — the effect lives in the macro-generated init
fn, orphaned behind the non-local `LocalKey::with`. FIXED 2026-06-18 (`6010832`): a method call on a
`LocalKey` receiver edges the forcing fn to the local init fn(s) referenced in that thread_local
item's body (intravisit FnDef-ref collector). Sound (pure init → nothing); gated by
ui/thread_local_effects.rs.

### 2026-06-18 — the write-fmt writer side: a systemic shared blind spot (R14 + R16)

*(Register essays moved here 2026-07-09 from the SOUNDNESS.md §5 R14/R16 cells.)*

The WRITER side of formatting read PURE — an effectful custom sink (`fmt::Write`/`io::Write` via
`write!`; Swift `TextOutputStream` via `print(to:)`/`write(to:)`) driven by a non-local format
helper was dropped (distinct from the arg-Display side, which all engines handled). Found in
rust-deep, then a cross-engine SWEEP found the SAME gap silent in **candor-scan** (the user-facing
floor) AND **candor-swift** — the dangerous shared case cross-engine agreement hides. ALL FIXED
2026-06-18 (deep `0e4bf50` HOLE 2c; scan `dabafd0` 0.5.18; swift `9368311` 0.5.22
modelOutputStreamCall). Gated by ui/write_trait.rs (deep), the write_macro test (scan), smoke N4b
(swift). candor-ts has no clean writer-sink idiom (N/A); `thread_local!` was swept in the same pass
— scan handles it (not shared).

The candor-java analog (R16, the 4th engine with the class): a custom effectful
`Appendable`/`Writer` wrapped in a JDK `Formatter`/`PrintWriter` and driven by `format`/`printf`
read PURE. FIXED 2026-06-18 (candor-java 0.5.40 `5f86d3e`) via a CONSTRUCTOR-site reentry: at
`new Formatter(Appendable)` / `new PrintWriter(Writer|OutputStream)` / `new PrintStream(OutputStream)`,
edge the enclosing method to the sink arg's `append`/`write` (new C_APPEND/C_WRITE contracts,
by-name reentryEdge over the arg's declType, same machinery as compareTo). Resolve-or-skip → a std
StringBuilder/FileOutputStream sink contributes nothing. Gated by
ImplicitReentryTest.writerSideCustomSinkCarriesEffect; PetClinic + jsoup/gson/HikariCP dogfoods
byte-for-byte unchanged (no fabrication). So the write-fmt writer-side class is closed in ALL 4
engines (rust deep/scan, swift, java).

### 2026-06-20 — Java adversarial round (candor-java 0.7.8 `@d6927ff`)

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
new framework still surfaces unmodeled effectful members (disclosed `invisible`, never silent), e.g. the
κ batch 24 entry's Hibernate-6/Jakarta-Data vein found on a Quarkus app. Evidence ladder, all three tiers now
exercised: synthetic = controlled (known effect → checked report); dogfood = real-world breadth; JFR+agent
corpus = runtime ground truth (the strongest, which catches even a shared blind spot). Remaining oracle
growth = more corpus programs / effects, not a missing capability.

### 2026-06-21 — cross-language adversarial round (Kotlin / Groovy, candor-java)

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

### 2026-06-21 — real-app dogfood → κ batch 24: Hibernate-6 / Jakarta Data (candor-java 0.7.9 `ed231ed`)

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

### 2026-06-21 — κ batch 25: Quarkus Panache → Db (candor-java post-0.7.9 `cf359ce`)

**A genuine SILENT-PURE cardinal sin, NOT just an `invisible` gap.** Continuing the dogfood thread to
Quarkus's *other* (and dominant) persistence — Panache active-record (`Fruit.listAll()`, `f.persist()`) +
`PanacheRepository` — found it read SILENT-PURE (the methods were ABSENT from the report, no `invisible`,
no `Unknown`), so the architecture gate was blind to ALL DB access in a Panache app. Why silent (vs Jakarta
Data's honest `invisible`): the call-site owner is the PROJECT entity/repo (`Fruit.listAll()` emits owner
`app/Fruit`), not an external package — so the κ-floor invisible disclosure (which fires on EXTERNAL owners)
never triggered, and CHA found no project body → dropped to pure. This is the dangerous shape: an
inherited-from-unmodeled-external method called via a project subtype receiver. MINED: repository promotion
(isPanacheRepoBase → repoTypes), active-record call-site rule (PANACHE_ENTITY_VERBS + `extendsPanacheEntity`
via transSupers, with the no-fabrication override guard), and PanacheQuery terminals (classify).
Verb+hierarchy-gated → a lookalike non-Panache class stays pure (fab probe OK). Gated: byte-identity
pc/jsoup/gson, full suite, soundness 40/0, conformance. LESSON: the "always disclosed `invisible` first"
claim above has an EXCEPTION — when the unmodeled-framework method is INHERITED into a project type (so the
call owner is a project class), it reads silent-pure, not invisible. That shape is the one to watch when
dogfooding the next framework (active-record / base-class-mixin APIs, not just repository/builder APIs whose
calls keep an external owner).

### 2026-06-21 — κ batch 26: the inherited-into-project vein class swept (candor-java post-0.7.9 `32229da`)

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

### 2026-06-21 — κ batch 27: general fix for classify-MODELED bases (candor-java post-0.7.9 `7421301`)

Batches 24–26 covered bases candor does NOT model at the leaf (via repoTypes/AR_DB_BASES
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

### 2026-06-21 — cross-engine verification: the vein was JAVA-SPECIFIC, not a shared blind spot

*(Moved to chronological position 2026-07-09 — it had been appended after the 2026-07-08 review-patch
entry, out of date order.)*

The tracker's #1 risk is a blind spot SHARED across engines (cross-engine agreement hides it), so after closing
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

### 2026-06-21 — java abstract-stream entry-point params (R17)

*(Register essay moved here 2026-07-09 from the SOUNDNESS.md §5 R17 cell.)*

I/O via an ABSTRACT `java.io` stream (`Reader`/`InputStream`/`Writer`/`OutputStream`) whose concrete
impl candor can't pin read PURE, not Unknown — e.g. an entry point
`void onData(InputStream s){ s.readAllBytes(); }` where the framework injects `s`. FIXED 2026-06-21
(provenance-gated, entry-point-scoped). Also the jsoup streaming-parser pattern.

**Fix:** in `analyze`, when a call classifies pure AND is an I/O verb on an abstract `java.io` stream
base (`isAbstractStreamIo`) AND the receiver is the method's OWN param by ProvValue identity
(`isOwnParam`) AND the method is a rooted ENTRY POINT (`ctx.entryPoints`), disclose `Unknown` with
`unknownWhy=dispatch:<owner>.<verb>`. Entry-point gating is what avoids the flood: an internal helper
reading a PASSED stream stays pure (its in-project caller holds the concrete → effect already
attributed at the creation site; the common case stays globally sound, e.g. the `AbstractReaderParse`
corpus fixture's Fs at `main` and jsoup's Net/Fs at `connect`/`parse(File)` are unchanged). Gated by
`R17AbstractStreamTest` (entry-point param read → Unknown; non-entry helper → pure, no flood; concrete
creator → Fs unchanged). PetClinic/jsoup/gson byte-for-byte unchanged; native==jar; soundness 40 +
kappa_libs 438 + conformance green.

RESIDUAL (low, MEASURED 2026-06-21): the TRANSITIVE case — an entry point that PASSES its
abstract-stream param to a helper which reads it — is not covered (would need interprocedural
param-flow). A code-review worried this might be the COMMON framework shape; MEASURED across 6 real
jars incl **spring-web** (4196 fns / 129 entry points): **0 rooted entry points take an
abstract-`java.io`-stream param at all, and R17 fires 0 times** — so both the direct and transitive
cases are genuinely rare. The real framework shape is `request.getInputStream().read()` (stream from a
getter INSIDE the method), NOT an `InputStream` param — a SEPARATE getter-return-abstract-stream
question R17 doesn't address (receiver is a call-return, not a param). PROBED 2026-06-21 → SOUND, no
cardinal sin: (i) JDK I/O types — `Socket`/`URLConnection`/`Process`/`HttpExchange` getters classify to
the precise effect (Net/Exec) even when the object is a PARAM (the getter itself is modelled, not just
the creation); (ii) framework interface types — `HttpServletRequest.getInputStream`/`getReader`, Spring
`HttpInputMessage.getBody` disclose `Unknown` via candor's GENERAL unresolved-interface dispatch (no
in-scope impl → the getter call itself is `dispatch:<iface>.<method>` Unknown, before any read); (iii)
in-memory concrete (`ByteArrayInputStream`) stays pure — no flood. So the getter-return shape needs no
fix; R17's narrow surface is the only place this class isn't already covered by precise-effect or
unresolved-dispatch disclosure. So the deeper param-taint fix is NOT warranted for this empty surface.
(#3 reviewed too: the `dispatch:` kind is spec-CANONICAL here — SPEC.md §4 defines
`dispatch:<type>.<method>` as "an abstraction with no visible impl", exactly R17's
abstract-stream-with-unknown-concrete; a new kind would break the 4-kind vocabulary for a 0-occurrence
case, so unchanged.)

### 2026-07-06 — κ batch 28: the legacy-enterprise frontier (candor-java post-0.8.2 `aefca4f`)

**JCL / Joda-Time / commons-lang3 / hibernate.criterion / Struts 1.x.** Found by dogfooding a real
2,257-class Struts webapp whose κ ledger listed 81 packages — dominated by struts (5,502 calls),
commons-lang3 (2,141), commons-logging (791), hibernate.criterion (586), joda-time (249): the pre-Spring
enterprise stack, still everywhere, previously entirely INVISIBLE-floored. METHOD (reusable): extract the
app's COMPLETE per-member call surface into the candidate namespaces from bytecode
(`javap -c | grep 'Method org/apache/…'` → `sort | uniq -c`) and triage every member — 169 distinct
members, of which only ~6 were effectful. Those six are classified verb-precisely (commons-logging emit
verbs → Log — on the dogfood app this UNMASKED 855 fns of logging, 756 → 1,611; Joda's now-family → Clock
with the no-arg instant ctors DESCRIPTOR-gated so `new DateTime(long)` stays a pure value ctor; lang3's
RandomStringUtils/RandomUtils → Rand and SystemProperties/SystemUtils getters → Env; Struts
`TagUtils.write/print` → Net — tag output is the client socket, the ServletResponse stance — and
`FormFile` content reads → Fs, the spooled multipart temp file); the verified-pure remainder floors under
KAPPA_COVERED_PREFIXES. Boundary discipline: `org.hibernate.criterion` (pure builders) is covered because
execution lives on the already-classified Session/Query terminals, but `org.hibernate` BROADLY stays
ledgered — coverage is only granted where the effectful surface is modeled or the namespace's inventory is
verified pure. Gates: anti-fabrication twins per package (KappaBatch28Test), jsoup/gson byte-IDENTICAL vs
the released jar; a Spring app's report legitimately GAINS Log lines (spring-jcl provides
org.apache.commons.logging) — unmasking, not regression.

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

### 2026-07-06 — κ batch 29: the next tier, same discipline (candor-java `2575683`)

The dogfood app's complete 68-member frontier into the residual heads, triaged member-by-member.
Pure-surface coverage: commons-validator (predicates), commons-beanutils (property shuffling), displaytag
(decorator getters), org.w3c.dom (a JDK namespace missing from the frontier list). Precise effectful
members: threeten-extra now() → Clock; jjwt parse* → Clock (parsing VALIDATES exp/nbf against the system
clock) + Keys generators → Rand, while signing/compact stays pure CPU; JDOM2 input effectful BY SOURCE
(build(File/String) → Fs, build(URL) → Net, caller-opened stream overloads pure-relative — the open
carried the effect); Ehcache at its ACQUISITION points (persistence(dir) → Fs so build/init are vouched
and heap-only apps never fabricate; clustered cluster(URI) → Net). A coverage-semantics finding worth
registering: vouching org.w3c.dom made 438 jsoup fns DROP from its report — their only content was
`invisible: [org.w3c.dom]` (zero effect changes, verified per-fn) — i.e. a widely-reachable uncovered
namespace can inflate a report with disclosure noise, and coverage legitimately shrinks it. Dogfood
trajectory across batches 28+29: ledger 81 → 64 → 49 packages; the top head fell from 5,502 calls (struts)
to 25 (jackson-databind — the one broadly-valuable batch-30 candidate; the rest is long tail).

### 2026-07-06 — κ batch 30 + 30b: Jackson, and a live SILENT-NET find (candor-java `cd617cb`)

Jackson yields to ONE descriptor-driven rule (a File/Path parameter is a source or sink → Fs; a URL → Net
— uniform across the stack; String/bytes/stream overloads pure-relative). The important entry is 30b: the
AWS rule's `owner.endsWith("Client")` gate missed calls through the v1 service INTERFACES
(`AmazonS3.copyObject` — a real S3 request — read silent-invisible on the dogfood app; `copy*` was also
missing from the verb list). The request-making surface is now the Client classes + the Amazon*/AWS*
interfaces (outside .model./Builder) + TransferManager. Unmasked Net 473 → 534 on the dogfood app. LESSON
for the register: a curated rule's OWNER GATE is itself a soundness surface — verify coverage against how
code actually types its variables (interfaces), not just the concrete classes. Dogfood ledger after
batches 28–30b: 81 → 37 packages, everything remaining ≤ 20 calls (long tail).

### 2026-07-07 — κ batch 31: the long-tail sweep, the ledger reaches zero (candor-java `17eb81d`)

All 37 remaining packages, 111 members triaged — the dogfood app's ledger reaches ZERO (81 → 0 across
batches 28–31). Register-worthy findings beyond the coverage itself: (1) **the sweep audits earlier
batches** — StopWatch (both commons-lang generations) reads the clock but went silent-pure under batch
28's lang3 coverage; a covered namespace must be RE-swept when new inventory arrives. (2) **A return-type
fabrication class**: the source/sink descriptor rules (File/Path → Fs, URL → Net) first used
whole-descriptor `contains`, which matches a File RETURN type — `FileUtils.getTempDirectory()` (pure,
returns a path) would have fabricated Fs; an existing round-12 anti-fab pin caught it; all descriptor
rules now match parameters only (`paramsOf`). (3) **Iteration can be a wire call**: Twilio's
`ResourceSet.iterator()` lazily fetches further pages — Net hiding in a for-each. (4) **proceed() is
reflection-shaped**: AOP Alliance's `MethodInvocation.proceed()` executes the intercepted target →
disclosed Unknown, never silenced by coverage. (5) **Defer to richer existing stances**: a new Fs rule for
`XMLReader.parse` was dead code below the pre-existing disclosed-Unknown rule (parse drives user handler
callbacks + XXE-class resolution) — check what already classifies before adding. Also: Redisson's R*
handles → Db (remote data structures by design), DbUnit execute → Db, hibernate's internal jdbc package
covered WITH its effectful internals classified so the one pure member apps reach (the SQL formatter, 685
fns of invisible noise) floors clean.

### 2026-07-08 — candor-java 0.8.4 review patch: six shipped regressions (R19, `4bdb996`)

**Six soundness regressions the batch 28–31 work SHIPPED in 0.8.3, caught by a high-effort code
review.** The same sweep that CLOSED veins opened new ones, via two failure shapes the inventory method
doesn't catch alone. (1) **Broad owner/verb gates fabricate on same-shaped pure members** — the AWS
`Amazon*`-name interface heuristic hit `AmazonS3URI` (a pure URI parser), "any Redisson R* → Db" hit
`getCodec`/`RFuture`, `parse*`→Clock hit the no-arg `Jwts.parser()` factory, whole-owner StopWatch→Clock
hit `create()`. LESSON: a name/prefix owner gate or a bare verb prefix fabricates wherever a namespace
mixes request-makers with same-named value types — require the effectful SHAPE (a token arg, an exact
verb, a started clock), not the name. (2) **A blanket coverage grant turns an under-vouched classifier
into SILENT-PURE** — `com.amazonaws` coverage silenced `DynamoDBMapper.save` (unmodeled facade, owner
doesn't match the *Client gate). LESSON: only ledger-cover a namespace whose effectful surface you
MODELED, not merely inventoried on one app; an unmodeled member of a covered namespace floors silent (the
worst class) — leave it uncovered and it discloses `invisible`. AWS and commons-io are now
classified-but-not-covered. Every fix carries an anti-fabrication twin; jsoup/gson byte-identical. The
byte-identity + kappa_libs gates only catch what their fixtures exercise — the review exercised the
shapes they didn't.

### 2026-07-09 — candor-swift κ batch: UserDefaults / Keychain / Bundle (R20, `dd134e2`)

**Covered-module silent-pure — the Panache shape, Swift edition:** `Foundation` and `Security` sit in
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

### 2026-07-09 — whole-project review: the porcelain fail-open class (R21)

A whole-project critical review opened a THIRD find category: gate surfaces that convert "the gate could
not run" into green — fail-opens in the porcelain and output/auxiliary channels the engine-level
fail-closed doctrine had never swept. Per repo: cargo-candor `policy` swallowed a build failure
(`|| true`) and `guard` passed with no baseline ever snapshotted; candor-java exited 0 when the
`--gate-json` target was unwritable, and a `CANDOR_DEPS` typo was silently ignored; the candor-ts MCP
`candor_whatif` accepted a bad policy path, and a configured-but-empty policy was falsy-skipped;
candor-agents `gate_reports` carried fail-open dead code and truncated observed paths without disclosure.
The review also surfaced one NORMATIVE contradiction: AS-EFF-008's opaque case — the spec text had lagged
the conformance-pinned fail-closed behavior since the 0.5.15 hardening. All fixed in a same-day wave, per
repo; chaining and the stale-baseline posture became conformance PARTs 14–15 as standing gates, and
PART 14's first run immediately caught candor-scan's missing empty-report ledger exemption (next entry).
Companion cargo-candor hardening in the same wave: `policy`'s `|| true` fail-open and `guard`'s
absent-baseline green both now exit 2, with a `GUARD-UNAVAILABLE` engine sentinel distinguishing
not-evaluated from violation, and the §3.3 verdict withheld when the guard could not evaluate.

### 2026-07-09 — candor-scan κ-ledger §2 rule-3 gap (over-disclosure, scan 0.8.4 `2d32086`)

Found by the new PART 14 chaining differential's FIRST run: the ledger exemption for chained reports was
keyed on the report *filename shape* + per-entry hash prefixes, so an EMPTY chained report
(`functions: []` — the §2 rule-3 purity claim) outside the `….<crate>.scan.json` naming still drew "κ
doesn't know N dependencies". The SAFE direction (over-disclosure, not a silent-pure sin), but a
conformance divergence vs candor-java/ts, which honor the claim. Coverage is now keyed on the envelope
`package`/`packages` field (hyphenated names also register in Rust ident form); pinned by PART 14.

### 2026-07-09 — candor-java mutation_probe rot (meta-soundness, `a6c60c0`)

The meta-soundness harness had decayed to 3/14 PATCH-ERROR — its anchors still targeted the pre-typed
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

### 2026-07-10 — the coverage wave: never-executed gate surfaces

**First-ever measurement, then closing every never-executed gate surface (TESTING.md's "verify before
pin" discipline).** Coverage tooling had never been wired into any repo; measuring with child-process
capture (java three-tier 67%→90% line; swift 61%→88%; ts ~95%; agents 90%; rust stable crates 81%)
surfaced the load-bearing surfaces with ZERO execution anywhere. Pinning them found four real bugs, each
fixed red-then-green in its pinning commit (§8):
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

*Correction (appended): agents' final coverage measure in the wave was **96.5%**, not the 90% interim
figure recorded above.*

### 2026-07-10 — swift inherited property-accessor vein (R22, silent → CLOSED)

A fresh adversarial round on a seam NOT on the scorecard: **effectful property accessors accessed via a
subclass**. candor already charges an OWN-class computed getter / `didSet`-`willSet` observer / subscript
(the 2026-earlier "property-arrow hole, Swift edition" fix — `Base.payload` reads Fs correctly). The probe
pushed on INHERITANCE.

THE FIND (candor-swift, SILENT, medium): an effectful accessor whose body lives on a **superclass** read
silent-pure when reached through a subclass — `viaInherited(d: Derived) { d.payload }` where `payload`'s
getter is on `Base`; the `didSet` edition (`s.name = "y"` on a subclass, observer on `Base`); and the
two-level case (`Leaf: Mid: Base`). All three read PURE. The controls stayed correct: an inherited METHOD
(`d.fetch()`) WAS charged, and access via the base static type (`b.payload`) WAS charged.

THE WHY: property-edge resolution (Driver, `cc.propertyEdges.compactMap { resolveQual($0) }`) matched only
the accessed type's OWN `Type.member` accessor unit. The METHOD-call path already climbs `supertypesOf`
(the protocol-extension-default / inherited-into-project logic) — but the property-edge path never did. So
methods climbed, property accessors did not: the exact R18 (inherited-into-project) vein, property edition.

THE FIX (`Driver.swift`): for each property edge, if the own-type key doesn't resolve, climb `supertypesOf`
(transitive — the inverse of the transitively-expanded `subtypesOf`, so two-level resolves in one loop) and
edge to any `<sup>.<member>` accessor unit. An override on the subclass still wins (its own unit resolves
first via the `if let t = resolveQual(pe)` branch), so nothing is fabricated; a member no supertype defines
edges nothing; a pure inherited property stays pure. Verified: `viaInherited`/`viaTwoLevel`/
`viaInheritedDidSet` → Fs; the method + base-type controls unchanged; pure control omitted.

CROSS-ENGINE (the §3 shared-blindness check — the dangerous case): candor-**ts** and **java** were probed
with the same inherited-getter shape and are SOUND (both climb for property accessors). So this is
swift-specific, NOT a shared blind spot — no family sweep needed.

GATE: `DriverResolutionProcessTests.testInheritedPropertyAccessorEffectsClimbTheHierarchy` (a twin: three
inherited-accessor forms → Fs, the inherited-method control → Fs, a pure inherited property → omitted/no
fabrication). Full suite 114 green. Shipped in candor-swift 0.8.7 (⚠ report-affecting). Find-rate: 1 this
round — the seam-inheritance frontier re-opened the count, as §1 predicts (methods were covered; the
accessor edition of the same climb was not).

*Follow-up (appended 2026-07-10, same day): the R22 entry's cross-engine line ("candor-ts and java were
probed … sound") was written after actually running only the candor-**ts** probe; the java claim was
reasoned from the compilation model (Kotlin computed properties lower to `getX()` methods → the bytecode
engine's CHA climbs). Now VERIFIED by a real run: a Kotlin `open val payload get() = File(...).readText()`
inherited into a subclass, compiled to bytecode and scanned by candor-java 0.8.7 — `viaInherited` and the
two-level `viaTwoLevel` both read `[Fs]`, the inherited-method control `[Fs]`, the pure control omitted.
candor-java is sound (the getter is a real method unit `Base.getPayload`; CHA resolves the inherited call).
Also confirmed the swift fix GENERALIZES beyond class inheritance: a protocol-extension-**default** computed
property and a protocol-default **subscript** (both reached via a concrete conformer) now charge their
effect — `supertypesOf` already unions protocol conformances, so the same climb covers them. KNOWN NARROW
BOUNDARY (not chased — no concrete case): a computed property whose body lives in an UNMODELED EXTERNAL base
class (vs a local/protocol super) is not verb-classified on the property-read path, so it would read pure
rather than disclosed-Unknown — the method path's external-super Unknown disclosure has no property-read
analog. Rare (subclassing an external class AND reading an effectful inherited computed property); logged
as a boundary, no open residual assigned pending a real instance.

### 2026-07-10 — error-path / cleanup-block effects (fresh seam, 0-find — convergence)

A fresh seam not previously on the scorecard: an effect that runs ONLY on a NON-straight-line control path
(a `finally`, a `catch` handler, a Swift `defer`/`guard-else`, a Rust error combinator, an implicit
resource close). The worry: a CFG/AST walker that attributes only the happy path would drop the cleanup
effect silent-pure. Probed with the try-body kept PURE so the effect is isolated to the error/cleanup path.

RESULT — 0 finds, sound across all four code engines:
- **swift**: `defer { write }`, `do/catch { write }`, `guard … else { write; return }` → all `[Fs]`.
- **ts**: `try {} finally { writeFileSync }`, `try { throw } catch { writeFileSync }` → `[Fs]`.
- **java**: `try {} finally { new FileWriter().write() }`, catch-handler write → `[Fs]`; and **try-with-
  resources** `try (Res r = …) {}` charges `Res.close()`'s Fs on the enclosing fn (the compiler-synthesized
  close is real bytecode the ASM walker sees) → `twr` = `[Fs]`.
- **rust-scan**: `r.unwrap_or_else(|_| { effectful() })`, `r.map_err(|e| { effectful(); e })`,
  `r.or_else(|_| …)` — the effect rides an error-only closure (no `finally` in Rust) → all `[Fs]`.

WHY SOUND: every engine walks the full statement tree of a function body (all branches/handlers/deferred
blocks), and a call inside any of them is an ordinary call edge — the error path is not special-cased away.
Java's try-with-resources is the sharpest case (an effect via an IMPLICIT, compiler-generated `close()`
call) and the bytecode engine sees it because the close IS in the emitted finally. NOT promoted to a
standing scorecard gate (these were one-shot probes, not CI fixtures) — recorded as convergence evidence:
error-path is checked-sound in all four, find-rate 0 this round. A future standing gate would add one
finally/defer fixture per engine's regression suite if the seam is ever wanted at 🟢.

### 2026-07-10 — swift setter `newValue` untyped (R23, silent → CLOSED)

The operator-overload probe (a symbol call site — `==`, `+`, `c[k] = v` — vs a named call). The operators
themselves were sound: swift `==`/`+` (static-func operator units) and the subscript GETTER charge their
effects; kotlin `operator fun plus`/`set` (bytecode methods), rust `impl Add`, and the ts property setter
all charge. But the swift subscript SETTER `c["k"] = "v"` read PURE.

THE FIND (candor-swift, SILENT, low-med): narrowed by discriminating probes — a setter body with a LITERAL
or STATIC-call effect DID charge (`set { "x".write(toFile:) }`, `set { FileManager.default.createFile(…) }`),
so the setter body IS collected and walked. What dropped was an effect reached THROUGH the implicit value
param: `set { newValue.write(toFile:) }`. `newValue` (subscript AND computed-property setters, plus
`willSet`) was never given a type, so the member call on it didn't resolve to `String.write` → silent-pure.
The callgraph confirmed `useSet -> [Cache.subscript]` (resolution fine) but `Cache.subscript` carried no
effect (the setter body's Fs never landed). NOTE the boundary: `newValue` as an ARG to an already-resolved
call (`UserDefaults.standard.set(newValue,…)`, `save(newValue)`) already worked — the common effectful-setter
patterns; the hole is the *receiver* case (`newValue.effectfulMethod()`).

THE WHY: `newValue` appeared NOWHERE in the engine source — the accessor units (DeclCollector) never seeded
the setter's implicit value param into `FnInfo.params` (the name→type map that lets CallCollector resolve a
receiver's member calls). Regular function params get typed there (`info.params[pname] = tn`); the synthetic
`newValue` did not.

THE FIX (`DeclCollector.swift`, both the var-accessor and subscript sites): for a set/willSet body seed
`params["newValue"] = <property/subscript element type>` (didSet → `oldValue`); honor a renamed param
(`set(v)`). Type from the binding's `typeAnnotation` / the subscript's `returnClause`; nil (inferred type)
→ skip. Verified: subscript-set / prop-set / named-param / willSet through newValue → `[Fs]`; a pure setter
stays pure (no fabrication); `==` unchanged.

CROSS-ENGINE: swift-specific by construction — ts/kotlin setters take EXPLICIT (typed) params and rust has
no property-setter concept, so none has an implicit-untyped-`newValue`. The operator symbol paths (`==`/`+`/
subscript get) were checked sound in all applicable engines. Gate:
`DriverResolutionProcessTests.testSetterNewValueIsTypedSoEffectsThroughItResolve`; suite 115 green. Shipped
in candor-swift 0.8.8 (⚠). This is the THIRD swift accessor-vein find in a row (R22 inherited accessors, R23
setter newValue) — the accessor surface is where swift's silent-pure risk concentrated; both are now gated.

### 2026-07-10 — swift accessor-vein sweep: projectedValue-$ + keypath (R24, R25 SILENT-low, OPEN)

Draining the swift accessor vein after R22/R23. Four more accessor access-paths probed, each with the
accessor unit KNOWN to carry the effect (so any miss is an access-site edging gap, not a collection gap):

- **`didSet { oldValue.write(…) }`** accessed via assignment → `[Fs]` SOUND — R23's fix seeded `oldValue`
  as well as `newValue`, so this generalised for free (confirms the fix).
- **property-wrapper `projectedValue` via `$`** (`m.$name`, `Tracker.projectedValue` has Fs) → PURE.
  **R24, SILENT low.** candor edges the `wrappedValue` path but not the `$`-prefixed projectedValue access.
- **keypath read** (`h[keyPath: \.data]`, `Holder.data` computed getter has Fs) → PURE. **R25, SILENT low.**
  The keypath literal's referenced member isn't resolved to the accessor unit.
- **`@dynamicMemberLookup`** (`p.anything` → `subscript(dynamicMember:)`, has Fs) → `[Unknown]`. NOT silent —
  DISCLOSED Unknown (the honest "unresolved member"), the sound over-disclosure direction. A precision gap
  (it could resolve to the dynamicMember subscript and charge Fs precisely), not a cardinal sin.

Both R24/R25 are SILENT but LOW: niche patterns (an effectful projectedValue accessed via `$`; an effectful
computed property read via `[keyPath:]`). Unlike the accepted syntactic-limit residuals R2–R8, they are
FIXABLE — the effect is already on the unit, only the access-site edge is missing (R24: recognise `$name` →
edge `<Wrapper>.projectedValue`, mirroring the wrappedValue edging; R25: resolve a `\.member` keypath
literal applied via `[keyPath:]` to the member's accessor unit). Recorded OPEN pending a fix decision (the
accessor vein has now yielded R22 inherited / R23 setter-newValue fixed+shipped, and R24/R25 low-open).

*Follow-up (appended 2026-07-10, same day): R24 + R25 FIXED (candor-swift 0.8.9), per Tom's "always fix" —
fixable silent holes get closed, not accepted. R24: the property-read visitor now edges `m.$name` to
`<Wrapper>.projectedValue` (mirroring the wrappedValue edging). R25: the keypath visitor's implicit-root
branch now recognises a `[keyPath:]` SUBSCRIPT application (root = the receiver's own type), not just the
element-iterator `map(\.p)` form. Verified: both → `[Fs]`; element-map keypath unregressed; a pure member
via `$`/keypath stays pure; `@dynamicMemberLookup` still discloses Unknown (sound). Gated by
`testProjectedValueAndKeyPathAccessorEffectsCharge`; suite 116 green. The swift ACCESSOR VEIN is now drained
across five findings — own-property (earlier), R22 inherited accessors, R23 setter-newValue, R24 projected,
R25 keypath — every access path onto a property/subscript/observer accessor unit now edges. Open SILENT
residuals back to 7 (R2–R8, syntactic-limit lows); 0 med+.
