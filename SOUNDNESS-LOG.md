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

### 2026-07-10 — swift generic-constrained dispatch: where-clause + type-level bounds (R26, R27, fixed)

After the accessor vein drained, the next non-accessor seam: an effect behind a method reached through a
GENERIC type-parameter constraint. candor already types a value param `x: T` by its bound (`<T: P>` →
dispatch like a `P`-typed param, via `genericBounds`), so `func persist<T: Saver>(_ x: T) { x.save() }` and
the associated-type form `func pull<S: Source>(_ s: S) { s.fetch() }` were SOUND. Two forms were not:

- **`where T: P`** (`func f<T>(_ x: T) where T: P { x.method() }`) → PURE. Only the inline `<T: P>` clause
  fed `genericBounds`; the `where`-clause conformance requirements were never read. **R26.**
- **type-level bound** (`struct Pipe<T: Saver> { let item: T; func run() { item.save() } }`) → PURE. A
  discriminating probe showed a plain protocol-typed field DOES dispatch (`struct Box { let s: Saver } →
  s.save()` = Fs) — so the only gap was that the field `item: T` wasn't resolved to its bound `Saver`. **R27.**

THE FIX (`DeclCollector`): (R26) also collect conformance requirements from the function/init
`genericWhereClause` into `genericBounds`. (R27) record TYPE-level generic bounds via a new
`recordTypeGenerics` on struct/class/enum/actor decls (both the `<T: P>` clause and a type-level
`where T: P`), and resolve a stored field typed as such a param to its bound — then the existing
protocol-typed-field dispatch fires with no further change. Controls hold: an unconstrained generic and a
bounded generic with NO dispatched call stay pure (no fabrication); the inline-bound and associated-type
forms are unregressed. Gate: `testGenericConstrainedDispatchWhereClauseAndTypeLevelBounds`; suite 117 green.
Folded into candor-swift 0.8.9 (⚠). swift-specific (the generic-bound → protocol-dispatch modelling is a
candor-swift resolution path). Open SILENT residuals stay 7 (R2–R8); R26/R27 opened + fixed same session.

### 2026-07-10 — non-accessor seam sweep (autonomous): 5 seams sound, R29 fixed, R28 open

Autonomous continuation past the accessor + generic veins. Probed six non-accessor seams; each with the
target unit KNOWN to carry the effect, so a miss is a resolution/edge gap.

SOUND (0-find — convergence evidence):
- **closure capture** — an escaping closure stored (init-assigned property, later-assigned var property,
  array element) then invoked far away: charges Fs (+ discloses Unknown where the flow is uncertain — the
  ideal: known effect charged, residual disclosed). Never silent.
- **async / concurrency** — `await` propagation, `Task { }`, `async let`, `Task.detached`: all Fs.
- **opaque / existential returns** — `-> some Worker` and `-> any Worker` resolve to the concrete impl and
  dispatch: Fs.
- **method references** — a bound instance method (`let f = s.m; f()`) and a static ref (`T.sm`): Fs.

FINDS:
- **R29 (FIXED)** — `@resultBuilder`: a func `@SomeBuilder` runs `SomeBuilder.buildBlock(…)` etc via the
  compiler transform (no call site), so an effectful builder read silent-pure. Fix: track `@resultBuilder`
  types, capture a func's capitalized attributes, and edge the func to the builder's `build*` units
  (resolveQual drops undefined ones; a pure builder contributes nothing — verified no fabrication). v.low
  severity (effectful builders are rare), but a clean fix. Gated. Folded into 0.8.9.
- **R28 (OPEN, SILENT low)** — conditional conformance on a stdlib type: `extension Array: Saveable where
  Element: Saveable` reached via `xs.persist()` read pure. Compound (two gaps: the array-receiver → Array-
  extension method edge, AND the self-element `$0` typing under the extension's `where Element: P`). Niche
  advanced pattern; recorded with a plan rather than fixed in this pass. Open SILENT residuals 7 → 8.

*Continuation (appended 2026-07-10): a second non-accessor batch — `@autoclosure` (charges the arg's
effect; a pure autoclosure call DISCLOSES Unknown, sound not silent), `indirect enum` methods, nested/local
functions, and enum-switch per-case dispatch — all SOUND, 0-find. The find-rate has dropped: after the
accessor + generic veins drained (R22–R27, R29), the non-accessor seams probed (closure capture, async/
concurrency, opaque/existential, method refs, autoclosure, indirect enum, nested fn, enum switch — 8 seams)
returned 0 cardinal sins, with only R28 (conditional conformance on a stdlib type, niche) left open. That
is convergence for this era — not proof, but the fresh-seam find-rate trending toward zero as §1 predicts.

### 2026-07-10 — cross-engine sweep (autonomous): candor-ts sound, candor-scan R31 fixed / R30 open

Pivoted the autonomous sweep to the OTHER syntactic engines (the swift finds were swift-specific — worth
checking whether ts/rust-scan share the class).

- **candor-ts**: probed the swift-analog seams — generic-constraint dispatch (`<T extends Saver>`), a
  generic-typed class field reaching a method (the R27 analog), a setter using its param, index-signature
  access. ALL SOUND (index access discloses Unknown). candor-ts's resolver is more complete than swift's
  here — 0-find.
- **candor-scan (rust)**: where-clause bound, trait-object (`&dyn`), and inline generic bound all SOUND
  (rust-scan handles the where-clause swift needed R26 for). Two finds:
  - **R31 (FIXED, candor-scan 0.8.7)** — a bounded-generic struct field (`Pipe<T: Saver>{item:T}` →
    `self.item.save()`) read pure: field types were resolved with an EMPTY bounds map (`decls.rs` passed
    `&no_generics`). Fix: `generic_bounds_of_generics(&s.generics)` (refactored to take `&syn::Generics`,
    inline + where) seeds the field trait-leaf resolution. The swift R27 analog, different codebase. Gated;
    77 lib + 36 cli green; no fabrication on an unconstrained field.
  - **R30 (OPEN, SILENT low-med)** — a trait DEFAULT method reached via an empty `impl Trait for T {}`:
    the default body IS collected (`Trait::method` unit carries the effect) but a concrete receiver with no
    own method doesn't fall back to its traits' defaults. Common idiom; needs a type→traits index + a
    resolver fallback (a larger change in candor-scan's core dispatch — recorded with a plan rather than
    fixed mid-sweep in an unfamiliar-to-this-session engine without running the full corpus differential).

Cross-engine picture: the swift accessor/dispatch vein is largely swift-specific; ts is clean; rust-scan
shares only the generic-field sub-vein (now fixed) and has its own trait-default gap (R30). Open SILENT
residuals 8 → 9.

### 2026-07-11 — candor-scan trait-default-via-empty-impl (R30, fixed)

Closing the R30 find from the cross-engine sweep. The trait-default caller fallback (`t.m()` on a concrete
type with no own `m` → the inherited `Trait::m` default body) was already WRITTEN in scan.rs — but my probe
showed `impl Logger for FileLogger {}` + `l.flush()` still read pure. Root-caused by instrumentation: the
fallback edge FORMED (`use_named -> Logger::flush` in the callgraph, `Logger::flush` carried Fs), but the
final report stayed pure — because `local_types` is built from fn QUALS, and a type whose ONLY impl is an
empty (or non-overriding) trait impl has no fn unit of its own, so it was absent from `local_types`. That
made its typed call fail the `resolvable` gate, which skipped the whole resolution block — the fallback
never ran on the first pass (and the "still pure" I saw after a partial fix was a VERIFICATION-SCRIPT bug:
it matched `endswith("::"+fn)` but crate-root fns have no `::` prefix — a good reminder to trust the
callgraph edges, not a lossy matcher). Fix (2 lines): after building `type_to_traits`, insert its keys into
`local_types` — every type with a local trait impl IS local. Verified: `use_named`/`use_s` → Fs; an OVERRIDE
(`impl Logger for Quiet { fn flush(&self){} }`) stays pure (the override wins, the default is not also
charged — no fabrication). Gated; 77 lib + 37 cli green. candor-scan 0.8.8. Open SILENT residuals 9 → 8.

### 2026-07-11 — swift conditional conformance on a stdlib collection (R28, fixed) — LAST fixable residual

The one fixable-silent residual left from the swift-resolution era, now closed (Tom: "no question over making
fixes, even niche ones" — niche-ness is never a defer reason). `extension Array: Saveable where Element:
Saveable { func persist() { forEach { $0.persist() } } }` reached via `xs.persist()` read silent-pure — TWO
coupled gaps, isolated by sub-probes (a `directArrayPersist` with an EXPLICIT `xs.forEach` already worked, so
the element-closure dispatch itself was fine):
1. **the array-receiver edge**: `xs.persist()` (xs: [Item]) didn't reach `Array.persist`. rootOf(xs) returns
   the identifier ("xs", not a type), so no branch fired. Fix: an array-receiver branch edging to the local
   `Array.<member>` extension unit — via `propertyEdges` (a soft resolveQual edge) NOT a typed call, so a std
   method (`xs.forEach`, no `Array.forEach` unit) drops SILENTLY (a typed call would have disclosed a spurious
   Unknown — caught by the directArrayPersist control gaining `[Fs, Unknown]` mid-fix).
2. **the self-element dispatch**: inside `Array.persist`, `forEach { $0.persist() }` is a BARE (implicit-self)
   iterator, so `elementTypeOf(base)` never ran and `$0` stayed untyped. Fix: capture the extension's
   `where Element: P` bound (`FnInfo.selfElementType`, via a `selfElementStack` parallel to `typeStack`), and
   type a bare-iterator's `$0` as it — `$0: Saveable` then dispatches via the protocol CHA.
Controls: a PURE conditional conformance stays pure; a std array method charges precisely (no Unknown). Full
suite 119 green. candor-swift 0.8.10.

**MILESTONE:** R28 was the LAST FIXABLE silent-under-report residual. Every fixable silent hole found this
era (R22–R27, R29 swift; R30, R31 rust-scan; R28) is now closed + gated. The 7 remaining open SILENT
residuals (R2–R8) are all FUNDAMENTAL syntactic limits — accepted flood-vs-precision tradeoffs, not
resolution bugs. The fixable-silent count is ZERO.

### 2026-07-11 — real-world dogfood of the swift wave (swift-argument-parser)

Validated the R22–R28 swift wave (0.8.7–0.8.10) on REAL third-party code, not just fixtures: candor-swift
0.8.10 over Apple's swift-argument-parser (an idiom-dense, generic/property-wrapper/Decodable-heavy pure
arg-parsing library — a hard target). Result: **no fabrication** — a library that touches no Fs/Net/Exec/Db
reported none; the only concrete effect was **Env (7 fns)**, and it's GROUND-TRUTH CORRECT — the source has
`getenv(key.rawValue)` in Platform.swift, candor charges `Platform.Environment.subscript` (a SUBSCRIPT
accessor — the very machinery the wave touched) with `direct:[Env]`, and it propagates transitively to the
shell-completion detectors that read the environment. The remaining 183 fns are `Unknown`-only — honest
over-disclosure on genuinely-unresolvable Decodable-synthesis / property-wrapper / generic code (sound; the
§4 marker, not silence). So the 10-fix wave introduces no fabrication on real code and charges real effects
correctly. Confidence: the wave is validated beyond fixtures on a real, ground-truth-checked corpus.

### 2026-07-13 — corrupt-report false all-clear on the read side (query verbs), rust+ts (fixed)

Dogfooding `candor tour` on a real crate (pgman), a report locator pointed at an unparseable file
made `tour` print "candor: nothing hidden — every effect sits where its name says it should" at exit
0. Root cause was NOT in the analyzer — it was the READ side (candor-query / candor-ts query.mjs): the
loud report loader failed loud only when the prefix matched NO files. When it matched a report that
then FAILED to parse, the tolerant loader disclosed on stderr but returned an EMPTY entry set →
Ok(empty). Every loud-consuming verb inherited a false all-clear: `tour` said "nothing hidden", and a
policy `map`/gate over the empty report would PASS — the §4 cardinal sin, over corrupt input rather
than mis-analyzed code. A valid report always LISTS its functions (even a pure crate lists them with
empty effect sets), so zero entries AFTER a matched file was found is always the corrupt case, never
an effect-free crate.

FIXED four-way-consistent: candor-rust `load_entries_loud` and candor-ts `loadReport`/loadReportOrDie
now return a hard error (exit 2, disclosed) when a found report yields no trustworthy functions. The
candor-ts fix has TWO halves — the fuzzer caught that the first pass only closed SYNTACTIC corruption
(a JSON parse throw); a report that parses to valid JSON of the WRONG SHAPE (a `null` doc, a bare junk
array, a non-array `functions`) still returned [] at exit 0, the same false all-clear in semantic
clothing. Both halves closed; a WELL-FORMED empty `functions: []` envelope still exits 0 (parity with
Rust — the only non-corrupt empty). java (throws → exit 2) and swift (→ no-report → exit 2) were
already immune; the fix brings rust+ts into line. GATED: candor-query unit test
`corrupt_report_fails_loud`; candor-ts CLI-9 tests + fuzz robustness seeds (all six corrupt shapes →
loud exit 2, silent stdout; plus a clean-empty complement seed); conformance PART 4k pins the
tour-loudness invariant four-way (a found-but-unparseable report → exit ≠0, disclosed, never "nothing
hidden"). KEY LESSON: the cardinal sin lives on the READ side too, not just the classifier — a
trustworthy analyzer can still be made to emit a false all-clear by a corrupt/typo'd report locator,
and "tolerate corrupt input" must never degrade into "report empty == all-clear".

Residual (tracked, not rushed): the four-way conformance pin covers SYNTACTIC corruption (truncated
report). candor-ts now also fails loud on SEMANTIC corruption (null/wrong-shape); whether candor-rust
/java/swift are equally loud on those specific malformed-but-valid-JSON shapes is unverified — a
follow-up sweep, not a known divergence (all four refuse to under-report on the syntactic case).

### 2026-07-13 — corrupt-report false all-clear, the cross-engine sweep (rust+java, residual closed)

Follow-up to the entry above, resolving its tracked residual. Probing the semantic-corruption shapes
(a `null` doc, a bare junk array `[1,2,3]`, a non-array `functions`) across ALL four engines found the
false all-clear was NOT ts-only: the bare junk-array shape ALSO read as "nothing hidden" at exit 0 in
candor-rust AND candor-java. Both parse `[1,2,3]` as a legacy bare array, drop every entry for a
missing `fn`, and read the net-empty result as an effect-free crate. (swift + ts were already loud on
it.) FIXED: candor-rust `load_entries_inner` marks hard_fail when a file parsed but all its entries
were dropped (`fdb5e63`); candor-java `load()` throws → loud exit 2 when a non-empty report array
yields zero usable functions (`60d812b`). A WELL-FORMED empty `functions: []` report still exits 0 in
all four (the only non-corrupt empty — parity preserved, pinned by a clean-empty complement seed).
Conformance PART 4k now pins BOTH shapes (syntactic + semantic) plus the complement, four-way. Residual
CLOSED: all four engines fail loud on null / junk-array / wrong-typed `functions`, and exit 0 only on a
valid empty report. KEY LESSON reinforced (the write-fmt pattern, now on the read side): a find in one
engine is a SWEEP trigger for ALL — the semantic-corruption false all-clear was a shared blind spot in
three of four engines that per-engine testing would have missed.

### 2026-07-13 — the loudness rule left unfinished: verbs × surfaces (max-review wave, all fixed)

The post-0.11 max review (44 agents, 15 CONFIRMED findings) exposed the sequel to the corrupt-report
entry above: the fix was swept across ENGINES but not across VERBS and SURFACES. The loud rule landed
in the shared single-report loaders — but candor-rust's comparative verbs (gains/diff/containment) kept
their own quiet loader, candor-ts's MCP tools (all 15 loadReport sites, plus the report resource)
never consulted the new hardFail tag, ts gains/diff had no files-at-locator guard at all, and the
brand-new swift gains verb reproduced the semantic-corruption hole from scratch. Each was an exit-0
empty all-clear a CI gate would trust — the same §4 class, resurfacing one surface over from where it
was fixed. Also found: the gains `origin` field downgraded the supply-chain ATTACK signal to a
feature-looking "new" whenever the baseline callgraph was PARTIAL (a disclosed-and-dropped corrupt
sidecar) rather than absent — in all four engines at once, because all four ported the same reference
ladder; and the conformance suite's OWN 4i/4j oracles were fail-open (an engine that crashed on the
fixture parsed as {} → MATCH), quietly capable of masking the class.

ALL FIXED same-day (rust 5390e66, java 654ad50 — which also caught a THIRD stdout-channel instance and
now unions multi-report baseline sidecars, ts 2d73b6f — bonus hole: MCP baselines bypassed
resolvePrefix confinement, swift 9d1ad94, spec d52089d, umbrella 1fbe269, web ad7c50d). GATED:
conformance PART 5b grew the partial-graph checks; 4i/4j oracles fail closed on empty output; 4k's
fixtures isolated from 4j's dir; per-engine unit/CLI/process-test pins throughout; dispatcher + web
smoke regression gates. KEY LESSON (extends the write-fmt and read-side lessons): a new invariant must
be swept across the full MATRIX — every ENGINE × every VERB that loads the same data × every SURFACE
(CLI, MCP, LSP, resources) — and the conformance oracle that pins it must itself fail CLOSED. A fix
that lands in the shared loader but not in a verb's private loader is the same bug wearing a new file.

### 2026-07-14 — max review r2: the alarm mutes through STORAGE and IDENTITY, not just parsing (all fixed)

The second max review of the gains/loudness work (43 agents, 50 verified → 15 distinct defects) found the
supply-chain ⚠⚠ alarm could still be downgraded to ⚠ (or exit-0) through seams the first review's
parse-focused sweep didn't reach — the existence ORACLE itself, not the report parse:
- **candor-gains corpus (2 finds):** an absent sidecar was cached as a fabricated `"{}"` — an
  authoritative-empty existence oracle that tiered every baseline-pure gain as new-function; and the
  corpus key hashed report bytes alone, so two versions differing only in PURE functions (identical
  reports, different graphs) silently shared one cached graph — cross-version existence contamination.
  The canonical attack (a shipped-pure fn now phones home) muted in both. FIXED: null-not-`{}` (→
  undecidable → alarm tier), hash over report+graph content.
- **candor-java (1):** the multi-report baseline union was engine-BLIND — a foreign engine's sidecar
  beside a sidecar-less java report served as "evidence", and foreign quals are systematically absent
  from a foreign graph → systematic "new" where "unknown" was right. FIXED: engine-owned union.
- **candor-swift (2):** per-entry junk silently dropped without disclosure; one corrupt sibling among
  valid ones passed exit-0. FIXED to rust's disclose-count + net-empty-loud rule (tightened a
  clean-empty+corrupt case too).
- **candor-rust (1):** the §2.1 mismatch disclosure was `--json`-scoped — the human TSV form
  (candor-run.sh's self-review input) presented a reclassification gain as real. FIXED: both modes.
Plus routing (dispatcher token-less→JS misrouted `baseline.json`-shaped files, and a ts report beside a
tokened family was shadowed — both closed by envelope-sniffing + an unconditional probe) and the two new
candor-ts watcher/reader features (rotation-replay flood, overlay clobber/wedge, wrong default root,
out-of-tree-baseline refusal, lexicographic `since`) — none alarm-muting, all fixed + pinned red-then-
green. KEY LESSON (extends "engine × verb × surface"): for a SECURITY signal, audit the whole
DECISION CHAIN — not just "is the input parsed correctly" but "is the ORACLE the decision reads
(cache, hash key, cross-engine sidecar) itself trustworthy, and does an undecidable oracle fail TOWARD
the alarm". A cached empty is as dangerous as a parsed empty.

### 2026-07-14 — Llm/privacy max review (r3): a NEW attribution surface over-matches (fabrication) — all fixed

The review of the Llm + privacy/1 feature waves (38 agents, 15 confirmed) found the failure mode a new
EFFECT introduces: not the silent under-report, but its mirror — FABRICATION by over-matching the new
attribution predicate, PLUS cross-engine divergence because only the happy path was pinned.
- **Host-predicate over-match (all engines):** the Ollama rule fired on ANY host with port 11434 (an
  unrelated internal service → fabricated Llm); the Bedrock rule matched the SUBSTRING "bedrock" (an S3
  bucket `bedrock-backups.s3.amazonaws.com` → fabricated Llm). Fixed to PRECISE rules four-way (Ollama =
  loopback host only; Bedrock = first-label service bedrock-runtime/bedrock-agent-runtime). Only java was
  briefed initially → the sibling parity gap was itself caught by grepping the four predicates, not by a
  test — the lesson that a shared table needs a shared FIX, checked across all copies.
- **ts :11434 on the RAW literal:** `axios.post("/v1/x:11434/y")` (a relative path) fabricated Llm because
  the port regex ran against the whole string, not an extracted host. Fixed: predicates run on the PARSED
  host, never the raw argument.
- **swift AVAudioEngine → Mic fabrication:** a general audio-graph type (playback) charged Mic; member-
  gated to .inputNode. The privacy ASYMMETRY was made explicit: never fabricate Llm (unknown host stays
  Net), but OVER-disclose an ambiguous privacy CAPTURE ({Camera,Mic}) — a missed sensor in a manifest is
  the costly error.
- **Under-report mirror (the dogfood, candor-scan):** reqwest was claimed-COVERED but only its convenience
  fns were classified — the BUILDER idiom (Client::builder()...post(url).send()), the dominant real-world
  form and ebman's actual api.anthropic.com call, was silently missed AND undisclosed. Fixed: the builder
  chain classifies Net + captures the host → Llm fires. The Llm gate-evasion twin (a model-SDK call that
  also classified Net dropped Llm) was fixed the same wave.
- **Toothless pin:** PART 4m only tested the happy path, so it couldn't catch any of the above; given
  NEGATIVE fabrication cases (s3-bedrock bucket, remote :11434) it now fails on over-classification.
KEY LESSON: a new EFFECT's attribution table is a two-sided risk — it can UNDER-match (miss the effect,
the classic sin) OR OVER-match (fabricate, a precision failure that erodes trust just as fast). Pin BOTH
directions (a positive AND a negative case) in conformance, and check a shared predicate's FIX across
every engine that copied it, not just the one the reviewer happened to file it against.

### 2026-07-14 — dogfood: top-level module effects silently dropped (ts + swift)

Broadening the 0.13 real-world dogfood (cloning real OSS LLM-SDK consumers), a scan of
openai-quickstart-node surfaced only the files with NAMED functions; the feature scripts that call the
SDK at **top-level module scope** (`embeddings/index.js`: `const e = await openai.embeddings.create(...)`
at load, no wrapping function) produced an **empty report, exit 0** — a valid "pure" verdict for a module
that reaches a model provider. Isolated hermetically (no resolution dependence): a module whose top-level
runs `readFileSync("/etc/config")` (Fs) + `fetch("https://api.openai.com/...")` (Llm+Net) → `functions:
[]`, exit 0 in **candor-ts**. Same in **candor-swift** for top-level `main.swift` code (Fs + Llm+Net → 0
units). A `deny Llm` / `deny Net` / `deny Fs` gate PASSES such a module — the cardinal sin (silent
under-report / false all-clear) for a whole class of real code: ESM top-level await, side-effecting setup
modules, serverless handler files, config modules that call out.

CROSS-ENGINE: **candor-java is SOUND here** — a `static { … }` initializer doing the same classifies
`p.S.<clinit> → [Llm, Net]`. **candor-rust N/A** (no top-level executable code; only `fn main`). So this
is a TWO-engine gap (ts, swift), and a cross-engine DIVERGENCE (java attributes, ts/swift drop). It is
SPEC-BACKED: SPEC §2 `unitKind` explicitly recommends `"initializer"` for "a JVM `<clinit>`, a lazy/static
initializer" — the unit model already covers top-level/init units; ts and swift simply never synthesize
one for a module's own top-level statements.

STATUS: **FIXED + gated (spec 0.14, 2026-07-14).** candor-ts synthesizes a `<module>` unit and
candor-swift a `<main>` unit per file with top-level statements (`unitKind:"initializer"`), carrying the
top-level statements' direct effects + call edges (transitive top-level reach); minted lazily so a pure
top-level never gains an empty unit. Injected at the single choke point — candor-ts `enclosing()` now
returns the module unit when the parent walk reaches the SourceFile (the decorator→null guard preserved,
so decorator applications stay unattributed); candor-swift adds a `visit(SourceFileSyntax)` collector
(declaration items excluded → a called function's effects reach `<main>` via an edge, not inlined).
Pinned four-way by conformance **PART 4p** (java `<clinit>` / ts `<module>` / swift `<main>` each →
initializer unit Llm+Net; rust N/A). Independently verified: the probe battery flips EMPTY → attributed;
ts `npm test` + swift `swift test` (201) + smoke green. REFINED SCOPE (the investigation payoff): the
ONLY hole was BARE top-level executable statements — every DECLARATION initializer (class fields, static
blocks, static/instance fields, computed props, swift global-var inits) was ALREADY sound in all engines,
and top-level code that delegates to a NAMED function already tripped the gate via that function; the
false-pure hole was only inline top-level effects with no named landing spot (the openai-quickstart
`embeddings/index.js` pattern). Distinct from the SOUNDNESS.md "lazy-init (deferred initializer forced
elsewhere)" 🟢 row — that is a function FORCING a deferred init; this is the module's own load-time code.
KEY LESSON (repeat): dogfood on REAL code finds the class the fixtures don't — every prior conformance
fixture wrote its effects inside a named function, so the top-level unit was never exercised. The
published-artifact scan (npx candor-ts@0.13.0) surfaced it.

### 2026-07-14 — top-level follow-ons: swift tuple-global drop + ts static-block label (0.14.1)

Probing ADJACENT cases after the 0.14 top-level rung (the discipline: a new unit-attribution seam is a
two-sided risk — audit the shapes the primary fix didn't exercise) surfaced two residuals, both fixed and
shipped as engine patch 0.14.1 (spec stays 0.14 — these are conformance fixes TO the existing §2
initializer contract, not a new rung).

- **candor-swift: a tuple-destructured global was SILENTLY DROPPED** (a real cardinal-sin residual, same
  class). `let (a, b) = effectfulInit()` at file scope binds names, so the `<main>` collector excludes it
  (it is a declaration, not a bare statement) — but the global-var unit path guarded on
  `IdentifierPatternSyntax` only, so a TUPLE pattern fell through and its initializer effect vanished (a
  `deny Fs` gate passed it). The NAMED global (`let cfg = …`) was already sound; only the tuple shape was
  lost. FIX: a `boundNames(pattern)` helper (recurses tuples) mints a lazy first-touch unit per bound name
  carrying the shared initializer — sound over-approximation (any name's first read forces the lazy
  global). Same fix covers the type-member sibling `static let (p, q) = …` (found during verification —
  "fix the copied guard everywhere"). Remaining rarer residual, NOTED not fixed: an INSTANCE tuple stored
  property (`let (a,b) = …` runs in the ctor, not first-touch) — obscure, disproportionate to fold into
  <init>.
- **candor-ts: a `static { … }` block was MISLABELED** (precision, NOT a silent drop — the effect was
  caught). Its body folded into the instance `C.constructor` unit (and carried no `unitKind`), so `new
  C()` falsely appeared to perform the static-init effect. FIX: a `staticBlockUnit` mints `C.<static-init>`
  with `unitKind:"initializer"` (mirrors the `<module>` synthesis), intercepted in `enclosing()` before
  the ClassDeclaration→ctor mapping. A `static x = fetch()` FIELD initializer still folds into the ctor —
  a lower-stakes precision nuance (effect caught, class still gated), left as noted.

Gated: candor-swift TopLevelMainProcessTests (+2 tuple pins), candor-ts test.mjs §8b (+3 static-block
pins). Conformance PART 4p (the four-way top-level/initializer differential) unchanged and still green —
these are engine-shape refinements within the contract it pins. LESSON (again): the primary fix's probe
battery wrote effects in the common shape; the residuals lived in the shapes it didn't — always sweep the
siblings (tuple vs identifier, static-block vs field-init, member vs global).

### 2026-07-14 — const-indirected host: source-engine recall to java's parity (unreleased on main)

Dogfooding real Rust LLM clients (aichat, async-openai) surfaced a cross-engine RECALL gap (not a soundness
violation): the Llm host-literal refinement fired only for an INLINE literal at the call. Real clients put
the host in a `const`/`static` and build the URL by interpolation/format — `const API_BASE =
"https://api.openai.com"; fetch(`${API_BASE}/chat`)`. SPEC §1 says a "STATICALLY-KNOWN request to a
recognized model host" → Llm; a literal const IS statically known, so the SOURCE-LEVEL engines
(rust/ts/swift) were UNDER-conforming. candor-java was already sound (javac inlines `static final String`
→ the literal is in the bytecode). Fixed rust/ts/swift with conservative const-string propagation: index a
`const/let NAME = "literal"` (module/global + one level of local), resolve it at the host arg for three
shapes — bare ref, interpolation/format HEAD, const-left concat — then run the EXISTING host-extraction +
refinement (so Llm, Db jdbc, and Net-allowlist hosts all benefit, effect-agnostic). SOUNDNESS held four
ways: a non-model const host (a CDN) stays bare Net (no fabrication); a runtime/config host, a reassignable
`var`/`let`, a literal-prefix-before-interpolation, and a non-const first arg all stay bare Net, never a
guess. Pinned by conformance **PART 4q** (const model host → Llm+Net; const CDN → Net; four-way incl. the
java inlining reference).

HONEST CORRECTION of the motivating dogfood: **aichat re-scans to 0 Llm — the SOUND answer, not a miss.**
Its providers read the host from RUNTIME config (`get_api_base()`), the const only a fallback
(`format!("{}/…", api_base.trim_end_matches(…))` — a method-chain result, not a bare const), so the host is
genuinely not statically known and MUST stay bare Net (java wouldn't flag it either). The guard correctly
held on real code — a good negative-control outcome. The feature's real value is the PURE-const pattern
(a hardcoded base with no runtime override). LESSON: a dogfound "gap" can be the engine being correctly
conservative; verify the target is actually statically-knowable before calling it an under-report.

### 2026-07-15 — literal-head host: four-way recall to the most common URL shape (unreleased on main)

The complement to the const-host work (2026-07-14), and higher-frequency: a URL whose LITERAL HEAD already
contains the complete host with interpolation only in the PATH — `fetch(`https://api.openai.com/v1/${p}`)`
/ `format!("https://…/{}", p)` / `"https://…/" + p` — read bare Net in ALL FOUR engines (java too: javac
does not fold a RUNTIME concat, and the host extractors only read a plain string literal). The host is
statically known → §1 under-conformance. Fixed four-way: at the host arg, accept a composed URL
(template / format! / interpolation / concat) when its first STATIC segment completes `scheme://authority/`
— a `/` after `://` WITHIN the literal, before any placeholder — then extract the authority (minus :port)
and run the EXISTING host refinement (Llm/Db/Net, effect-agnostic). candor-java recovers the literal prefix
from BOTH javac concat shapes (`makeConcatWithConstants` indy recipe + classic StringBuilder append chain).
SOUNDNESS BOUNDARY pinned by conformance **PART 4r**: a SPLIT authority (`https://api.${x}.com/…` — the
placeholder is inside the authority, no `/` terminates it in the literal) stays bare Net; a whole-host
interpolation, an unterminated host, and an interpolated-port-before-`/` all stay bare Net (safe
under-reports); a literal-head NON-model host (a CDN) stays bare Net (fabrication guard). Committed
UNVERSIONED, batched with the held const-host work (PART 4q) — floor stays 0.14, publish held. Each engine
independently re-verified on the full boundary battery; tests green (ts 393, swift 212, java 358, rust
229). LESSON: the two host-resolution gaps (const-anchored head `${CONST}/x` vs literal-complete head
`https://host/${x}`) are complementary halves of "the host is statically knowable but not a bare literal" —
real code uses both; pin the boundary (what is NOT resolvable) as hard as the positive.

### 2026-07-15 — candor-scan: cross-crate call via glob-re-export / use-rebind silently dropped (dogfood, CONFIRMED)

Autonomous dogfood of real crates (sqlx). A cross-crate EFFECTFUL call reached through a **glob re-export**
(`use extern_crate::prelude::*`) OR a **`use crate::localname` re-bind in a submodule** is reported PURE and
NOT disclosed anywhere — no effect, no Unknown, no coverage-ledger entry. Contrast a DIRECT
`use extern_crate::module` (`use sqlx_core::net`), which correctly discloses the crate in the ledger.
Isolated four ways (repro iso_A glob / iso_B nested-mod-rebind / iso_C glob-fullpath = all silent+undisclosed;
iso_D direct = disclosed). WORSE than a single-scan gap: the effect is FULLY LOST even under proper `--deps`
chaining (case A chained → still PURE; case D chained → correctly Net) — so it is not recoverable in ANY
workflow. Real-world hit: **sqlx-postgres `PgStream::connect` (the TCP dial to Postgres) reads PURE** — it does
`pub(crate) use sqlx_core::driver_prelude::*` then `use crate::net; net::connect_tcp(host, port, …)`. This is
a ubiquitous Rust idiom (every crate with a `prelude`/`driver_prelude` glob; every submodule `use crate::x`),
so the blast radius is large: any Net/Fs/Db/Exec reached this way vanishes. ROOT: candor-scan attributes a
cross-crate call only through a DIRECT `use extern::module` binding; a glob or a `use crate::name` rebind
loses the external origin, the qualifier resolves to no local module definition, and the call falls into a
"resolved to nothing → PURE" hole instead of "unresolved/external → disclosed or Unknown". FIX (honesty-first,
in progress): an unresolved module-qualified call (qualifier is neither a known local module NOR a known
crate) must NOT read pure — trace the glob/rebind to the origin crate to disclose it (and edge it for
chaining), or at minimum mark the call Unknown. HARD CONSTRAINT: no fabrication — local-pure and std calls
must stay pure; the 1337-crate realworld-oracle must not gain fabrications. VERDICT: REAL, high-severity,
fix+gate (held per Tom's publish-hold).

### 2026-07-15 — candor-ts: process.env read via bracket/alias/destructure/`in` was silent (dogfood, FIXED)

Dogfooding chalk/supports-color: candor-ts classified `Env` ONLY for a direct `process.env.KEY` dot access.
It silently missed (read pure) `process.env["KEY"]` (bracket), `const env = process.env; env.KEY` (alias),
`const {KEY} = process.env` (destructure), and `"KEY" in process.env` (membership) — all common config
idioms. supports-color reads env via `const {env}=process; 'FORCE_COLOR' in env; env.TERM` → reported 0 Env.
Engine-specific (a JS global-property idiom; rust/java/swift read env via function calls). Bounded: candor-ts
already handles fs/child_process alias+destructure correctly, so this was process.env-specific, not a general
alias-resolution gap. FIXED: extended the recognizer to bracket access, symbol-based const-alias tracking
(`x = process.env`, cleared on reassignment), destructuring, and `in` — including `import process from
'node:process'` as the process global. NO fabrication: a non-env object / a fn param / a reassigned-away
local stays pure (verified). Gated by candor-ts test.mjs (+13 checks) — engine-local, no cross-engine
differential (the idiom doesn't map to the other languages). VERDICT: REAL, moderate (Env is benign but
gate-relevant), fixed + gated, held per Tom's publish-hold.

### 2026-07-15 — candor-scan glob-reexport/use-rebind silent drop: FIXED

Fix for the 2026-07-15 cross-crate glob-reexport find (above). candor-scan now maps a module-qualified call
to its origin through a GLOB re-export (`use x::prelude::*`, recorded under a GLOB_KEY sentinel) and a
`use crate::name` re-bind (resolved through the crate-root re-exports), not only a direct `use x::module`.
Cross-file plumbing added `root_reexports` (captured from the crate root file, seeded into every file's use
map, folded into the incremental digest → byte-identical). Guardrails prevent fabrication: a BARE qualifier
(`dotenvy::var`) is never glob-rewritten (keeps external identity); `self::`/`super::` rebinds keep their
literal (module-relative). Re-export chains traced ONE hop through the crate root; 2+ globs = ambiguous →
honest under-report (never guess the prelude). VERIFIED: iso A/B/C/D all disclose the origin (single scan) +
recover Net under chaining; **sqlx-postgres recovered real effects** — `PgListener::connect → Net`,
`PgConnection::begin`/`begin_with → Db` (Net 0→1, Db 4→7), previously silently pure. NO FABRICATION: clap_builder
byte-identical, reqwest +14 pure blind-spot disclosures (Ipc:3 = real Unix-socket transport, verified in
source) with 0 phantom effects, sqlx-core Net:9 preserved; cargo test green (scan 97, +3 focused). Engine-local
(ts/swift/java resolve re-exports natively — verified), gated by candor-scan tests, held per Tom's publish-hold.

### 2026-07-15 — candor-scan: effects inside cfg_if! macro dropped (dogfood, FIXED)

Dogfooding sqlx-core: effects inside a `cfg_if::cfg_if! { if #[cfg(..)]{..} else {..} }` macro block were
dropped — a covered `std::net`/`std::fs` call inside a cfg_if! arm read PURE. candor-scan already traverses
matches!/vec!/format!/assert!/dbg! correctly; cfg_if! was the specific miss (treated as an opaque external
macro). Technically DISCLOSED (ledger "cfg_if uncovered") but MISLEADINGLY — it named cfg_if the crate when
the dropped effect was the user's own covered call, and unrecoverable (a macro, no crate report to chain).
FIXED: visit_macro now parses the cfg_if arm grammar (`if #[cfg]{..} [else if..]* [else{..}]?`) and walks
EVERY arm's block through the normal effect walk (all-arm over-approximation, consistent with the existing
all-cfg-branch handling); a non-conforming shape falls back to the opaque path (never panics). RECALL WIN:
sqlx-core `net::socket::connect_tcp` [] → [Net] (its cfg_if arm reaches connect_tcp_async_io → a real
TcpStream connect — this also solves the "connect_tcp reads pure" sub-mystery from the glob-fix investigation).
60 functions cleared of the misleading invisible:[cfg_if] disclosure. NO FABRICATION: clap_builder
byte-identical, spot-checked pure functions stay pure; cargo test green (scan 97→102, +5). Bounded to
cfg_if! (matches/vec/format/etc. verified sound; thread_local! declaration correctly pure = lazy first-touch).
Engine-local, gated by candor-scan tests, held per Tom's publish-hold.

### 2026-07-15 — candor-scan: block-nested `use` not tracked (dogfood, CONFIRMED, DEFERRED)

Dogfooding fd: a `use path::X` inside a NESTED BLOCK (`{ use std::process::Command; Command::new(..).status(); }`
/ an `if`/`else` arm) is not tracked → the call resolves to nothing → PURE. Module-level and fn-BODY-level uses
work (verified); only block-nested are missed. SILENT for std calls (std isn't ledger-disclosed). Real hit: fd
main.rs:442 `else { use std::process::{Command,Stdio}; Command::new("gls").status() }` reads pure. NARROW
(block-nested use is uncommon vs module/fn-level) but real. Fix lives in the same use-resolution the glob fix
touched (extend use-binding capture to nested block scopes). STATUS: DEFERRED — recorded not fixed, to avoid a
late-autonomous-run agent round + clippy churn; a focused follow-up in candor-scan collector's use-handling
closes it. VERDICT: REAL, narrow, tracked residual.

### 2026-07-15 — autonomous dogfood+audit run summary

An ~8h autonomous run (Tom: dogfood then audit, held on main unversioned). Swept 4 engines across ~18 real
repos. FINDINGS: (1) candor-scan glob-reexport/use-rebind silent drop [HIGH — FIXED, oracle-green]; (2)
candor-ts process.env bracket/alias/destructure/in recall [MOD — FIXED]; (3) candor-scan cfg_if! macro
effect-drop [MOD — FIXED, oracle-green]; (4) candor-scan block-nested use [NARROW — deferred]. All fixes
held-committed unversioned, gated by engine tests, CI/oracle-validated. NEGATIVE CONTROLS (engine-sound, no
fabrication): sqlx, clap, undici, express, reqwest, axum, ripgrep, Alamofire, swift-nio, TCA, okhttp,
langchain4j (Llm:133 ✓), spring-web, nix, fd, tokio(covered), argmax(disclosed). LESSON reinforced: the
triage bar is "is the target actually statically-knowable / is it disclosed" — most apparent gaps were the
engine being correctly conservative or transitively-correct; the 4 real ones were undisclosed/misleading holes.

### 2026-07-15 — DESIGN FINDING: coverage ledger absent from report JSON → verbs give over-confident verdicts

Dogfooding privacy-manifest on a real OSS iOS app (wikipedia-ios). The verb's verdict does not surface the
underlying scan's COVERAGE GAP. wikipedia-ios uses Location/Photos in uncovered WMF framework modules
(disclosed at SCAN time: 19 modules invisible), so a scan of Wikipedia/Code alone reports Location/Photos
over-declared + ok:true, with NO coverage caveat in the verdict. Safe direction here (over-declaration), but
the dangerous mirror is real: an UNDER-declaration in an uncovered module would be silently missed and read as
a clean "✓ ok". ROOT (spans ALL engines + ALL report-consuming verbs): the coverage/κ ledger is a scan-time
STDERR artifact — NOT in the report JSON (swift report keys: candor/extensions/functions/package; rust:
candor/package/functions). So a downstream verb reading the JSON (privacy-manifest, gains, containment, a
gate) cannot re-disclose that its answer is conditional on partial coverage. This is a §2 report-envelope
DESIGN question (Tom's call, like the extensions/unitKind decisions): make the coverage ledger a first-class
report field, and have report-consuming verbs mark verdicts CONDITIONAL when modules/deps are uncovered
("underDeclared:none is conditional on N invisible modules"). Directly serves the core honesty ethos (no
false all-clear). Found via the verb-layer dogfood angle. STATUS: surfaced for design decision, not
unilaterally fixed (report-schema change spanning the family). VERDICT: REAL, moderate, DESIGN.

### 2026-07-15 — candor-scan block-nested `use`: FIXED (was deferred)

Fixed the block-nested-use silent drop (recorded deferred above). `fninfo` collected function-local `use`
statements from only the TOP level of the fn body; a `LocalUseCollector` (syn::visit::Visit) now walks the
whole body tree and expands every nested `use`. Scope guard (load-bearing): stops at nested fn/impl/mod items
so an inner fn's imports don't leak onto the enclosing fn (proved — without it, `outer()` fabricates Exec).
VERIFIED: all four nesting forms (block, if/else arm, match arm, loop body) resolve like a module-level use;
external-crate use in a nested block discloses like module-level; fd's `determine_ls_command` [] → [Exec] with
cmds=[gls,ls] (the gls-check now Exec, propagates up). NO FABRICATION: fd only gains Exec:5, clap/ripgrep
byte-identical, inner-fn-guard + pure-nested negatives hold; cargo test 242 green; clippy -D warnings CLEAN
(ran this time — the lesson from the cfg_if CI miss). Engine-local, gated by candor-scan tests, held.

### 2026-07-15 — the coverage envelope: FIXED four-way (⟨0.15 staged⟩)

Closure for the DESIGN finding above (coverage ledger absent from report JSON → verb over-confidence).
Built at full scope per Tom's "do the absolute best possible": (1) the §2 `coverage` envelope field — the κ
ledger as data, OMITTED when empty (fully-covered reports byte-identical, verified per-engine against
pre-change binaries); (2) the per-fn `invisible` field FORMALIZED (audit: rust/java/swift already emitted
it; ts emits BOTH postures — invisible for resolvable-but-uncovered, Unknown for unresolvable — the design
doc's audit table corrected); (3) VERB CONDITIONALITY, verdict-preserving (the ⟨0.9⟩ precedent): every
engine's --gate-json re-discloses coverage as an advisory (ok/violations/exit unchanged — byte-identical
verdicts on covered scans, pinned); gains --json carries the current ledger + coverageDelta
{nowUncovered, noLongerUncovered} (names-only compare, java's reference shape adopted cross-engine
mid-wave); candor-swift privacy-manifest gains `conditional: true` + the human ⚠ line. ARCHITECTURE:
engines emit direct facts; verbs compute transitive conditionality from the callgraph they already load —
one shared ledger computation per engine feeds stderr/envelope/gate so the three can never disagree.
THE ACCEPTANCE EXHIBIT: wikipedia-ios privacy-manifest, before {ok:true, no caveat — false confidence} →
after {ok:true, conditional:true, coverage:{uncovered:19}, "⚠ verdict is conditional on 19 uncovered
modules…"}, exits unchanged. Conformance **PART 4s** pins four-way (envelope named + omitted-when-covered +
per-fn disclosure + gate advisory verdict-preserving); full suite green. Tests: java 365, ts 417 main
(full battery green), swift 220 + smoke 99, rust 248 + clippy clean. Engine code marked ⟨0.15 staged⟩;
spec §2/§8 + COVERAGE-DESIGN.md committed; ALL HELD unversioned per the publish-hold.

### 2026-07-15 — terminology correction (Tom): "dogfood" ≠ real-world corpus testing

Correction, appended per this log's own append-only rule rather than rewriting entries. Several entries
above (the 2026-07-15 run especially) say "dogfood"/"dogfooding" for what is actually **real-world corpus
testing** — running the engines against THIRD-PARTY codebases (sqlx, okhttp, chalk, fd, wikipedia-ios, …).
That is the project's established term (the candor-rust `realworld-oracle` workflow; the per-engine
"corpus rounds"). **"Dogfooding" is reserved for candor-on-candor** — the SPEC §7 self-gate ("the
falsifiable form of dogfooding"), candor's own `deny Fs lang` policy on its own code, the engines scanning
their own repos in smoke tests. Where an entry above says "dogfound on <third-party repo>", read
"found by real-world corpus testing on <repo>". Prior entries are not rewritten (append-only); this note
governs, and new entries use the correct terms.

---

## 2026-07-16 — ⟨0.16⟩ baseline-guard corpus test: the Unknown-gain false-positive class

Real-world corpus test of the ⟨0.16 staged⟩ callgraph-aware baseline guard (keys existence on the
baseline callgraph sidecar → a formerly-PURE fn turning effectful is a GAIN), BEFORE shipping 0.16.
Method: version-pair scans (scan v_old → baseline+sidecar; scan v_new under CANDOR_BASELINE) — the exact
"you bumped a dependency" scenario. 10 rust crate pairs (candor-scan, syntactic) + 1 JVM jar pair (gson,
sound bytecode) + candor-on-candor self-gate.

RESULTS:
- **Control (rescan the SAME version vs its own baseline): CLEAN in every case** (10/10 rust, gson,
  self-gate) — 0 fires. The guard does not false-positive on unchanged code. Good.
- **Version-bump fires: 3 rust (serde ×2, itertools ×1) + 1 JVM (gson). ALL were gained-`Unknown`.
  ZERO were a real capability gain** (no Net/Fs/Db/Exec/Llm anywhere in the corpus).
- Triage:
  - serde `VariantRefDeserializer::{struct,tuple}_variant` 1.0.190→1.0.210: **byte-identical source**,
    yet classified pure→Unknown — the syntactic backend's dispatch resolution flipped under surrounding-
    code churn. FALSE POSITIVE.
  - itertools `Powerset::size_hint` 0.11→0.12: code genuinely changed, but the gain is only Unknown (an
    unresolved call to a new helper) — a WEAK signal, not a capability.
  - gson `ConstructorConstructor$9.construct` 2.9.0→2.10.1 (SOUND engine): gained Unknown, but `$9` is an
    anonymous class whose positional numbering is unstable across versions — a DIFFERENT class matched by
    an unstable name. FALSE POSITIVE (identity) + Unknown.

FINDING: the ⟨0.16⟩ guard's exit-1 (CI-breaking) currently fires on an **Unknown-only** gain. On real
dependency bumps this is the DOMINANT (here, the only) fire class, and it is dominated by noise:
syntactic dispatch-resolution variance (rust) and unstable synthetic-member identity (jvm anon `$N`).
Unknown is the §4 TRUST MARKER, not an effect — `pure` policies already exclude it (PART 16, the
2026-07-09 deny-alignment). So exit-1 on pure→Unknown would break CI on innocuous bumps — a
false-alarm class that erodes gate trust (the cardinal sin inverted).

RECOMMENDATION (staged 0.16, not yet shipped — fold in before ship): the baseline guard ratchets (exit 1)
only on gaining a REAL boundary effect (Net/Fs/Db/Exec/Llm/Env/Clock/Ipc/Log/Rand/Clipboard); an
Unknown-ONLY gain is DISCLOSED as advisory (a note, exit 0) — consistent with the family's existing
Unknown-is-not-an-effect treatment. Preserves the real supply-chain signal (pure→Net = exit 1;
conformance PART 15b uses pure→Fs, still passes) while removing the false-positive class. Four-way +
PART 15b amendment. **RESOLVED 2026-07-16**: built four-way (rust reference + java/ts/swift), each with a real-effect-still-fails check; conformance PART 15c (pure→Unknown = exit 0 + advisory note, no [AS-EFF-005]) green four-way; the corpus that found it (serde, itertools) now exit 0 + advisory. Staged with the rest of ⟨0.16⟩.

### 2026-07-17 — the honesty-oracle attribution hole (verify dogfood, candor-ts)

Dogfooding `candor verify` (the dynamic honesty oracle — runs a program under a runtime capture and
checks `observed(f) ⊆ inferred(f) ∪ {Unknown}` per executed fn) found a silent false-all-clear IN
THE ORACLE — the exact failure it exists to catch. The Node arm's runtime→fn attribution anchored a
captured effect site to the nearest fn whose declaration line ≤ the site line, drawing ONLY from the
§2 report's EFFECTFUL fns. Pure fns are omitted from §2 (no loc), so a fn candor called pure carried
no anchor: an effect executed inside it folded onto the nearest PRECEDING effectful fn, whose claim
usually already covered it, and the cardinal-sin escape vanished. Reproduced end-to-end: a pure
`computeTotal` between two Fs fns ran `readFileSync`; the oracle reported HOLDS, 0 violations.

Scope: **Node arm only.** The JVM `-javaagent` arm attributes at ASM transform time by the TRUE
enclosing method (no line-nearest guess), so it caught the identical seeded case (`computeTotal` →
VIOLATION exit 1) — empirically re-confirmed, no change. The syscall arm is program-level (no per-fn
attribution). No static engine relies on this attribution; it is oracle-internal, not a §2 classifier
regression — so no spec change and no version move.

FIXED (candor-ts `5d3e19d`): scan emits `<prefix>.locs.json`, the declaration loc of EVERY analyzed
fn (pure included — the internal `fns` map already held them; only serialization dropped them). The
oracle attributes over the full universe, so a pure fn's effect anchors to ITSELF and surfaces as a
VIOLATION. Without the index it FAILS CLOSED: `attributionComplete=false` + a ⚠ disclosure ("not a
sound all-clear") whenever unlocated pure fns exist (`analyzed.count > |functions|`) — never a silent
HOLDS. The sidecar is excluded from report-sibling discovery (`isReport` + the CANDOR_DEPS dir filter,
which also closed a latent `.hierarchy.json` gap). Gated: 3 unit (fold-without-index DISCLOSED /
caught-with-index VIOLATION / complete-when-no-pure) + 2 e2e (index emitted with pure fns; a pure fn
that runs an effect is caught, not folded). 99 unit + 495 suite green. verify stays UNPUBLISHED on
main. Follow-on (open): a full-universe loc index for rust/swift IF they gain a language-level oracle
arm; end-lines would additionally close the disclosed "module-top-level code after a fn" residual.

### 2026-07-17 — corpus follow-on: the loc index needed SPANS (the start-only fix was regressive)

Correction/completion of the entry above. Corpus-testing the oracle on a real 7k-line app (stock-trading's
smoke test) showed the start-line-only loc index was not just incomplete but REGRESSIVE: a real
`fs.readFileSync` deep inside an effectful `run()` bucketed onto a PURE test-callback arrow declared
earlier (the arrow was the greatest declaration ≤ the site, though it had already closed) → a
DETERMINISTIC false cardinal-sin VIOLATION (exit 1) on honest code. Adding all-fn START locs CAUSED this
by putting pure nested arrows where they shadow their enclosing effectful fn for later sites. Root cause:
attribution needs function SPANS, not starts. FIXED (candor-ts `a218ef9`): every fn record carries
`endLine`; the sidecar is now `{fn:{loc,end}}`; `attribute()` picks the INNERMOST fn whose [start,end]
CONTAINS the site. The real smoke test flips VIOLATED→HOLDS; the seeded silent-miss still VIOLATES; +2
unit (101 unit + 495 suite green). LESSON: a synthetic fixture (my /tmp/vapp) validated the silent-miss
fix but could not have surfaced the false-positive regression — only real code with big functions holding
nested pure callbacks did. Corpus testing earns its keep precisely on the cases you would not think to write.

### 2026-07-18 — provided io::Write/io::Read methods → the local required-method impl (candor-rust, both front-ends)

Probing candor-rust indirect-effect veins (session e1c32da9, Tom "keep going"). Confirmed sound on
closure-in-iterator, fn-pointer→Unknown, `set_var`/`var`→Env, `Command::spawn`→Exec, custom `dyn Sink`/
`dyn Fn`→Unknown. Then a DECISIVE fixture surfaced a real silent under-report: a std-PROVIDED trait method
whose body lives in std and dispatches back into the receiver's REQUIRED method. `w.write_all(..)` /
`w.write_fmt(..)` drive `io::Write::write`; `w.write_char(..)` drives `fmt::Write::write_str`;
`r.read_to_end(..)`/`read_to_string`/`read_exact` drive `io::Read::read` — the driving happens INSIDE std,
invisible to the scan. So a call on a CONCRETE LOCAL `impl Write`/`impl Read` whose `write`/`read` is
effectful read PURE at EVERY caller, even on a concrete receiver (a `FileSink` doing `fs::write` inside its
`write`, reached via `s.write_all()`, with a pure ctor → the Fs vanished). Only the `write!`/`writeln!`
MACRO writer edge had been recovered; the direct METHOD-CALL form had not — asymmetric with the custom
`dyn Sink` case, which correctly disclosed Unknown.

FIX, both Rust front-ends (the shipped stable scan AND the nightly MIR lint — one spec, so both):
 • candor-scan (`445a1e0`): `is_write_provided`/`is_read_provided` (lang.rs) + a coercion charge in
   `visit_expr_method_call` (collector.rs), exactly like the existing iterator-`next` / `to_string`-`fmt`
   coercions. Resolve-or-skip on the concrete local type via `charge_coercion` — a std `Vec`/`File`/`String`
   receiver is absent from `trait_impls` (LOCAL impls only) → no edge; a generic/`dyn` receiver yields no
   concrete type → the documented external-dispatch miss, unchanged. `s.write_all()` → precise Fs.
 • dylint lint (`445a1e0`): generalized `fmt_write_local_edge` → `io_provided_local_edge`, lifting the
   callee-name gate from `write_fmt`-only to the full provided-method set, driven method chosen by
   (trait, provided-method) so an io method never resolves against `fmt::Write` and vice-versa. `w.write_all()`
   → Fs* + its honest Unknown residual (identical to the pre-existing `write!`-macro `via_write_io` case).

Both engines now recover the effect AND AGREE. GATES: full candor-rust workspace suite green (new
in-process regression `provided_io_methods_reach_local_impl_required_method` in candor-scan tests.rs +
extended `ui/write_trait.rs` with the direct method-call forms, re-blessed); ZERO over-fire — A/B on ~900
real functions (candor-rust members, ebman, pgman, tb-tui-common, termcolor, flate2) diffed 0 changed,
and the pure-impl + std-`Vec`-receiver controls stay pure (no fabrication); four-way conformance OK. The
generic/`dyn` Write/Read consumer staying pure is the SAME documented no-fabrication boundary as
`fn f(it: impl Iterator)` (charging it would fabricate a local impl's effect onto a pure generic fn) —
sound because the effect is disclosed at the concrete constructor (`File::create`/`TcpStream::connect`).
LESSON: candor-rust already models Iterator (`collect`→`next`), Display (`to_string`→`fmt`), From, Deref,
and operators as provided→required coercions — io::Write/io::Read were the one std-trait family missing
that treatment. When an engine hand-lists the std traits whose provided methods drive a required method,
audit the list for completeness: a missing family is a silent-pure vein on every concrete local impl.

### 2026-07-18 — R32 cross-engine sweep: the JVM sibling (candor-java `453cbe9`)

The R32 vein (a provided Write/Read method driving the receiver's required override, the driving
invisible inside std/JDK) is not rust-specific — the SOUNDNESS-LOG discipline is to sweep every engine.
The JVM analog: `java.io.Writer.write(String)`/`write(int)`/`append(..)` are CONCRETE JDK methods that
drive the abstract `Writer.write(char[],int,int)`; `Reader.read(char[])`/`skip`/`InputStream.transferTo`
drive the abstract read. A CUSTOM effectful `Writer`/`Reader` subclass reached ONLY via a provided
overload read PURE at every caller — CONFIRMED a `deny Fs` false all-clear on a probe (`w.write("hello")`
on a `LoudWriter extends Writer` whose abstract override does `Files.write` → escaped the gate).

candor-java already had the R16 machinery (reentryTargets CHAs a C_WRITE/C_APPEND contract to a project
override) but only fired it on the SINK ARG of a constructed formatting facade (`new PrintWriter(sink)`) —
never on a DIRECT inherited call's RECEIVER. FIX (contractReentry): a new C_READ contract + key the reentry
on the RECEIVER's TYPE being a java.io stream (isJavaIoStreamType via transSupers), NOT on `min.owner` — an
`invokevirtual` owns the inherited overload at the receiver's STATIC type, usually the project subclass
(`W$LoudWriter`), not the JDK base, so an owner-based gate missed every project-typed receiver (the first
cut fired only for the rare base-typed local `Writer w = new LoudWriter()`). reentryTargets then CHAs the
override; a std FileWriter/StringWriter or a coincidental non-io `write()` resolves to no local override →
nothing. GATES: full suite 412 green + `directProvidedIoMethodReachesReceiverOverride` (every receiver form
carries; pure-impl + coincidental-write + std-sink stay pure); ZERO over-fire A/B across ~12k real functions
(uflexi 10619, tomlib, spring-demo, candor-java-self — 0 changed) with a GENUINE recovery on jsoup —
`DataUtil.crossStreams` + `HttpConnection$Response.writePost` gained a real, previously-SILENT `Clock`
(they drive `ControllableInputStream.read`, whose timeout tracking is Clock — reachable but dropped at the
abstract `in.read()`); four-way conformance OK. So R32 is closed in the rust AND jvm engines. Cross-engine
vein check still OPEN for candor-ts (a Node `Writable._write` reached via `.write()`) and candor-swift (a
protocol extension's provided method driving a required witness) — probing next.

### 2026-07-18 — R32 sweep COMPLETE: swift + ts siblings (candor-swift `ef1d1c7`, candor-ts `77cd4ae`)

Completing the cross-engine R32 sweep. Both remaining engines had the same family — a PROVIDED method
driving a required override the engine never reached — confirmed by probe (each a `deny Fs` false all-clear):

 • candor-swift: an UNQUALIFIED requirement call inside a PROTOCOL EXTENSION (`extension Sink { func
   provided() { req() } }`) dispatches to the conforming type's WITNESS. `req()` (implicit self, `Self: Sink`)
   was collected as a plain Call, never a protoDispatch, so the extension never dispatched to conformers →
   `s.provided()` → `S.req`'s Fs read pure. FIX (CallCollector): an unqualified call inside a protocol
   extension/default body also records a protoDispatch(protocol, name); the Driver's existing bounded-CHA
   (≤12 conformers, protocolMethods guard) resolves it ONLY for a real requirement, so a bare free-fn call
   is filtered there and still resolved by the plain Call (kept — no loss, the `viaFree` control proved it).
   238 suite + regression; 0 over-fire A/B ~1.5k fns (pollen, self, swift-argument-parser — the last
   protocol-extension-heavy).

 • candor-ts: a node:stream Writable's public `.write()`/`.end()` drive the user's `_write`/`_writev`/
   `_final`/`_transform`/`_flush` and a Readable's `.read()` drives `_read` — INSIDE node core, invisible.
   A custom effectful stream reached only via the public API read pure. FIX (scan.mjs): at `recv.method()`,
   when method is a stream driver and `recv`'s class transitively `extends` a node stream base (matched
   SYNTACTICALLY by canonical base name that is NOT a local class — resolves WITHOUT @types/node, and a
   project `class Writable` shadows), edge to the local `_write`/`_read` override. resolve-or-skip: non-stream
   receiver / external stream / inert override adds nothing (the `viaInert`/`viaLogger` controls proved no
   fabrication). 551 suite + 5 regression checks; 0 over-fire A/B ~770 fns (got, node-tar — stream-heavy).

Four-way conformance OK after each. R32 is now closed in ALL FOUR engines — the exact shape of a
cross-engine-agreement blind spot (every engine agreeing on the wrong pure answer) that the SOUNDNESS-LOG
sweep discipline exists to catch. DURABLE: when one engine surfaces a "provided method drives a required
override" vein, sweep the OTHER three immediately — the driving mechanism differs per language (std trait
provided method / JDK abstract-class provided method / protocol-extension default / node-stream public API)
but the silent-pure outcome is identical, and cross-engine agreement HID it in all four at once.

### 2026-07-18 — R33 deinit-glue: an effectful deinit charges the constructing scope (candor-swift `3f5b0f4`)

Probing the destructor/cleanup family (the deliberate R32 leftover). Confirmed swift-only: rust's Drop-glue
already charges the constructing scope (verified — `let r = Resource;`→Fs, `factory()->Resource`→pure);
java's finalizer/Cleaner is non-deterministic (rightly not scope-attributed) and try-with-resources emits an
explicit `close()`; ts has no deterministic destructor. candor-swift MINTED `Type.deinit` but its own comment
said "there is no single caller site to charge" — so `func f() { let r = Resource(); … }` with an effectful
`Resource.deinit` read SILENT-PURE at every caller (a `deny Fs` false all-clear, deterministic under ARC for
a non-escaping local).

FIX (CallCollector), mirroring rust's let-bound Drop-glue: a `let`/`var` LOCAL bound to a fresh CONSTRUCTION
(the ctor/factory-CALL branch, never a bare-identifier alias) of a local type edges to `<t>.deinit`. TWO
subtleties earned in corpus A/B: (1) emit a `propertyEdges` SOFT edge, NOT a typed Call — a typed
`Struct.deinit` fell through to the external-protocol member-dispatch fallback and FABRICATED Unknown for any
conformer of a non-pure external protocol (pollen's `PollenActivityAttributes: ActivityAttributes` — a struct
with no deinit — got a spurious Unknown on `start()`); the soft edge resolves-or-drops via resolveQual and
never reaches that fallback. (2) a returned binding ESCAPES (`let v = View(); return v` — the pervasive SwiftUI
`makeNSView` factory) must be skipped, via a per-function returned-identifier pre-scan (ReturnedNameCollector)
— else 6 makeNSView methods in pollen over-charged. Field-store (`self.f = Type()`) and alias (`let r = other`)
are structurally excluded (not the ctor-binding branch). GATES: 240 suite green + regression; ZERO over-fire
A/B across ~1483 real functions (pollen, swift-argument-parser, candor-swift-self — 0 changed after both
subtleties fixed); four-way conformance OK. DURABLE: the destructor/cleanup vein is deterministic ONLY where
the language guarantees scope-exit destruction (rust Drop, swift ARC deinit of a non-escaping local) — a
GC/finalizer language (java, ts) has no such edge, so this class is a two-engine concern, both now closed.

### 2026-07-18 — R34 + R35: swift generic-operator + @dynamicCallable dispatch (candor-swift `7f6ba58`, `2667fdc`)

Continuing the autonomous probe of indirect-dispatch veins. Confirmed SOUND (no fix) across a wide battery:
default-parameter effects (folded into the fn — `caller()` that omits the arg carries; only the explicit-arg
caller over-reports, a precision cost not a sin), property observers `didSet`/`willSet`, subscripts get/set,
computed getters, property WRAPPERS, `perform(#selector)` (discloses Unknown), async/concurrency (Task /
async let / TaskGroup / detached / setTimeout / queueMicrotask / Promise executor — spawned-closure effects
charged lexically), keypath access, result builders, `defer`, `map` closures, and rust's `Index` trait. Two
real SILENT-PURE misses found + fixed, both swift-only:

 • R34 — a GENERIC/protocol-typed OPERATOR: `a + b` where `a: T: P` and `P` declares `static func +`.
   candor-swift dispatches a generic METHOD (`x.act()` on `x: T: P`) to conformers via bounded CHA, but the
   operator visitor only edged a CONCRETE localTypes operand — a generic/protocol operand resolved no
   concrete type → an effectful `+` witness read pure. FIX: when neither operand is concrete-local, check
   each operand identifier for a protoTyped binding and emit a protoDispatch(P, op); the Driver's bounded CHA
   resolves the conformer witnesses, gated on P declaring `op` (a std `Numeric`/`Comparable` bound has no
   local witness → nothing). NOTE rust has the same generic-operator shape but its operators are ALWAYS on
   external `std::ops` traits, which candor-scan deliberately does NOT CHA (dispatching to all local `Add`
   impls would fabricate `Fs` on an `i32+i32` call) — so rust's `adds_generic<T: Add>`→pure is the documented
   external-trait boundary, not a fixable sin. Swift was fixable precisely because its operator protocol is
   LOCAL. java/ts have no operator overloading.

 • R35 — a `@dynamicCallable` value: `c(1, 2)` desugars to `c.dynamicallyCall(withArguments:)`, an effectful
   witness that read pure (candor edged only the `callAsFunction` value-call desugar). FIX: at a bare `f()`
   on a local-type instance, also emit a `<t>.dynamicallyCall` soft edge; resolveQual drops it for a
   non-@dynamicCallable type. Niche (Python-interop / DSLs) but a real cardinal sin. `@dynamicMemberLookup`
   (`d.member`) already disclosed Unknown — sound, left as-is.

Each: full suite green + a named regression, ZERO over-fire A/B ~1483 real fns (pollen, swift-argument-parser,
candor-swift-self), four-way conformance OK. DURABLE: swift has a LONG tail of dispatch-desugar veins
(operators, callAsFunction, dynamicallyCall, dynamicMemberLookup, keypath, subscript, property wrappers,
result builders) — each a separate desugar path that must be wired into the effect graph; sweep them as a
family, and the discriminator for "fix vs leave" is whether the dispatch target is LOCAL (fix, precise) or
EXTERNAL (leave — CHA would fabricate or flood, per the Iterator/Add precedent).

### 2026-07-18 — R36: rust trait-default → required-method dispatch (candor-rust `7f80e41`)

The general form of the R32 vein (a default method calling a requirement) swept across all four engines.
Java (`default void saveAll(){ persist(); }`) and TS (`abstract class Store { abstract persist(); saveAll(){
this.persist(); } }`) already resolve it — java via bytecode CHA on the default's `invokeinterface this.persist`,
ts via class-CHA — and swift via R32's protocol-extension→conformer dispatch. candor-RUST was the one miss:
inside a trait default, decls.rs types `self` as the TRAIT, so `self.persist()` is `Store::persist` — a bodiless
REQUIREMENT (no unit) and the existing trait-default fallback keys `type_to_traits` on IMPL types, not the trait
— so an effectful `impl Store for Db { fn persist }` reached ONLY through the default read silent-pure.

FIX (scan.rs typed-method fallback): when the receiver type is a LOCAL TRAIT (`trait_decls`) declaring `leaf`
and nothing resolved locally, CHA `leaf` over the trait's IMPLS (`trait_impls`) and edge to each impl witness,
bounded ≤12. The `trait_decls` gate stops a struct-named receiver from hijacking; the bounded union is sound
(a default's callers can use any impl); a pure impl contributes nothing. GATES: full workspace + regression
`trait_default_dispatches_required_to_impl_witness`; corpus A/B ~950 real fns ZERO effect changes (flate2 gains
2 call-graph edges to PURE compression targets — coverage, not fabrication); four-way conformance OK. So this
vein is now closed four-way: rust R36 (fix), swift R32, java + ts (already sound). Also part of the broad
autonomous dispatch-vein sweep that confirmed SOUND (no fix): default-parameter effects, property observers /
subscripts / computed getters, property wrappers, `perform`, async/concurrency (Task/async-let/TaskGroup/
setTimeout/Promise-executor), keypath, result builders, `defer`, `map`/`forEach` closures, rust `Index` /
`?`-effectful-From / enum / closure-field, java Stream / CompletableFuture / enum-abstract / anon-inner /
Runnable, ts async-gen / yield* / Proxy / #private / object-getter. TS method DECORATORS that rewrite a method
to inject an effect are a known UNFIXABLE limitation (blanket-Unknown on every decorated call would flood the
ubiquitous metadata-only `@Get`/`@Input`; the effect mis-attributes to the decorator fn) — the "can't see
arbitrary runtime metaprogramming" boundary.

### 2026-07-18 — R37 (rust collection-of-trait-objects) + R38 (java unbound interface-method-ref)

Continuing the autonomous dispatch-vein sweep — the heterogeneous-collection iteration shape, probed four-way.

 • R37 (candor-rust `27b0e34`): iterating a COLLECTION OF TRAIT OBJECTS — `for it in &items { it.go() }` /
   `items.iter().for_each(|it| it.go())` over `items: Vec<Box<dyn Doer>>` (or `&[Box<dyn>]`) — read
   silent-pure. `elem_type` returns None for a `dyn`/`impl` element (no nominal path), so the loop/closure
   var was untyped and its method call dropped. FIX: a new `elem_trait_leaves` (the trait-object counterpart
   of `elem_type`) seeds an `elem_trait_of` map per collection PARAM; the for-loop + iterator-adapter-closure
   binders type the element var into `trait_vars` (bounded-CHA dispatch) instead of `vars`. A concrete-element
   collection keeps the `vars` route (no over-fire); a >12-impl dispatch discloses Unknown per the existing
   bound. Corpus A/B ~950 real fns 0 regressions + one GENUINE recovery: ebman `run_rules(&[Box<dyn Rule>])`
   over 18 rule impls (>12) now discloses Unknown instead of silent-pure. Swift already handled `[any Doer]`;
   ts (array-of-interface) + java (List<Interface> enhanced-for) already handled it too.

 • R38 (candor-java `7047572`): an UNBOUND interface-method reference — `stream.forEach(Doer::go)` /
   `list.removeIf(Rule::stale)` — targets an ABSTRACT method (no body), so the LambdaMetafactory Handle edge
   was silent-pure, while the equivalent LAMBDA (`it -> it.go()`) worked via its synthetic body's
   invokeinterface CHA. The ubiquitous idiomatic-streams shape read pure at every caller. FIX: at the Handle
   site, CHA the method-ref target over the owner's PROJECT impls exactly like a direct invokeinterface —
   narrow → edge every override, broad (>CHA_FANOUT_LIMIT) → Unknown. A concrete/lambda/static-pure target is
   unchanged. Corpus A/B ~12.4k real JVM fns ZERO over-fire/regression. Distinct from the R37 sweep: this is
   the METHOD-REF sugar of forEach dispatch (ts/swift desugar method-refs to lambdas/closures the analyzer
   already walks, so the sugar is transparent there; java's bytecode method-ref is a distinct invokedynamic
   target). Both closed. Session dispatch-vein tally: R32 (four-way provided→override), R33 (swift deinit),
   R34 (swift generic-operator), R35 (swift @dynamicCallable), R36 (rust trait-default), R37 (rust dyn-vec),
   R38 (java method-ref) — every one gated with a regression + corpus A/B + four-way conformance, all riding 0.22.

### 2026-07-18 — R37b + R39: generic-bound collection elements (candor-rust `b00f2e6`, candor-swift `c67506c`)

Extending the collection-of-trait-objects vein (R37) from concrete `dyn` elements to GENERIC-BOUND elements.

 • R37b (candor-rust `b00f2e6`): `fn f<T: Doer>(items: Vec<T>) { for it in items { it.go() } }` (and
   `where T: Doer`, and `.iter().for_each`) read silent-pure — R37 seeded `elem_trait_of` with EMPTY generic
   bounds, so a bare `T` element didn't resolve. FIX: (1) thread `generic_bounds_of(sig)` into
   `elem_trait_leaves` so `T` resolves through its bound to `["Doer"]`; (2) the for-loop / adapter binders
   PREFER the trait-object route whenever `elem_trait_of` is non-empty — `elem_type` returns the bogus
   generic-param name "T" (not None) for a `Vec<T>` element, so the old `elem.is_none()` gate took the dead
   concrete route. 0 over-fire A/B ~950 fns.

 • R39 (candor-swift `c67506c`): the swift twin — `func f<T: Doer>(items: [T])` iterated read pure while the
   existential `[any Doer]` worked. FIX: resolve the array element through `genericBounds` in the param
   seeding (one line), mirroring the plain-`x: T` generic resolution, so `[T: Doer]` types the element as
   the protocol `Doer`. 0 over-fire A/B ~1.5k fns. Both gated with regressions + four-way conformance OK.

OPEN (next target, precisely characterized — NOT a silent residual, a queued mechanical fix): the candor-rust
FIELD form — `struct Registry { handlers: Vec<Box<dyn Handler>> }` + `self.handlers.iter().for_each(|h|
h.handle())` — still reads silent-pure. R37/R37b seeded `elem_trait_of` for PARAMS (per-fn `seed_elem_of`);
the FIELD form needs a parallel `field_elem_trait` index (the trait-object counterpart of `field_elem`)
populated in `collect_decls` from the struct field walk (using the struct's `generic_bounds_of_generics`,
already computed there) and threaded through the cache/merge layer + `ElemIndexes` + the collector's
`resolve_elem_trait_leaves` Field arm — exactly the shape of the existing `field_elem` plumbing. Deferred to
its own pass to avoid rushing ~15-site multi-file plumbing (incl. the MergedDecls merge) at session depth;
registries/observers-as-fields are common, so this is high-priority. The swift/ts/java field forms should be
swept at the same time (java erases generics + the enhanced-for over a field already worked in the R37 probe;
ts/swift field-of-existential likely already handled — confirm).

### 2026-07-18 — R40: the collection-of-trait-objects FIELD form (candor-rust `3f5dd5a`) — vein now fully closed

The queued follow-on from the R37b entry, DONE. `struct Registry { handlers: Vec<Box<dyn Handler>> }` +
`self.handlers.iter().for_each(|h| h.handle())` read silent-pure — R37/R37b's `elem_trait_of` covered PARAMS
only. FIX: a new `field_elem_trait` index (trait-object counterpart of `field_elem`), populated in
`collect_decls`'s struct-field walk via `elem_trait_leaves` + the struct's `generic_bounds_of_generics`
(covers `Vec<Box<dyn Handler>>` AND a generic `Vec<T>` field on `struct Registry<T: Handler>`), threaded
through the cache/merge layer (FileDecls/MergedDecls/merge_decls, serde-default, FOLDED INTO
`decl_index_digest` — the `every_merged_decls_field_is_folded_into_the_digest` guard proves the incremental
cache won't serve a stale FnInfo) + ElemIndexes → the collector's `resolve_elem_trait_leaves` Field arm.
~15-site plumbing, all mechanical, no merge-layer bug. Gated: full workspace + digest guard + extended
regression (concrete / for_each / generic FIELD carry; concrete-element field pure); corpus A/B ~950 real
fns ZERO over-fire; four-way conformance OK.

CROSS-ENGINE SWEEP of the field form (probed): swift (`self.handlers: [any Handler]` for-loop + forEach),
ts (`this.handlers: Handler[]`), java (`List<Handler>` enhanced-for + `forEach(Handler::handle)`) ALL
already handle it → rust was the sole miss. So the collection-of-trait-objects vein is now CLOSED four-way
across params, generic bounds, AND fields. Session dispatch-vein arc complete: R32 (four-way provided→
override), R33-R35 (swift deinit/generic-operator/@dynamicCallable), R36 (rust trait-default), R37/R37b/R40
(rust dyn-collection param/generic/field), R38 (java method-ref), R39 (swift generic-array) — every one
regression-gated + corpus-A/B'd + four-way-conformance-clean, all riding 0.22.

### 2026-07-18 — R41: container / Option trait-object dispatch (candor-rust `0b0881e` + candor-swift `54e54c8`, done IN PARALLEL)

Extending the collection-of-trait-objects vein to the remaining common container shapes, and — as a test of
parallel execution — the rust and swift halves were done SIMULTANEOUSLY (a background subagent took swift
while the main loop took rust), reconverging only at four-way conformance (the one serialization point). Both
were independent repos, so no conflict; conformance OK after.

 • candor-rust (`0b0881e`): (1) MAP VALUES `HashMap<String, Box<dyn Handler>>` via `.values()` —
   `elem_trait_leaves` takes a map's 2nd type arg; (2) SMART-POINTER / interior-mutability chains
   `Arc<Mutex<Vec<Box<dyn>>>>` / `Rc<RefCell<..>>` — `elem_trait_leaves` peels Mutex/RwLock/RefCell/Cell and
   `resolve_elem_trait_leaves` peels the guard chain (`.lock`/`.unwrap`/`.borrow`/`.read`/`.as_ref`/…);
   (3) OPTION/RESULT unwrap in EVERY form — `.map`/`for`/`.iter()` (elem_trait_leaves peels Option/Result to
   the payload) PLUS the pattern forms `if let Some(d)` (visit_expr_if), `match { Some(d) => }`
   (visit_expr_match), `let Some(d) = o else` (visit_local), each scoping the payload into `trait_vars` via a
   `some_ok_binding` helper. Corpus A/B: ZERO over-fire + 4 GENUINE recoveries in pgman — `cancel_running_query`
   et al. dispatch a `let Some(d) = self.cancel_dispatcher.as_ref() else` over `Option<Box<dyn CancelDispatcher>>`
   whose `PgCancelDispatcher::dispatch` does `tracing::warn!` = Log (silent-missed before).

 • candor-swift (`54e54c8`, background subagent): the swift twin — dict `.values` iteration, optional if-let,
   and optional `.map` over `[any Doer]` / `(any Doer)?` all read pure. Fixes in CallCollector: `elementTypeOf`
   yields the dict VALUE for a `.values` base; the OptionalBinding visitor binds a protoTyped-param unwrap into
   `vars` so the existing `localProtocols` dispatch fires; the `.map` element-closure falls back to the
   protoTyped payload. All funnel into the existing bounded-CHA `protoDispatches`. 244 tests + regression; A/B
   pollen 3 NEW (genuine — `severities.values.contains { $0 != .none }` types `$0` as a local enum whose
   Comparable `!=` witness reads honest Unknown via R34, sound), others 0.

ts + java already handled all these container/optional forms (probed: Map values, Optional.ifPresent/get,
Record.values). PARALLELISM NOTE: a cross-engine vein is N independent fix-cycles that fan out to per-engine
subagents (separate repos, separate build+test) and reconverge at four-way conformance; within one engine the
edit→build→test→A/B cycle stays sequential. This session's arc: R32–R41, ~15 fixes across all four engines,
every one regression-gated + corpus-A/B'd + four-way-conformance-clean, all riding 0.22.

### 2026-07-18 — R42: a METHOD factory returning a trait object dispatches (candor-rust `2c59637`)

`self.handler().go()` where `handler(&self) -> &dyn Doer` / `-> Box<dyn Doer>` read silent-pure, while a
free/static `Reg::make().go()` (an `Expr::Call`) already dispatched. Root cause: `resolve_recv_type`'s
MethodCall arm walked THROUGH the chain to the base receiver's type (`Reg`), so the concrete path fired
(`Reg::go`, unresolved) and shadowed dispatch; `resolve_recv_traits` had only a free-fn Call arm, no
MethodCall arm. FIX (collector): (1) `resolve_recv_type` returns None for a method whose recorded return is
a `<dyn>` sentinel (None only declines typing, never fabricates); (2) `resolve_recv_traits` gains a MethodCall
arm decoding the `<dyn>` sentinel by leaf, like the Call arm. `record_return` already encoded `&dyn`/`Box<dyn>`/
`impl Trait` method returns. Full workspace + regression; corpus A/B ~950 fns 0 over-fire; four-way conformance
OK. Rust-only — swift/ts/java already handle getter-returns-interface (probed). Session dispatch-vein arc:
R32–R42, ~17 fixes across all four engines, R41 done partly in PARALLEL (swift subagent + main-loop rust),
every one regression-gated + corpus-A/B'd + four-way-conformance-clean, all riding 0.22.

### 2026-07-18 — dispatch-vein LONG-TAIL residuals (characterized, queued — NOT silent-unknowns)

After R32–R43 the trait-object/dispatch vein is covered comprehensively (direct calls; provided-method →
required override; trait/interface defaults; generic & dyn params; fields; HashMap values; Arc<Mutex>/RefCell
guard chains; Option/Result unwrap in all forms; getter/method returning a bare trait object; supertraits).
The remaining misses are the NICHE long tail — each real but progressively rarer; recorded here so they are
documented, not silently dropped, and picked up in a focused pass:

 • rust — a METHOD returning a COLLECTION of trait objects (`for d in r.all()` where `all() -> Vec<Box<dyn
   Doer>>`): `record_return` records a SCALAR `<dyn>` sentinel for a direct dyn return (R42) but not an
   ELEMENT-dyn sentinel for a collection return, and `resolve_elem_trait_leaves` has no method-call arm →
   silent-pure. Needs a distinct element-dyn return sentinel (the scalar one means "the value IS a dyn" for
   resolve_recv_traits; conflating them would mistype `r.all()` as a dyn). Moderate.
 • rust — NESTED containers `Vec<Option<Box<dyn>>>` (`for o in xs { if let Some(d) = o { .. } }`): `trait_leaves`
   doesn't peel Option, so the Vec element `o` gets no dyn leaves and the inner if-let has nothing to unwrap.
   Two-level unwrap; niche.
 • rust — TUPLE-destructured factory return `let (_, d) = make_pair()` where `make_pair() -> (u32, Box<dyn
   Doer>)`: the tuple binder doesn't capture a dyn element. Niche.
 • rust — BLANKET impls `impl<T: Super> Ext for T` + `i.ext()`: candor keys `trait_impls` by concrete type, so
   a blanket impl (applies to all T meeting a bound) isn't in the CHA universe → silent-pure. Structurally
   harder (blanket resolution). Moderately common for extension-trait crates.
 • rust — `Default::default()` TURBOFISH/inferred (`let c: Cfg = Default::default()` with an effectful
   `impl Default for Cfg`): the explicit `Cfg::default()` resolves, but the inferred form needs to edge the
   annotated type's `default` (like `charge_from` does for `From`/`.into()`). Niche (effectful Default is
   unusual).
 • ts — a sub-interface SUPER-method (`s.base()` on `s: Sub` where `interface Sub extends Sup`, base ∈ Sup)
   reads Unknown (disclosed, SOUND — not a cardinal sin) rather than the precise Fs java/rust give. A
   PRECISION opportunity, not a soundness bug; left per the honesty-first posture.

The rust supertrait fix (R43) has a cross-engine sibling: swift MISSES it SILENT-PURE (the same cardinal sin);
java handles it (bytecode CHA); ts discloses Unknown (sound). The swift fix is in flight (parallel subagent).

### 2026-07-18 — R43-swift: the super-protocol sibling (candor-swift `11f40a7`, parallel subagent)

The R43 supertrait vein's swift half, done as a parallel background subagent while the main loop did rust
R42/R43. `s.base()` where `base ∈ Sup`, `s: any Sub` / `T: Sub`, `protocol Sub: Sup` read silent-pure — two
gates rejected the inherited member: DeclCollector never recorded the `: Sup` inheritance clause (protocols
don't go through `pushType`), and the protoDispatch gate checked `protocolMethods[Sub].contains(member)` only.
FIX: a dedicated `protocolSupers: [String: Set<String>]` map (recorded from the protocol inheritance clause,
threaded through the per-file merge) + a transitive `protoOrSuperDeclares(proto, member)` walk at the
protoDispatch AND protoPropRead gates; on a super match it still CHAs `conformers[Sub]`. GATE: 245 tests +
regression; A/B ZERO over-fire (pollen/swift-argument-parser/self all 0). NOTABLE — the subagent's FIRST
approach reused the existing `supertypesOf`/`conformers` transitive index for protocol inheritance and
OVER-FIRED badly (a 139-fn Unknown blast on swift-argument-parser, because a protocol name in `conformers[P]`
polluted every concrete-dispatch CHA over P and broke its `impls.count == conf.count` guard); it caught this
in its own corpus A/B and switched to the dedicated map — the A/B gate doing exactly its job on a parallel
branch. So the supertrait vein is closed: rust R43, swift `11f40a7`, java (bytecode CHA) already; ts discloses
sound Unknown (a precision residual, not a sin). Four-way conformance OK after reconvergence.

### 2026-07-18 — R44: method/factory returning a collection of trait objects (candor-rust `afcd20a`)

Cleared the most common of the just-queued long-tail residuals. `for d in r.all()` where `all() -> Vec<Box<dyn
Doer>>`, and `if let Some(d) = self.opt()` where `opt() -> Option<Box<dyn>>`, read silent-pure (record_return
recorded the Vec return as the useless "Vec"). R42 handled a SCALAR-dyn return; this is the COLLECTION sibling.
FIX: a new `<elemdyn>` return sentinel (element bound leaves for a collection-of-dyn return), filtered from
concrete typing in `ctor_type` like the scalar `<dyn>`, decoded by new MethodCall/Call arms in
`resolve_elem_trait_leaves` (falling back to the scalar `<dyn>` for an Option-returning method, safe because
that arm is only reached in a collection/option context). Full workspace + regression; corpus A/B ~950 fns 0
over-fire; four-way conformance OK. REMAINING long-tail (still queued): rust nested `Vec<Option<Box<dyn>>>`,
tuple-destructure of a dyn factory return, BLANKET impls (`impl<T: Bound> Ext for T`), `Default::default()`
turbofish; ts sub-interface super-method precision (Unknown→Fs). Session dispatch arc: R32–R44 across all four
engines, ~20 fixes, R41/R43 halves done in PARALLEL via subagents, every one regression-gated + corpus-A/B'd
+ four-way-conformance-clean, all on 0.22.

### 2026-07-18 — post-dispatch probing: gate surface verified sound; R48/R49 characterized (rust-scan)

After the R32–R44 dispatch arc saturated, probed two fresh families. **(1) The gate/verify surface** —
confirmed SOUND on both axes a machine consumer depends on. `Unknown` handling: `deny Fs` does NOT silently
pass a disclosed `Unknown` (prints the `→ add 'deny Fs Unknown'` remediation), `deny Unknown` catches it, and
a MISTYPED reason-class (`Unknown[callback]` where the class is `unresolved`) FAILS CLOSED (flags anyway, not a
silent pass). Completeness manifest (0.21): an unparseable file under `deny Fs` yields **exit 2**,
`ok:false, incomplete:true`, and names the unanalyzed file — no green gate over code candor couldn't read.
**(2) Two theoretical rust-scan veins found + characterized as residuals, NOT shipped**, both on evidence:

**R48 — local `macro_rules!` with a DIRECT-I/O template.** `macro_rules! do_io { () => { fs::write(..) } }`
reads pure (`visit_macro` scans invocation ARG tokens + expands `cfg_if!`, never the definition template).
Metavar templates (`$m` interpolating a caller expr) ARE already caught (the effectful call comes from the
arg). Zero corpus incidence: dozens of crates, 8 `macro_rules!` total, NONE direct-I/O (only the synthetic
probe). Pre-designed fix (deferred): cache-threaded `local_macros` map → `$`-strip + parse-or-skip the arm
template + inline `visit_block`. Not shipped — 15-site plumbing for a construct that never appears (real
effectful macros interpolate a caller expr or call a fn, both already caught).

**R49 — local effectful-`Drop` guard held as a struct FIELD.** `struct Session { _g: Guard }` constructed
locally runs `Guard::drop` at scope exit but reads pure; only the DIRECT case (a local of the drop-type) is
charged. A prototype fix (transitive drop-owner closure over `drop_types` × `fields`/`field_elem`, no new
cache plumbing) was BUILT + regression-green, then **REVERTED on the A/B gate**: it fabricated **14 false
`Unknown`s on flate2** — `Compress::new`/`Decompress::new`/… CONSTRUCT AND RETURN the owner, whose owned
`Stream` FFI-Drop runs in the CALLER's scope, not the constructor's. Field-owners are overwhelmingly
constructed-to-be-RETURNED (resource wrappers), so the returned-value ESCAPE case DOMINATES this vein — unlike
direct guards (used locally), where the same over-approximation is rare/accepted (the existing
`returns_via_let` over-charge). A correct fix needs a swift-R33-style escape gate, which needs return-type info
not cheaply available (FnInfo carries none; the `returns` index is leaf-keyed so `::new` collides → dropped
ambiguous). Zero corpus incidence for direct effects (flate2, the only real local-Drop crate, flushes to a
generic writer — not a classified effect). LESSON: the A/B gate did its job — a fix that is green on synthetic
regressions can still do NET HARM on real code; the naive drop-field extension fabricates on the pervasive
constructor pattern while helping ~zero real cases. Both R48/R49 are documented-with-fix, not accepted-blind:
the honesty-first posture prefers a disclosed known-gap over shipping either a no-incidence plumbing round or a
fabricating over-approximation.

### 2026-07-18 — R50: inline struct-literal receiver typed (candor-rust `71fad60`)

A REAL (shipped) fix in the same probing session that produced R48/R49 (both residual). A value
CONSTRUCTED INLINE and immediately consumed read silent-pure: `for _ in (RowIter { conn }) {}` and
`(RowIter { conn }).count()` — the iterator-forcing edge (`charge_iter_next`) and method resolution both
type the receiver via `resolve_recv_type`, which handled a constructor CALL (`Expr::Call` → `ctor_type`) but
had no `Expr::Struct` arm, so an inline struct literal returned None. FIX: one `Expr::Struct` arm delegating
to `ctor_type` (which already types a struct literal via `type_from_value_path`); `Paren`/`Group` wrappers
were already unwrapped by existing arms, so a parenthesised for-head (Rust grammar REQUIRES the literal
parenthesised there) reaches it. The var / method-result / consuming-combinator cases already worked — only
the inline-literal receiver was missed. SOUND: the receiver genuinely IS that type, and scan.rs's
`local_types` gate confines any resulting `Type::method` link to LOCAL types → never fabricates. Contrast
with R49 (reverted): R49's A/B fabricated 14 Unknowns on flate2; THIS A/B is **zero over-fire AND zero
removal across ~2600 real fns** (syn 1442, serde_json 348, tokio 148, clap_builder 142, hyper 124,
candor-scan 73, flate2 48, regex 16) — the same gate cleanly separating a sound completion from a fabricating
over-approximation. Four-way conformance OK. FOUR-WAY SWEEP: ts (`new RowIter().drive()`) and swift
(`RowIter().drive()`) both already SOUND — rust-specific because only Rust has struct-literal construction
syntax distinct from a call; the others construct via `new`/`T(..)` calls that already type the receiver.
LESSON pair with R49: incidence is low for BOTH, but R50 ships (correct + zero-over-fire) while R49 doesn't
(fabricates) — the discriminator is the A/B gate, not the incidence.
