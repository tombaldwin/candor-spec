# Soundness log — the adversarial rounds and κ batches, in full

The append-only evidence scroll behind [SOUNDNESS.md](SOUNDNESS.md). The tracker keeps the
*instrument* (scorecard, residual register, metrics, index); this file keeps the *prose* — one
`### <date> — <slug>` entry per adversarial round / κ batch / review patch, with the find, the why,
the fix, and the gates. Entries sit in chronological order; new ones append at the end. Entry BODIES
are append-only history — corrections are appended, never edited in. The index table in
SOUNDNESS.md §8.1 is the one-line-per-entry view.

### 2026-08-24 — `"peeked": "true"` deleted a refusal: the coercion class, four instances (candor-java `0d9e7fc`)

**The sin.** `Query.readEnvelope` read `excluded[].peeked` with `getAsBoolean()`. Gson answers
`Boolean.parseBoolean` on a JSON *string*, so `"peeked": "true"` — a string where a boolean belongs —
came back `true`, hit `if (peeked || judgedElsewhere) continue;` and DELETED the ⟨0.32⟩ unread-code
refusal. Exit 2 → exit 0, `ok:true`, no `incomplete`, nothing on stderr. Four-way on identical bytes:
java 0, rust 2, ts 2, swift 2.

**Why it survived.** The SAME commit that shipped it hardened `judgedElsewhere` against exactly this,
its comment calling that key "the ONE key here that can DELETE a refusal" — one block below the key it
left coercing. The comment is part of why nobody looked up. Conformance had `judgedElsewhere:
non-boolean` cells FOUR-WAY and no `peeked` cell at all: **the sibling key was pinned and this one was
not.**

**Only a STRING was fail-open.** `1`, `0` and `null` coerce to `false` and refused anyway — *for the
wrong reason*. Reasoning about the class would have stopped at "this coerces safely"; the shapes had
to be enumerated.

**The class, not the instance.** The sweep's generalisable statement: *every top-level shape check on
these keys had landed and every member/field read beneath it still coerced.* Four more instances, each
measured turning a violation into a pass — `inferred` as string/null/mixed-array, `interfaceUnion:
"true"`, `fn: {}` (exit 1 → 0), and `unanalyzed: [123]` (exit 2 → 0).

**The search bias worth remembering.** All four were found because they MOVED AN EXIT CODE — a biased
sample of exactly the wrong kind, since the readers are shared, so any key with no exit-code
consequence sits behind the identical coercion where no exit-driven search reaches it (`unitKind`, 14
of 15 array keys, `entryPoint`, `unresolved`, four of `outOfScope`'s five fields). The fix pins the
READER's argument list, so adding a key without a row makes the claim false.

**The over-charge backed out.** `excluded[].class` was hardened in the first draft and should not have
been — nothing decides on that token. That would have been a fail-closed regression shipped inside a
fail-open repair; it withholds and answers, with a control row saying why.

**Pinned:** PART 62's `peeked`-corruption cell, four-way over `"true"`/`"false"`/`1`/`0`/`null`/`{}`/
`[]`/absent plus the `bool-true`/`bool-false` over-charge pair (candor-spec `3d3af89`). All four engines
clean on every shape at HEAD; the arm was falsified by injecting `bool-true` into the shape set. This is
the FOURTH type-coercion bug to delete a refusal in this family — JS truthiness, Foundation bridging
integer `1` to a number `as? Bool` accepts, `Gson.getAsBoolean` on `judgedElsewhere`, and now on
`peeked`. **Read the value's own type tag; a bare cast coerces.**

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

### 2026-07-18 — R51: smart-pointer ctor typed as its pointee (candor-rust `f93bd6a`)

Second REAL ship of the receiver-typing sweep (after R50). `let db = Arc::new(Db::new()); db.migrate()`
read silent-pure — `ctor_type`'s Call arm typed the ctor as the impl-less wrapper "Arc" and DROPPED the
`<Db>` generic arg, so `db.migrate()` sought "Arc::migrate" and dropped. `type_path` already peels an
`Arc<Db>` FIELD/param (the duct corpus find — a whole public API pure because `self.0: Arc<ExpressionInner>`);
this closes the LOCAL-BINDING form `let x = Arc::new(..)` + the inline `Arc::new(Db::new()).query()` shape.
FIX: `ctor_type` types a transparent owned smart-pointer ctor (`Box`/`Rc`/`Arc::new(x)`) as the pointee
(the arg's `ctor_type`); Mutex/RefCell/RwLock/Cell are NOT peeled (their `.lock()`/`.borrow()` live on the
wrapper, so `Arc::new(Mutex::new(x))` stays "Mutex"). SOUND: the value auto-derefs to the pointee, and the
`local_types` gate confines the `Type::method` link to LOCAL types. A/B **zero over-fire AND zero removal
across ~2400 real fns**; recovers the realistic Arc<Service>/Box<Engine> setup pattern. CRITICAL CHECK — the
fix types `db` as the pointee "Db", so I verified it did NOT open the clone-fabrication hole the existing
`smart_pointer_receiver_resolves_pointee_method_but_not_clone` test guards: a local `let db = Arc::new(Inner);
db.clone()` with an EFFECTFUL `Inner::clone` stays pure (the general `.clone()` suppression is receiver-type-
independent). Regression added; four-way conformance OK; rust-specific (Box/Rc/Arc have no java/ts/swift
analog). The clone-REBIND sibling (`let b = a.clone(); b.run()` loses `b`'s type) is left as R52 — low
incidence + touches `visit_local`'s hot typing path; the safe fix is a clone-only type-carry (carry the type,
never charge the clone). Session receiver-typing arc: R50 (inline struct-literal) + R51 (smart-pointer ctor)
shipped, R52 residual — all discovered while sitting in `resolve_recv_type`/`ctor_type` after the R48/R49
probes; the A/B gate passed both ships (zero over-fire) and had rejected R49 (14 flate2 fabrications).

### 2026-07-18 — R52 SHIPPED: clone-rebind type-carry recovers the clone-then-use idiom (candor-rust `2f487dd`)

Characterized as a residual earlier this session, then reconsidered + shipped when the A/B revealed it
recovers REAL silent-pure. `let b = a.clone(); b.method()` read pure — `ctor_type` doesn't consult `vars`
for the clone receiver, so `b` typed to nothing and `b.method()` dropped. `Clone::clone(&self) -> Self` is
type-preserving, so the rebind keeps the receiver's type. FIX: at the `let` binding, an untyped
`<expr>.clone()` init carries `resolve_recv_type(<expr>)` to the binding. The clone CALL stays uncharged, so
the anti-fabrication guard (`smart_pointer_receiver_resolves_pointee_method_but_not_clone`: `arc.clone()` is
the pure `Arc::clone`, never the effectful pointee clone) is untouched — verified a local `let db =
Arc::new(Inner); db.clone()` with an EFFECTFUL `Inner::clone` stays pure. This is THE async-service idiom:
`let self_ = self.clone(); self_.call_async(dst).await` (tower/hyper `Service::call` clone self into the async
block) and `let mut cmd = self.cmd.clone(); cmd.build()` (command builders). A/B — ALL recoveries, ZERO
concrete fabrication, ZERO removed: **hyper-util `HttpConnector::call` → [Log,Unknown]** (CONFIRMED: `let mut
self_ = self.clone(); self_.call_async(dst)` → the DNS/TCP connect path's `trace!` + the async dispatch, a
genuine silent-pure recovery — the tower Service pattern), **clap_builder +30** (Usage/Parser/Validator clone
`self.cmd: Command` then `cmd.build()`/`find_subcommand`, which dispatch through `Box<dyn TypedValueParser>`
value parsers → honest Unknown; `MapValueParser` has a real `callback:unresolved call` at the leaf). reqwest/
bytes/mio/tower-service/syn/tokio/serde_json: zero change. LESSON: don't pre-judge a vein's value by a crude
incidence grep — the clone-rebind looked like "3–4 per crate, mostly not-fixable", but the A/B on real code
showed the `self.clone()`-into-async-block pattern is pervasive and was silently dropping whole Service::call
effect chains. The session receiver-typing arc is now R50 + R51 + R52 all SHIPPED (inline struct-literal,
smart-pointer ctor, clone-rebind); R48/R49/R53 residual. Four-way conformance OK after each.

### 2026-07-18 — residuals closed: R53 (UFCS), R48 (local macro), R49 (drop-field)

"Close residuals" pass — all three open rust-scan residuals fixed, each A/B-validated + regression-gated +
four-way conformance OK, every one turning out sound (and two far more valuable than their "low incidence"
estimates suggested).

**R53 — trait-qualified UFCS** (`dbc1e24`). `<T as Trait>::m(&t)` / `Trait::m(&t)` dropped silent (no fn
`Trait::m`; the impl is `T::m`). FIX: an ADDITIONAL precise typed `T::method` edge from the STATICALLY-KNOWN
receiver — the qself type of `<T as Trait>::m` (explicit impl, correct even for an associated fn) or the first
arg's type of `Trait::m(&t)`. NEVER CHA-over-all-impls (T is known → charging other impls fabricates). Gate:
`LocalTrait.methods` filtered to `&self` methods (both its uses are receiver calls), so an ASSOCIATED fn
(`Trait::build(&data)`) is never mis-read as a receiver call on `data`. A/B zero concrete over-fire ~2600 fns
(only +Unknown recoveries, e.g. syn `Box::parse` resolving `<Pat as ParseQuote>::parse`). Controls pass.

**R48 — local `macro_rules!` template** (`94f333c`). A bare `NAME!(..)` whose TEMPLATE does I/O read pure
(syn leaves the body opaque; the arg-walk sees only invocation args). FIX: collect each `macro_rules!` → its
arm tokens (a cache-threaded string map mirroring const_strings — new `local_macros` through FileDecls/
MergedDecls/merge/digest); at a bare invocation, `$`-strip metavars + parse-or-skip each arm as a block +
inline-visit it (recursion-guarded; only ever ADDS visibility). FAR higher value than "zero incidence": it
recovers the PERVASIVE local-logging-wrapper pattern (`macro_rules! trace { ($($a:tt)*) => { tracing::trace!(
$($a)*) } }`) — tokio-util +4 Log (FramedImpl::poll_*), h2 +8 Log (proto_err! wrapping tracing::debug), zero
fabrication. The original do_io!/log_file!/call_sink! probes + the metavar case all work.

**R49 — effectful-Drop guard as a struct FIELD** (`3e2a52c`). The hard one — the first prototype A/B-reverted
(14 flate2 fabrications) because a constructor's owned drop-type ESCAPES into the returned aggregate
(`Compress::new` builds a `Stream`, returns the `Compress`). FIX has three parts: (1) a transitive drop-owner
closure (`drop_types` × `fields`/`field_elem`, leaf-keyed, to a fixpoint); (2) a RETURN-ESCAPE gate — skip the
field charge when the fn returns a local aggregate or drop-type (a new `FnInfo.ret_idents`, `-> Self` resolved
to the impl type). The gate is a CONSERVATIVE MEMBERSHIP check, not ownership traversal, because flate2's
parallel read/write/bufread modules create leaf-name COLLISIONS (three `GzEncoder`s etc.) that defeat precise
ownership — a membership check stays sound there (over-skips toward under-report, never fabricates); (3)
ADDITIVE-only — the shipped DIRECT drop-glue is untouched, so no new under-reports (an earlier variant that
also gated the direct case removed 12 flate2 + 13 h2 charges of uncertain correctness → rejected). A/B: ZERO
concrete fabrication AND zero removed across flate2/syn/h2/tokio-util/hyper/clap/reqwest; recovers the clean
local-guard-as-field cases; flate2 +2 (the two `reset` methods legitimately flush+recreate the FFI stream).
LESSON: when precise analysis is defeated by a corpus pathology (name collisions), a conservative membership
gate + additive-only composition buys soundness without trading the cardinal sin for its mirror
(under-report). The debugging path — instrument `drops_here`/`escaping`/`owned_drops`, find the leaf-vs-
qualified key mismatch, then the collision — is the template for the next ownership-closure bug.

Residual register: R48/R49/R52/R53 all CLOSED this session (+ R50/R51 shipped). The rust-scan receiver/
dispatch/macro/drop surface is now saturated for the veins probed; open long-tail is the niche dispatch
shapes (blanket impls R45, nested Vec<Option<Box<dyn>>> R46) + ts super-interface precision (R47, disclosed).

### 2026-07-19 — residual-register CLEARED: R45/R46/R47 + Unary-deref (rust-scan + candor-ts)

The "do the remaining open items" pass — every open residual closed, each regression-gated + A/B
zero-fabrication + four-way conformance OK.

**R45 blanket impls** (`edf35b3`). `x.ext()` from `impl<T> Ext for T` read pure (the blanket body's qual is
`T::ext`, the generic self param). FIX: a cache-threaded `blanket_methods` map (leaf -> self-param, ambiguous
-> ""); a TYPED unresolved `x.leaf()` edges to `by_tail2["<param>::leaf"]`. Gated to a typed receiver so an
inherent method resolves first (regression: `calls_inherent` stays Net, not the blanket's Fs). A/B zero
fabrication across futures-util (13 blanket impls)/syn/hyper/h2/tower — effectful blanket bodies are rare, so
no recovery, but the vein is closed.

**R46 dispatch long-tail** (`d2a58d2` nesting + `bf8ed07` tuple). (a) Nested `Vec<Option<Box<dyn>>>` /
`Option<Vec<Box<dyn>>>`: `elem_trait_leaves` peel steps now compose (trait_leaves-or-elem_trait_leaves) and
`resolve_elem_trait_leaves` on a bare var falls back to `trait_vars`, so the outer-then-inner unwrap keeps the
dispatch. (b) Tuple-of-dyn destructure (`let (d,_) = pair; d.go()`): a new per-fn `tuple_trait_of` (param),
inline-cast element extraction, and a `<tupledyn>` return sentinel (factory) — all three source forms. The
turbofish sub-case already worked. FULLY closed.

**R47 ts super-interface** (candor-ts `94d1658`). `s.base()` on `s: Sub` (`interface Sub extends Sup`, base on
Sup) read disclosed-Unknown. FIX: register an impl class under its interface's transitive SUPER-interfaces
(climb `extends`), so the super-method CHA finds it — the ts sibling of the rust/swift supertrait dispatch.
553 tests + fabrication probe OK.

**Unary-deref** (`249c947`). `(*b).method()` read pure — `resolve_recv_type` had no Unary arm; since candor
collapses pointers to pointees, `*b` is transparent (recurse into the operand).

The residual register is now EMPTY of open SILENT rows. Session arc (2026-07-18/19): R32–R53 + Unary-deref —
~24 soundness fixes across rust-scan/candor-ts (+ earlier java/swift), every one A/B-validated and
conformance-clean. The rust-scan receiver/dispatch/macro/drop/tuple surface is saturated for all probed veins;
dynamic ground truth (the syscall oracle) remains the growth axis (§3 #1).

### 2026-07-19 — code review of the receiver-typing cohort: 3 fabrications fixed + R53 reverted (candor-rust `8585c42`)

A high-effort multi-agent code review of the R45–R53 receiver-typing/close-residuals fixes found FABRICATIONS
the corpus A/B had passed (the A/B crates lacked the exact shapes; the review reached them by construction):
- **R48 arm-union** — `macro_template_blocks` walked EVERY arm of a multi-arm `macro_rules!`; an invocation
  matches ONE arm, so a `(log)=>{Log}; (save)=>{fs::write}` macro charged Fs to a `log`-only call. FIX: expand
  ONLY single-arm macros (count total arms incl. unparseable).
- **R48 metavar-callee** — `$f()`/`$x.m()` `$`-stripped to a bare `f()`/`x.m()` that resolved to a same-named
  local fn/method. FIX: mark macro-expanded calls `is_macro` → suppresses LOCAL resolution while keeping
  classification of `::`-qualified std/crate calls (fs::write→Fs, tracing::trace!→Log survive).
- **R45 blanket collision** — a receiver type whose inherent `leaf` was AMBIGUOUS (tail2 collision →
  resolve_target None) fell through to the blanket and fabricated. FIX: fire the blanket only when the
  receiver type has NO local `leaf` at all.
- **R53 UFCS — REVERTED**: the typed `T::method` edge could resolve to T's INHERENT `method` when the call
  ran the trait's DEFAULT (candor keys both as `T::m`). No cheap gate distinguishes them + no concrete
  recoveries (only +Unknown on syn), so the edge was withdrawn to an honest under-report. The `&self`-methods
  filter is kept.
The sound-direction findings (R49 whole-fn escape gate; R46 trait_vars fallback on non-compiling code) are
left as documented over-approximations (under-report / dead-code over-connection, never fabrication). Net A/B
post-fix: recoveries kept (tokio-util/hyper Log, clap/syn Unknown), h2 proto_err +8 Log dropped (multi-arm),
ZERO concrete fabrication, ZERO removed. Full suite + four-way conformance OK. LESSON: a fix green on the
corpus can still carry a fabrication only CONSTRUCTION reaches — corpus A/B and adversarial review are
complementary on the FABRICATION axis, not just the missed-effect axis; and an un-gatable fix is REVERTED,
not shipped behind a hopeful gate.

### 2026-07-19 — dogfood negative control: the completeness manifest holds on 20 fresh crates (candor-rust scan, deployed)

A proactive corpus round (two batches, 20 crates) on real crates NOT previously scanned this session, run
with the deployed stable `candor-scan` — chosen for high effect-surface behind abstraction. Batch 1:
**openssl-probe, rustls-native-certs, home, dirs-sys, tar, nix, mio, native-tls, which, walkdir, tempfile,
url, rayon**. Batch 2 (bigger FFI/IO/global-state surface): **git2 (234 fns), socket2 (129), tracing-subscriber
(204), zip (133), tokio-util (151), hyper-util (133), memmap2, filetime, signal-hook-registry**. Method: dump
each report,
flag any function that is `inferred:[]` AND carries NO `invisible`/`unknown`/coverage disclosure AND whose
`calls` reach an effect-looking symbol — the exact silent-under-report signature. **Result: 0 candidates.**
Every pure function is either genuinely pure or travels with a disclosure. Specifics worth recording:
- **The coverage envelope names every uncovered external boundary, per-function AND per-crate.**
  `rustls-native-certs::macos::load_native_certs` is `inferred:[]` — but carries `invisible:[security_framework,
  pki_types]`, and the report's `coverage.uncovered` lists `security_framework(3), schannel(1), pki_types(4),
  openssl_probe(1)`. So the cert-trust-store reach is a DISCLOSED boundary, not a false all-clear. `nix`
  (198 fns, a raw-libc FFI crate) prints its own coverage line to stderr (`memoffset(10), bitflags(1) …
  INVISIBLE … NOT a claim they're pure`) and still lands 0 pure-with-no-disclosure.
- **Transitive propagation intact on real code:** candor's own "most surprising reach" line surfaced
  `nix::sys::wait::wait → Exec`, 1 hop via `waitpid`.
- **One classification checked for over-report and cleared:** `waitpid → Exec` looked like it might be a
  fabrication (reaping ≠ executing), but `candor-classify` lib.rs:226 deliberately lists the libc
  process-control family (`wait/waitpid/wait3/wait4/waitid/popen/pclose`) as Exec — subprocess *lifecycle*,
  matching the spec's `Exec (subprocess)`. Intentional, documented, correct.
This is a clean **negative control** (in the RQ3 sense — evidence the instrument isn't merely confirming what
it went looking for) and an independent re-validation of the COMPLETENESS-MANIFEST rung (spec 0.21) on fresh
real code: the load-bearing property is that `inferred:[]` never travels alone when an external boundary was
crossed — and on this corpus it never did. **Precision observation (sound, not a sin):** in without-`--deps`
mode the envelope is conservative to a fault — `tracing-subscriber` reports 151/204 functions as `invisible:[…]`
(every non-effectful fn discloses an unresolved external ref: `tracing_core`, `matchers`, …), 0 bare-pure. The
attachment is call-site-driven (the body references an unresolved external path), not blanket, so it is honest;
but it is noisy, and `--deps` chaining is the precision path that collapses most of these to pure. Over-disclosure
never causes a false all-clear, so this is a UX/precision axis, not a soundness one. Root cause of why these
rounds now come up clean where pre-0.21 they would not: the manifest turned the unresolved-external-call vein
(historically the dominant silent-under-report source) into a disclosed `invisible`/`coverage.uncovered` edge.

### 2026-07-19 — four-way dogfood: TS typeorm connection-open silent-pure (candor-ts `9459e8f`); swift clean

Extending the rust negative-control round to the other three engines on fresh real code, run from the
0.22 SOURCE builds (the local install is stale at 0.17/0.18). Method: file-level cross-check — where source
shows an effect API but the report has no matching-effect-or-Unknown function in that (non-test) file.
- **candor-swift on `pollen`** (a real iOS app, 180 .swift files, 2921 analyzed): rich effect surface
  correctly recovered — Clock 336, Fs 312, Unknown 435, Net 49, Exec 50, Location 63, Contacts 10, Mic 18 —
  with `coverage.uncovered` naming MapKit/WidgetKit/Metal/… . Cross-check flagged only TEST files (excluded
  by design). CLEAN.
- **candor-ts on `ukri-tfs`** (a real TS services monorepo): found a genuine SILENT UNDER-REPORT.
  `service/adaptor/repository/typeOrmDataSourceFactory.buildPostgresDataSource` did
  `new DataSource(options).initialize()` — `.initialize()` opens the Postgres connection pool (a real Db
  round-trip) — and read PURE (omitted from the report, no Unknown). The typeorm verb rule covered the QUERY
  surface (find/save/execute/…) but not the DataSource LIFECYCLE. FIX (`9459e8f`): add the connection/DDL
  I/O verbs `initialize|connect|synchronize|runMigrations|undoLastMigration|dropDatabase` to the same
  module-gated typeorm rule (fires only on a typeorm-typed receiver; pure builder heads stay pure).
  A/B on two services: recovery propagates transitively up the real startup chain
  (`startService`/`buildFastifyServerConfig`/`getConnection` went `[Env,Unknown] -> [Db,Env,Unknown]` — a
  false all-clear on Db, closed), ZERO fabrication, ZERO removed. Unit(103)+integration(553)+probe all green.

FOUR-WAY SWEEP of the vein ("DB connection lifecycle is Db, not only queries"): the REFERENCE engine already
upholds it — `Classifier.java:180` classifies `java.sql.Driver.connect` (connection-open) as Db, with a
comment flagging it was a silent-pure hole. candor-ts was the lone straggler; now at parity. Swift/rust ORMs
absent from the corpus (rust `sqlx`/`diesel` connection-open — e.g. `PgPool::connect` — is an untested
follow-on, no corpus miss observed). Spec CLASSIFIER.md §TS-Db amended to state the shared principle
explicitly. Durable: dogfooding a REAL framework app (typeorm/Nest, a fastify service) finds ecosystem sins
a synthetic seam never would; and when one engine surfaces a Db/lifecycle vein, the reference engine's
existing rule is the parity oracle.

*(Correction to the entry above, same-day verification: the rust "untested follow-on" is resolved — rust
ALREADY covers ORM connection-open. `DB_CRATES` (sqlx/postgres/tokio_postgres/diesel/sea_orm/deadpool_postgres/
…) match `connect`/`connect_timeout` in the Db verb block (candor-classify lib.rs:1605). So the vein was closed
three-way already (java Driver.connect, rust DB_CRATES ::connect) and candor-ts was the CONFIRMED lone straggler.)*

### 2026-07-19 — extended TS hunt across the ukri-tfs AWS-Lambda monorepo (34 source roots)

Following the typeorm fix (`9459e8f`), swept candor-ts across 15 ukri-tfs services + 10 packages (34 source
roots, node_modules installed so the curated κ tier + @types mapping are live) with the effect-API file-level
cross-check. RESULT: the completeness manifest holds; the one new fixable sin was the typeorm one, already
shipped. Confirmations worth recording:
- **The modular AWS SDK v3 is correctly DISCLOSED, not silent.** `@aws-sdk/client-sns`/`-sqs`/`-ses` are
  κ-uncovered, so SNS `.publish()`, SQS `.receiveMessage()`, SES `.sendEmail()` read `inferred:[]` WITH
  `invisible:['@aws-sdk/client-sns',…]` + `coverage.uncovered` naming them — a disclosed boundary on every
  AWS effect, not a false all-clear. (candor DOES model `@aws-sdk/client-bedrock-runtime` → Llm.)
- typeorm `@Entity`/`@Column` classes (metadata) and `import { Headers, Response } from 'node-fetch'`
  (TYPE-only imports) correctly read pure — not sins.
- CHARACTERIZED RESIDUAL (known class, NOT cheaply fixable): an external **INTERFACE** method whose impl
  lives in an uncovered sibling package reads PURE where a concrete external CLASS call gets `invisible`.
  `post-decision DomainEventPublisher.publish*` calls `channels.X.publish()` on `OutboundChannel` (an
  interface from `@ukri-tfs/message-handling`), whose real impl `AwsOutboundChannel.publish` reaches SNS
  (Net) — so Net is reachable but read pure with no disclosure. candor discloses `invisible` for a call on a
  concrete external class (`new SNS()`, receiver pinned to the package) but an external interface method has
  no body and candor does not CHA into the sibling package's implementations. The only blanket fix
  (external-interface method → invisible) would FLOOD `logger.info()`/every DI'd interface — the same
  unfixable tradeoff recorded at the decorator-injection limitation (SOUNDNESS-LOG line ~1439). Tracked here
  as a known residual; a real fix needs cross-package (workspace) report chaining, not a κ rule. DURABLE: a
  real framework monorepo separates the concrete-external-class disclosure (sound) from the
  external-interface-dispatch residual (the logger-flood class) — the AWS SDK proves the manifest works; the
  message-handling interface proves the boundary's edge.

### 2026-07-19 — workspace report chaining PROTOTYPE: the external-interface-dispatch residual, disclosed (candor-ts `710178e`)

The external-INTERFACE-dispatch residual characterized in the ukri-tfs entry above (a consumer's
`channels.X.publish()` on an `OutboundChannel` imported from the sibling package
`@ukri-tfs/message-handling`, whose impl reaches SNS/Net, reading PURE) now has a working prototype fix via
CROSS-PACKAGE (workspace) report chaining — the candor-ts analog of rust `--deps`. Three parts, one of which
was a load-bearing GENERAL bug: (1) `declModule` returned the RAW ABSOLUTE PATH for a workspace-symlinked dep
(real path has no `node_modules/` segment) → an unmatchable κ key + an ugly `invisible:[/abs/path]` + the
chain never joined; fixed to walk up to the nearest package.json `name` (ungated correctness improvement).
(2) `crossDeps` now carries+inherits `invisible`, so a chained dep's own blind boundary travels to the
consumer as ITS `invisible` (transitive disclosure across the edge; active only under `CANDOR_DEPS`).
(3) synthetic interface-CHA union entries (`Iface.method` = union over local impls, reusing the existing
`interfaceImpls` universe) so a consumer's interface-method lookup resolves — GATED behind
`CANDOR_WORKSPACE_CHAIN` so default reports stay byte-identical / four-way-conformance-safe. VALIDATED on the
REAL post-decision service: chaining message-handling turns `DomainEventPublisherV1.publish*` from pure into
`invisible:[@aws-sdk/client-sns, @aws-sdk/smithy-client, ajv]`. Unit 103 / integration 553 / probe / lint
green; fuzz unchanged (the lone deep_nesting stack-depth failure is pre-existing on baseline). This confirms
the residual was NOT the unfixable logger-flood class after all — it is fixable with report chaining (the
right fix, as predicted), NOT a blanket external-interface→Unknown. Productionizing (auto-scan workspace
deps, spec the `interfaceUnion` field + flag) is the follow-on. DURABLE: the workspace-symlink `declModule`
bug means ANY monorepo dep's effects were mis-keyed — a general recall gap the chaining work surfaced.

### 2026-07-19 — workspace chaining PRODUCTIONIZED (`--workspace`) + the monorepo recall sweep (candor-ts `2af77fc`)

The prototype above is now a one-command flag: `candor-ts <target> --workspace` (alias `--deps`)
auto-discovers the target's symlinked monorepo deps, scans each into `.candor/deps/` (with interface-CHA
union entries), and chains them — the candor-ts analog of rust `--deps`. SWEEP across all 11 ukri-tfs services:
**+545 functions disclosed that previously read PURE** (1396 → 1941 effectful/disclosed; every service gained,
+1 to +158). SOUNDNESS of the gains verified: the split is dominated by HARD inferred effects (e.g.
application-manager +140 = 135 hard-inferred / 5 invisible), NOT the union over-approximation — because most
are PRECISE concrete-class resolutions through the chain: `getUserByTfsId → client.get('/users/…') → Net`
(party-manager), `getOrganisationById → admin-services → Net`, repository calls → Db, config reads → Env, all
traced to real workspace-client HTTP/DB calls candor was systematically under-reporting across the package
boundary. This quantifies the SCALE of the cross-package under-report class the earlier ukri-tfs entry found a
single instance of: a monorepo/microservice TS codebase reads HUNDREDS of its real effect reaches as pure when
scanned per-package, because the effect lives one workspace hop away. Regression green; default (no --workspace)
byte-identical. FOLLOW-ONS: transitive workspace-dep chaining (a dep's own workspace deps); the four-way roll
(java/swift analogs — rust already has --deps); spec the `interfaceUnion` field + the `CANDOR_WORKSPACE_CHAIN`
flag. DURABLE: per-package scanning of a monorepo is a systematic under-report multiplier — chaining is not a
nicety but the difference between reading a microservice backend as mostly-pure and seeing its real reach.

### 2026-07-19 — workspace chaining: transitive fixpoint + the four-way assessment + spec (candor-ts `c6b8767`, spec `9ba6b9b`)

Two follow-ons to the `--workspace` productionization. (1) TRANSITIVE chaining: `--workspace` now scans the
workspace dep graph to a monotone FIXPOINT (each dep re-scanned WITH the accumulating deps dir chained), so a
dep's calls into ITS OWN workspace deps resolve — bounded by dep-graph depth, converges in ~9s for
post-decision's 5 deps. Monotone → always a superset of direct-only; the marginal gain is corpus-dependent
(ukri-tfs effects are mostly one hop away). (2) FOUR-WAY ASSESSMENT (the honest result, now spec'd in
`WORKSPACE-CHAINING-DESIGN.md`): the SILENT-PURE form of the cross-package interface-dispatch miss was UNIQUE
to candor-ts. It leans on the TS type checker to type the receiver, then keys the chain lookup on the
interface METHOD SIGNATURE (no body → no entry → join missed → PURE). The other engines fall to a disclosed
`Unknown` for an unresolved external dispatch instead — candor-swift explicitly (Driver.swift:454-475: an
unmodeled external protocol member → Unknown with `why: dispatch:Sup.member`, a MODELED one like Fluent Model
CRUD → Db), rust similar via its never-silent posture, java sidesteps via whole-classpath bytecode. So the
rung's SOUNDNESS value is ts-specific and SHIPPED; the four-way roll is the OPTIONAL PRECISION arm (turn a
disclosed Unknown into the exact chained effect) — promoted to a floor rung only when it earns its keep on a
real Unknown-heavy corpus. DURABLE: not every "four-way vein" is a four-way SIN — sometimes one engine's
resolution strategy (ts's type-checker-keyed lookup) creates a silent-pure hole the others' never-silent
default already covers; the honest roll assesses posture per engine before porting.

### 2026-07-19 — interfaceUnion rolled to candor-swift + pinned four-way (swift `f7acad5`, spec `297f239`)

The workspace-chaining `interfaceUnion` rung now SHIPS on a SECOND engine and is conformance-pinned.
candor-swift: gated behind `CANDOR_WORKSPACE_CHAIN`, emit synthetic `pkg#Protocol.method` union entries =
the union over local conformers (reusing the `conformers` CHA universe), so a consumer's cross-package
protocol call resolves. Verified end-to-end with a 2-package fixture (`use(ch: OutboundChannel)` calling
`ch.publish()` on a chained Dep whose AwsChannel conformer does Fs → `use → Fs`). 245 swift tests pass;
default (no flag) reports byte-identical. Conformance **PART 18** pins it: a per-shipping-engine 2-package
fixture — the consumer must resolve the chained interface/protocol method to the impl's effect, never pure
(ts `use→Net`, swift `use→Fs`), and the dep must emit the union entry. Full suite green (18 parts MATCH).
CORRECTION to the earlier four-way assessment: candor-swift ALSO read the external-protocol-typed-receiver
cross-package call as PURE when unchained (the empirical fixture proved it) — a DIFFERENT resolution path
than ts (ts keys the chain lookup on the bodyless interface method signature; swift on an unresolved
external-protocol receiver) but the SAME silent-pure outcome. So this was a genuine soundness fix in BOTH
source engines, not the precision-only upgrade the earlier code-read (Driver.swift:454-475, a different
shape: project-conforms-to-external) suggested. DURABLE: repo-reading ONE resolution path mis-scoped the
gap; the 2-package empirical fixture is the honest oracle for "does this engine read cross-package interface
dispatch as pure?" — and both source engines did. rust roll (trait-union) is the remaining source-engine
follow-on; java sidesteps via whole-classpath bytecode.

### 2026-07-19 — interfaceUnion rolled to candor-scan (rust) → PART 18 THREE-WAY + swift --workspace (rust `c51a369`, swift `d7ed521`, spec `5413b49`)

The workspace-chaining `interfaceUnion` rung now ships on ALL THREE source engines. (1) candor-scan (rust):
PRODUCER trait-CHA union entries (gated CANDOR_WORKSPACE_CHAIN, unioning trait_impls over trait_decls'
methods) + a CONSUMER fix — an external `&dyn Trait` dispatch was a documented miss (dropped to PURE because
the trait's impls live in another crate, so in-crate CHA found nothing); now, when the trait resolves via
`use` to a dependency-qualified path (not std/core/alloc), it emits a crate-qualified `Call` so the CANDOR_DEPS
chain resolves it against the dep's union entry. A/B on syn/serde_json/h2: **+80 recoveries, 0 fabrication, 0
removed** — the recoveries are genuine external-trait dispatches (serde_json's serialize/deserialize/
next_key_seed → invisible:[serde]/[indexmap], previously silent-pure). So UNCHAINED it now discloses
`invisible:[crate]` (was pure); CHAINED it resolves the precise effect. candor-scan tests 124+48 pass. (2)
candor-swift gained the `--workspace` flag (parse `.package(path:)` from Package.swift, scan+chain to a
fixpoint) for ergonomics parity with ts. CONFORMANCE **PART 18 is now THREE-WAY** (candor-scan + candor-ts +
candor-swift each resolve a chained interface/protocol/trait method to the impl's effect + emit the union
entry) — full suite green. FINAL FOUR-WAY PICTURE: the silent-pure cross-package interface/protocol/trait
dispatch hole existed in ALL THREE source engines (each via a different resolution path — ts's bodyless
interface-signature chain key, swift's external-protocol receiver, rust's cross-crate `&dyn` impl-drop);
java is N/A (whole-classpath bytecode). DURABLE (reinforced): the 2-package empirical fixture — not a
code-read of one resolution path — is the honest oracle for "does this engine read cross-package dispatch as
pure?"; it read pure in every source engine. All rides 0.22, unpublished.

### 2026-07-19 — code review of the interfaceUnion rung: a three-way collision-fabrication guard (rust `b4ae3b9`, swift `0de57e4`, ts `4a75e5c`)

Adversarial code review of the workspace-chaining / interfaceUnion work (the review workflow crashed on an
infra StructuredOutput error, so it was done inline). Found ONE real cross-crate FABRICATION risk the corpus
A/B had not exercised, present in all three source engines' union emission: the union entry is keyed by a
NAME (trait leaf / protocol conformer's bare tail type / interface name), so a same-name COLLISION merges two
unrelated declarations — `mod a { trait T } mod b { trait T }` (rust), `A.Foo`/`B.Foo` (swift), two
`interface I` in different files (ts) — and the union entry `pkg#T::m` would then carry an UNRELATED type's
impl effect. A cross-package consumer of the pure declaration would inherit the effectful one's effect (an
over-report). The in-crate dispatch already bails to Unknown on this (rust `collector.rs lt.count > 1` "never
guess between traits"; swift/ts have the same never-guess discipline) — the EMISSION did not mirror it. FIX
(three-way): skip the ambiguous name (rust `lt.count > 1`; swift `ownersByTail[t].count > 1`; ts
`ifaceNameCounts[name] > 1`) — an honest under-report, never a guess. Verified with an adversarial 2-trait
rust fixture (a::T pure + b::T Fs → NO `T::go` union entry emitted); single-decl fixtures still resolve; all
engine suites green (rust 124+48, swift 245, ts 103+553+probe); conformance PART 18 still green three-way.
DURABLE: a NAME-keyed CHA index (leaf/tail/bare-name) that the in-crate path guards with a never-guess rule
must carry the SAME guard when its union is EXPOSED to cross-package consumers — the exposure is a new place
the collision can fabricate. And: a corpus A/B is necessary-not-sufficient (the collision shape wasn't in
syn/serde_json/h2) — constructive review reaches it by construction, the recurring lesson.

### 2026-07-19 — the sync-callback-invoker vein, swept + pinned FOUR-WAY

The transitive verify-oracle's reconcile-against-reality engine (RQ1 on independent code) surfaced this
on Apache commons-compress: an OPAQUE functional param handed to a SYNCHRONOUS higher-order invoker
(`Iterator.forEachRemaining`, `Iterable/Collection/Map/Stream.forEach`, `Optional.ifPresent`) read
SILENT-PURE, while a DIRECT opaque call (`cb()`) was already correctly Unknown. candor-java closed it
first (`c755acd`: `SYNC_CALLBACK_INVOKERS` + `isSyncCallbackInvoker`, opaque-arg-only guard so inline
lambdas keep their edged effect). Per the standing "a find in one engine is a SWEEP trigger for ALL"
rule, probed the other three with a calibrated repro (known-pure / known-effect / `forEach(opaqueParam)`
/ direct `cb()`): the vein was present in ALL THREE — candor-scan (`for_each(cb)` direct-pass leaked
while the closure-wrapped `for_each(|x| cb(x))` was already Unknown — the asymmetry was the tell),
candor-ts (`arr.forEach(cb)` pure while `cb()` Unknown), candor-swift (`arr.forEach(cb)` pure while
`cb()` Unknown). FIXED four-way, fanned out to three parallel subagents (separate repos, reconverged at
conformance): candor-scan `0784052` (route the direct-pass fn-typed arg through the existing
`expr_is_fn_typed`→unresolved path; +Option/Result combinators; A/B itertools +16 Unknown, zero fab),
candor-swift `027b184` (`SYNC_CALLBACK_INVOKERS` table + param→`callbackInvoked` index-resolved / local→Unknown;
250/250; A/B swift-argument-parser +5, zero fab), candor-ts `014fcd8` (`HOF_INVOKERS` opaque-callback arm
with four guards — inline-arrow-preserved, resolvable-preserved, arg-0-only, opacity; the initial cut hit
a `reduce`-seed and `.filter(Boolean)` false-positive, both gated; 568 tests; A/B fp-ts +10, zero fab on
zod/ky/p-map/emittery). Each fix: additive-only, zero fabrication, full suite green, opaque-args-only so
no inline-lambda flood.

MID-RUNG CATCH — the differential did its job. Pinned the parity with a new PART 1 effect-set case,
`sync_callback_opaque` (`list.forEach(opaqueCallback)` → expected `["Unknown"]`, added to all four
fixtures + expected.json). First run: `Unknown/Unknown/(pure)` DIVERGE — candor-JAVA read it pure. Root
cause: `SYNC_CALLBACK_INVOKERS` was keyed on the EXACT bytecode owner (`java/lang/Iterable`,
`java/util/Collection`…), but `list.forEach(cb)` — the single most common form — compiles to an owner of
the STATIC receiver type (`java/util/List`, `ArrayList`, `HashSet`, a user collection), NOT the
`java/lang/Iterable` where the default method is declared, and candor-java has no JDK supertype index to
normalize it. The Rust/TS/Swift arms all key their sync-invoker check on the method NAME (owner-agnostic),
so they caught it; java's owner-exact table silently missed the most common case. FIX candor-java
`ead40c6`: match `forEach`/`forEachOrdered`/`forEachRemaining` by name (`FOR_EACH_FAMILY`), any owner —
the forEach idiom invokes its functional arg synchronously by contract across the whole JDK and user
collections alike; over-disclosure stays at the floor (A/B commons-io 1188→1188 and commons-compress
824→824: ZERO new Unknowns — the corpora's forEach sites are inline lambdas or already-Iterable-typed).
Regression `StructuralDispatchTest.syncCallbackInvokerOwnerAgnosticListForEach`. Full four-way conformance
green end-to-end (exit 0), `sync_callback_opaque` = Unknown in all four.

DURABLE: (1) a cross-engine vein = N independent per-engine fix-cycles → fan out to subagents (separate
repos, no shared state), reconverge at four-way conformance. (2) The conformance DIFFERENTIAL caught an
owner-exact under-coverage (`List.forEach`) that the per-engine A/B on commons-io/compress had NOT — those
corpora happened to lack the `List.forEach(opaqueArg)` shape, exactly as the interfaceUnion name-collision
(prev entry) wasn't in syn/serde_json/h2. Constructive conformance reaches by construction what corpus A/B
can miss — the recurring lesson, now twice in one week. (3) When one engine keys a check on an EXACT owner
and its siblings key on the method NAME, the exact-owner engine is the likely under-cover — prefer the
name-keyed, hierarchy-agnostic form for the universal-contract idioms (forEach), reserving owner-scoping
for the genuinely type-specific ones (Optional.ifPresent). Riding candor-java 0.22, candor-scan/ts/swift
unpublished — harness-blocked, Tom remote.

### 2026-07-19 — commons-vfs2: the doPrivileged + filter/buffered-stream delegate veins (5th reconcile codebase)

The reconcile-against-reality engine's 5th independent codebase: Apache commons-vfs2 (a virtual filesystem
whose architecture IS stream/FileObject delegation — chosen deliberately as high vein-yield; Net 591 / Fs
609 / Log 629 / Env 427 / Clock 420 / Rand 358, the first Net-AND-Fs-heavy corpus, vs the Fs-only io/
compress). Ran its OFFLINE provider suites (local/ram/temp/zip/jar/tar/bzip2/gzip/filter/util/cache) in one
JVM via ConsoleLauncher under the transitive `candor verify` agent. **4 real silent under-reports**, two
distinct veins, both closed, oracle re-run confirms **0 violations (was 4), exit 0**:

(1) **`AccessController.doPrivileged` as a synchronous invoking HOF** (candor-java `3a63266`). `Privileged
FileReplicator.init` → `AccessController.doPrivileged(new InitAction())` where InitAction is a project
`PrivilegedExceptionAction` whose `run()` calls the wrapped replicator's effectful `init()` (Net/Fs); candor
read the caller PURE because it did not model doPrivileged as INVOKING `action.run()` — the exact
creation-edge asymmetry `namedFunctionalToHof` already fixes for `Stream.forEach`/`List.sort`, just missing
this invoker + these SAM interfaces. FIX: `doPrivileged` → `isInvokingHof`; `PrivilegedAction`/
`PrivilegedExceptionAction` → `isHofFunctionalIface`. Both init/replicateFile now resolve (CHA effect set
over the wrapped FileReplicator, covering observed Net/Fs). A/B io 1188→1188, compress 824→824 (zero — they
don't use doPrivileged). Regression `SoundnessSweepTest.doPrivilegedActionRunsSynchronouslyAndPropagates`.

(2) **filter/buffered stream read/write/skip DELEGATE to the unknown wrapped sink** (candor-java `3353860`,
extending the close/flush rule `2433db6`). `MonitorOutputStream.write`/`flush` → `super.write`/`super.flush`
(super = BufferedOutputStream) → the wrapped `out` — here a RAM sink updating lastModified = Clock — read
PURE. Extended the wrapped-sink rule to the ACTIVE-I/O methods (read/write/skip) and the Buffered* bases:
Filter/Buffered {Output,Input}Stream/{Reader,Writer} read/write/skip/flush/close → Unknown. NATURALLY NARROW
— the abstract declared type (`OutputStream x = new Buffered…`) has bytecode owner java/io/OutputStream and
does NOT match; only the exact-typed or `super.`-from-subclass call matches, i.e. the delegating-subclass
vein itself. A/B io 1188→1192 (+4), compress 824→828 (+4), vfs2 800→831 (+31 — ALL genuine Monitor/Raw/
Http/Ftp/Sftp stream delegates, several reaching Net through wrapped network sources the offline suite could
not even exercise). Zero fabrication, no flood. Regression `StructuralDispatchTest.bufferedAndFilterStream
ReadWriteDelegateToUnknownWrappedSink`. Both veins are JVM-java.io/java.security-SPECIFIC by mechanism (no
doPrivileged / no java.io FilterStream in the sibling engines — like the super-call and filter-close veins,
the other three engines are immune by construction), so no four-way sweep needed.

DURABLE: delegation-heavy corpora are the high-yield hunting ground for the reconcile engine — vfs2's whole
design is stream/component wrapping, and it surfaced 4 finds where the Fs-only libraries were nearly clean.
And the wrapped-sink Unknown rule is safe to broaden precisely BECAUSE the abstract-declared-type call keeps
owner=java/io/OutputStream (unmatched) — the exact-owner match self-limits to the super-from-subclass vein.
candor-java commits now include 3a63266, 3353860. All unpublished (harness-blocked, Tom remote).

### 2026-07-19 — commons-configuration2: a CLEAN run + the coverage-boundary false-positive (6th reconcile codebase)

The 6th reconcile codebase, picked to diversify structural IDIOMS away from stream-delegation: Apache
commons-configuration2 (builder chains, reflection bean instantiation, provider/handler delegation; a very
CONNECTED callgraph — AbstractConfiguration CHA-smears through JNDI(Net)/Database(Db)/Environment(Env)/file
(Fs) impls, so nearly every method transitively reaches everything: the scan profile is a near-uniform
~1520/effect). Ran its effect-rich offline suites (root incl. DatabaseConfiguration=embedded HSQLDB Db,
Environment=Env, file configs=Fs; + builder/io/tree/beanutils/convert/interpol/plist/event) single-JVM under
the transitive `candor verify` agent → **130 functions checked, 1 "violation" — and that one is NOT a
classifier cardinal sin.** So this structurally-different, effect-rich codebase is **CLEAN of classifier
silent-under-reports** — a convergence signal (5 codebases → 15 clean veins fixed; the 6th → 0 new veins).

The 1 flagged "violation": `CatalogResolver.getResolver` → observed Net, inferred []. Root cause: it lazily
constructs `new org.apache.xml.resolver.tools.CatalogResolver(manager)` — an UNMODELED THIRD-PARTY class
(candor scanned target/classes WITHOUT the xml-resolver dep) whose ctor does Net (fetches an XML catalog) at
runtime. This is a **coverage-boundary case, working AS DESIGNED, not a silent-pure**: candor's scan already
DISCLOSES the blind reach — getResolver's report entry carries `invisible: ["org.apache.xml.resolver.tools"]`
and the gate emits `coverage: {uncovered: 17, packages: [… org.apache.xml.resolver, xml.resolver.tools …]}`
(the 0.15 coverage-envelope + 0.21 completeness-manifest rungs). The Net originates ENTIRELY inside the
uncovered package; candor never saw it and honestly says so via the `invisible`/`coverage` channel (never
"pure through a named package"). The naive "fix" — promote a non-empty `invisible` reach to `Unknown` in
`inferred` — was MEASURED and REJECTED: it flips **129 functions** to Unknown on configuration2, almost all
BENIGN (createPropertiesWriter/parseProperty/unescapePropertyName → commons-text string helpers that are
PURE), i.e. the fabrication mirror — flooding `inferred` for any code not scanned with all deps, the exact
thing candor's `invisible ≠ Unknown` design deliberately prevents. (Confirmed with a minimal ctor-vs-method
repro: an uncovered-external call is `invisible` NOT `Unknown` for BOTH ctor and method — the earlier
`resolveEntity` Unknown came from OTHER unresolved dispatch, not the invisible call.)

So the miss is on the ORACLE side, not the classifier: `HonestyCheck` (verify) flags `observed ⊄ inferred ∧
Unknown ∉ inferred` as a VIOLATION but does NOT credit the `invisible`/`coverage.uncovered` disclosure
channel, so it reports a false positive whenever a fn reaches an effect purely through a disclosed-uncovered
package. The SOUND refinement is PATH-BASED (don't blame frame F for an effect whose observed stack routes
F→leaf THROUGH a frame in an uncovered package — candor's static chain legitimately breaks there and
disclosed it); the LENIENT version (any non-empty `invisible` excuses any escaped effect) is UNSOUND — it
would MASK a real cardinal sin in COVERED code from a fn that also happens to touch a benign uncovered lib.
The precise fix needs effect-origin-package tracking in the verify agent + the coverage set — a shipped-
oracle semantics change that also touches the paper's RQ1, so it is Tom's call, flagged not unilaterally
shipped. DURABLE: not every oracle-flagged "violation" is a classifier sin — the coverage-boundary is a
disclosed-incompleteness the oracle must learn to credit; and a highly-connected CHA-smearing codebase is a
POOR vein-hunting target (candor over-reports so broadly that few functions are pure enough to falsify) —
prefer moderately-connected codebases where sound-complete (D=∅) functions actually exist. No code shipped
this run (correctly — the only actionable item is a paper-affecting oracle change deferred to Tom).

### 2026-07-19 — compress re-verify (fixes hold) + the source/sink boundary + reconcile CONVERGENCE

Two confirmations + a second model-boundary, closing out the reconcile arc.

**(a) commons-compress re-verified — the 3 earlier fixes HOLD.** Re-ran the transitive oracle on compress
under the current engine (sync-callback c755acd + filter-close 2433db6 + owner-agnostic ead40c6 all in):
**174 fns checked, 1 violation** (was 4). The 3 previously-found veins (ArchiveInputStream.forEach,
CompressFilterOutputStream.close, ZipArchiveOutputStream.destroy) are CONFIRMED closed under the runtime
oracle, not just the scan. The 1 remaining = the documented `ZipArchiveInputStream.readFully(byte[],int)`
residual.

**(b) readFully IS the source/sink-stance boundary, NOT a classifier miss.** Root-caused: two-arg readFully
→ `org.apache.commons.io.IOUtils.read(in, b, off, len)` (EXTERNAL commons-io, candor-CLASSIFIED via the κ
rule, so NOT invisible) reads the wrapped `in`; at runtime `in` is file-backed → Fs, but candor read it
pure. candor's commons-io rule descriptor-matches File/Path→Fs, URL→Net, and lets the STREAM overloads fall
through to null — the DELIBERATE **source/sink stance**: Fs/Net is charged at a stream's CREATION, reads are
pure-relative (`ClassifierLongTailTest.commonsIoFollowsTheSourceSinkStance` pins
`IOUtils.toByteArray(InputStream)→null` = "a caller-opened stream is pure-relative"). A prototype promoting
the stream verbs (read/copy/toByteArray/…) to Unknown recovered **50 net-new** archive-parser readers on
compress (all genuine wrapped-stream reads, 3 redundant, 0 fabrication) — but BROKE the stance test: it
imposes charge-at-USE on the whole library. The transitive oracle attributes a file-backed read to the READ
site; the creation-site stance charges the OPEN site (for a library, in the caller = out of scope) — a
model-vs-oracle boundary, the library-view under-report of the source/sink stance. Reverted the prototype;
kept only a documenting comment + 3 stance-pinning table rows (candor-java 04f3b97). Whether to shift the
stance toward charge-at-use for stream utilities (whole-program soundness vs library-view completeness) is a
DESIGN decision, deferred to Tom.

**RECONCILE CONVERGENCE.** Two independent well-exercised codebases this arc (configuration2, compress
re-verify) each returned exactly ONE oracle "violation", and BOTH turned out to be candor's DELIBERATE
modeling boundaries — the coverage/invisible boundary (getResolver → unmodeled xml.resolver ctor) and the
source/sink stance (readFully → caller-opened stream) — NOT silent-pure classifier bugs. So the
reconcile-against-reality engine has CONVERGED on the classifier: 5 codebases → 15 clean veins found+fixed
(super-call, sync-callback [4-way], filter-close, stream read/write delegate, doPrivileged); the 6th/7th
surface only model-boundary cases. The two open items are both Tom's design calls, cleanly characterized: (1)
should the verify oracle CREDIT the invisible/coverage disclosure channel (path-based, sound) so it stops
false-positiving on unmodeled-library effects; (2) should the source/sink stance shift toward charge-at-use
for stream-consuming utilities (recovers library-view reads at the cost of redundant Unknowns whole-program).
DURABLE: once the reconcile engine's finds on good targets are all deliberate-model-boundaries rather than
silent-pure bugs, the classifier has converged — the remaining decisions are about the disclosure MODEL, not
the κ rules. candor-java commits this arc: …,3a63266,3353860,04f3b97 (last = doc-only).

### 2026-07-20 — value provenance Phase 1 + coverage crediting: the two model boundaries RESOLVED

Tom's "absolute best product, ignoring effort" call → build interprocedural value provenance (dissolve the
source/sink trade-off) + the companion oracle fix. Both concrete findings from the convergence
(readFully = source/sink boundary; getResolver = coverage boundary) are now RESOLVED soundly, each with a
regression pinning it. Design: VALUE-PROVENANCE-DESIGN.md.

**Phase 1 (candor-java 8537909) — external-origin stream read → Unknown.** The intraprocedural half. A
stream-consuming utility (commons-io IOUtils.read/copy/toByteArray, Guava ByteStreams/CharStreams) reads the
stream passed to it; candor's source/sink stance classifies these pure-relative — sound when the stream was
opened IN THIS method (a fresh `new FileInputStream`, newType set, so the method carries the Fs), a silent
under-report when the argument is a PARAM/FIELD opened elsewhere. New CALL-SITE handler `externalStreamUtility`:
an InputStream/Reader arg with `newType == null` (not a fresh in-scope `new`) discloses Unknown — at the call
site, NOT in classify(), so the pure-relative stance table stands. This is R17's `entryAbstractStream`
generalised from "an entry point's own param" to "any stream not opened here". Effect: readFully(byte[],int)
→ Unknown, compress runtime oracle 1→0, 32 net-new external-stream recoveries; the in-scope-open case stays
pure (no redundant Unknown — MORE precise than the reverted blanket κ-rule, which also fired on 18 in-scope
cases). A/B commons-io +6. Regression `externalStreamReadViaUtilityIsUnknownButInScopeOpenStaysPure` pins
external-field/param → Unknown AND in-scope-open → Fs-not-Unknown.

**Coverage crediting (candor-java fbb8cda) — the verify oracle stops at an uncovered boundary.** The
transitive attribution blamed a project caller for an effect it reaches only THROUGH a package candor cannot
see (getResolver → `new xml.resolver.tools.CatalogResolver(manager)` → the ctor calls back an instrumented
manager method that does Net). VerifyCli now passes `coverage.uncovered` to the agent (CANDOR_VERIFY_UNCOVERED);
`Trace.emit` walks the stack from the leaf outward and STOPS attributing once it crosses an uncovered-package
frame. Strictly sound, ZERO masking: a genuine miss reached through ALL-COVERED frames has no uncovered frame
on its stack → still attributed → still caught. configuration2 oracle 1→0. Regression
`attributionStopsAtUncoveredBoundaryButNotThroughCoveredFrames` pins BOTH halves end-to-end (an uncovered Sink
ctor calling back an app Task → outer credited; a seeded-pure midCovered through covered frames → still flagged).

DURABLE: the source/sink stance and the coverage envelope are DELIBERATE model boundaries; the fix is not to
abandon them but to (Phase 1) CHECK the stance's "a caller-opened stream" assumption at the call site via the
existing intraprocedural provenance, and (crediting) teach the oracle to honour the coverage disclosure it
already emits. Both are report-shape-neutral precision, sound-direction-only. Phase 2 (whole-program co-scan
precision via construction-carried binding) is scoped but unbuilt — it needs a provenance pre-pass and is
narrower-value; Phase 1's in-function-open case is already precise. candor-java commits this arc:
…,04f3b97,8537909,fbb8cda.

### 2026-07-20 — code review of value provenance: 4 soundness bugs in the new code, fixed (candor-java 2694324)

A high-effort workflow-backed code review of the value-provenance work (Phase 1 8537909, oracle crediting
fbb8cda, Phase 2 552553f) found FOUR real soundness bugs in the freshly-written code — three silent-under-
report veins and one oracle-masking — plus one efficiency issue. All CONFIRMED by the review's adversarial
verifier, all fixed with a regression (`StructuralDispatchTest.valueProvenanceReviewFixesAreSound`). A pointed
reminder that new analysis code is exactly where the cardinal sin hides, and that constructive review catches
what corpus A/B (all four corpora unchanged) does not.

1. **externalStreamUtility first-arg-only** — it `return`ed after the FIRST InputStream/Reader argument, so a
   DUAL-input verb (`IOUtils.contentEquals(in,in)`) with a fresh first arg masked an external SECOND stream →
   silent under-report. Fix: check EVERY stream arg.
2. **cross-class field rebinding invisible** — `computeStreamFieldOrigins` scanned only PUTFIELDs where
   `fi.owner==cn.name`, so a rebinding of an accessible field from another class (`B: a.in = external`) or a
   nestmate write left the field wrongly suppressible. Fix: a GLOBAL stream-field key set scanned against every
   PUTFIELD in every class; a param binding trusted only in the field's DECLARING class's own `<init>`.
3. **ProvValue.merge dropped fieldOrigin from its short-circuit** — a control-flow join of `this.in` and an
   external param (all else equal) returned the field value, keeping fieldOrigin → suppression fired on a value
   that can be the external operand. Fix: merge fieldOrigin (disagreement → null), matching newType/declType.
4. **verify oracle prefix-collision masking** — `Trace.emit` checked `inUncoveredPackage` (a dotted-PREFIX
   match) BEFORE the QUALS lookup, so a project package under an uncovered ANCESTOR prefix (`com.acme.vendor`
   uncovered, project `com.acme.vendor.app`) was dropped from attribution → a real miss through covered frames
   masked. Fix: attribute any ANALYZED project frame FIRST (never a boundary); only a non-project frame in an
   uncovered package is the boundary. Also neutralises the callback-through-uncovered concern (an inline
   callback is edged to its caller at creation, so the caller isn't wrongly pure). Regression
   `VerifyOracleTest.attributionStopsAtUncoveredBoundaryButNotThroughCoveredFrames` still green + the new one.

Plus an efficiency fix: a consume-once `provFramesCache` so the Phase-2 pre-pass and the main pass share one
ASM dataflow computation per stream-touching method. Verified: full suite green; corpora unchanged (compress
861, io 1194); configuration2 oracle 0 (crediting intact), compress oracle 0. DURABLE: the reconcile engine
finds the classifier's cardinal sins on real code; adversarial code review finds them in the analysis code
ITSELF — run BOTH on new provenance logic.

### 2026-07-25 — the syscall arms' disclosure-recall calibration: is the oracle able to fail?

**The hole.** The Rust and Swift **syscall** oracles (`soundness/realworld/run.sh` in each, plus rust's
per-function `pf/run_pf.sh`) reported **0 violations** — and that number was not admissible as evidence the
honesty invariant held. It is equally consistent with an instrument that *cannot* report one. A marker that
stops firing, a report path that stops resolving, a verdict loosened during a refactor: each produces a
silent, permanent green indistinguishable from soundness, and each is far likelier than soundness. The
language arms (Node preload, JVM `-javaagent`) already carried a disclosure-recall battery; these two
carried **attribution** calibration only (`oracle_pf` checks a *known* effect lands on the right frame),
which is a different question. The paper conceded it in §6.1 as a named gap.

**What was built.** `soundness/realworld/recall/disclosure_recall.sh` (+ `mutate_report.py`,
`disclosure_recall_check.py`, `README.md`) in candor-rust and candor-swift. It runs the **real** oracle three
or four times over, identical except that candor's report is falsified between the analyzer and the verdict
(`CANDOR_ORACLE_MUTATE`, unset in every normal run). Nothing is stubbed — each pass builds the drivers,
executes them, and reads real `strace` output — so what is calibrated is the deployed instrument end to end
rather than a re-implementation of its verdict, which would have calibrated a copy.

| mutant | what is falsified | catches an oracle that… |
|---|---|---|
| `silent` | every effect **and** every disclosure flag | never actually reads the report |
| `wrong` | a decoy effect (`Rand`) replaces the real one | tests non-emptiness instead of *the* effect |
| `transitive` | **only the entry point**, effect's leaf left honest | adjudicates only where the effect was issued |

`transitive` is the sharp one and applies to the per-function verdict alone: it is the shape a dropped
call-graph edge produces — the (A3) failure — and neither of the others can distinguish an oracle that
checks *every* frame on the stack from one that checks only the leaf. A program-level verdict cannot see it
at all, since the effect still appears somewhere in the report.

**Result (Docker + `strace`, Linux/arm64).** Rust, program level: **19/19** falsifiable drivers caught on
`silent`, **19/19** on `wrong`, 0 uncalibrated, and the fabrication mirror fired on the pure control. Rust,
per-function: **4/4** on each of `silent`, `wrong` and `transitive` — and the transitive pass named exactly
`main{}` in all four drivers, the one frame falsified, leaving the honest leaf unflagged. So the oracle does
not merely notice that *something* is wrong; it localizes the lie to the frame that told it. Swift, program
level: **12/12** on each mutant with the fabrication mirror firing, and one effect (`realtool`'s `Fs`)
reported **uncalibrated by name** because its marker did not fire at the lowered local timeout.

**Two defects the battery found on its first run, neither in the oracle:**

1. **The pure control was unfalsifiable.** candor emits no `functions` entries for a wholly pure program, so
   the mutator had nothing to edit and the `wrong` pass sailed past it — the verdict's **fabrication** branch
   was never exercised. Fixed by *synthesizing* the claim instead of editing it. The checker refused to
   certify until then, which is the behaviour wanted: an untested branch reads as a blind spot, not a pass.
2. **A missing `python3` produced a wall of confident findings.** The Swift container lacked the interpreter;
   the harness's inline reader silently returned an empty prediction for every driver and the oracle reported
   **13 NEW UNDER-REPORTs**. Loud rather than dangerous — it fails closed — but a missing dependency should
   not impersonate a soundness catastrophe. All three harnesses now guard on `python3` alongside `strace`.
   Caught only because the battery's first act is to require the control pass green.

A third, in the checker itself: a **multi-effect driver whose marker did not fire vanished from BOTH** the
falsifiable set and the uncalibrated list, so recall would have read 1.0 over a quietly smaller denominator
— the exact silent truncation the design exists to prevent, in my own code. Found on the Swift arm and
fixed (candor-rust `c0a142c`).

A fourth, environmental: under Docker Desktop, `strace` + Foundation's `Process` hangs indefinitely, which
previously confined those Swift drivers to CI. The traced run is now bounded (`timeout 90`), degrading a
hang to a partial trace — the verdict still stands if the marker fired, and the driver is reported
**uncalibrated by name** if it did not.

**Standing gates.** candor-rust `.github/workflows/disclosure-recall.yml` (on changes to
`soundness/realworld/**`, weekly, and on demand — three-plus full oracle passes is too costly per-PR);
candor-swift as a schedule/dispatch-gated step in `ci.yml`. Recall is always reported **as a fraction of the
falsifiable set, with the uncalibrated remainder printed by name** — an oracle falsifiable on 3 of 20
drivers has a recall of 1.0 and is still nearly blind, so the two numbers travel together.

### 2026-07-25 — how far up a call chain can the Node oracle falsify? (measured, not asserted)

The companion to the same day's syscall-arm calibration. `candor-ts/sensitivity.mjs` asks whether the oracle
catches an effect at the function that **performs** it, disclosure stripped, and answers 8/8. The question
one level up is the one H actually turns on: candor's signatures are **transitive**, so a false all-clear can
sit on a **caller** whose leaf is perfectly honest. Whether this arm could see that was recorded as "weaker
against a dropped-caller-edge miss" — an adjective standing in for a measurement.

**`candor-ts/transitive-recall.mjs`.** Seven three-deep `entry → mid → leaf` chains hold the effect and the
depth fixed and vary **only** the boundary between caller and leaf. Every signature is stripped to
complete-pure, so the oracle is the only net. Each frame reads one of four things — and the taxonomy is the
substance:

| verdict | meaning |
|---|---|
| `CHARGED` | the oracle reached it — a lie here would be caught |
| `UNCORROBORATED` | out of reach, but candor discloses — H holds on the **analyzer's own claim**, no independent check |
| `BLIND` | out of reach **and** claimed complete-pure — a lie here is invisible |
| `NO-REACH` | the control's callers, off the causal path by construction |

**Result: 7 of 12 on-path caller frames reachable, 5 uncorroborated, 0 blind.** And the rule is sharp: the
oracle charges up to the function whose **source span lexically contains the continuation**, and nothing
above it — callers suspended across an `await` are off the stack when the effect fires. A probe fixture
confirms the mechanism instead of leaving it a story: move the continuation into a helper outside the
caller's span and that caller drops out of reach exactly as predicted.

**Why the middle verdict earns its own row.** Scoring those 5 as caught would credit the falsifier for the
analyzer's work; scoring them as blind would manufacture a defect out of a correct answer. They are frames
where we are **trusting candor, not confirming it**, and the number is only meaningful if that is said.

**A control the first draft did not have, and needed.** An earlier version used fire-and-forget chains
(`mid` schedules a timer and returns) and reported **four blind frames**. They were nothing of the kind: the
caller genuinely never reaches the effect, so `pure` is correct. Every scored shape now `await`s the work —
the caller provably cannot have returned — with one fire-and-forget shape kept as an explicit control.
**Durable: a recall battery needs a negative control or it will invent blind spots out of correct answers.**

**Gate.** Reds on a blind frame or an inconclusive shape (a fixture whose effect never ran measured nothing),
and **verified to catch**: forcing the uncorroborated frames to classify as blind reds it. The uncorroborated
count is a property of JavaScript, not a defect — closing it needs continuation-tracking capture
(`AsyncLocalStorage`), which stays future work. Wired into candor-ts CI as its own step. candor-ts `cf91b95`.

### 2026-07-25 — the falsifier's own stack was truncated at ten frames (Node arm)

Found while trying to close the previous entry's 5 uncorroborated frames with continuation tracking. The
continuation work recovered only one frame, and rather than publish a number I could not explain I traced it
— the standing rule. The explanation was not about async at all.

**The find.** `candor-ts`'s preload attributes an effect to **every project frame on the stack**
(`verify-emit.mjs`), which is what makes the Node arm transitive. It reads that stack from
`new Error().stack`. V8 captures at most `Error.stackTraceLimit` frames and **the default is TEN** — several
of which the patched builtin, the emit path and Node's internals consume before app code is reached. The
engine never raised it. So on any chain deeper than a handful, **the OUTERMOST project frames were silently
dropped from the trace**, and a caller the trace never mentions is a caller whose false all-clear the oracle
cannot catch.

**Measured on a 16-deep plain synchronous chain: 5 of 16 frames charged.** No boundary crossed, no async
involved, nothing in the oracle's output announcing a truncation. **Fixed** by raising the limit for the
duration of our own capture and restoring it (the application's `Error` behaviour is untouched); the same
probe now charges **16 of 16**. Bounded at `CAPTURE_DEPTH = 256` and the bound is stated, not assumed
infinite. candor-ts `verify-emit.mjs`.

**Why it matters beyond the fixture.** This is the shipped falsifier, so it affects real results, and it
biases them in the dangerous direction: truncation can only *lose* checked frames and *miss* violations,
never invent them. Every Node-arm "H held" was therefore weaker than it read, over an effectively shallower
frame set than reported. The held-out slice was re-run on the corrected engine and filed **beside** the
frozen record rather than replacing it (`results-depthfix/`, `EXPECT_SHA`/`RESULTS_DIR` overrides) — amending
a pre-registered pin in place would restate a result as though the original run had never happened.

**A second defect the first had been hiding.** With the outer frames restored, **CommonJS module-loader
reads turned out to be charged to the program**: `require()` reads a file, the loader performs that read
while every module in the chain is still on the stack, so a program whose only "effect" is `require()` was
charged `Fs` at every require site — the fabrication mirror, in the instrument built to catch its opposite.
The guard keys on the **caller**: a loader read has `node:internal/modules` immediately beneath our
machinery; a program's own top-level `fs` call has the program's frame there. Keying on "a loader frame
anywhere on the stack" would instead silence genuine top-level I/O during module initialization — the sin
this oracle exists to find. Verified both directions.

**And the order is the lesson.** The depth fix *alone* took the held-out slice from 3 violations to **9**,
across five previously-clean packages. Reported at that moment they would have read as a dramatic set of new
catches. They were artifacts of the second defect. A run between the two fixes is filed nowhere: a number
that was never true is not a datapoint.

**Corrected held-out slice** (filed beside the frozen record, never replacing it — `RERUN.md`,
`results-corrected/`): **92 frames checked against 85**, the same 5 sound-complete, **4 violations**. Two
were already on the record. **Two are new and were traced to source rather than counted:**
`proper-lockfile`'s `index.<module>` ran `{Env,Fs}` while declared complete-pure — it `require`s
`lib/lockfile` → `graceful-fs`, whose module top level reads `process.env.NODE_DEBUG` (`graceful-fs.js:35`);
`write-file-atomic`'s `lib.index.<module>` ran `{Rand}` on the same shape. A module initializer reaching an
**unanalyzed dependency's** top-level effect must disclose `Unknown`, not claim purity. Candidate silent
under-reports of one class, invisible before the truncation fix because they live on the outermost frames.
**Recorded, not repaired** — adjudicating the class is separate work.

**Standing gate.** A depth probe in `transitive-recall.mjs`, verified to CATCH: revert the fix in a scratch
copy of the engine and it reports 5/16 and exits 1. `npm test`, fuzz 25/25 and the sensitivity battery
(8/8 disclosure, 8/8 oracle recall) are unchanged by both fixes.

**On the continuation tracking that started this.** With the capture no longer truncated,
`CANDOR_VERIFY_ASYNC_STACKS=1` (async_hooks trigger-chain inheritance) recovers **all 5** previously
unreachable caller frames at ~1.05× — and **fabricates on 2** frames of the fire-and-forget control, charging
callers that had already returned and left the dynamic extent. Trigger-chain inheritance cannot distinguish a
caller *suspended awaiting* the work from one that merely *scheduled* it. So it is shipped **opt-in and off**:
buying reach with the cardinal sin's mirror is precisely the trade this project refuses. A sound version needs
promise-graph rather than trigger-chain tracking. The control earned its place here — without it the mode
would have looked like a clean win.

**Durable lesson.** Two entries in one day turned on the same discipline and it is worth stating plainly: *a
number you cannot explain is not a result.* The 1-of-5 recovery looked like a modest, plausible finding about
JavaScript semantics. It was a ten-frame limit in our own instrument, and every negative result the Node arm
had ever produced was quietly resting on it.

### 2026-07-25 — the initializer edge, and the `gains` case that was structurally invisible

The day's last thread, and the one that connects the soundness work to what the product sells.

**The vein.** A module whose own top level is pure imports a module whose top level is not. Importing runs
that top level, so the importer transitively performs the effect — and candor reported `(∅,∅)`. Found on two
held-out npm packages by the corrected Node oracle, traced to source rather than counted:
`proper-lockfile`'s `index.<module>` reaches `graceful-fs.js:35`'s `process.env.NODE_DEBUG` through
`require`; `write-file-atomic`'s reaches `Rand` through `signal-exit`.

**The concept was right in the reference engine; only an edge was missing** — the
[implicit-stringification](SOUNDNESS-VEIN-implicit-stringify.md) pattern again. With the dependency inside
the scanned set candor-java models it exactly (`app.App.<clinit> { Env* }`, one hop via `dep.Dep.<clinit>`);
move it out and it reads pure. Full record in
[SOUNDNESS-VEIN-initializer-edge.md](SOUNDNESS-VEIN-initializer-edge.md).

**Two write-ups of mine were wrong before testing them.** I recorded the vein as being about *unanalyzed
dependencies* and asserted that chaining a dep report via the existing `deps` key would resolve it. Chaining
changed nothing — there was no edge for a chained report to resolve — and the edge turned out to be missing
**even between two analyzed modules inside one project**. Both corrections are kept in the vein doc. The
second one established the order that made everything else work: **the edge first, then the chain becomes
useful.**

**Resolution was DETERMINATION, not disclosure, at every step.** The obvious fix — disclose `Unknown` for any
top-level import of an unanalyzed dependency — was measured and rejected: it fires on **60–100% of modules**
across six real packages (candor-ts itself 83%), which does not make the initializer unit honest, it makes it
uninformative. What shipped instead: the intra-project edge (`70553c3`), chained dep reports resolving it
(`3643cd9` — the effect set was *already* in `crossDeps` under `<pkg>#<module>`, the edge just never
consulted it), and `--dep-inits` (`fab67fd`) scanning the project's direct dependencies, because the blocker
was never analysis — it was that nobody had scanned the dependency, and `node_modules` is on disk.

**Both held-out findings resolved.** `proper-lockfile` 1 violation → 0 intra-project; `write-file-atomic`
pure → `['Rand','Unknown']` once `signal-exit` is scanned. Neither by weakening a check or widening `Unknown`.

**And the payoff.** The `gains` headline case — *"a dependency bump added a top-level `Net` call"* — was
**structurally invisible**. Exhibit at `candor-ts/eval/dep-init-supply-chain`: the app's own source is
unchanged; the dependency adds one file-scope `https.get`.

    without --dep-inits    gained: []                                   ← the attack is invisible
    with    --dep-inits    gained: ['Net']   src.a.<module>  origin=existing

`origin: existing` is the ⟨0.12⟩ attack signal — the function **shipped pure and now performs the effect** —
which is the distinction between a feature and a compromise, and the reason the verb exists. A commercial
claim the tool could not previously substantiate on its own headline case.

**Swift's sibling closed the same day** (globals are lazy, so a *read* forces the initializer): `acfed07`,
after three reverts that were each right at the time — 113 fabrications under bare-name keying, 34 once
global identity was unique per module ([SOUNDNESS-VEIN-global-unit-identity.md](SOUNDNESS-VEIN-global-unit-identity.md)),
26 after excluding same-named instance properties, and then **all 26 traced and found genuine**. *When the
fabrication count stops shrinking, trace the remainder before calling it fabrication — I nearly discarded a
correct fix twice.*

### 2026-07-26 — the boundary rung, and what a code review found in a day's verified work

The scan-boundary vein's disclosure half ("half 1" of
[DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md)) shipped **four-way** and is pinned by
conformance PART 21, verified-to-catch per engine row. Four engines, four different triggers, one rule:
*absence under a key licenses a purity claim only if the key names something that could have had a body.*
rust and swift key on an untyped receiver from a dependency factory; java on the **opcode**, since bytecode
always carries a static owner and `INVOKEINTERFACE` proves the site names a declaration the JVM will never
run; ts on a receiver typed to an **abstraction**, having refuted the factory probe outright because its
return types travel in `.d.ts`.

Then a workflow code review over the same day's commits returned **ten confirmed defects** — two cardinal
sins, six fabrications, two disclosure gaps — in work that had already passed per-fix A/B on real corpora,
per-fix regression tests verified-to-catch, each engine's own suite, and four-way conformance. Every one of
those gates did its job; none of them was positioned to see these.

**The pattern in the severe ones, and the reason this entry exists.** In three separate cases the correct
principle was written in a comment and the code beneath it did the opposite:

- rust `typeSurface` **became the leaf-key join the design doc rejects**, four paragraphs under a heading
  reading "the trap this must not walk into". Type identity read as a naming detail; it was the mechanism.
- java's hand-off comment argued "the parameter is gated to Runnable/Callable, so the constructed type is a
  task type and its reported surface is what the runtime invokes." The gate constrains which TYPE is handed
  off and says nothing about which MEMBER runs. `executor.submit(new lib.ReportJob())` inherited an
  unrelated `exportCsv()`'s Fs and `upload()`'s Net.
- swift's `depBoundLocals` comment said "cleared on any rebind by the clearBinding path below"; that path
  cleared four other maps and not this one.

A comment that states a justification reads like reasoning and is only an assertion. These three were each
*confident, specific, and wrong*, and each survived review-by-author precisely because the comment answered
the question the code should have been asked.

**The two I found myself came from counts, not diffs.** Both had clean A/Bs. `typeSurface` was near-inert on
real code — the producer took the owning type as the segment after `#`, which is the MODULE on any modular
crate — and the tell was pgman showing 356 factory returns against 16 non-pure types with ZERO intersection.
Swift's half-1 provenance conjunct was not checking provenance at all — instrumented, its top hits were
`max()`, `min()`, `abs()` and the engine's own local functions — and its A/B was 0/0 because the corpora
were unchained and conjunct 3 correctly suppressed everything. *An A/B diff shows what changed; it cannot
show that a mechanism never fires, or fires on the wrong thing and is masked downstream. Count how often the
preconditions hold.*

**`typeSurface` was REVERTED, not patched.** Two of its four defects were design errors — the leaf-key join,
and removing half 1's fail-closed floor exactly where `by_key` deliberately refuses to answer an ambiguous
key. Patching those means designing qualified type identity and distinguishing "no entry" from "I dropped an
entry", which is the rung's actual design work. Requirements for a second attempt are recorded in the design
doc, each derived from a confirmed defect rather than imagined.

Half 1 is untouched and remains the floor in all four engines. Fixes: rust `71c2495`, java `ba8c0c5`,
ts `8ee89f5`, swift `81a9dc3`; revert `eb12d3e`.

### 2026-07-26 (cont.) — auditing the review's own repairs: four defects in five fixes

The code-review round above produced five fixes. Each was then re-checked in the OTHER direction — the
discipline the round itself had just added to the standing bar — and **four of the five were wrong**, two of
them cardinal sins:

| fix | other-direction result |
|---|---|
| rust `trait_quals` tombstone | **cardinal sin** — a colliding leaf was dropped for BOTH crates, so `b.go()`'s genuine `Net` vanished. Pre-fix last-wins had it right by accident. |
| java hand-off SAM filter | an **allowlist of method names**, already missing `getAsInt`/`getAsLong`/`getAsDouble`/`getAsBoolean` — an `IntSupplier` implementation's effects would have been dropped |
| ts callback-position guard | **cardinal sin** — `then(onFulfilled, onRejected)` invokes its SECOND argument, and moving the dep charge below a blanket arg-0 guard lost it |
| swift erasure split | clean — verified, a shadowing local resolves via `vars` and never reaches the CHA arm |
| rust provenance scoping | clean — and it exposed a pre-existing gap: trait-typed LOCALS never recorded their own crate |

**The mechanism, which did not vary.** Each fix narrowed a sound over-approximation to kill a fabrication,
and narrowed past the real reaches. The fixture that demonstrates the fabrication is *structurally incapable*
of demonstrating the loss — it contains only the pure receiver (`only_alpha` calls `a.go()` and never
`b.go()`), only the uninvoked argument (`forEach(cb, thisArg)` and never `then(ok, err)`), only the one call.
Passing it is evidence about one direction and silence about the other.

**Two corollaries.** Narrow with a **denylist** of proven-safe cases, never an allowlist of permitted ones —
the java fix reached for the forbidden shape *while fixing an over-charge*, and had already forgotten four
entries. And prefer **disambiguating** to **dropping**: tombstoning a colliding key is safe against
fabrication and silently costs every genuine use; the information to separate the cases existed one level
down (per-receiver rather than per-leaf).

**A guess that is right for the wrong reason hides the gap underneath it.** rust's leaf map was last-wins,
which by accident stored the crate a shadowing local needed — so "trait-typed locals never record their own
qualification", a whole missing feature, looked like working code. Removing the guess did not create that
gap; it revealed it. Expect an apparent regression when you stop guessing, and establish which it is before
treating it as one.

Fixes: rust `0eca79c` + `fee73fe`, java `020fb62`, ts `c08063a`.

### 2026-07-26 — java joins PART 18: the `interfaceUnion` PRODUCER, and the `implements` rung comes off the queue

candor-java was the one engine marked **N/A** for conformance PART 18, on the recorded grounds that
"whole-classpath bytecode resolves cross-module dispatch natively". That is true of an UNCHAINED
whole-classpath scan and **false of a chained one**, where the implementer sits in the other tree — the same
"ask separately what an engine does at the BOUNDARY" lesson the initializer-edge vein taught. Split the two
packages, chain the dep report, and `void run(lib.Store s) { s.save(…) }` reads `Unknown[dispatch:…]` (half
1's disclosure) rather than the `Fs` its single-tree control gives.

**What was missing was only a PRODUCER.** The consumer was already correct and needed no change: candor-java
keys report entries by `owner.name+desc`, which is exactly the key `crossDepJoin` forms for an
INVOKEINTERFACE site, so a union entry lands where the join already looks. This retires the proposed
`typeSurface.implements` field entirely — the union publishes the implementer set the consumer's question
needs, so the hierarchy encoding is redundant (DEP-RECEIVER-TYPING-DESIGN.md). `returns` remains the one
genuinely new field, wanted by rust and swift only.

Emission is gated on `CANDOR_WORKSPACE_CHAIN` (the flag rust and swift already read), per interface method,
effects = the union over `Cha.chaTargets` — the same CHA universe in-scan dispatch uses, so a union can only
name bodies the scan analysed. Gate exit 1 (single-tree control) → 0 (split + chained) → **1** again.

**Measured.** Flag OFF: twelve real jars byte-identical to the pre-change engine, byte for byte. Flag ON:
entries +0.9%–14.8%, every addition an `interfaceUnion`, ordinary entries untouched. The empty-union skip is
the dominant filter rather than a rubber stamp — jackson-databind: 198 candidate interface methods, 161 pure
across every implementer, 36 emitted. Six chained library pairs, 21 922 analyzed functions: **65 effect
gains, 0 effect losses**; 7 half-1 `Unknown`s resolved to a precise effect; 10 functions newly disclosing
`Unknown` (httpcore's `Cancellable.cancel` implementers are themselves unresolved, so the union says so
instead of letting httpclient's `abort()` claim a complete set). Gains traced to okio `RealBufferedSink`/
`RealBufferedSource` (okhttp's `ResponseBody.byteStream`, every `WebSocketWriter.write*`) and httpcore
`DefaultBHttpClientConnection.flush` → `Net` reaching httpclient's three connection adapters.

**A guard written, measured and REMOVED — standing-bar item 0 in its exact shape, caught before shipping.**
"Emit only for an interface with at least one local subtype" read like a bound on `chaTargets`'
owner-inherits-a-default fallback. It changed **not one entry** across the twelve jars, and the single shape
where it did fire — an interface re-abstracting a method whose only body is a super-interface `default` — is
a genuinely runnable body that an EXTERNAL implementer inherits and cannot see for itself, a dep supertype
not being on candor's classpath. It was an under-report wearing a bound's clothes; `chaTargets` finding
nothing is what actually delivers "nothing implements it, so nothing is published".

**And two guards that DID survive were only shown load-bearing after their first fixture failed to exercise
them.** Every guard was mutated out and the suite re-run: two mutations changed nothing, which is not
evidence that the guards are unnecessary but evidence that the fixtures were. The static/private filter
needs a PURE `static` interface method beside an implementer declaring the same `name+desc` as an INSTANCE
method — otherwise the static call site is charged a body it never runs. A test that has never failed is not
evidence, and neither is a guard that has never fired.

Fixes: java `5f29f08`, spec (this commit) — PART 18 java arm, verified to catch against the pre-fix jar:
both java rows FAIL there and pass here.

### 2026-07-26 (cont.) — review round 2: the repairs needed repairs

A second review over the repairs from round 1 returned **10 confirmed defects**, and the four most severe were
in the repair chain itself. Round 1 found 10; the audit of its fixes found 4 more; round 2 found 10 again.
**Three rounds, and each round found defects in the previous round's fixes.**

The rust chain is the clearest case, because the same defect survived three attempts in different clothes:

| attempt | what it did | what it missed |
|---|---|---|
| last-wins map | picked one crate for a colliding trait leaf | FABRICATED the other crate's effects |
| tombstone (`71c2495`) | dropped the colliding leaf for both | LOST the genuine reach — cardinal sin |
| per-receiver (`0eca79c`) | resolved `&dyn` receivers per parameter | GENERIC and WHERE spellings still collided |
| per-type-param (`eac96e7`) | attributed each bound to its own type param | — plus two scoping holes the previous fix opened |

The through-line is not carelessness about any one case. It is that **each fix was written against the
fixture that demonstrated the previous defect**, and that fixture contains only the shape already known to be
broken. `only_alpha` calls `a.go()` and never `b.go()`; the `dyn` fixture has no generic spelling in it;
neither has a nested item or a block shadow. Every fix passed, and every fix was partial in the direction its
fixture could not see.

**Comments asserted properties the code lacked — three times, independently.** "the trap this must not walk
into" sat four paragraphs above a leaf-key join; "the parameter is gated to Runnable/Callable, so its reported
surface is what the runtime invokes" (the gate constrains the TYPE, never which MEMBER runs); "collision
inside a single parameter is impossible" (true of a parameter's own type, irrelevant to the shared map beneath
it). Each read as reasoning and was an assertion, and each survived self-review *because* it answered the
question the code should have been asked.

**A rule that can VETO costs a reach; a rule that only WIDENS costs precision.** Replacing the ts callback
position map with the callee's signature was strictly better information — and as a *replacement* it dropped
`setTimeout`, whose DOM overload declares `TimerHandler = string | Function`, a type carrying no call
signatures. Unioning the two sources keeps both blind spots harmless. That regression was caught by a test
written months ago, which is the case for running the whole suite rather than the new case.

Fixes: rust `eac96e7`, ts `4958a6d`, java + swift in progress. Round 1 and the audit are the two entries above.

### 2026-07-26 — the erasure gate, and the fifth case of a fix scoped to its own fixture

The entry above names the through-line for round 2: *each fix was written against the fixture that
demonstrated the previous defect, and every fix was partial in the direction its fixture could not
see*. Here is the fifth independent instance, and this one arrived with a cross-engine escort.

candor-rust's R4 measured that gating an imported-trait CHA on PROVENANCE alone put **32 fresh
Unknowns on serde_json**, and that the discriminator that works is **erasure**: a `dyn` receiver is
type-erased, so the crate's impls really are its candidate witnesses; a `T: Trait` bound or an
`impl Trait` parameter is monomorphized *by the caller*, so they are not. R4 had cited swift's
`eae2de2` as precedent for the shape, so the queue asked the reverse question — is the engine that
supplied the precedent fabricating too?

**Yes, and it took two fixes, not one.**

`d62dd69` closed the `some P` PARAMETER — the spelling rust's finding literally names — by keying
the gate on `isOpaqueParam(p.type)`. That check can only ever answer for a parameter's own type.
`02fb0ad` then found four more doors to the same CHA, each resolving a receiver to the bound `P`
and each monomorphized by the caller: `[T]` under a `<T: P>` bound, `[some P]`, the `forEach`
closure form of either, a field typed as the enclosing type's generic parameter, and
`extension Array where Element: P`. Every one was measured charging the effectful conformer's Env
to a function whose only call site passes the pure conformer.

Three things worth keeping:

- **The one spelling that was already safe was safe by ACCIDENT, and that is what hid the rest.**
  `<T: P>(_ x: T)` never fabricated because `params` records the spelling `T`, which resolves to
  nothing — so the `some P`/`<T: P>` pair looked closed. The container and field paths resolve to
  the bound *deliberately*, because R28/R39 need them to, and that is exactly why they leaked.
  A case that passes for a reason you have not checked is not evidence about its siblings.
- **A gate on a TYPE and a gate on a RECEIVER are different gates.** The same receiver spelling
  resolves through `vars`, an implicit-self field, a field walk or a subscript element, and only
  the branch that answered knows which. The flag now travels with `rootOf`'s resolution.
- **The mid-flight trade, from `81a9dc3`, is the standing-bar item 1 case in miniature.** The first
  erasure fix enforced the distinction by withholding the receiver's TYPE. `vars` is seeded from
  the parameter types, so that removed typed resolution for the classifier AND for the SPEC §2 dep
  join, and an Fs-performing function read PURE. A fabrication was closed by opening a cardinal
  sin, inside the fix for the cardinal sin's mirror.

And a carve-out that survives the round: `RAW_VALUE_BASE_TYPES` is **not** subsumed by erasure,
measured by removing it with the erasure gate in place — `plainString(_ s: String)` reads Env via
`enum Rank: String`. Erasure is a question about the receiver's spelling; the raw-value carve-out is
about Swift's inheritance clause being overloaded for a concrete receiver nobody monomorphizes.

A/B for `02fb0ad`: 11 real Swift targets, 10 609 report entries; zero entry, effect, Unknown and
unknownWhy deltas, and one traced change (TCA's `TransactionPublisher.receive`, whose
`var upstream: Upstream` was CHA'd over five local `Publisher` conformers although its single
construction site passes a Combine `AnyPublisher`). Instrumented, the gate fires exactly once
across all eleven targets — the trigger is real and this corpus barely exercises it, which is the
honest reading of a clean A/B rather than a claim that the fix is free.

Fixes: swift `d62dd69`, `81a9dc3`, `af9dbf8`, `02fb0ad`; rust `1950a27`, `7a5fc1d`.

### 2026-07-26 — a proc-macro2 span crossing a thread, and the `let` annotation that never asked

Two candor-rust rounds in one session, unrelated in mechanism and related in shape: both are places
where the *question was never asked*, and in both the code carried a comment asserting a
justification that did not cover the case (standing-bar item 9).

**1. The `getrandom` parse abort was a SPAN CROSSING A THREAD.** `candor-scan` died deterministically
on three registry crates with proc-macro2's `unreachable!("Invalid span with no related FileInfo!")`.
The fallback `Span` is a pair of byte offsets into a THREAD-LOCAL source map; candor parses files on
rayon workers and walks them on the collector thread (`SendFile`). The code knew half of this —
`fn_locs` runs in the parse closure precisely because line/col only resolves there — but the
`SendFile` contract was written as if candor were the only span reader. **syn's parser reads spans
too.** `visit_macro` hands the macro's token stream straight back to `syn::parse2`, and
`syn::lit::parsing::parse_negative_lit` JOINs the `-` punct's span with the literal's. A `-1` inside
any macro body is the whole trigger; getrandom spells it
`debug_assert!({ match ret { 0 => true, -1 => …, _ => false } })`.

Three things worth keeping:

- **The quiet outcome is the one that matters.** Past the end of the walking thread's map the lookup
  panics; INSIDE it, it silently resolves against an unrelated file. Which you get depends on how much
  each thread happened to parse — that is why the crash looked data-dependent, why it would not
  reproduce on the file alone, and why the loud form is the tail of the distribution rather than the
  distribution. Instrumented over 121 crates: **88 927 macro re-parses, 72.4% of them handed a stream
  whose span this thread cannot resolve.** The A/B changed 3 crates out of 976; the counts are what
  say the mechanism is pervasive (standing-bar item 8).
- **The first diagnosis was not just wrong, it was inverted.** It blamed synthesized `Group::new`
  call-site spans. `Span::call_site()` is `(0,0)`, the dummy file proc-macro2 seeds EVERY thread's
  map with — the one span that is always valid. It is now the FIX (`respan_call_site`), applied at all
  four sites that re-parse moved tokens.
- **"Cannot be reduced to a fixture" was a property of the setup, not of the bug.** Parse on one
  thread, walk on a second FRESH thread whose map holds only the dummy file, and the panic is
  deterministic. Each of the four call sites was mutated out and its named failing test recorded.
  A third fixture settles the attribute parsers (`parse_nested_meta`) by measurement instead of by
  argument: they survive the same crossing.

Measured on the whole local registry, both arms preserved by content hash: panics 3 → 0, **21 effect
gains, 0 losses**, `unanalyzed` −3, 973 of 976 crates identical, every gain traced (`libc::open` →
`Fs`, `libc::nanosleep` → `Clock`). Fix: candor-rust `4f7b704`; the per-file containment from
`a593197` stays — this closes one trigger, not the class.

**2. A `let`'s annotation can NAME a generic, and nothing asked the signature for its bound.** Opened
by a note from the swift `02fb0ad` round asking whether rust has swift's shape — a container/field
position where a generic bound WOULD resolve but the code never asks, i.e. correct BY ACCIDENT.
Answered with a probe crate: every dispatch position, each with a `dyn` CONTROL beside it.

The container and field positions are **not** it — `Vec<T>`, `&[T]`, `HashMap<K,T>` and every field
form already thread the bound map and all resolve. The gap is the LOCAL `let` ANNOTATION, the one
position Pass A cannot reach: `trait_leaves` was called with a literal empty map, so
`let d: T = pick(); d.go()` read silent-pure while the identical PARAMETER resolved and while
`let d: Box<dyn Doer> = x` — the same line, one spelling along — resolved too. The site was also
short of `elem_trait_leaves`, `tuple_trait_leaves` and the `is_callable_type` map entirely.

And underneath it, **a PARAMETER-position defect the accident was hiding** (standing-bar 0b): the
tuple destructure wrote BOTH maps for a position — `tuple_types` yields the spelling (`"T"`),
`tuple_trait_leaves` yields the bound — and `vars` wins at the call site, so the binding resolved to
a type named `T`, which is nothing. The `dyn` spelling escaped only because `tuple_types` yields
`None` for it. Removing the guess revealed the gap rather than causing it.

976 crates: **4 gains, 0 losses**, entry +2, Unknown +3/−0. Every gain is a DISCLOSURE, not an
effect, and every one is the existing 12-impl CHA bound reaching a receiver it could not see —
pinned by a fixture where the PARAMETER form of a 13-impl trait reads `Unknown` in BOTH arms.
Traced: image's `interpolate_bilinear<P: Pixel>` (`let mut out: P`), rand's `WeightedIndex::new`
(`let mut total_weight: X`), moxcms' `lut_interp_linear_gamma_impl` (`where u32: AsPrimitive<T>`
plus `let mut value: u32 = …; value.as_()`, which was ABSENT and so a purity claim, now
`invisible: ["num_traits"]`), and ebman's `lint::default_rules` (`let candidates: Vec<Box<dyn Rule>>`,
19 impls). Six guards, six mutants, six named failing tests. The residuals — tuple INDEX access, an
unannotated rebind, a factory return bound into a local — are pinned as a test WITH the finding that
makes them residuals: each one's `dyn` control is silent too, so they are POSITION-level gaps rather
than this rung's "never asks". Fix: candor-rust `a80bb15`.

### 2026-07-26 — java: four supertype walks resolved by DEPTH; the JVM resolves the CLASS first

One defect, four sites, and one of them was the ordinary virtual-dispatch path. JLS 15.12.2.5 /
8.4.8: a concrete method inherited from a SUPERCLASS beats an interface `default` at ANY depth. Four
walks in candor-java each polled ONE queue seeded from a list that flattened "superclass" and
"interfaces" together, so the traversal interleaved the two BY DEPTH:

    class Root { public void write(byte[] b) { /* writes a file */ } }
    class Mid extends Root {}
    interface Trace { default void write(byte[] b) {} }        // pure
    class Half extends Mid implements Trace {}

Depth 1 is {Mid, Trace}; `Trace` settles the descriptor; `Root.write` at depth 2 is skipped as
already decided. The JVM runs `Root.write`. **Both halves of the honesty invariant failed at once** —
the real `Fs` was dropped (the cardinal sin) and Trace's empty effects were charged in its place.

**The review named two sites; there were three, and the third was the worst.** `reentryTargets`
(in-scan, `9ae68f7`) and `nearestDepFnsNamed` (the chained-boundary sibling, `dd81bfa`) were the
known pair. `Cha.nearestConcreteSuper` — which `chaTargets` and `monomorphicTarget` both end in, i.e.
every polymorphic dispatch candor resolves — walked `transSupers`, a **HashSet**, and returned the
first `declaresConcrete` hit in HASH order, with no notion of the class chain at all. It was not
"ordered wrongly"; it was not ordered. `nearestDepFn` had the same queue shape. All four now share
ONE traversal (`Cha.resolutionOrder`), which is the point: this vein has now produced three separate
cases of duplicated join/walk logic drifting apart (rust three copies, java two, swift three), and a
fourth was not written.

**The instruction "reuse `nearestConcreteSuper` rather than writing a third walk" was right about the
shape and wrong about the helper** — the thing to reuse was broken, and only checking it showed that.
A cross-site precedent tells you where a walk belongs, not that the walk is correct.

**A zero-delta consumer arm, and what made it a result rather than an absence.** Nine chained jar
pairs, each arm generating its own dep reports with its own jar, both jars kept by content hash:
consumer side **0 gains, 0 losses**, entry and Unknown counts identical. Per standing-bar item 8 that
is a claim about the experiment first, so the preconditions were instrumented: `nearestConcreteSuper`
is entered 5k–27k times per consumer and its ANSWER differs 5–531 times per pair (277 distinct sites
in jackson-databind alone), while the dep-facing walks are entered 8–30k times and differ **zero**
times on these pairs. So the boundary defect is real — the fixtures prove it — and rare on real
library pairs, which is a precise statement where "no change" would have been an empty one.

**Sampling five families was not enough, and the mechanical check replaced it.** A wider sweep of 45
standalone jars moved 203 entries: 80 gains and **119 losses**, including concrete effects
disappearing — exactly the direction this queue says to distrust. The claim that both directions are
CORRECTIONS was then checked rather than sampled: over those jars the answer changed **11 277**
times, and in **11 193** the new owner is a proper SUBTYPE of the old, so the new declaration shadows
it and the old named a body the JVM cannot dispatch to. All **84** remaining cases have an INTERFACE
as the old owner and a superclass-chain CLASS as the new one — the headline defect, where the JLS
says the class wins — and all 27 distinct replaced owners were confirmed to carry `ACC_INTERFACE`.
Every difference moves the answer to the one the JVM resolves.

Traced to bytecode, both directions:
- **spring-core** `ResourceDecoder.decode` `[]` → `['Log','Unknown']`. It resolved to
  `AbstractDecoder.decodeToMono`, whose entire body is `throw new UnsupportedOperationException()`,
  while the body that runs is `AbstractDataBufferDecoder`'s. A purity claim on a method that drains a
  data-buffer stream.
- **guava** `AbstractStreamingHasher.putLong` `['Clock','Log','Unknown']` → pure. It was charged
  through `AbstractHasher.putLong` → `putByte` → `MacHasher.update` → `Preconditions.<clinit>`, a
  chain a `final` override replaces. The fabrication mirror, removed.
- **netty** `ReadOnlyUnsafeDirectByteBuf` resolved `getByte` to the far `AbstractByteBuf.getByte`
  (whose abstract `_getByte` fans out past `CHA_FANOUT_LIMIT` → Unknown) rather than the near
  `ReadOnlyByteBufferBuf.getByte`. **caffeine** (68 entries) and **jackson-databind**
  (`BeanDeserializer` → `BeanDeserializerBase`, not `StdDeserializer`) are the same shape.

Worth carrying: **most of the damage was CLASS-vs-CLASS, not class-vs-interface.** The reported
defect was the interface `default` shadowing a superclass body; the HashSet made a *near override*
lose to a *far base* far more often (11 193 vs 84). The narrower story would have fixed the ordering
and left the unordered helper in place.

Both fixtures, second written first: the case that must NOW resolve (superclass body wins, in-scan +
across the boundary + ordinary dispatch) and the case that must STILL resolve (a genuine interface
`default` with no competing class declaration is still charged — "the class wins" is not implemented
by dropping interfaces). Three guards, three mutants, each with the named failing test recorded;
`9ae68f7`'s per-OVERLOAD shadowing invariant untouched and still asserted in both directions.

**A measurement trap, and it was in my own instrument.** The first mutation round reported the wrong
tests failing, in a pattern that looked like a real inversion, because the results parser matched
`<testcase name="X" …>(.*?)</testcase>` — and a PASSING JUnit testcase is self-closing, so the regex
ran from the first testcase's name to a *later* failing one's `</testcase>` and attributed every
failure to the wrong name. Two rounds were spent theorising about the engine before the CLI
contradicted the harness. *Item 7's "delete the output before you measure" has a sibling: check that
the thing reading your output can name what it read.*

RESIDUAL, named in `Cha#resolutionOrder`: `ReportWriter.writeHierarchy` records a dep type's
supertypes as a sorted `TreeSet` with no superclass marker, so a chain lying ENTIRELY inside a
dependency stays depth-ordered. The consumer's own classes state their superclass and interfaces
separately, so the shape the defect was found in resolves exactly. Closing the rest means a sidecar
key whose value is an OBJECT (`Loader#loadDepHierarchy` skips non-array values, so an older consumer
ignores it) — a format rung with its own compatibility surface, so it does not ride here.

Also fixed in the same pass, from the same review and marked "could not confirm":
`ReportWriter.mergeUnionInto`'s `unchanged` test compared each widened `TreeSet`'s SIZE against the
original LIST's size, which agree only while no list holds a duplicate — a genuine widening could
land on the same count, read as "no change", and drop the union, leaving the entry claiming a
narrower effect set than the dispatch reaches under the exact hash a chained consumer keys on.
**Established NOT reachable** (every list field of an ordinary entry is materialised from a sorted
`TreeSet` in `writeJson`, and `real` is always an ordinary entry), and fixed anyway: the size test
was right for a reason it did not state, and the invariant it leans on lives three hundred lines
away. Because no corpus can reach it, the unit test IS the evidence — it feeds the duplicate directly
and asserts both directions (a real widening survives; a union that adds nothing still returns the
SAME entry). Verified to catch: restoring the size comparison fails that test and, across all 512,
only that test.

Fix: candor-java `9f8e71c` (walks) + `c583da7` (merge). 512 tests, `check`, 392-case smoke and
four-way conformance all green. Unpushed.

2026-08-02 (⟨0.26⟩, the sidecar manifest): a SILENT UNDER-REPORT in the `callers --include-unknown`
frontier, in all three engines that ship the verb. The §2.2 hierarchy sidecar spelled "this type has
no supertypes" and "this type was never indexed" the same way — absence — so a subtype walk that ran
off the indexed set answered `false`, a positive claim about a type nobody analysed, and the reacher
disappeared from the disclosure with no diagnostic.

MEASURED on a real scan with only the sidecar doctored: removing the REACHING implementor's entry gave
`[]` where the control gives `[Dispatcher.run]`, while removing the sidecar ENTIRELY left the answer
correct. **A partial sidecar was worse than an absent one.** That non-monotonicity is what made this a
FORMAT change rather than a consumer patch: without a manifest a consumer cannot tell a producer's
silence from its answer. java and ts behaved identically — evidence about the format, since neither had
a third answer available.

Fixed four-way: java `78aad6d`, ts `caeda66`, swift `ea3de21` (producer; protocols were missing from
its sidecar ENTIRELY, as keys and as edges, so every two-level chain dead-ended), rust `4cae735`
(consumer-only — candor-scan writes no sidecar, so every hierarchy it walks came from another engine).
Pinned by conformance PART 30 (P6), 12 live cells, verified to catch on all four by reverting each
engine's own commit.

THE STRUCTURAL LESSON, which is the durable part: P2 and P3 degrade the chained dep REPORT, and nothing
degraded a SIDECAR. The defect sat in that gap for as long as the sidecar has existed. It was not found
by auditing coverage — it was found by tripping over the defect and then asking which property should
have caught it. **A second input shape needs its own degradation property; it does not inherit one.**

2026-08-03 (swift, `super.` across the scan boundary): a GATE-LEVEL false all-clear. `class Sub: DepBase
{ override func load() { super.load() } }` with `DepBase` in a CHAINED dependency: one package gives
`Sub.load -> ['Fs']`, the split arm dropped it from `functions` entirely and `deny Fs` exited 0 with
"policy ✓" on identical source.

Mechanism: the driver's super branch resolves on the supertype chain against PROJECT units only, and the
generic §2 dep join keys on `call.extOwner` — which for a `super.` call is the literal `<super>` MARKER,
not a type. The key it built could never match anything, in silence. The dep's report carried the answer
under exactly the key computable at that site. Fixed candor-swift `69df1f1`, union over the chain,
pinned by ScanBoundaryVeinProcessTests with a one-package control, the gate flip, and an unchained
no-fabrication control.

HOW IT WAS FOUND is the durable part: instrumenting `Call.extOwner` for an UNRELATED question (the
κ-attribution corpus study, which refuted its own hypothesis) and noticing `<super>` in the value
distribution — 21 records, inert in that corpus. **A marker leaking into a field documented as a resolved
type is worth one fixture when that field is a JOIN KEY, because a key that cannot match fails silently.**
The study that produced this finding produced no engine change of its own; the by-catch was worth more
than the hypothesis.

2026-08-03 (rust, ⟨0.26⟩ deserialization): `#[serde(default)]` over the §5 trio turned an ABSENT key back
into `vec![]` on the way in, collapsing "no conformance pass ran" into "the pass ran and found nothing" —
the same claim the producer had just carefully omitted. Now `Option<Vec<String>>`; the stable scanner
writes None and the deep lint writes Some, which is two honest answers from one type. candor-rust
`296d11b`.

### 2026-08-05 — a partial scan claiming the whole package's identity: real in swift, checked and ABSENT in rust/ts

candor-swift grew `--target <name>`, scoping a scan to one product of a multi-target package. The feature
itself is a soundness improvement — it removes a verdict about code the product never compiles — but the
first cut opened a cardinal-sin channel one level down, and it was found by asking what a **machine**
consumer sees rather than what the terminal prints.

**The find.** A scoped report was byte-shaped exactly like a whole-package one: same `package` field, same
`hash` key namespace (`MultiTarget#…`), just fewer functions. The scope was disclosed only on stderr,
which is not in the artifact anyone chains. Under ⟨0.21⟩ absence from `functions` is a positive purity
claim, so a consumer chaining that report as `MultiTarget` reads every function in the targets it never
scanned as pure.

**The fix, with no format change.** A scoped scan qualifies the key: `MultiTarget/MacApp#…`. A consumer
looking for `MultiTarget#…` then simply misses, and a miss resolves to DISCLOSED (unresolved / invisible)
rather than to a purity claim — failing in the safe direction instead of being right in the dangerous one.

**A wrong first fix, recorded because the failure mode is the interesting part.** The same change
initially put the target in the report FILENAME too, so a package's scoped reports could coexist. That
read as a bonus until discovery had to choose between three files in one `.candor/`: after
`--target MacApp` the privacy verb reported the microphone, a sensor only the iOS target reaches. A
silently wrong answer is worse than the overwrite it replaced. The scope belongs where a consumer reads
it, not where discovery trips over it.

**THE VEIN WAS THEN CHECKED IN THE OTHER ENGINES AND IS NOT THERE.** Scanning a subdirectory of a package:

| engine | whole scan | partial scan | joinable as the package? |
|---|---|---|---|
| candor-rust | `partialpkg#a::writes` | `crate#writes` | **no** — no manifest under the subdir, so it falls back |
| candor-ts | `partialpkg#writes` | `a#writes` | **no** — falls back to the directory name |
| candor-swift (`--target`) | `MultiTarget#…` | `MultiTarget#…` *(before the fix)* | **yes** — the bug |

The asymmetry has a cause worth keeping: rust and ts are handed a subdirectory, so the manifest is simply
not found and the package identity is never claimed. `--target` is different in kind — it stands at the
package ROOT, where the manifest *is* found, and scopes what gets read underneath. **A flag that narrows
what a scan reads without moving where it stands is the shape that produces this**, and it is the thing to
look for if candor-ts or candor-rust ever grows a per-workspace-member or per-crate scoping flag.

Gates: two properties pinned in `TargetScopeProcessTests` — a scoped key must not be joinable as the
package's, and a scoped scan must leave exactly ONE report in `.candor/`. 593 swift tests + 108 smoke;
four-way conformance green.

### 2026-08-12 — the gate verb's sink guard compared the locator TOKEN; the loader reads its EXPANSION

**The clause existed and nothing executed it** — §3.3.1 (3) ⟨0.28⟩ ("AND AN INPUT LOCATOR NAMES A SET —
COMPARE THE EXPANSION, NEVER THE TOKEN") is one of the two clauses that motivated the PART 41 must-ledger,
and on the day the ledger shipped the clause was still inert on three of the four engines' `gate --report`
routes. candor-swift closed the report half first (`ef6476a`) and its commit named the other three;
measured today, all three had it, on both spellings:

    gate --report r --policy P --gate-json r.<crate>.scan.json     (rust; java/ts identical in shape)
        → exit 2, the operator's report replaced by the armed refusal — and the diagnostic blames the
          report ("failed to parse — corrupt input" / "object has no 'functions' array") for the
          corruption the run itself inflicted. The run reports the corpse of the file it killed.
    the discovery spelling — no --report anywhere in argv, sink = the discovered .candor report —
        destroyed it identically: nothing in the command line names the file that dies.

**And the sidecar half was live in ALL FOUR, including post-fix swift.** The swift fix derived its list
from the gate's loader, which opens no sidecar — so the sidecars read as not-inputs and were carved out.
Measured: `gate --report r --gate-json r.<unit>.<eng>.callgraph.json` loads the report FINE, runs the
gate, and lands a REAL verdict where the graph belongs at a SUCCESS exit (rust exit 1, swift exit 0
"policy ✓") — the §2.2 pair destroyed one half at a time with nothing red anywhere, and every later
`callers`/`fix`/`rewire` reads a verdict document as a callgraph. The clause's second consequence ("THE
SIDECARS EXPAND TOO") says exactly this; the reference fix for the vein had itself under-read the clause.

**The fix, four engines, one shape.** A loader-adjacent enumerator per engine (rust
`gate_report_input_files` beside `load_gate_report`; java `Query.gateReportInputFiles` beside
`locatorReportSet`; ts `gateReportInputFiles` beside `reportFilesAt`/`loadGateReport`; swift
`withGateReportSidecars` inside the existing `gateReportInputFiles`) — the reports by the loader's own
resolution rule, discovery included, plus each report's §2.2 sidecars, existing files only. `gate` is
excluded from every sidecar walk: `<report-stem>.gate.json` is the verdict sink's own beside-the-report
layout — the exact spelling `--gate-json` exists for — and each engine's control test pins that it still
gates with a real verdict, because over-refusal (a stem-glob guard) is the plausible-but-wrong fix here.

**Pinned by PART 37 (g)**, never-skips, four engines × three spellings + the `<stem>.gate.json` control,
every row on BYTES — the report rows also exited 2 before the fix and the sidecar rows exited 0/1, so no
exit-code assertion can see either defect. Falsified per engine (each regression test red at the parent
commit, on bytes or on the engine blaming the file it destroyed) and in the harness (guard reverted →
the (g) rows fail naming the destroyed path). The three clause blocks moved from `pre-ledger` to
`PART 37 (g)` in the must-ledger — the ledger's first upgrade in the direction it was built for.

Commits: candor-rust `4b4384a` · candor-java `3a805d4` · candor-ts `18d10f0` · candor-swift `2853068`.

### 2026-08-12 — two sink routes nobody had audited, and the matrix's own binary list made checkable

**The same vein, two unmeasured routes — measured first, both defective.** After the token-vs-expansion
sweep above, two routes had never been driven: candor-java's SCAN-side baseline channel, and
cargo-candor's bespoke `policy`/`guard --gate-json` (not one of the seven binaries PART 43 runs, so no
guard written today and no conformance row could reach it).

**candor-java: the baseline pair, both directions of the expansion.** `checkBaseline` answers the ⟨0.16⟩
pure→effectful ratchet FROM the baseline's `.callgraph.json` sidecar while `runInputs` registered the
token. Measured at HEAD: `CANDOR_BASELINE=base.json candor cls --json base.callgraph.json` wrote the
report OVER the ratchet's sidecar (98 → 1180 bytes) and then blamed the wreckage ("corrupt/unreadable")
at exit 2; the `.candor/config` `baseline` spelling — the spelling that defeated the first version of
this guard in all four engines — destroyed it identically through `--gate-json`. And the SINK is a set
too: file-mode `--json <stem>` also writes `<stem>.callgraph.json`, so `CANDOR_BASELINE=base.json …
--json base` replaced the ratchet's sidecar with the CURRENT call graph at a SUCCESS exit — candor-scan's
`baseline_artifact_files` defect (`e9b1aff`), one spelling over, silently narrowing the ratchet from the
next run on. Fixed in `runInputs` (report-shaped inputs registered with their on-disk §2.2 sidecars, via
`Loader.reportSidecarSegments` so the `gate` exclusion rides along) and `refuseJsonOverAnyInput` (the
sink's full write set compared). Four `SinkArmingIntegrityTest` rows on bytes; the stem-collision row's
first draft failed only on the exit code — an identical tree writes identical bytes back — so the fixture
drifts the code before the attack run. A vacuous byte assertion is this vein's own trap.

**cargo-candor: one `rm -f`, the whole defect family.** The wrapper cleared the sink up front, so `guard
.candor/base --gate-json .candor/base.app.Executable.json` DELETED the baseline member and then reported
"no baseline found" — exit 2 diagnosing its own act (at the parent commit the falsification run exited 1
with a verdict over the half-destroyed baseline); the `.candor-version` provenance sidecar and the policy
file died identically. A usage error left a PREVIOUS run's `{"ok":true}` at the sink in both argv orders;
every post-parse exit-2 wrote nothing; the stream form put 0 bytes on stdout; and a config-load refusal
(the ⟨0.27⟩ "armed after config load" window) kept the stale green too. Fixed with the family shape:
exemption FIRST over the baseline locator's expansion (`$pre.*.json` + `$pre.candor-version`, `-ef`
device+inode), then ARM the file sink with the refusal document, usage errors deferred past arming,
every exit-2 through one helper that also serves the stream form, and the config-load window writes the
document under the same exemption. 21 `ci/wrapper-smoke.sh` rows on bytes, 10 red at the parent.

**And the reason route 2 existed at all is now a checked invariant.** PART 43 derives FLAGS from --help
precisely because hand lists find only the surface in front of the author — and its BINARIES were a hand
list of seven. `gen_sink_surface.py` now declares its route inventory and reconciles it BOTH WAYS against
the route list SPEC §3.3.1 (5) actually names, parsed from SPEC.md at run time (the part_declarations.py
construction: declaration, not inference — inference measured 1:8). A spec-named route absent from the
matrix FAILS; a declaration the clause no longer names FAILS; a gap must be DECLARED with a reason and is
printed every run — candor-agents' `scan`/`observe --json` are today's two declared gaps, visible instead
of absent. Falsified both directions. Not waivable through the ratchet: a waiver accuses an engine, these
accuse the suite's own coverage.

Commits: candor-java `d841550` · candor-rust `c96c474` · candor-spec `a097c54`.

### 2026-08-13 — a caller of a body-less declaration read pure: the dependency case was pinned, the local one never asked

**candor-ts certified callers of declarations it had never seen a body for, and `deny Unknown` was
green on them.** `localName` mints a unit for any declaration it can name and never asks whether the
declaration has a BODY. An ambient `declare function`, any member of a local `.d.ts`, an `abstract`
member no subclass overrides — each got a unit, the call site edged the caller to it, the unit was
EMPTY, and so the caller unioned nothing and came back pure. `deny Unknown`, the gate whose entire
purpose is *fail if candor cannot see what this reaches*, exited **0** where candor-rust, candor-java
and candor-swift all exit 1 on the same input.

**Found by the corpus round, and unreachable from any fixture anyone had thought to write.**
candor-ts's whole report for `axios` is 54 `index.d.ts` declarations while its 61 `.js` implementation
files are never analyzed: `analyzed.count: 54`, `functions: []`, no `unanalyzed` — ⟨0.24⟩ **row 2**,
the row that instructs a consumer to believe the report and not hedge. Note what did NOT catch it:
`check_honesty.py` called that report HONEST, correctly and within its documented scope, because it
sees uncertainty an engine HAD and failed to propagate, never BLINDNESS. Only the four-way
differential reached it.

**THE SIBLING ROUTE, again.** This exact shape crossing a PACKAGE boundary has been pinned since the
scan-boundary work — PART 21, and candor-ts's own `boundary:` suite has four rows on a chained
dependency's interface members, abstract members and function-valued property signatures. Every one of
them asks about a DEPENDENCY. Nobody asked the same question of the project's own source, and the
answer there was the opposite. The new rows sit directly beneath the old ones for that reason.

**Ruled, not invented: the engines already disagreed about WHERE the disclosure goes, and may.** java
charges the DECLARATION unit (`native:ambient`) and lets its fixpoint carry it caller-ward; rust and
swift charge at the EDGE (`native:extern fn`, `dispatch:Ambient.ping`). Both are the same observation
to a consumer, so **PART 46 asserts on the CALLER's transitive set** — what a gate actually reads —
and not on the reason string, which §4 makes per-language and best-effort. candor-ts takes java's
shape because it already mints the unit and already forms the edge, making mint-side ONE place; the
edge-side alternative would have to touch every call and desugar site, which is the drift that made
`discloseUnanswerableKey` one function after it had been two. **No spec version moves** — §3's honesty
invariant already required this and §4 already defines `native:` as "a boundary to code the engine
cannot analyse". What was missing was a row.

**The over-charge half is measured, and it is most of the work.** A body-less declaration is charged
only where NO LOCAL BODY ANSWERS IT: a base member with a local bodied override is already resolved by
the class-CHA at the dispatch site, which edges the caller to the overrides and runs its own
`allResolved` gate. Charging the empty base as well would manufacture uncertainty over code the engine
can see. Measured on the corpus, that single condition is the difference between an adoptable fix and
an unusable one — **zod +0** (its one abstract, `ZodType._parse`, is locally overridden) and **hono
+18 → +9**; the naive form charges hono's `EventProcessor`, six abstracts with three local subclasses.
The nine remaining hono flips are all true positives (`Deno.mkdir`/`writeFile` Fs,
`Deno.upgradeWebSocket`/`FetcherLike.fetch` Net — local `.d.ts` shims with no body), and axios's 52 are
the correct answer for a report that is nothing but declarations. PART 46 therefore carries the
locally-bodied CONTROL in every arm: without it the row would pass while charging every abstract
member in every real project. The second over-charge trap is the OVERLOAD SET — N body-less signatures
precede the implementation under the same unit name — so the marker mirrors `fns.set`'s
last-write-wins exactly, or every overloaded function in every project becomes unanalysable.

**Calibrated:** PART 46 was run with the fix reverted and reddens on ts alone, all three other arms
green. **Residual, stated so the axios headline is not over-read:** this closes the *"candor cannot
see"* channel, not the blindness. `deny Unknown` on axios now exits 1; **`deny Net` still exits 0**,
because recovering that means analyzing the `.js` implementation.

**Found alongside it, same class of silence, different surface:** `candor-ts --agents` truncated its
own contract at **8170 of 23121 characters** whenever stdout was a pipe — `printAgents` wrote
asynchronously and scan.mjs called `process.exit(0)` on the next line, discarding the buffer. Exit 0,
nothing on stderr, cut mid-sentence: an agent piping the contract into its context read a third of its
instructions and could not tell. The function's own header claimed one shared implementation "can
never diverge within an install"; query.mjs drains on the way out and scan.mjs exits, so sharing the
PRINTER did not share the EXIT — the sibling route inside the very function written to prevent it.
Fixed with a synchronous `fs.writeSync(1, …)` loop in the printer, so the next caller inherits it. Only
pipes were affected, which is why a redirect to a file looked correct and only the suite's
`execFileSync` ever saw it.


### 2026-08-24 — `deny Exec` did not see a subprocess being ASSEMBLED (candor-java)

**THE FIND.** candor-java charged `Exec` at the LAUNCH VERBS — `ProcessBuilder.start`/`startPipeline`,
`Runtime.exec`, the `java.awt.Desktop` openers — plus the live-child control surface on
`java.lang.Process`. Everything else on `java.lang.ProcessBuilder` read pure. Measured:

```java
public ProcessBuilder arm(String[] argv) { return new ProcessBuilder(argv); }
public void configure(ProcessBuilder pb) { pb.directory(new java.io.File("/")); }
```

under `deny Exec`: **exit 0, `no violations`, `arm` reporting `inferred: []`**. A method that assembles a
fully-armed invocation out of caller-supplied argv and hands it back was certified clean. Splitting build
from launch across two methods — or two jars, which is the supply-chain form — left nobody holding the
effect. Not a wrong rule; an ABSENT one, and absent in the silent direction: **an allowlist under-reports
every verb nobody enumerated**.

**WHY IT SURVIVED.** The type was already recognised at construction — `extractLiteralSurfaces` mines the
`cmds` program head from `new ProcessBuilder(…)`, and the surface-incompleteness guard even wrote
`incomplete: ["Exec"]` onto `arm` for its runtime head. So the engine knew the receiver's type, knew the
call was Exec-shaped, and published a marker about it, while the EFFECT that marker qualifies was never
emitted. Recognised for the LITERAL, not for the EFFECT.

**THE FAMILY WAS ALREADY RIGHT.** candor-rust charges the whole `std::process::Command` type,
candor-swift `Process()`, candor-ts the whole `child_process` module. java was the lone engine holding an
allowlist, which is the shape SPEC §1 ⟨0.32⟩ now forbids in as many words.

**THE FIX IS A DENYLIST, and the direction is the point.** The whole `java.lang.ProcessBuilder` type is
`Exec`, with the proven-pure surface carved out by name: `environment()` (still `Env` — the child's env
map, not an added capability), the NO-ARG read-back overloads (`command()`, `directory()`,
`redirect{Input,Output,Error}()`, `redirectErrorStream()`), and the §4 Object protocol. The read-backs are
keyed on the DESCRIPTOR, not the name, because each shares its name with the setter it reads back — and a
blanket "takes no argument ⇒ pure" would have exempted `start()` and `inheritIO()`, turning the fix into a
fresh cardinal sin. A wrong carve-out over-charges loudly; a forgotten allowlist entry under-reports
silently.

**THE OVER-CHARGE CONTROL IS THE DELIVERABLE, and it was written FIRST.** Four controls, all green BEFORE
and AFTER the change: a read-back-getter-only method, a project-local type that merely shares the name
`ProcessBuilder`, `environment()` staying `Env`, and an `OpenOptions`-shaped option builder for another
effect staying pure (`HttpRequest.Builder`, `StandardOpenOption`) — the last of these is the BOUNDARY of
the ruling, since an option builder carries no resource of its own and its file/socket arrives at a
terminal verb charged at its own call site.

**MEASURED.** JVM corpus A/B under `deny Exec` — 933 jars (the Gradle module cache, 371, plus an exploded
production war's `WEB-INF/lib`, 562): **0 artifact-level verdict flips, 0 functions losing an effect, 0
functions newly flagged.** uflexi's `build/classes/java/main`: byte-identical reports, unchanged verdict
(and it holds zero `ProcessBuilder` references, so the null result is explained rather than assumed). The
A/B harness was proved to CATCH before the null was believed — run against the gap fixture it reports
rc 0→1 and two gained functions.

**AND THE NULL RESULT WAS EXPLAINED, NOT ACCEPTED.** A bytecode census of the corpus: **21
`ProcessBuilder` member call sites in 9 methods across 933 jars** (9 `<init>`, 9 `start`, 2
`redirectErrorStream`, 1 `command`), and **every one of those 9 methods launches in the same body**. Three
jars reference the type and yield no `Exec` at all in either arm, each for a reason that is correct:
`smallrye-common-os` and `wildfly-common` read the static FIELD `ProcessBuilder$Redirect.DISCARD` (a value
object, no program), and `ognl` holds a class LITERAL. So the change CANNOT flip anything on this corpus —
which is the value story too: the defect is a code SHAPE (build here, launch there) that mature libraries
happen not to use, and that a dependency growing invocation-assembly would introduce invisibly.

**GATES.** `ExecInvocationCapabilityTest` (5 tests, 4 of them controls); candor-java 797 tests + 529 smoke
checks green; conformance **PART 66**, four-way, whose `readBack` and `lookalike` cells are the
over-charge controls and carry a Clock marker so the checker can REQUIRE them present — every engine omits
pure functions, so "absent from the report" would have passed a control that asked nothing.

**CROSS-ENGINE RESIDUALS, MEASURED WHILE BUILDING PART 66 — filed, not fixed (out of scope of this
change), and each is why its cell in the part is measured-absent rather than asserted:**

- **candor-swift charges construction but NOT configuration.** `t.arguments = ["-x"]` on a RECEIVED
  `Process` reports no effect at all — the same half of the gap java had, in the setter direction.
- **candor-swift misses the QUALIFIED spelling.** `Foundation.Process()` reports nothing where bare
  `Process()` is `Exec`. A sibling-route gap: one spelling of the same constructor is invisible.
- **candor-rust over-charges the read-back.** `c.get_program()` answers `Clock+Exec` — the whole-type
  `Command` rule has no read-back carve-out, which is exactly what §1 ⟨0.32⟩ now requires.
- **candor-rust over-charges an option builder for another effect.** `OpenOptions::new().read(true)…`
  answers `Fs`, while `o.open(p)` on a RECEIVED `OpenOptions` answers nothing — the over-charge and an
  under-report on the same type, in opposite directions.
- **candor-rust fabricates on a shadowed local type.** A project-local `Command` in a submodule is charged
  `Exec` when the FILE also carries `use std::process::Command;`; without that import it is correctly
  pure. PART 66's lookalike fixture uses the unshadowed form, so the fabrication is recorded here rather
  than pinned.

### 2026-08-24 — the advisory verbs certified what the gate had just started refusing, and the editor still does

**THE FIND, in one shape.** ⟨0.32⟩ made an unread exclusion class a verdict cause. All four engines
shipped it into `gate --report` and into NEITHER of the two advisory verbs that answer `ok` over the
identical bytes:

    gate --report <no-policy report> --policy <deny Exec>   -> 2
    fix-gate   --strict   (same report, same policy)        -> 0   "no deny/pure boundary crossings ✓"
    unverified --strict   (same report, same policy)        -> 0   "every function … PROVABLY clean ✓"

`--strict` is how CI consumes both verbs, so this is a green CI step over code the producing scan never
opened, printed with a tick. Fixed four-way on the day (candor-rust `9bf3f2f`, candor-swift `2bf8de7`,
candor-java `3682835`, candor-ts `9f22581`).

**THE THIRD TIME, WHICH IS THE ACTUAL FINDING.** candor-java's own `ReportCompleteness` comments record
⟨0.24⟩ doing this for `unanalyzed` and ⟨0.30⟩ doing it again for `outOfScope`, and say so in as many
words — *"the second time, which says the ARM is what a new verdict cause needs, not a note telling the
next person to remember"*. ⟨0.32⟩ is the third, and it happened in a file that carries that sentence.
A verdict cause is added at the gate and the two siblings are a separate edit nobody's checklist names.

**AND NOTHING ASSERTED THE FIX.** PART 62 pins the ⟨0.32⟩ CAUSE and drives `gate --report` only; no row
anywhere ran a `--strict` verb over an unread report. Four commits with no gate under them, which is
exactly how this defect survived in one engine while three others closed it. Closed by **PART 67**, named
for the RELATION (§3.1 ⟨0.24⟩: *"AN ADVISORY VERB MUST NEVER BE LESS SENSITIVE TO INCOMPLETENESS THAN THE
GATE OVER THE SAME BYTES"*) rather than for ⟨0.32⟩, so the fourth cause needs a fixture and not a rewrite.
Two §3.1 statements moved from `pre-ledger` to part-named in the MUST ledger — both had been correct,
prominent and unasked since ⟨0.24⟩.

**THE TRAP, and it nearly cost half the blocker.** `unverified --strict` HAS ITS OWN EXIT 1 — an
`Unknown` hole in the analysed set. Over a fixture carrying one, the verb answers non-zero and that reads
as the rule firing when it is the verb doing its ordinary job while the ⟨0.32⟩ cause goes on being
ignored. The two are indistinguishable if the row only asks *"did it refuse?"*. PART 67's `ck67` therefore
REFUSES a fixture whose reports carry any `Unknown`, and refuses an empty `functions` array too — a verb
that certifies the empty set passes its cell without asking anything.

**FALSIFIED AGAINST PRE-FIX BINARIES, not by reasoning about them.** candor-query built at `9bf3f2f^` over
PART 67's own fixture: gate 2, `fix-gate --strict` 0, `unverified --strict` 0, with both ticks printed —
the isolated advisory case, rust's gate-route fix (`ab505c0`) having already landed. candor-java at
`3682835^`: all three 0, that engine having closed both halves in one commit. The over-charge control
answered 0/0/0 on both, before and after, so the control is not what moved.

**THE FIXTURE SHAPE WORTH REUSING.** One tree, scanned TWICE — once with the policy, once without — so the
only difference between the two reports is whether the peek was ever put the question, and the excluded
file is CLEAN in both. That makes the refusal attributable to the DOCUMENT's own statement that nothing
looked, rather than to content: `peeked: false` and "looked and found nothing" are the two states ⟨0.32⟩
exists to keep apart, and here they are literally the same bytes on disk.

**TWO ROUTES CHECKED AND CLEAN, both now pinned in PART 67 rather than reasoned about:**

- **candor-java `--parallel`.** It is the one route in the family that produces reports and CANNOT gate
  (no `--policy`; its own usage text says "report-generation only"). So the question is whether the
  DOCUMENT it writes carries the evidence — a producer that dropped `excluded` would hand every downstream
  gate a clean pass in silence, a route with no policy having no verdict to go red. MEASURED: `excluded`
  byte-equal to a standalone no-policy scan of the same target, and all three verbs refuse over it. Worth
  asking rather than assuming: ⟨0.32⟩ had already caught this arm writing an ORDINARY report for an
  unevaluable target where the single-target path refused.
- **candor-ts's MCP `candor_gate`.** Shares `loadGateReport` with the CLI gate and DOES inherit ⟨0.32⟩:
  `ok` not true, `incomplete: true`, `unread` naming the class, against a peeked control that answers
  `ok: true` unhedged. Measured rather than inherited on paper, because *"believed to inherit"* is exactly
  what was said about this engine enforcing the rule on both of its CLI routes — and PART 62's ts row
  records that as false (`scan=2 gate--report=0`, pre-fix). A shared helper is a reason to expect
  inheritance, never evidence of it: that CLI defect was not in the reader either, it was in the caller
  ignoring what the reader returned.

**OPEN — candor-ts's LSP diagnostics route is fail-open on ⟨0.32⟩, and it is the least visible surface in
the family.** `lsp.mjs` does NOT share `loadGateReport`; it reads `Q.loadReport` and calls
`evaluatePolicy` directly, and the string `peeked` does not occur anywhere in that file. MEASURED on PART
67's ts fixture over real LSP stdio: `didOpen` over the no-policy report under `deny Exec` publishes
`diagnostics: []` and NO `window/logMessage` — byte-indistinguishable from the peeked control, where
`gate --report` legitimately answers 0. The instrument was proven FIRST, because a broken probe's negative
is indistinguishable from a real one: `deny Fs` over the SAME report at the SAME locator draws its
AS-EFF-006 squiggle, so the route resolved both report and policy and the empty result is the answer.
The surface has no exit code, so its obligation is the disclosure channel that file already carries three
of — a judged-nothing report, a zero-rule policy, dropped policy lines — and ⟨0.32⟩ has none. Squiggles
are this surface's entire vocabulary, which is what makes a missing one the quietest false all-clear the
project has. **NOT FIXED HERE** — the fix belongs to candor-ts, and the conformance suite must not go red
on an engine defect it cannot repair; PART 67 records the measurement in place of a row, and the row lands
with the fix. Its control must be that the PEEKED report draws no such warning, or the part passes for an
engine that warns unconditionally.

**A DISCLOSURE DIVERGENCE, noted while measuring, not a fail-open.** candor-java's `fix-gate --strict`
exits 2 correctly over the unread report and its `--json` body carries `incomplete: true`, but the TEXT
channel prints *"the report(s) named on stderr judged nothing (or could not be re-read)"* — the by-
elimination branch, since `unpeeked` has no prose of its own there. `analyzed.count` is 3 on that report,
so the sentence is false about the only thing it says. candor-rust and candor-ts both NAME the unread
class in their human channel. The exit and the machine document are right; the human one names the wrong
cause.

**GATES.** conformance **PART 67**, four-way, six cells per engine plus the `--parallel` and MCP arms;
`conformance/mcp_gate_probe.mjs` (its own over-charge control inside); `ck67`, whose five failure modes
were each falsified by hand.

### 2026-08-27 — the macro/codegen row's "—" was never independently reasoned about, for three of four engines

**The sin (swift, CLOSED same day).** §4's `macro / codegen reach` seam has read "—" (N/A, immune by
construction) across java/ts/swift/agents since the scorecard's first commit. The row's prose only ever
discussed rust's `macro_rules!`/`cfg_if!` — "java/swift/ts lack C-style macros" is true of C-style macros
and false of Swift's compiler-plugin macro system. Measured: `#urlFetch("https://danger.example.com")`
(freestanding) and `@Observable class Store` / `@MyBodyMacro func doThing()` (attached — the shape
SwiftData/`@Model`, Observation/`@Observable`, and Swift Testing actually take) scanned clean under `deny
Net`: exit 0, `functions: []`, zero disclosure. No visitor existed for `MacroExpansionExprSyntax` at all,
and no attribute-handling path treated a decl's own custom attributes as a possible attached macro.

**The fix (candor-swift `dc27915`).** Both forms route into the existing `Unknown`/`unknownWhy`
vocabulary (`"macro:<name>"` / `"macro:@Attr"`) rather than resolving what the macro does — a syntax-only
engine cannot run a compiler plugin, so disclosing the miss is the sound move, not guessing at it. A
trailing-closure macro (`#Preview { ... }`) is unaffected: the existing `ClosureExprSyntax` visitor
already walks it regardless of what syntactically contains it, so double-disclosing there would regress a
concrete catch to a vague one beside it — measured in first testing (it double-counted `#Preview { … }`)
and gated out. An attached macro attribute on a func/init/type is handled the same way, and for a TYPE
attribute the disclosure propagates onto every member the scan already collected for that type (Swift
admits exactly two explanations for a capitalized type-level attribute — a global actor or an attached
macro — so the two carve-outs, `@resultBuilder`/`@globalActor`, are exhaustive, not heuristic).
**Over-charge control, the real work here**: a first denylist cut of compiler-builtin freestanding
literals (`#file`/`#line`/…) MISSED `fileID` (SE-0274) and `isolation` (SE-0420) — the 13-package
before/after corpus diff surfaced 93 `fileID` and 8 `isolation` hits (swift-nio and Nimble default nearly
every logging/assertion parameter to one or the other), which would have been exactly the noise this fix
exists to prevent. Residual: a macro-decorated type with zero source-declared members has no function to
attach the disclosure to (the same pre-existing gap any compiler-synthesized member already has); an
EXTERNAL (non-local) `@resultBuilder`/`@globalActor` is conservatively treated as a possible macro — sound
(over-discloses, never under-reports), unmeasured precision cost. 13-package corpus (Alamofire,
CryptoSwift, Nimble, PromiseKit, Quick, ReactiveSwift, RxSwift, swift-algorithms, swift-collections,
swift-nio, swift-syntax, SwiftyJSON, Swinject) byte-identical post-fix; the nested `swift-syntax/Examples`
package (real macro usage a root scan doesn't cross) confirms the mechanism end-to-end with zero
fabrication. swift test 892/892, smoke.sh 148/148, fuzz.py 25/25, self-gate all pass. R56.

**ts's "—" is ALSO false, and open (R57) — candor-spec does not own candor-ts, so this is a finding, not a
fix.** A NAMED decorator factory is sound: `enclosing()` in scan.mjs (`ts.isDecorator(p) → null`)
deliberately keeps a decorator application's call site from wiring onto the decorated declaration, so the
factory's own effects land on its own unit rather than mis-attributing onto the thing it decorates (tested,
test.mjs:5102-5126). But an ANONYMOUS decorator — a function literal sitting directly in decorator
position with no top-level name (`@((_t,_k,_d) => { fs.readFileSync("/etc/hosts"); }) method(){}`) — mints
no unit at all, because the same `isDecorator` guard that correctly stops a named factory from being
mis-wired never mints a synthetic unit for the unnamed literal either. Live-reproduced: `deny Fs` over a
fixture with exactly this shape exits 0, `"violations": []`, nothing in the 16-function report — a real
filesystem read at class-definition/module-load time, completely invisible. Do not conflate this with the
already-known, already-DISCLOSED limitation at SOUNDNESS-LOG.md:1478-1481 (a decorator that WRAPS a method
to inject an effect at call time reads pure on the true call path, but the effect still surfaces on the
decorator's own unit — mis-attributed, not silent). Bundler-time codegen (babel-plugin-macros, loader-
injected code) is NOT a coherent seam for this row: code a preprocessor hasn't generated yet simply isn't
in the file candor-ts opens, true of any static source scanner for any preprocessor in any language —
that belongs with scan-boundary/staleness concerns, not this one.

**java's "—" holds for ONE mechanism, unmeasured for another (R58, open, not marked SILENT).**
candor-java reads compiled `.class` files (`Loader.java`'s directory walk), never source, with no
`generated`/annotation-processor path exclusion. Lombok (`@Data`/`@Builder`) rewrites bytecode inside the
SAME `javac` invocation a user runs before scanning, so it is genuinely immune by construction — the
rust-deep shape (seeing post-expansion code), verified by reading `Loader.java` rather than assumed from
"java lacks macros". But an annotation processor that emits a SEPARATE `.java` file compiled to its OWN
`.class` (Dagger, Room, AutoValue, MapStruct) is a different mechanism the bytecode argument doesn't cover
for free: Gradle/Maven land those generated `.class` files in the same output directory
(`build/classes/java/main`) the README tells users to point candor-java at, and nothing in the loader's
walk special-cases or drops them — plausible, but never checked against a real annotation-processor
project. Unlike R57 there is no reproduction either way, so this is logged as UNMEASURED rather than
rounded up to immune (this row's own original mistake) or down to a confirmed sin.

**Why this happened.** The scorecard's "—" cells across java/ts/swift/agents were pasted identically at
the row's creation and never revisited per engine — the exact shape the corpus brief's rule 9 warns about
("an audit's boundary must not be drawn around its own trigger"): the original author reasoned about ONE
mechanism (rust's macros) and let the verdict stand for three engines it never examined. Widening the
audit past its own trigger — asking what java's and ts's actual macro/codegen-adjacent mechanisms even
ARE, rather than trusting the pasted "—" — is what found R57 and R58; the same discipline had already
found R56 by the time the audit reached ts and java.

**GATES.** R56 gated by candor-swift's own regression suite (`MacroDisclosureProcessTests.swift`) and its
13-package corpus diff; a cross-engine conformance PART for the macro-disclosure vocabulary is deferred
(no fix exists yet for ts/java to conform against). R57/R58 have no gate — they are open findings, filed
against candor-ts and candor-java respectively.

### 2026-08-27 — the FFI row had the identical shape, and it was NOT the same verdict on every cell (R59-R61)

The macro row's correction (above) was found by widening past the trigger; the same day's follow-on audit
applied the identical discipline to the FFI row, which had the SAME "—"-pasted-across-non-rust-cells shape
(§4: "the FFI row has the same '—' shape for swift/agents, unaudited by this pass"). Per the corpus brief's
rule 1 (calibrate before trusting a clean result) and rule 9 (widen past the trigger), every cell was
independently MEASURED against a live fixture and a live binary rather than reasoned about from the row's
prose — and unlike the macro row (one engine wrong, three right), the FFI row had TWO cells wrong in
OPPOSITE directions: rust-deep's "verified by construction" was false in the dangerous direction (a real
silent sin), and rust-scan's existing 🟡 undersold a genuinely sound mechanism while hiding a different,
real one underneath it.

**rust-scan (R59, SILENT open).** The audit's starting hypothesis — "rust-scan's FFI cell is 🟡 because
nobody ever wrote a cross-engine gate for it" — was half right. The DIRECT mechanism (`extern "C" { fn
system(..); }`, exactly what bindgen emits) is genuinely closed: `decls.rs`'s `ForeignMod` handling records
every declared foreign name, and `scan.rs` already has a REGRESSION FIXTURE FOR IT (`tests.rs:6950`,
`extern_fns => |m| { m.extern_fns.insert("system".into()); }`). Reproducing it fresh against
`target/release/candor-scan` 0.33.1 confirmed: `run_cmd`'s `inferred == ["Unknown"]`, `unknownWhy ==
["native:extern fn"]`. `#[link(name = "c")]` (the attribute bindgen output actually carries, which the
existing fixture doesn't) changes nothing — `ForeignMod` handling doesn't branch on it. So far, unremarkable
confirmation. But `candor-classify/src/lib.rs` puts `libc`/`nix`/`rustix` in `CALIBRATED_CRATES` — the set
of crates the syscall-name table claims to have fully reasoned about — and the table's own comment
DELIBERATELY skips the generic fd verbs (`read`/`write`/`close`/`lseek`/`dup`/`fcntl`/`ioctl`/`poll`/
`select`/`epoll*`/`mmap`): "a fixed label would mis-categorise as often as it helps… an honest no-classify
(under-report) beats emitting the WRONG effect." That sentence is the exact shape of
`feedback-documented-limitation-is-not-measured`: a limitation written as a comment reads as CONSIDERED,
which stops it being measured. It was measured here, and the comment's own framing turned out to be wrong
about what actually happens. `fn drain(fd: i32) -> usize { unsafe { libc::read(fd, buf, 64) as usize } }`
called from `main` on `fd = 0` (reading stdin — a real effect) produces `"functions": []` on
`target/release/candor-scan` 0.33.1 — not `drain` alone, `main` too, and not as `invisible` or `incomplete`
or anything else: `scan.rs`'s emission gate (`if inf.is_empty() && !has_blind { continue; }`) drops a
function the instant BOTH its inferred set and its blind-reach set are empty, and an unclassified call into
a `CALIBRATED_CRATES` member sets neither — the crate is "known", so nothing routes it to `invisible` the
way an uncovered THIRD-PARTY crate would. CONTROL: when a classified sibling (`libc::open`) runs first in
the same function, the composite correctly reads `["Fs"]` — the gap is isolated to a function whose entire
effectful surface is the unclassified verb, the mio/raw-reactor shape (an fd arriving via a param or a
struct field, never opened/socketed locally). This explains why a prior corpus round's negative control
("0 candidates" across nix and 15 other crates, an earlier SOUNDNESS-LOG entry) never tripped it: real code
overwhelmingly has a proximate classified call, so the design comment's trade-off has held up empirically
even though the underlying mechanism — silence, not disclosure — is unsound. Filed as R59, SILENT, open;
severity low-med (rare by measured incidence, genuinely silent when it occurs).

**rust-deep (R60, SILENT open) — the row's prior claim, finally measured, was false.** The footnote this
row carried ("🟢¹ … clean/correct by construction") existed because nobody had ever built the ONE fixture
it was actually about: a local, bodiless `extern "C"` foreign declaration. Built here, against the nightly
dylib (`d0c906d`, via `cargo dylint --lib-path`) using a fixture identical in shape to rust-scan's own
`native:extern fn` regression: the report is `"functions": []`, but the SAME run's callgraph sidecar reads
`{"main":["run_cmd"],"run_cmd":["system"]}` — the HIR walk visited the call, and attached nothing to it. A
sanity fixture (`std::fs::write` in the same harness) confirmed the pipeline itself works
(`inferred: ["Fs"]` correctly), so this is not a broken local setup. The sharper finding: the SAME binary
correctly discloses `"invisible": ["libc"]` for R59's own `libc::read` fixture — rust-deep's coverage-
envelope `invisible` mechanism is crate-name-keyed, and `libc::` has a crate name to hang the disclosure
off; a foreign item declared directly IN the local crate (bindgen's shape) has none, so the identical
mechanism that correctly saves the libc case has nothing to attach to here. This makes rust-deep — described
elsewhere in this file as "the sound gate" specifically for seams the syntactic scanner accepts — WORSE than
rust-scan on this exact seam: rust-scan's `decls.rs` discloses unconditionally by declared name, with no
crate-naming dependency to fall through. Filed as R60, SILENT, open; severity med — not because incidence is
high, but because a hole in the engine positioned as the backstop for exactly this class of miss is a
higher-priority gap than the same severity would be in the scanner it backstops.

**swift (R61, SILENT open) — the "—" was as false as the macro row's, and remains open.** Three
independently-idiomatic C-interop mechanisms, all live-reproduced against `.build/release/candor-swift`
0.33.1, all `"functions": []`, all passing `deny Exec`/`deny Fs` at exit 0 ("policy ✓") over code that
performs the effect:

- `import Darwin; system("rm -rf /tmp/x")` and the Fs analog `unlink(...)`. `Classifier.swift`'s `kappaFree`
  documents the omission of `system`/`fork`/`mkdir`/`rename`/`unlink` as a DELIBERATE choice ("collision-
  prone… under-report the rare direct-syscall program beats a wrong label on a common one") — but the
  comment reasons about precision, never about disclosure, and never connects to the fact that `Darwin`/
  `Glibc` are `PLATFORM_MODULES`: the exact set this file's own κ-batch comment says gets "no ledger naming
  and no Unknown" for an unmodeled member (documented for Foundation/Security, never extended in the
  author's mind to the C-interop boundary itself). CONTROL: the modeled `Process`/Foundation API stays
  correctly charged `Exec` in the same file — this is not "Exec is broken", it is specifically the raw-libc-
  via-Darwin path.
- `@_silgen_name("system") func c_system(_: UnsafePointer<CChar>) -> Int32` — Swift's compiler-level direct
  C-symbol-linkage declaration, which bypasses `import` (and therefore `kappaFree`'s module-qualified
  reasoning) entirely. Same silent result.
- `dlopen(path, RTLD_NOW)` + `dlsym(handle, "sym")` + `unsafeBitCast(sym, to: SomeCFn.self)` + calling it.
  Same silent result — arguably the highest-severity of the three, since it is dynamic loading of arbitrary
  code with no static callee at all.

Unlike rust (`native:extern fn`) or ts (`callback:`/`native:` on an unresolved call through an untyped
value), candor-swift's dispatch model has NO generic "unresolved call through an opaque/foreign value"
fallback for any of the three shapes — there is no vocabulary slot to route through, so the gap is not a
missing case in an existing mechanism, it is a missing mechanism. **NOT fixed here** — candor-spec doesn't
own candor-swift, and R56 was only fixable in-session because it happened to be a candor-swift PR the same
agent could land; R61 is filed the same way R57/R58 were, as a finding against a sibling repo. Filed as R61,
SILENT, open; severity med-high — raw Darwin/Glibc imports are the standard POSIX-level idiom for Swift on
Linux/server-side Swift, and `dlopen`/`dlsym` is the standard plugin-loading idiom, so (unlike R56's macro
finding, which has an idiomatic Foundation alternative candor-swift already models) there is no reason to
expect low real-world incidence — it is simply unmeasured.

**java and ts (CLOSED, both genuinely sound, both re-measured rather than assumed).** java: `ACC_NATIVE`
always discloses `Unknown` (`native:<name>`); an interface with zero implementing classes anywhere (the JNA
`Native.load(Lib.class, …)` shape, where the real implementation is a runtime dynamic proxy, never a
`.class` file) resolves through the ordinary zero-CHA-target dispatch path to `Unknown`
(`dispatch:Lib.deleteAllFiles`); a JDK-21/22 Panama downcall (`Linker.downcallHandle(...).invoke(...)`) is
caught by the REFLECTION path (`reflect:java.lang.foreign.SymbolLookup.find`,
`reflect:java.lang.invoke.MethodHandle.invoke`) rather than a dedicated rule, sound incidentally rather than
by design, but sound. Measured against `build/libs/candor-java-0.33.1-all.jar` on JDK 21. ts: a literal
`require('./addon.node')` with an untyped member call falls through the generic unresolved-call-on-untyped-
value path (`callback:addon.wipeDisk`); the SAME addon typed via a co-located `.d.ts` ambient declaration —
the realistic N-API shape (`better-sqlite3`, `sharp`, `bcrypt`) — is caught by PART 46's existing body-less-
declaration disclosure (`native:wipeDisk`), for free, since an N-API `.d.ts` is structurally identical to
axios's; `WebAssembly.instantiate(...)` + a call through `instance.exports`, and legacy
`process.binding(...)`, both fall through the same untyped-value callback path. Measured against `scan.mjs`
at candor-ts HEAD (`fbb9ea2`).

**agents.** No FFI concept exists to audit — its input is a fleet definition (agent roles, tool
permissions, delegation graphs), never source code with a foreign-function boundary, the same reasoning
that already exempts it from the macro/codegen row. "—" stands, correctly, unlike every other cell in this
row.

**GATES.** None of R59/R60/R61 has a gate — all three are open findings against sibling repos or an
accepted-but-wrong design comment; candor-spec doesn't own the fix. java's and ts's CLOSED verdicts have no
NEW gate either (they confirm existing, already-shipped behaviour — java's `ACC_NATIVE` handling and PART
46's body-less-declaration disclosure — rather than land a fix), so a cross-engine conformance PART
protecting them is deferred rather than landed in this pass: the bar this suite holds itself to is that "a
row is not evidence until it reddens a pre-fix binary (or a mutant, where a probed skip would skip rather
than redden)", and asserting CLOSED behaviour with a real mutation-based falsification (patching a scratch
clone to remove the disclosure, rebuilding, confirming red) is real work that deserves its own pass rather
than being rushed into this one.

### 2026-08-28 — R64's two closed shapes re-verified, and the four-way byte-equality blind spot has a row

**R64 close-out.** candor-ts `b4c3a22` closed two of R64's three shapes (a raw effect directly in a
decorator's own ARGUMENT, `@Decorate(fs.readFileSync(...))`; a closure nested in a NAMED factory's
argument DATA, `@Factory({ init: () => { fs.readFileSync(...) } })` — the real TypeORM
`@Column({ default: () => … })` idiom) the day after R57's own fix (`0a5d493`) shipped and was pinned by
PART 81. Per this file's own rule 12 ("a cited BACKLOG/SOUNDNESS entry is a snapshot, verify it against
HEAD"), the closure was NOT taken on trust: built candor-ts `9a8a5c7` (immediately pre-fix) and `b4c3a22`
in a throwaway clone under scratch, and ran all three R64 shapes plus a literal-decorator-argument control
and a pure-local-function-argument control against both binaries independently. Pre-fix: all five read
`functions: []`/`ok:true`/zero violations. Post-fix: the two claimed-fixed shapes read
`inferred:["Fs"]`/`paths:["/etc/hosts"]` on a minted `<decorator-arg>@…` unit and fail `deny Fs`
(AS-EFF-006); the third shape (an external body-less decorator reference) and both over-charge controls
are byte-for-byte UNCHANGED. Matches the commit's own claims exactly, independently reproduced rather than
quoted. SOUNDNESS.md's R64 row rewritten: shapes 1/2 `~~SILENT~~ CLOSED`, shape 3 still `SILENT (open)`,
and shape 3's rationale replaced — it used to read "low, unmeasured real-world incidence"; `b4c3a22`'s own
experiment measured a blanket-fix simulation against three real corpora with dependencies genuinely
installed and found it byte-identical to the shipped fix on two (a real NestJS+TypeORM app, TypeORM's own
513-file functional suite) but **+42 report rows on a base of 80 (+52%)** on a real Angular app — the
"would flood real framework code" argument is no longer folklore, it is a measured, framework-specific
number. PART 82 (conformance/run.sh) pins both fixed shapes, both over-charge controls, and shape 3 as a
DOCUMENTED-OPEN cell that asserts the current silent value rather than a wanted one — falsified against
`9a8a5c7` the same way, four cells reddening pre-fix, two controls and the open cell unmoved. Cross-engine:
argued fresh rather than assumed from R57's own ruling — none of rust/swift/java permits an arbitrary
RUNTIME expression inside a decorator/attribute argument (rust attribute-macro args are unevaluated token
streams; swift compiler-plugin macro args are compile-time AST; java annotation element values must be
compile-time constants, JLS 9.7.1), so the construct these two shapes depend on does not exist in any of
the three.

**The four-way byte-equality blind spot, verified before acting on it.** The claim handed down (every
byte-equality suite in the family scopes its rule to a name matching NOTHING ANYWHERE) was checked against
each file directly rather than trusted: this suite's PART 32/36 use `zzz_no_such_layer`/`zzz.nomatch`;
candor-java's `GateReportVerbTest.scanAndGateProduceByteEqualVerdictDocuments` uses `pure app.Nothing`
("scope matches nothing" per its own comment); candor-ts's `POLICIES` corpus (test.mjs ~8747) has
`scoped_none` (`pure ZzzNoSuchScope`) beside `scoped` (`deny Fs src.app.readIt`, and `readIt` genuinely
performs `Fs` — a real but EFFECTFUL match, not the missing quadrant); candor-swift's
`testGateJsonIsByteEqualToTheScanRoute` carries `pure ZzzNoSuchScope` only. All four confirmed by reading
the actual files, not by re-summarising the filing.

Built the missing quadrant fresh — a rule scoped to a REAL function that is pure on BOTH routes — against
throwaway-clone builds of all four engines at HEAD (candor-rust `caca530`, candor-java `fee92bd`,
candor-ts `b4c3a22`, candor-swift `328a67f`), not against whatever binary happened to be sitting in
`target/`/`.build/` (the R60 lesson: `cargo build --release` at candor-rust's OWN root builds the dylint
lint, not `candor-scan`/`candor-query` — its own Cargo.toml says so in a comment, `-p candor-scan
-p candor-query` is required). Fixture: `add_numbers`/`write_something` (rust), `app.Svc.addNumbers`/
`app.Svc.writeSomething` (java), `src.e.addNumbers`/`src.e.writeSomething` (ts), bare `addNumbers`/
`writeSomething` (swift) — a pure sibling and an effectful sibling in the same file, so the fixture cannot
be answered by an engine that finds no functions at all.

**It does not pass cleanly, in all four.** `deny Fs <pure-fn>`: the SCAN route (`ok:true`,
`violations:[]`, no `zeroMatch` key) and the REPORT route over that scan's own report (`ok:true`,
`violations:[]`, but `zeroMatch:["deny Fs <pure-fn>"]`) diverge in exactly one key, in every engine.
Mechanism, read from source rather than guessed: a report's `functions` array carries only
effectful/incomplete entries (§2.1's purity-by-absence design) — a pure function has NO entry there at
all. The scan route computes `zeroMatch` from the full in-memory analysed-function set, built before that
emission gate drops pure entries; the report route computes it from the persisted `functions` array alone,
where the same pure function simply does not appear, so the identical rule reads as unbound. `ok`,
`violations` and `analyzed.count` never move on either route — a FALSE DISCLOSURE (a rule that bound a
real function reported as binding nothing), never an under-report. This independent measurement matches
BACKLOG.md's own same-day finding (`add_numbers`/`write_something`, byte diff a single `zeroMatch` key)
almost exactly, arrived at before reading that entry's numbers, which is the useful kind of agreement.

PART 83 (conformance/run.sh) adds the quadrant, deliberately NOT resolving the underlying §3.1 question —
that ruling is Tom's, open in BACKLOG.md's "CURRENT QUEUE" item 1 (options A-D priced there). The row pins
the CURRENT MEASURED divergence (scan silent, report false-`zeroMatch`) rather than a wanted value, pairs
each defect cell with a control scoped to the sibling EFFECTFUL function (proving the divergence stays
confined to the pure-matched quadrant — both routes byte-equal, one `AS-EFF-006`, no `zeroMatch` on
either), and says explicitly in its own comment what to do when it goes red: if the REPORT route stops
falsely emitting `zeroMatch`, that is the ruling landing a fix, not a regression — rewrite the row's wanted
value and update this file, do not loosen the assertion to keep the suite green.

**A checker that could not fail, caught by its own mutation control.** The first draft of PART 83's python
checkers used single-quoted Python string literals for dict keys (`s.get('ok')`) inside a python source
that is ITSELF the body of a bash single-quoted string (`python3 -c '...'`). Bash single quotes cannot
nest — the embedded apostrophes silently close and reopen the outer quoted string, and because every
occurrence hugs a bare identifier with no surrounding whitespace, bash reassembles the pieces into ONE
argument with the quote CHARACTERS themselves stripped (`s.get('ok')` arrives at Python as the bare,
undefined name `s.get(ok)`). The PASSING path never touched this: `bad.append(...)` is only evaluated when
a check actually fires, so every real-measured-state cell printed a clean `OK` and the row read green.
Only a deliberate mutation control (feeding the checker a synthetic "divergence closed" document and a
synthetic "routes now differ" document) reached the buggy branches and turned up a Python `NameError`
instead of the intended `FAIL: ...` line — exactly the failure mode this suite's own `run.sh` preamble
warns about for its shell-level checkers ("a checker crash must not masquerade as an engine disagreement"),
reproduced here at the Python-literal level instead. Fixed by pulling every dict lookup into a plain
variable before building any message string, so no quote character ever appears inside an f-string/string
build — verified by re-running both mutation controls (now printing correct `FAIL:` lines) and the real
four-engine measurement (still printing correct `OK:` lines) against the corrected checkers before this
row was considered done. Not caught by `bash -n` (that only validates surrounding shell syntax, not that
python receives the source the author intended) or by the row's own success path — only by attacking it.

**GATES.** PART 82 and PART 83 are both new, falsified against pre-fix/pre-existing states as described
above. Neither introduces a new SKIP key for `skip_ratchet.py`: both spell an absent-engine SKIP in the
existing runner-absence form (`-> SKIP     (candor-X: not present on this runner — NOT asked)`, matching
PART 81's own wording) rather than the reference-led form the ratchet counts, and on this machine (ts and
swift both present) neither branch fires at all.

### 2026-08-29 — a full-family adversarial day: the peek scope-match cardinal sin (four-way) plus six more

Full detail and per-item evidence lives in SOUNDNESS.md's §8.1 round/batch index table (the seven rows
dated 2026-08-29); this entry is the index pointer the file's own convention asks for. Summary, in the
order the table carries them:

1. **The peek scope-match cardinal sin, four-way** (swift `7378f4f`, rust `27f4beb`, java `a034371`,
   ts `8584572`) — a peek finding's `<scope>` test ran only against the excluded declaration's own
   qualified name, never against an in-scope caller reaching it via dynamic dispatch, so a scoped `deny`
   rule silently missed effects an unscoped rule already caught. Closed with four genuinely different
   mechanisms sharing one property (SPEC §2/§6.2 ⟨0.34⟩), pinned by conformance PART 85 with the
   `dispatch-widened` fallback CONDITIONAL on rust's peek never unioning (so it never needs the class).
   PART 85 was falsified against all four engines' own pre-fix commits in throwaway worktrees before being
   trusted — the java falsification also surfaced an unrelated classpath-layout interaction (a nested
   `classes/` directory trips the OLD binary's separate, ancillary classpath bug), isolated by using a
   flat compiled-output layout so the row measures the scope-match fix alone.
2. **rust-deep**: closure/coroutine captures and `drop(x)` container walking were silently pure
   (`3e9848c`) — two independent gaps in the implicit-Drop model, fixed by recursing into upvar types and
   by routing the explicit-`drop` edge through the same walker the scope-exit case already uses.
3. **swift**: R33 deinit-glue only fired for the unannotated `let`/`var` binder shape (`10dc79e`) — the
   annotated and wildcard binder forms silently missed an effectful `deinit`, fixed by extracting one
   shared `applyDeinitGlue` function called from all three binder shapes.
4. **java records**: a component's effectful `equals`/`hashCode`/`toString` override ran unattributed
   (`3a84522`) — the JEP 384 `ObjectMethods` bootstrap's per-component contract-method reentry was never
   wired up. Falsified on 388 real third-party jars, byte-identical except one genuine, honestly-disclosed
   recovery.
5. **candor-agents**: `deny Unknown` compiled to nothing, and the compound `deny Net Unknown` silently
   dropped the `Net` denial too (`69e9e98`) — `guard.py`'s hand-rolled parser never inherited `policy.py`'s
   `Unknown` special case. First time this repo had been attacked; the rest of it (`drift`/`observe`/
   `scan`/`policy`) came back a verifiably clean negative.
6. **The consumer-refusal class** (candor `0d483a8`/`ac4a71b`) — three `integrations/` consumers each
   converted an engine's fail-closed refusal into a clean pass (the Stop hook, `candor-sarif`, and
   `fingerprint/`), defeating every scan-side completeness rung at once. The most consequential class found
   this session precisely because it sits downstream of everything else that was ever hardened.
7. **The instrument survey**: 13 of 13 standalone conformance checkers survived having their body replaced
   with `sys.exit(0)` (`90cee30`, partial fix) — `mutation-gate.sh` extracts checker bodies out of `run.sh`
   and a standalone `conformance/*.py` file is structurally invisible to it, including `check_honesty.py`
   (the family's one cardinal-sin detector) and `peek_route_equality_check.py`. Seven hardened, six filed,
   and a generator now owed for the fourth recurrence of the same four comparison-shape bypasses.

**The shared thread.** Every engine fix that succeeded reused an existing authority instead of hand-rolling
a second one (rust's peek fix reuses primary-scan facts; java's re-runs its own `runScan`; swift diffs
against its own finalized result; the rust-deep and swift-deinit fixes both collapse two divergent code
paths into one shared function) — the fixes that would have failed all shared the opposite shape. And three
separate "instruments that cannot fail" surfaced in overlapping investigations the same week
(`mutation-gate.sh`'s own blindness to standalone checkers, java's `mutation_probe.sh` going a quarter
blind silently, and this survey), each with the identical failure shape: the detector worked and the
aggregator lost it.
