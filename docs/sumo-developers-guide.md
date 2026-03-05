# SUMO for Software Engineers

> A practical guide to using the Suggested Upper Merged Ontology in production software systems.

**Audience**: Software engineers, architects, and technical leads evaluating or integrating SUMO.
**Reading time**: ~35 minutes.
**Prerequisites**: Familiarity with knowledge graphs (nodes + edges) and basic first-order logic (if X then Y).

**What this document covers**: What SUMO actually is, what's in the KIF files, what the toolchain can do, a phased adoption model from taxonomy to formal data model, and a complete workflow for extending SUMO with new terms.

---

## 1. What SUMO Is (and Is Not)

SUMO (Suggested Upper Merged Ontology) is a formal ontology — a machine-readable description of ~25,000 concepts and ~130 relations, with ~4,000 logical rules that define how those concepts relate. It is expressed in SUO-KIF (Knowledge Interchange Format), developed since 2001, and maintained at [ontologyportal.org](https://www.ontologyportal.org). It is licensed under GPL-2.0.

**SUMO is**:
- A class hierarchy where every concept has a formal position (e.g., `Human > Primate > Mammal > Animal > Organism > ... > Entity`)
- A set of typed relations with domain/range constraints (e.g., `agent` connects a `Process` to an `Agent`)
- A body of logical rules expressible in first-order logic, checkable by automated theorem provers
- The largest formally axiomatized public ontology in existence

**SUMO is not**:
- A database or storage system — it defines the *schema*, not the data
- A knowledge graph — but it provides the type system and relation vocabulary for building one
- An AI model — it does not learn or predict; it defines and constrains
- A lightweight taxonomy — it has 4,000+ logical rules that go far beyond parent-child relationships

**Why a software engineer should care**: If your system has a knowledge graph, entity types, or relationship types, you are maintaining an informal ontology. SUMO replaces your ad-hoc type system with a formal one that supports subsumption queries ("find all Vehicles" automatically includes Automobiles), schema validation (reject invalid relationships at write time), and automated reasoning (prove facts about your data).

---

## 2. What's in the KIF Files

### SUO-KIF Syntax in 60 Seconds

SUMO is written in SUO-KIF, a Lisp-like syntax where every statement is an S-expression:

```lisp
(subclass Human Primate)
```

This says "Human is a subclass of Primate." Statements can nest with logical connectives:

```lisp
(=>
   (and
      (subclass ?X ?Y)
      (instance ?Z ?X))
   (instance ?Z ?Y))
```

This says "if X is a subclass of Y, and Z is an instance of X, then Z is also an instance of Y." Variables start with `?`.

### Axiom Types in Merge.kif

The core file is `Merge.kif` (621 KB, ~18,800 lines). Every line starting with `(` is an axiom. Here are all the axiom types:

| Axiom Type | Count | What It Does |
|---|---|---|
| `(documentation ...)` | 1,240 | English description of a concept |
| `(instance ...)` | 1,022 | Declares that a thing is a member of a class |
| `(=> ...)` | 1,020 | Material implication — if-then rules |
| `(subclass ...)` | 802 | Class hierarchy (taxonomy) |
| `(domain ...)` | 714 | Type constraint on a relation's Nth argument |
| `(range ...)` | 102 | Type constraint on a function's return value |
| `(subrelation ...)` | 101 | Relation hierarchy (analogous to subclass for relations) |
| `(disjoint ...)` | 42 | Two classes share no instances |
| `(partition ...)` | 39 | A class is exactly divided into subclasses |
| `(termFormat ...)` | 37 | Display name in a human language |
| `(format ...)` | 27 | NLG template for presenting a relation in natural language |
| `(<=> ...)` | 20 | Biconditional (if and only if) |
| `(equal ...)` | 5 | Identity between two terms |

**What most implementations parse**: Only `subclass` and `documentation` — the taxonomy and English descriptions. This gives you a class hierarchy with subsumption checking. Everything else — domain/range constraints, logical rules, instance declarations, disjointness — is typically left on the table.

**What you're missing if you only parse `subclass`**: 714 type constraints on relations, 1,020 inference rules, 42 disjointness assertions, 101 relation hierarchy assertions. The taxonomy is valuable, but it is not a data model — it does not constrain relationships or enable reasoning.

### Axiom Type Reference

#### `(subclass Child Parent)` — 802 occurrences

Every instance of `Child` is also an instance of `Parent`.

```lisp
(subclass Human Primate)
(subclass Automobile Vehicle)
```

**What you can do with it**: Build a class hierarchy. Check subsumption ("is Automobile a kind of Vehicle?"). Expand queries ("find all Vehicles" includes Automobiles, Aircraft, etc.). Compute ontological distance between concepts.

#### `(instance Thing Class)` — 1,022 occurrences

`Thing` is a member of `Class`. Unlike `subclass` (which relates two classes), `instance` relates an individual to a class.

```lisp
(instance part BinaryPredicate)
(instance agent CaseRole)
```

**What you can do with it**: Discover what kind of thing something is. Critically, this is how SUMO declares its ~130 BinaryPredicates. Without parsing `instance`, you cannot programmatically discover the predicates SUMO defines — you must hardcode them.

#### `(domain Relation Position Class)` — 714 occurrences

The Nth argument of `Relation` must be an instance of `Class`.

```lisp
(domain agent 1 Process)     ; arg 1 of 'agent' must be a Process
(domain agent 2 Agent)       ; arg 2 of 'agent' must be an Agent
(domain part 1 Object)       ; arg 1 of 'part' must be an Object
(domain part 2 Object)       ; arg 2 of 'part' must be an Object
```

**What you can do with it**: Validate relationships at write time. If someone creates an `agent` edge where the source is a `Document` (not a `Process`), reject it. This is schema enforcement for knowledge graphs — the single highest-value capability beyond basic taxonomy.

#### `(range Function Class)` — 102 occurrences

The return value of `Function` must be an instance of `Class`.

```lisp
(range MeasureFn Quantity)
(range BeginFn TimePoint)
```

**What you can do with it**: Validate function outputs in computed attributes.

#### `(=> Antecedent Consequent)` — 1,020 occurrences

If the antecedent is true, the consequent must be true. These are the rules of the ontology.

```lisp
;; Subsumption inheritance:
(=>
   (and
      (subclass ?X ?Y)
      (instance ?Z ?X))
   (instance ?Z ?Y))

;; Disjointness:
(=>
   (disjoint ?CLASS1 ?CLASS2)
   (not
      (exists (?INST)
         (and
            (instance ?INST ?CLASS1)
            (instance ?INST ?CLASS2)))))
```

**What you can do with it**: Automated theorem proving. A prover like Vampire takes these rules and checks whether new statements are consistent with them, or derives new facts from existing ones.

**What you need**: These rules are only accessible when SUMO is loaded into a theorem prover via TPTP conversion (see Section 4). They are not available through simple KIF parsing.

#### `(subrelation Child Parent)` — 101 occurrences

Every tuple in `Child` is also a tuple in `Parent`. If `mother` is a subrelation of `parent`, then every mother-child pair is also a parent-child pair.

```lisp
(subrelation mother parent)
(subrelation geographicSubregion part)
(subrelation component part)
```

**What you can do with it**: Relation inheritance. Query for all `parent` relationships and automatically get `mother` and `father`. Domain/range constraints propagate downward.

#### `(disjoint Class1 Class2)` — 42 occurrences

`Class1` and `Class2` share no instances.

```lisp
(disjoint Physical Abstract)
(disjoint Object Process)
```

**What you can do with it**: Consistency checking. If your knowledge graph types something as both `Physical` and `Abstract`, it is contradictory.

#### `(partition Parent Child1 Child2 ...)` — 39 occurrences

`Parent` is exhaustively divided into the listed children, which are mutually disjoint.

```lisp
(partition Entity Physical Abstract)
(partition Physical Object Process)
```

**What you can do with it**: Exhaustive classification. Everything is either Physical or Abstract, with no overlap and no third option. Stronger than both `subclass` and `disjoint` individually.

---

## 3. Domain KIF Files

Beyond `Merge.kif`, SUMO includes 67 domain-specific KIF files totaling ~17 MB. They fall into four categories:

**Upper ontology** (always load these):

| File | Size | Purpose |
|---|---|---|
| `Merge.kif` | 621 KB | Upper ontology — all core concepts and relations |
| `Mid-level-ontology.kif` | 1.1 MB | Bridge between upper and domain ontologies (everyday concepts like `Meeting`, `Document`, `Building`) |

**Domain ontologies** (load based on your application):

| File | Size | Domain |
|---|---|---|
| `Military.kif` + `MilitaryProcesses.kif` | 169 KB | Military operations, organizations, doctrine |
| `Medicine.kif` | 257 KB | Medical equipment, procedures, anatomy |
| `Economy.kif` | 239 KB | GDP, labor, industries, economic indicators |
| `Government.kif` | 219 KB | Government types, political structures |
| `FinancialOntology.kif` | 147 KB | Financial instruments, transactions, markets |
| `Geography.kif` | 313 KB | Regions, landforms, bodies of water |
| `Transportation.kif` | 155 KB | Railways, airports, roads, shipping |
| `Cars.kif` | 174 KB | Automobile makes, models, specifications |
| `engineering.kif` | 64 KB | Physical dimensions, units, engineering concepts |

**Instance data** (named entities):

| File | Size | Content |
|---|---|---|
| `WorldAirports.kif` | 1.9 MB | ~10,000 named airports |
| `mondial.kif` | 2.9 MB | CIA World Factbook countries/regions |
| `Languages.kif` | 960 KB | ~7,000 human languages |

**Formatting/NLG** (presentation, not knowledge):

| File | Size | Content |
|---|---|---|
| `domainEnglishFormat.kif` | 3.8 MB | English templates for all relations |

**Recommendation**: Start with `Merge.kif` only. Add `Mid-level-ontology.kif` when you need everyday concepts. Add domain files as your application requires them. Do not load everything — 17 MB of concepts includes a lot you will never use.

---

## 4. The SigmaKEE Toolchain

SigmaKEE is the open-source engineering environment for SUMO. It converts KIF into formats that other tools can consume.

```
KIF Source Files (Merge.kif + domain files)
         │
    SigmaKEE (Java)
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
KButilities -r            SUMOKBtoTPTPKB / SUMOKBtoTFAKB
    │                         │
    ▼                         ▼
triples.txt               SUMO.fof / SUMO.tff
(pipe-delimited)          (TPTP first-order logic)
    │                         │
    ▼                         ▼
Neo4j / Graph DB          Vampire Theorem Prover
```

### KButilities -r: Producing triples.txt

Flattens every simple assertion into a pipe-delimited triple file:

```
Physical|subclass|Entity
Human|subclass|Primate
agent|domain|1|Process
agent|domain|2|Agent
agent|instance|CaseRole
```

**What is lost**: All quantified axioms (`=>`), biconditionals (`<=>`), nested expressions. The 1,020 implication rules and 20 biconditional definitions are entirely absent. You get the skeleton; you lose the reasoning power.

**Why use a lossy format?** triples.txt and TPTP serve different purposes:

- **triples.txt is for navigation** — browsing the hierarchy, running graph queries, visualizing concept relationships. You do not need `=>` rules to answer "what are the subclasses of Vehicle?" or "what is the domain of the `agent` predicate?" Those are structural assertions that triples.txt preserves.
- **TPTP is for reasoning** — proving conjectures, checking consistency, deriving new facts. You need the full logical content for that.

Use triples.txt when you need to explore and query the ontology structure (e.g., load into Neo4j for Cypher traversals, build a browseable concept explorer, populate autocomplete for entity typing). Use TPTP when you need to prove things about it.

### SUMOKBtoTPTPKB: Converting to First-Order Logic

Converts all SUMO KIF into TPTP (Thousands of Problems for Theorem Provers) format. This preserves the full logical content.

A KIF axiom:

```lisp
(=>
   (and (subclass ?X ?Y) (instance ?Z ?X))
   (instance ?Z ?Y))
```

Becomes TPTP:

```
fof(ax_subclass_instance, axiom,
    ! [X, Y, Z] :
      ((s__subclass(X, Y) & s__instance(Z, X))
       => s__instance(Z, Y))).
```

### Vampire: Automated Theorem Proving

Given TPTP axioms and a conjecture, Vampire either proves the conjecture (refutation found) or times out.

```bash
vampire --mode casc -t 60 SUMO.fof
```

**Example conjecture**: "Does SUMO entail that all Automobiles are Vehicles?"

```
fof(my_conjecture, conjecture,
    ! [X] : (s__instance(X, s__Automobile) => s__instance(X, s__Vehicle))).
```

If Vampire finds a refutation with `negated_conjecture`, the answer is yes.

**Practical applications in software**: Vampire is a batch tool — each run takes seconds to minutes depending on conjecture complexity and SUMO axiom set size. Common integration patterns include: CI pipelines that run domain-specific conjectures on every push (catch ontology regressions), batch jobs that periodically check knowledge graph consistency against SUMO constraints, and design-time validation of data models. Real-time theorem proving at query time is not feasible for an ontology of SUMO's size.

**What exists in ontologyportal today**: The [sigmakee](https://github.com/ontologyportal/sigmakee) repo includes `SUMOKBtoTPTPKB` and `SUMOKBtoTFAKB` for TPTP conversion. Vampire is an external dependency ([vprover/vampire](https://github.com/vprover/vampire)). SigmaKEE's web interface can submit conjectures interactively. CI integration (running Vampire automatically on push) is an application-level pattern you build yourself.

---

## 5. SUMO's BinaryPredicates — The Relationship Vocabulary

SUMO defines ~130 BinaryPredicates in Merge.kif. Each has formal domain/range constraints. These are the building blocks for knowledge graph edges. The most important groups:

### Structural (Part-Whole)

| Predicate | Domain → Range | KIF Source | Meaning |
|---|---|---|---|
| `part` | Object → Object | Merge.kif | X is a part of Y (transitive, reflexive, antisymmetric) |
| `component` | CorpuscularObject → CorpuscularObject | Merge.kif | Functional part (subrelation of `part`) |
| `contains` | SelfConnectedObject → Object | Merge.kif | Physical containment |
| `member` | SelfConnectedObject → Collection | Merge.kif | Membership in a collection |

### Causal (Agency)

| Predicate | Domain → Range | KIF Source | Meaning |
|---|---|---|---|
| `agent` | Process → Agent | Merge.kif | The deliberate performer of a process |
| `patient` | Process → Entity | Merge.kif | The entity affected by a process |
| `instrument` | Process → Object | Merge.kif | The tool used |
| `result` | Process → Entity | Merge.kif | The entity produced |
| `causes` | Process → Process | Merge.kif | Direct causation |
| `precondition` | Process → Process | Merge.kif | X must happen before Y |

### Spatial

| Predicate | Domain → Range | KIF Source | Meaning |
|---|---|---|---|
| `located` | Physical → Object | Merge.kif | General location |
| `geographicSubregion` | GeographicArea → GeographicArea | Merge.kif | Sub-region (subrelation of `part`) |
| `connected` | Object → Object | Merge.kif | Shares a boundary |

### Temporal

| Predicate | Domain → Range | KIF Source | Meaning |
|---|---|---|---|
| `time` | Physical → TimePosition | Merge.kif | When something exists or occurs |
| `before` | TimePoint → TimePoint | Merge.kif | Strict temporal ordering |
| `during` | TimeInterval → TimeInterval | Merge.kif | Interval containment |
| `duration` | Process → TimeDuration | Merge.kif | How long a process takes |

### Information

| Predicate | Domain → Range | KIF Source | Meaning |
|---|---|---|---|
| `refers` | ContentBearingObject → Entity | Merge.kif | Content references an entity |
| `represents` | ContentBearingObject → Entity | Merge.kif | Content depicts an entity |
| `authors` | CognitiveAgent → ContentBearingObject | Merge.kif | Agent created the content |
| `knows` | CognitiveAgent → Proposition | Merge.kif | Agent knows a fact |

### Logical/Modal

| Predicate | Domain → Range | KIF Source | Meaning |
|---|---|---|---|
| `entails` | Proposition → Proposition | Merge.kif | If X is true, Y must be true |
| `increasesLikelihood` | Formula → Formula | Merge.kif | X makes Y more probable |
| `decreasesLikelihood` | Formula → Formula | Merge.kif | X makes Y less probable |
| `holdsObligation` | Formula → CognitiveAgent | Merge.kif | Agent is obligated to make formula true |

---

## 6. Phased Adoption — From Taxonomy to Data Model

SUMO adoption does not need to be all-or-nothing. Each phase is independently valuable and builds on the previous one.

### Phase 1: Type Classification

**Parse**: `subclass` (802 axioms) + `documentation` (1,240 axioms).

**What you get**: A class hierarchy with ~25,000 concepts. Subsumption checking ("is Automobile a Vehicle?"), query expansion ("find all Vehicles" includes subtypes), ontological distance between concepts.

**What you don't get**: Relationship validation, disjointness enforcement, automated reasoning.

**Effort**: Small. Parse two axiom types from one file. Build an in-memory tree. Ship a JSON cache in your container image.

**License**: CLEAR. Merge.kif is IEEE-licensed (permissive, commercial OK). Credit IEEE in package metadata. See Section 9.

**Honest assessment**: You have a type system with no type checker. Genuinely valuable for entity classification and query expansion, but not a data model.

### Phase 2: Schema Validation

**Parse additionally**: `domain` (714), `range` (102), `instance` (1,022), `subrelation` (101), `disjoint` (42).

**What you get**: Write-time schema enforcement (reject invalid edges), automatic predicate discovery, relation inheritance, disjointness checking.

**Effort**: Medium. Extend your KIF parser to extract 5 more axiom types. Build a validation function that checks relationship arguments against domain/range constraints.

**License**: CLEAR for Merge.kif (IEEE). Domain KIF files (Military.kif, MILO) are GPL-2.0 — safe for SaaS servers, do not bake into externally distributed artifacts. See Section 9.

**Honest assessment**: You now have a type system with a type checker. Every edge in your knowledge graph is validated against formal constraints. This is the highest-value step relative to effort.

### Phase 3: Theorem Proving

**Requires**: SigmaKEE TPTP conversion + Vampire theorem prover. Access to the 1,020 `=>` rules and 20 `<=>` definitions.

**What you get**: Consistency checking, automated inference, conjecture validation.

**Effort**: High. Deploy SigmaKEE (Java), manage TPTP conversion, write conjectures in TPTP syntax, interpret Vampire output.

**License**: Vampire is BSD-3 (no concerns). SigmaKEE is GPL-3.0 — safe in CI and as internal SaaS infrastructure, but distributing it in on-prem images triggers copyleft. This is the main licensing decision point. Clean-room TPTP converter is the escape hatch (~2-4 weeks). See Section 9.

**Honest assessment**: Powerful but batch-oriented. Best suited for CI pipelines and offline validation, not real-time queries.

### Phase 4: SUMO as Edge Vocabulary (application-level pattern)

> **Note**: Phases 1-3 use tools that exist in the [ontologyportal](https://github.com/ontologyportal) repositories today (SigmaKEE, KButilities, SUMOKBtoTPTPKB, Vampire). Phase 4 is an application-level design pattern — it describes how *your* software would use SUMO predicates as edge types. There is no ontologyportal tool that does this for you; you build the mapping layer in your application.

**What you do**: Replace ad-hoc edge types in your knowledge graph with SUMO BinaryPredicates. Use `contains` instead of "CONTAINS", `causes` instead of "TRIGGERED", `agent` instead of "EXECUTED_BY".

**What you get**: A shared edge vocabulary grounded in formal semantics. If two systems both use `agent` for "who performed this process," they agree on what that means because SUMO defines `(domain agent 1 Process)` and `(domain agent 2 Agent)`. Automatic NLG is available via `domainEnglishFormat.kif` templates.

**How you would implement it**: Build a mapping table from your application's edge types to SUMO BinaryPredicates. Validate each mapping against SUMO's `(domain ...)` and `(range ...)` constraints. For edges that SUMO does not cover, either compose from existing predicates (see Section 7, Discovery Step 2) or extend SUMO with a new predicate following the full axiomatization workflow.

**License**: CLEAR. Application code is ours. NLG templates from `domainEnglishFormat.kif` are LGPL-2.1 (weak copyleft — linking is fine, modifications to the LGPL file itself must be shared).

### Phase 5: SUMO as Universal Data Model (organizational commitment)

> **Note**: Phase 5 is an architectural vision, not a tool. No ontologyportal tool implements this. It describes what happens when an entire organization commits to SUMO as its shared schema.

**What it means**: Every entity has a SUMO type. Every relationship uses a SUMO predicate. Every attribute uses a SUMO measurement relation. Any query in one system can be answered by any other because they share a formal schema.

**Why it does not exist as a tool**: This is a property of how you build your systems, not a feature of SUMO itself. SUMO provides the vocabulary and constraints; your organization provides the discipline to use them consistently. The closest existing tool is SigmaKEE's KB Browse, which lets you navigate the shared vocabulary, but the actual integration is application code.

**License**: CLEAR. All application code at this level is ours.

**Honest assessment**: Multi-quarter effort requiring organizational commitment. But each preceding phase is independently valuable — you do not need Phase 5 to benefit from Phases 1-3.

---

## 7. How to Extend SUMO with New Terms

When your application encounters a concept that SUMO does not cover, follow this three-phase workflow. Most proposed terms are unnecessary — Discovery exists to prevent term proliferation.

Reference flowcharts:
- [Phase 1: Discovery](data/sumo-axiomatization-phase1-discovery.png)
- [Phase 2: Classification](data/sumo-axiomatization-phase2-classification.png)
- [Phase 3: Implementation](data/sumo-axiomatization-phase3-implementation.png)

### Phase 1: Discovery — "Do I need a new term?"

**Step 0: Scope the problem.** Write down in plain language: (a) the real-world problem that needs formal justification, and (b) 1-2 example inferences a theorem prover should derive. These inferences are your acceptance test. If you cannot name a concrete inference the new term enables, you do not need it.

**Step 1: Search before you build.** Check whether SUMO already has your concept:
- Browse [SigmaKEE KB](https://sigma.ontologyportal.org:8443/sigma/Browse.jsp) — search by name
- `grep -r "YourTerm" *.kif` across Merge.kif, Mid-level-ontology.kif, and relevant domain files

Three outcomes:
- **Exact match** → use the existing term. No new term needed.
- **Similar term** → define as subclass of the similar term, or plan connecting axioms.
- **No match** → proceed to Step 2.

**Step 2: Justify.** Ask: "Can existing terms + axioms express this without a new name?" SUMO has 25,000 concepts and 130 predicates — many gaps are composable. For example, "a record of a process" might be expressible as `(and (instance ?T ContentBearingObject) (represents ?T ?P) (instance ?P Process))` without inventing a new class.

If composition works, use it. If not, verify the new term enables your Step 0 inferences. If it does, proceed.

### Phase 2: Classification — "What kind of term?"

**Step 3: What kind of thing is it?**

| If it... | It is a... |
|---|---|
| Describes a quality | ATTRIBUTE (→ InternalAttribute or RelationalAttribute) |
| Connects two+ things | RELATION (→ Predicate if yes/no, Function if value) |
| Other things are instances of it | CLASS (`subclass X Parent`) |
| It is one specific thing | INSTANCE (`instance X SomeClass`) |

**Step 4: Find its parent.** For relations: how many arguments? (BinaryPredicate, TernaryPredicate, etc.) For classes: Physical (Object if it persists, Process if it happens over time) or Abstract?

### Phase 3: Implementation — "Write, validate, prove"

**Step 5: Write the definition** in SUO-KIF. Every new term needs:
- `(subclass ...)` or `(instance ...)` placing it in the hierarchy
- `(documentation ... EnglishLanguage "...")`
- `(domain ...)` / `(range ...)` for predicates
- At least one `(=> ...)` rule or `(instance ...)` that uses the new class

**Step 5b: Check WordNet mapping.** If the term corresponds to a natural-language word, link it to the WordNet synset.

**Step 6: Run diagnostics.** Before proving:
- `KIFChecker` — catches syntax errors, undefined terms, arity mismatches
- Consistency check — load alongside full SUMO, check for warnings
- SUMOtoKIF syntax normalization

**Step 7: Prove it.** Create a `.tptp` test file with your axioms and the Step 0 inferences as conjectures. Run Vampire:

```bash
vampire --mode casc -t 10 test.tptp
```

| Result | Meaning | Action |
|---|---|---|
| Refutation + negated_conjecture | Conjecture proven | Proceed |
| Counter-example | Axioms insufficient or contradictory | Simplify axioms |
| Timeout | Search space too large | Increase timeout or simplify |

**Step 8: Readiness checklist.**

- [ ] Documentation string present
- [ ] Parent class makes sense
- [ ] Domain/range for all relations
- [ ] At least one instance or existing axiom
- [ ] No variable typos (`?Y` vs `Y`)
- [ ] Prover finds at least one inference
- [ ] WordNet mapping in place (or noted as N/A)
- [ ] KIFChecker passes clean

---

## 8. Quick Start

### Parse the hierarchy (Python pseudocode)

```python
import re
from pathlib import Path

SUBCLASS = re.compile(r"^\(subclass\s+(\S+)\s+(\S+)\)")

hierarchy = {}  # child -> parent
for line in Path("Merge.kif").read_text().splitlines():
    m = SUBCLASS.match(line)
    if m:
        child, parent = m.group(1), m.group(2)
        hierarchy[child] = parent

def is_subclass(child: str, ancestor: str) -> bool:
    current = child
    while current in hierarchy:
        if current == ancestor:
            return True
        current = hierarchy[current]
    return current == ancestor

is_subclass("Automobile", "Vehicle")  # True
```

### Load into a graph database

SigmaKEE's `KButilities -r` produces `triples.txt` — a pipe-delimited flat file of structural assertions. This is the existing ontologyportal tool for exporting SUMO to a navigable format.

```bash
# Existing SigmaKEE tool (requires Java + SigmaKEE installation)
java -Xmx10g -Xss1m -cp "/path/to/sigmakee/*" com.articulate.sigma.KButilities -r
```

Loading `triples.txt` into a specific graph database (Neo4j, Amazon Neptune, etc.) requires application code you write yourself — there is no ontologyportal tool for this. SigmaKEE does include its own Neo4j integration via `SUMOtoNeo.py` (Adam Pease's reference loader in `sigmakee/SUMOtoNeo.py`), but it loads from KIF directly rather than from triples.txt. Check the sigmakee repo for the latest approach.

### Validate an edge (application code you build)

There is no ontologyportal tool that validates knowledge graph edges against SUMO constraints at runtime. You build this in your application by parsing `(domain ...)` and `(range ...)` axioms from KIF and checking them against your entity types. Here is the pattern:

```python
def validate_edge(predicate: str, source_type: str, target_type: str) -> bool:
    """Check if source_type satisfies domain and target_type satisfies range."""
    domain_constraint = domains.get((predicate, 1))
    range_constraint = domains.get((predicate, 2))
    if domain_constraint and not is_subclass(source_type, domain_constraint):
        return False
    if range_constraint and not is_subclass(target_type, range_constraint):
        return False
    return True

validate_edge("agent", "Investigating", "Human")  # True: Process -> Agent
validate_edge("agent", "Document", "Human")        # False: Document is not a Process
```

---

## 9. Licensing and Adoption Strategy

The ontologyportal ecosystem has a mixed licensing landscape. Some components are permissively licensed and safe for any use. Others carry GPL copyleft that constrains distribution. This section maps each component to the adoption phases and marks exactly where we cross a licensing boundary — with options to adopt cleanly, clean-room reimplement, or push through and deal with consequences.

### Component License Map

| Component | License | Copyleft | Source File / Repo |
|-----------|---------|----------|--------------------|
| **Merge.kif** (core SUMO) | IEEE custom | **No** | `libs/sumo/Merge.kif` lines 8-40 |
| **Domain .kif files** (MILO, Military, etc.) | GPL-2.0 | **Yes** | Headers in each domain .kif file |
| **SigmaKEE** (Java toolchain) | GPL-3.0 | **Yes** | `ontologyportal/sigmakee` |
| **Vampire** (theorem prover) | BSD-3-Clause | **No** | `vprover/vampire` |
| **SUMOjEdit, SigmaUtils** | GPL-3.0 | **Yes** | `ontologyportal/SUMOjEdit`, `ontologyportal/SigmaUtils` |
| **TPTP-ANTLR** | BSD-3-Clause | **No** | `ontologyportal/TPTP-ANTLR` |
| **Format files** (english_format.kif, etc.) | LGPL-2.1 | **Weak** | Headers in format .kif files |

**Critical correction**: Existing docs (ADR-145, sumo-formal-ontology-layer.md) state "SUMO is GPL-2.0 licensed." This is wrong. `Merge.kif` — the core upper ontology and the only file we parse in Phases 1-2 — carries an IEEE custom license that is perpetual, royalty-free, allows commercial use and derivative works, and requires only that IEEE is credited as source and copyright holder. GPL-2.0 applies to the **domain ontology** KIF files (Military.kif, Mid-level-ontology.kif, etc.), not to the core.

### The IEEE License (Merge.kif)

Reproduced from `Merge.kif` lines 8-40:

> Copyright (c) 2004 by the Institute of Electrical and Electronics Engineers, Inc.
>
> The IEEE hereby grants Licensee a perpetual, non-exclusive, royalty-free, world-wide right and license to copy, publish and distribute the Document in any way, and to prepare derivative works that are based on or incorporate all or part of the Document provided that the IEEE is appropriately acknowledged as the source and copyright owner in each and every use.

This means: use it, sell it, modify it, ship it — just credit IEEE.

### Phase-by-Phase License Boundaries

#### Phase 1 — Type Classification: CLEAR

| What we use | License | Distributed? | Verdict |
|-------------|---------|-------------|---------|
| Merge.kif | IEEE | JSON cache in `bz-sumo` wheel (internal CodeArtifact) | No copyleft. Credit IEEE. |
| `registry.py` | Bravo Zero original | In `bz-sumo` wheel | We own this. |

No line crossed. Add IEEE attribution to `bz-sumo` package metadata and we are fully compliant.

#### Phase 2 — Schema Validation: CLEAR (with caveat)

| What we use | License | Distributed? | Verdict |
|-------------|---------|-------------|---------|
| Merge.kif (domain/range/instance) | IEEE | Extended JSON cache | No copyleft. |
| Domain .kif files (Military, MILO) | GPL-2.0 | Loaded at runtime | See below. |

**The caveat**: If domain KIF files are loaded and their data is baked into the `bz-sumo` JSON cache, that cache becomes a GPL-2.0 derivative work. Distribution of that cache triggers GPL obligations (source availability, copyleft to the whole distribution).

**Why this is probably fine**: GPL restricts *distribution*, not use. Running GPL-derived code on our own servers (SaaS) is not distribution. The GPL (unlike AGPL) has no network-use provision. As long as we are SaaS-only, we can use domain KIF files freely on our servers without triggering copyleft.

**When the line gets crossed**: If we ever distribute Docker images, on-prem packages, or the `bz-sumo` wheel to external parties and that artifact contains data derived from GPL domain ontologies.

| Option | Description |
|--------|-------------|
| **Adopt (SaaS)** | Use domain KIF files freely on our servers. No distribution = no GPL trigger. |
| **Clean room** | Keep `bz-sumo` cache derived from Merge.kif only (IEEE). Load domain files at runtime from raw KIF, never bake into distributable artifacts. |
| **Blow through** | Bake domain data into distributed artifacts. Accept GPL-2.0 for that distribution channel. Manageable — GPL-2.0 requires source availability for the derivative work, not for your entire product. |

#### Phase 3 — Theorem Proving: MAIN RISK ZONE

**Phase 3a — CI pipeline (current plan): CLEAR**

SigmaKEE (GPL-3.0) runs in GitHub Actions containers. Vampire (BSD-3) proves conjectures. None of this is distributed to end users. No line crossed.

**Phase 3b — SigmaKEE as K8s microservice (future): THE LINE**

| Scenario | GPL-3.0 triggered? | Action |
|----------|-------------------|--------|
| SigmaKEE deployed as internal SaaS infrastructure | **No** — GPL-3.0 has no network-use clause | Adopt. Deploy freely. |
| Docker images containing SigmaKEE distributed to customers (on-prem) | **Yes** — this is distribution of a GPL-3.0 work | See options below. |
| SigmaKEE code linked/embedded into Bravo Zero services that are distributed | **Yes** — combined work must be GPL-3.0 | See options below. |

**Options when on-prem distribution forces the line:**

| Option | Description | Effort | Risk |
|--------|-------------|--------|------|
| **Adopt for SaaS only** | Never distribute SigmaKEE. Keep it as internal infrastructure. | Zero | Limits business model to SaaS. |
| **Clean room the TPTP converter** | Build a Bravo Zero `kif-to-tptp` tool that replaces `SUMOKBtoTPTPKB`. The conversion is a deterministic syntax transformation. Vampire (BSD-3) needs no clean room. | 2-4 weeks | Moderate — must handle SUMO naming conventions, sort declarations, quantifier translation. |
| **Negotiate a commercial license** | Contact Adam Pease / Articulate Software to license SigmaKEE under non-GPL terms. SigmaKEE is primarily a one-maintainer project. | Unknown | Depends on willingness of copyright holder. |
| **Blow through** | Ship SigmaKEE in on-prem images. The entire image becomes GPL-3.0. Provide source on request. If the company succeeds, resolve retroactively via relicensing or commercial agreement. | Zero now, nonzero later | Legal exposure if a competitor or troll requests source. Manageable if the company has revenue. |

**Clean room candidates (if we need to replace SigmaKEE components):**

| Component | What it does | Clean room effort |
|-----------|-------------|-------------------|
| `SUMOKBtoTPTPKB` | KIF → TPTP FOF conversion | 2-4 weeks. The main dependency. |
| `SUMOKBtoTFAKB` | KIF → TPTP TFF (typed) conversion | Shared with above. |
| `KButilities -r` | KIF → pipe-delimited triples | 1-2 days. Trivial flattening of S-expressions. |
| `KIFChecker` | KIF syntax validation | 3-5 days. Paren matching, term resolution, arity checks. |
| `neo4j_loader.py` | Triples → Neo4j | Already done. Bravo Zero owns this code. |

#### Phase 4-5 — Edge Vocabulary / Universal Data Model: CLEAR

Application-level design patterns using Bravo Zero's own code. No ontologyportal code involved. No line crossed.

### Decision Summary

```
Phase 1  ───── IEEE ──────────────────────────────── CLEAR
Phase 2  ───── IEEE + GPL(domain) ────────────────── CLEAR for SaaS │ YELLOW for distribution
Phase 3a ───── GPL-3.0 in CI ─────────────────────── CLEAR (not distributed)
Phase 3b ───── GPL-3.0 as service ────────────────── CLEAR for SaaS │ RED for on-prem
Phase 4-5 ──── Bravo Zero code ───────────────────── CLEAR

The line: distributing GPL-licensed components or their derivatives to external parties.
SaaS deployment is not distribution under GPL-2.0 or GPL-3.0.
```

### Practical Guidance for Engineers

1. **Merge.kif is safe**. Parse it, cache it, ship the cache. Credit IEEE in package metadata.
2. **Domain KIF files are GPL**. Use them on our servers freely. Do not bake their data into artifacts that leave the building.
3. **SigmaKEE is GPL-3.0**. Run it in CI and as internal infrastructure. Do not embed it in distributed software without a clean-room replacement or commercial license.
4. **Vampire is BSD-3**. Use it anywhere, any way.
5. **If you are unsure whether something counts as "distribution"**: if a customer receives a copy of the software (Docker image, package, binary), it is distribution. If they access it over a network (SaaS API), it is not.

---

## Glossary

| Term | Definition |
|---|---|
| **SUO-KIF** | Standard Upper Ontology — Knowledge Interchange Format. The language SUMO is written in. |
| **TPTP** | Thousands of Problems for Theorem Provers. Standard exchange format for theorem provers. |
| **Vampire** | An automated theorem prover for first-order logic. |
| **SigmaKEE** | Sigma Knowledge Engineering Environment. The Java toolchain for SUMO. |
| **BinaryPredicate** | A SUMO relation with exactly two arguments. The building blocks for knowledge graph edges. |
| **Subsumption** | The subclass relationship. "A subsumes B" means every instance of B is also an instance of A. |
| **Merge.kif** | The core SUMO upper ontology file. |
| **MILO** | Mid-Level Ontology (`Mid-level-ontology.kif`). Bridges upper and domain ontologies. |
| **triples.txt** | Pipe-delimited flat file produced by SigmaKEE. Lossy — drops all logical rules. |
| **Ontological distance** | Number of hierarchy hops between two concepts via their common ancestor. |

---

*SUMO for Software Engineers v1.1.0*
