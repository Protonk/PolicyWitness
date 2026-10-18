#!/usr/bin/env python3
"""Build this frozen triage record; does not modify the document or its machinery."""
import collections
import functools
import hashlib
import json
from pathlib import Path
import subprocess

BASE = '5f878fe0603b039ef1edf3119d448b65534e2e18'
OUT = Path('records/worker-language-triage')
INPUT = Path('records/worker-language-sweep/inventory.json')
inventory = json.loads(INPUT.read_text())
entries = {e['id']: e for e in inventory['entries']}


@functools.lru_cache(None)
def source(path, revision=BASE):
    return subprocess.check_output(['git', 'show', f'{revision}:{path}'], text=True)


def ref(path, quote, revision=BASE):
    text = source(path, revision)
    offset = text.index(quote)
    return dict(path=path, revision=revision,
                start_line=text[:offset].count('\n') + 1,
                end_line=text[:offset + len(quote)].count('\n') + 1, quote=quote)


def worker(quote):
    return ref('docs/WORKER.md', quote)


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


origins = []


def origin(ident, title, finding, refs, status='documented_basis'):
    origins.append(dict(id=ident, title=title, status=status, finding=finding, references=refs))


origin('O01', 'Evidence-basis annotations',
       'The plan explicitly requires per-resource observed/source-only/unknown scope. The generated qualifiers entered with the pass-2 graph in 83f61f3. They record how a claim is supported, rather than documenting a particular reader error. This establishes documentary provenance and a current purpose; it does not establish private author intent.', [
    ref('docs/WORKER-INST-DOC-PLAN.md', 'Mark source-only conclusions as such.'),
    ref('docs/WORKER-INST-DOC-PLAN.md', '| Sandbox-gated | Observed (cite the case), source-only, or unknown |'),
    ref('docs/WORKER-INST-DOC-PLAN.md', 'No ordinary file, Mach, extension, mutation-barrier or allocation\ncase was freshly executed for this pass. Source-only conclusions and inspected\ncheckers above are not credited as live observations.')])
origin('O02', 'Bounded launch observation',
       'Row 11 and the launch-inventory contract identify what L observed and what it could not inspect. A complete starting-authority census was explicitly declined. These are settled observation boundaries; identifying the inference does not require completing the missing census.', [
    ref('docs/WORKER-INST-DOC-PLAN.md', 'The\npre-ready and post-apply specimens use distinct workers, so VM address or size\ndifferences are not within-process changes. No subtraction of them is claimed.'),
    ref('tests/suites/runner_exec_inheritance/README.md', 'Signal state, resource limits and extension-bearing workers remain\noutside this observation.'),
    ref('docs/WORKER-INST-DOC-PLAN.md', 'Adjudication: Explain the measured starting substrate and accept the explicitly bounded observation as a Known gap. No new isolation guarantee or runtime change is authorized.')])
origin('O03', 'Published source versus installed native internals',
       'Row 6 traced and rejected blanket allocation claims. The pinned published sources are not an authenticated reconstruction of the installed libraries, and no allocation probe was credited. Retaining that distinction preserves useful source findings without promoting them to runtime observations.', [
    ref('docs/WORKER-INST-DOC-PLAN.md', "These are published-source conclusions, not a match of\nApple's source release to every instruction in the installed shared cache;\nallocator, locale, lazy binding and private extension internals remain\nunobserved."),
    ref('docs/WORKER-INST-DOC-PLAN.md', 'Call-site completeness does not reach library internals, such as what\n`sandbox_compile_string`, the extension routines or libc formatting allocate.\nRecord the call and mark its internal behavior unobserved, unless a source or\nprobe establishes it.')])
origin('O04', 'Private extension state and identity',
       'The limitation originated in the extension account in 1f7abc0 and moved to WORKER in pass 3 under row 8. Its present basis includes native results versus access observations, PW-buffer erasure versus private copies, and preparation-time target identity versus later opens. These origins explain the boundaries; they do not authorize changes to other documents or reopen the accepted limitation.', [
    ref('docs/ARCHITECTURE.md', 'Known gap: private extension calls may allocate or retain internal state that PW\ncannot inspect. Erasure observations cover PW-owned transient buffers; successful\nnative results and phase progress do not establish kernel extension state,\nstable identity, effective permissions or access revocation.', '1f7abc0'),
    ref('docs/WORKER-INST-DOC-PLAN.md', 'The existing architecture paragraph separates PW buffer erasure from\nprivate allocation/retention, kernel state, identity, permissions and\nrevocation. Existing adjudication remains: move ownership to WORKER.md in\npass 3 and link from ARCHITECTURE.'),
    ref('tests/FAILURE-PROPAGATION-CONTRACT.md', 'Resolution\nand metadata are host observations before issuance; neither establishes that a\nlater open reached the same object.'),
    ref('tests/FAILURE-PROPAGATION-CONTRACT.md', '`host_buffer_erased`\nrecords clearing the host\'s mapping, not proof that every process or native\nlibrary has erased every copy.'),
    ref('docs/WORKER-INST-DOC-PLAN.md', 'Adjudication: Retain the accepted private-API limitation under row 8 and explain the observed after-release read with its allowed outcomes. No universal revocation claim or native API change is authorized.')])
origin('O05', 'Compiled-profile ownership overclaim',
       'Row 16 records the actual rejected sentence: retaining a pointer until exit was being expanded into an allocation-lifetime claim. The current guard marks the opaque apply boundary. Native ownership research is required before a future free, not before settling the editorial value of this boundary.', [
    ref('docs/WORKER-INST-DOC-PLAN.md', '**Row 16.** First candidate: “The compiled profile is retained until worker\nexit.” That allocation-lifetime sentence exceeds the visible source:\n`sandbox_apply` is private and may have ownership behavior not established\nhere. What PW itself does is keep the returned pointer, optionally read the\nprofile, call apply and make no explicit free call.')])
origin('O06', 'Spawn observation versus helper outcome',
       'The public exec account explicitly separates spawn, child disposition and helper-supplied evidence. This is a present external basis for the D2 distinction, not a claim that the guide caused the WORKER sentence.', [
    ref('docs/PolicyWitness.md', 'The helper must supply evidence about its internal operation; PW does not turn that evidence into a record for that operation, and a successful spawn can coexist with a failed exec result.')])
origin('O07', 'Native completion versus publication',
       'The document supplies a concrete independent counterexample: the file exists while its result is withheld. Preserve that positive account and payload-admission rule. It can support removing the duplicate negative counterfactual from the change-examples table.', [
    worker('independently observes the created file while requiring the reply to withhold\nthe unpublished result. Partially written payload remains outside the evidence\nthe host is entitled to decode.')])
origin('O08', 'Ordering versus conditions at execution',
       'The release hold orders query collection before an action batch. The current guide expressly identifies earlier actions changing later conditions. This distinguishes temporal order from a shared state snapshot; it is a useful instrument limit even with precise ordering vocabulary.', [
    ref('docs/PolicyWitness.md', 'Earlier actions in the phase, including consumption or release, can change what a later attempt encounters. Use another phase for a new query collection; neither interval is a common state snapshot.')])
origin('O09', 'Citation machinery and assertion coverage',
       'The renderer labels a column Checks and associates each row with implementing sources/checks, while the helper and G10 explicitly limit mechanical verification to definitions. A WORKER-specific caption/header repair can narrow that presentation. The shared helper comment and G10 remain settled rules for all their consumers.', [
    ref('docs/generator_common.py', 'A definition is a place to look, never evidence that a test asserts a claim.'),
    ref('tests/suites/source_drift/README.md', '- **G10. Captions state the verified guarantee.** A generated caption or\n  summary says what the generator verified about citations, presence and\n  definition, and nothing stronger; it never says a test exercises, covers or\n  proves a row.'),
    ref('docs/generate_architecture.py', 'parts.append(_table(["Id", "Node", "Kind", *columns, "Sources", "Checks", "Limits"], rows))')])
origin('O10', 'Explicit fixture intervention',
       'The fixture contract identifies both deliberate low-descriptor setup and containment of invalid native handles. These are concrete conditions that WORKER can state directly, allowing its two generalization disclaimers to go after repair.', [
    ref('tests/fixtures/host_setup/README.md', 'The collision case closes stdin and low unused descriptors;\nthe checker requires the actual source/destination overlap and the child\'s wrong\nevidence endpoint, not merely a low-descriptor label.'),
    ref('tests/fixtures/host_setup/README.md', 'A failed handle initialization leaves nil. Subsequent adapter calls record the\ninvalid use and return EINVAL instead of passing nil into libc; an attempted\nspawn with such a handle is likewise contained.')])
origin('O11', 'Selected graph and resource-role account',
       'The worker graph is an explicitly authored set of resource relationships, and its white/mixed resources have positive multiple-role descriptions. The selection legend and mixed-role account help read that representation. Neither needs an inference RCA to remain useful.', [
    worker('The edges select relationships among the inventoried resources.'),
    worker('White nodes have multiple roles or form the ambient\nexecution substrate:'),
    ref('docs/generate_architecture.py', 'for edge in graph["edges"]:\n        attrs = dict(styles["edge_kinds"][edge["kind"]])')])
origin('O12', 'File status and later pathname observations',
       'WORKER determines open_read/open_write attempt status from open and separately describes later host pathname observations. W50 points that later observation at the newly created object, while W53 already preserves the supported attachment of later observations. Local labels and that edge can be repaired without inventing object identity or changing another document.', [
    worker('Published success is the open result; the write and close returns are discarded.'),
    worker('Later host path inspection may observe file effect'),
    worker('Host attaches later path observations'),
    ref('docs/PolicyWitness.md', 'or that a path named the same object both times')])
origin('O13', 'Causal attribution and compiler receipt boundaries',
       'The repository witness principle and the worker tour distinguish native records, external correlation and pre-apply receipt capture. Their meaning survives any concise local label: association remains useful precisely with its causal boundary, and a compiler receipt remains useful with its application boundary.', [
    ref('AGENTS.md', '**No dishonest attribution**: never turn a permission-shaped failure into a sandbox-cause claim without supporting evidence, or claim agreement or disagreement between prediction and enforcement.'),
    worker('Capture before apply; host decode after publication'),
    worker('Controller associates external log candidates with run evidence')])
origin('O14', 'Unresolved specific inference behind three cautions',
       'Git pickaxe located these phrases at the pass-2 graph introduction, but neither that insertion nor the targeted plan/contract reads identify the specific rationale for size-based object attribution, the undefined scope of exact child policy effects, or byte-erasure caveats on temporary frames. The RCA briefs distinguish plausible motivations from established provenance.', [
    ref('docs/architecture.json', '"Sandbox-gated": "L shared mappings observed; no mapping-identity attribution from size alone"', '83f61f3'),
    ref('docs/architecture.json', '"Reaches exec children": "Inherited sandbox constraints; exact child policy effects not inventoried here"', '83f61f3'),
    ref('docs/architecture.json', '"Released": "Return or process exit; no claim of byte erasure"', '83f61f3')], 'specific_inference_unresolved')

manifest = json.loads(source('docs/architecture.json'))
graph = next(g for g in manifest['graphs'] if g['id'] == 'worker_capabilities')
items = {i['id']: i for i in graph['nodes'] + graph['edges']}
repairs = []


def doc_edit(before, after):
    return dict(owner='docs/WORKER.md authored prose', before=worker(before), after=after)


def fact_edit(item, field, after):
    return dict(owner='docs/architecture.json', selector=f'graphs[id=worker_capabilities].items[id={item}].facts[{field}]',
                before=items[item]['facts'][field], after=after)


def repair(ident, title, ids, rationale, edits, preserved, counterread, verification, dependencies=()):
    repairs.append(dict(id=ident, title=title, sweep_ids=ids.split(), rationale=rationale,
        edits=edits, preserved=preserved, guard_absent_read=counterread,
        verification=verification, dependencies=list(dependencies), status='draft; not applied'))


repair('R01', 'Name requested cleanup as an action', 'N004 N239',
       'Released can look like an achieved outcome. State the kind of information in the heading itself; keep every recorded return/failure and actual lifetime fact.', [
    dict(owner='docs/architecture.json', selector='worker_capabilities.node_facts and every worker node facts key named Released',
         before='Released', after='Release / teardown action'),
    doc_edit('Cleanup entries name calls; retained\nnative returns establish their observed outcomes where available.', ''),
    fact_edit('s36b', 'Released', 'Conditional process-group kill request')],
    'All cleanup calls, retained results, ignored-return descriptions, process-exit/reference lifetimes, group lifetime and escaped-descendant facts remain. Rows 10/19 are not resolved by this repair.',
    'Reading a request under Release / teardown action supplies no completed-cleanup result. The group row still says members may remain beyond the attempt/worker; no absence of descendants follows.',
    'Rename the owning key and node_facts declaration together; regenerate the worker table/map and check that every value except the named s36b edit survives. Review every cleanup-result cell for lost outcome data.')
repair('R02', 'Describe cited definitions precisely', 'N005 N057',
       'Remove the presentation-level suggestion that a named check verifies the whole resource row. State the actual mechanical operation in the caption and label the cited definitions as such.', [
    dict(owner='docs/generate_architecture.py:render_region, worker_capabilities output only',
         selector='WORKER caption, details summary, node/edge check-column labels',
         before='Shared caption pairs implementing source/checks, followed by the assertion-coverage disclaimer; column label Checks.',
         after='WORKER caption text after the figure/manifest/generator links: "Figure IDs correspond to the table IDs. Each row lists source references and cited test or rule definitions. The generator checks source-symbol presence and resolves those definitions." Details summary: "Worker capabilities: {node_count} nodes and {edge_count} edges; source symbols and cited definitions checked". Node/edge column label: "Cited check definitions". Counts remain generated.'),
    doc_edit('checks publication\nunder its bare-deny and full-region cases; that assertion scope belongs beside\nthe source account of preparation.', 'checks publication\nunder its bare-deny and full-region cases.')],
    'Every source/check citation, every per-resource evidence qualifier, G10, generator_common.py guidance, and N053 source/assertion/execution distinction remain. Existing row-25 citation-ownership findings remain unresolved.',
    'A definition-resolution caption and Cited check definitions header describe locating definitions. They contain no assertion that a test ran or proved the row. The specific publication cases remain named in prose.',
    'Use worker-specific rendering; compare every other generated document and figure byte-for-byte. Preserve G10 and the shared verification logic. Review the complete caption and table together; no new assertion-coverage or call-site-completeness enforcement is introduced.')
repair('R03', 'State launch and fixture conditions at the observation', 'N019 N122',
       'Name the production case and deliberate descriptor intervention before describing their outcomes, so the reader has the actual configuration rather than an ordinary-launch generalization to retract.', [
    doc_edit('The recorded launch observation found matching\nplain and environment-displaying process output, inherited null-device standard\noutput/error, and the expected protocol endpoints.', 'The recorded production launch case used an empty allow-default specimen.\nIts observation found matching plain and environment-displaying process output,\ninherited null-device standard output/error, and the expected protocol endpoints.'),
    doc_edit('With stdin closed\nin the low-descriptor control, evidence is allocated at fd 0.', 'The low-descriptor fixture deliberately closes stdin and low unused\ndescriptors before exercising launch setup. In that configuration, evidence is\nallocated at fd 0.'),
    doc_edit('These controlled launches do not establish that an ordinary XPC\nhost starts with the same descriptor arrangement.', ''),
    fact_edit('s14a', 'Sandbox-gated', 'L: inherited null-device stdout/stderr observed')],
    'Both ordinary and contaminated launch observations, the exact fd collision and missing-ready-endpoint outcomes, and the Known gap census remain. No universal launch invariant or additional observation is added.',
    'An ordinary host with stdin open has not been described by the deliberately modified fixture setup. The stdio cell is explicitly an L observation under the case named in prose.',
    'Cross-check the fixture setup description and the retained L configuration; retain source facts about inheritance independently of the two observations.')
repair('R04', 'Name adapter calls instead of general native uses', 'N017',
       'The actual control-flow observation is through fixture adapters. Naming their concrete action removes the broader libc-behavior premise.', [
    doc_edit('Failed handle initialization reaches later uses of the\ninvalid handle; fixture adapters contain those uses, so the controls establish\ncontinued host flow without claiming libc\'s behavior on that input.', 'After a failed handle initialization, the fixture adapters record subsequent\ninvalid-handle uses and return EINVAL. Their receipts record the host control\nflow through those adapter calls.')],
    'Unchecked production setup and the other actual failure-flow observations remain. Fixture containment remains explicit. This does not close the reopened setup-verification finding.',
    'The described EINVAL comes from an adapter whose calls are named. Reading the paragraph supplies an adapter receipt, not an observed libc call on that invalid handle.',
    'Match the fixture contract at its invalid-handle boundary; retain the existing link to host setup controls and its fixture contract.')
repair('R05', 'Name the source of attempt status', 'N025 N216',
       'Replace high-level success phrasing with the operation whose return determines attempt status; preserve independent filesystem observations beside it.', [
    doc_edit('Opens read-only, attempts a one-byte read and close, and discards those latter returns. Published success is the open result, with an available descriptor-path observation.', 'Opens read-only. The open result determines the published attempt status. On successful open, records an available descriptor-path observation, attempts a one-byte read and close, and discards those latter returns.'),
    doc_edit('Opens with `O_WRONLY \\| O_TRUNC`, then attempts to write `x` and close. Published success is the open result; the write and close returns are discarded.', 'Opens with `O_WRONLY \\| O_TRUNC`. The open result determines the published attempt status. On successful open, attempts to write `x` and close and discards their returns.'),
    doc_edit('The source\nestablishes where each call occurs and which returns are discarded; those are\nseparate from an independently observed filesystem effect.', ''),
    fact_edit('s31b', 'Sandbox-gated', 'Source-only; conditional new-object acquisition at open(O_CREAT)')],
    'Native operations, status transformation, discarded returns, existing-target/no-truncation behavior, source-only evidence and the existing-file byte/identity control remain. Attempt status is not relabeled as a raw syscall return.',
    'An open can determine attempt status while a later write fails; the draft explicitly discards the write return. Existing-target behavior is still stated in the create row, and S31b is expressly conditional.',
    'Review against the original action table and the attempt-channel contract. Retain every operation and returned/discarded-status distinction; no new filesystem-effect observation is claimed.')
repair('R06', 'Use the concrete publication counterexample once', 'N051',
       'The positive create-then-kill observation already supplies the counterexample. Make the event separation explicit at its introduction and remove the duplicate negative counterfactual from the later change table.', [
    doc_edit('A native call and publication are distinct boundaries.', 'A native call can complete before the worker publishes the attempt slot.'),
    doc_edit('| Move reply assembly into the worker or use missing publication as proof of no effect | Couples reporting to specimen-controlled communication or substitutes absence of evidence |', '| Move reply assembly into the worker | Couples reporting to specimen-controlled communication |')],
    'N042, the independently observed created file with withheld result, payload eligibility, the evidence-contract link, and the reply-assembly design example remain.',
    'The reader sees a completed native effect followed by an unpublished result in a concrete case. That fact defeats the absent-publication inference without repeating it as a prohibited conclusion in the change table.',
    'Read the complete native-observation section with the shortened table row. Preserve both sides of the independent counterexample and its control citation.')
repair('R07', 'Remove the unsupported object-identity edge', 'N299',
       'The x3-to-s31b observation arrow visually associates later pathname metadata with the newly created object. W53 already carries the supported relation: attaching later path observations to the host record.', [
    dict(owner='docs/architecture.json', selector='worker_capabilities.edges[id=W50]', before=items['W50'], after=None),
    dict(owner='docs/architecture.json', selector='worker_capabilities.nodes[id=x3].note', before=items['x3']['note'], after=None),
    dict(owner='docs/architecture.json', selector='worker_capabilities.edges[id=W53].label', before=items['W53']['label'], after='Host attaches later target-path metadata')],
    'Keep S31b, all worker acquisition/effect edges, X3 and its source/check citations, W53 and the externally observed metadata. The independent create-effect control is unchanged. No resource is removed.',
    'If a pathname resolves to a replacement object before host inspection, the repaired graph still says exactly what occurred: later target-path metadata was attached. It draws no identity relationship to the worker-created object.',
    'Regenerate the worker figure/table and inspect the complete graph: X3 joins the host record through W53; it no longer observes S31b. Confirm the worker-created resource/effect account and all other documents remain intact.')

rcas = [
 dict(id='Q01', sweep_ids=['N164'], title='What mapping attribution is the size caution guarding?',
      established='The phrase entered in pass 2. L recorded accessible VM regions in separate workers; row 11 declines allocation attribution and cross-worker subtraction.',
      hypotheses=['A matching region size was used to associate an observed region with the evidence object.', 'The warning is a generic precaution inserted without any such attribution claim.'],
      question='Does any retained L observation or interpretation credit the S18 evidence object by size alone, and is the guarded error source-to-object attribution or cross-worker comparison?',
      bounded_work='Inspect the two retained launch_inventory mappings.stdout/observations.json records and their interpretation notes; trace the S18 evidence credit. Keep row-19 fixture VM observations separate from L. Do not run a new probe merely to find the wording origin.',
      completion='Produce the exact attribution premise and its evidence path. If present, draft a local repair that separates raw region observation from object attribution; if absent, record the completed search and assess deletion of the unmotivated caution. Missing retained artifacts remain an explicit evidence limit.',
      interim='Keep the size/identity caution; retain actual source/mapping facts.'),
 dict(id='Q02', sweep_ids=['N203'], title='Define the alleged child-policy inference',
      established='The pass-2 cell states inherited constraints and then disclaims an unspecified inventory of exact child policy effects. The exec contract separately defines spawn/child/helper evidence, which settles N028 but not this phrase.',
      hypotheses=['Inheritance was being overread as identical effective access for parent and child.', 'The qualifier only meant that the sweep did not inventory every helper operation.'],
      question='Which concrete claim about child effects is being blocked, and what text, API terminology or reader expectation supplies its premise?',
      bounded_work='Trace the S28 child-inheritance wording to the pass-1 inventory and relevant exec/augment/worker-child authority accounts. Identify an exact proposition before considering platform/native research; other documents are read-only.',
      completion='Name the premise, inferred child claim and owner of the meaning. Then either keep a specific useful boundary, repair a discovered WORKER trigger, or justify removing the unspecified disclaimer. Do not invent a universal child-policy equivalence claim.',
      interim='Keep the exact-child-effects qualifier and the positive inherited-constraints fact.'),
 dict(id='Q03', sweep_ids=['N266','N270'], title='Why do temporary-frame lifetimes carry a byte-erasure disclaimer?',
      established='Both no-claim-of-byte-erasure clauses first appear in pass 2. The document separately describes token-buffer erasure, but the inspected introduction supplies no specific requirement or mistaken inference about these temporary frames.',
      hypotheses=['Return/process exit in the Released column was being mistaken for overwriting bytes.', 'Token-buffer erasure language was being generalized to temporary frames.', 'The caveat is defensive prose with no identified current use.'],
      question='Which data and observer make byte erasure of these frames relevant, and where is return or teardown being treated as an erasure guarantee?',
      bounded_work='Review the original inventory/erasure discussion and the two rows\' data ownership. Look for a concrete erasure requirement or inference; keep PW token mappings, issuer storage and private-library state distinct. Do not add a wipe or create a new confidentiality guarantee.',
      completion='Identify the precise requirement/inference and a supporting passage, or document that the named search found none. Decide whether a local lifetime-label repair suffices or the caution states a necessary separate boundary.',
      interim='Keep both disclaimers while setting aside their actual return/process-exit lifetime clauses.')
]

groups = {}


def group(ident, title, ids, origins_, reason, failed_trial):
    groups[ident] = dict(id=ident, title=title, sweep_ids=ids.split(), origins=origins_.split(),
                        settled_reason=reason, rejected_rewrite=failed_trial)


group('S01', 'Evidence provenance and scoped controls',
      'N004 N027 N032 N058 N060 N063 N066 N069 N071 N072 N078 N081 N108 N110 N113 N116 N120 N130 N141 N144 N147 N149 N152 N155 N157 N161 N171 N174 N177 N180 N184 N195 N198 N201 N204 N208 N212 N216 N219 N223 N226 N229 N231 N236 N238 N240 N260 N276 N279 N307 N309 N258 N285 N287 N289 N291 N293', 'O01 O02',
      'The qualifier identifies the support actually credited to this resource or configuration. Source inspection, observed presence, native failure and missing measurement remain different facts. There is no unresolved editorial question about preserving this scope; completing the missing runtime evidence would be separate work.',
      'Deleting or globally replacing resource-specific qualifiers with a general assurance would lose which resource/case was actually observed. More precise headings alone do not supply the missing observations.')
group('S02', 'Launch and observation boundaries', 'N012 N014 N020 N054 N136 N138 N158 N308 N126', 'O02',
      'The exact observed configuration, observer limitation or accepted census boundary is useful information about the instrument. It remains valid as a scope statement without deciding native facts outside that observation.',
      'Replacing the observations with a generic inherited-state description would discard the actual control results or the observer\'s SIGPIPE limitation. Renaming freshness cannot establish a complete authority census.')
group('S03', 'Native/private call boundaries', 'N026 N043 N056 N167 N188 N232 N234 N264 N268 N272 N281 N283', 'O03 O04',
      'The account distinguishes PW-owned storage/calls and inspected published implementations from private or installed-library internals. The earlier allocation overclaims and version boundary give this distinction a documented present purpose.',
      'Saying only that PW calls a native function would erase useful allocation/source findings; calling fixed buffers allocation-free would repeat the overclaim. The boundary remains useful alongside the positive facts.')
group('S04', 'Compiled-profile ownership', 'N009 N190 N191', 'O05',
      'The actual rejected lifetime sentence is recorded. No PW free does not decide private apply ownership. The editorial boundary is settled; researching ownership before a future free is a separate implementation question.',
      'A pointer-retention sentence alone can repeat the allocation-lifetime overclaim. Removing all lifetime discussion would hide a resource constraint relevant to a proposed destruction call.')
group('S05', 'Extension observations and private state', 'N039 N040 N241 N243', 'O04',
      'Native outcomes, after-release fresh reads, erasure of owned buffers and unobserved private state have distinct meanings. The accepted limitation and owning contract identify the current basis, including preparation identity versus later opens.',
      'Renaming S37 to only a worker handle would drop its native-authority/resource subject or move the same private-state qualification elsewhere. Native-call wording alone also cannot turn release success into revocation evidence.')
group('S06', 'Publication and temporal order', 'N042 N044 N052', 'O07 O08',
      'The concrete withheld-result effect and the difference between ordered queries and later conditions are useful instrument facts. Keep the independent observation and actual timing consequence; neither needs an inference-origin RCA.',
      'Replacing the account with completed-slot or query-first vocabulary leaves the same inference available and loses the counterexample or changing-conditions explanation.')
group('S07', 'Review duties and shared verification rules', 'N053 N305 N306', 'O01 O09',
      'The source/assertion/execution distinction and call-site review responsibility state the actual workflow. The shared machinery rules govern more than WORKER and remain useful independently of a worker-caption repair.',
      'Removing the rules after changing WORKER would weaken the stated verification contract or edit other documentation. A caption repair does not supply assertion coverage or a call-site completeness rule.')
group('S08', 'Diagram scope and multiple roles', 'N003 N304', 'O11',
      'The legend explains the selected graph and positive multiple-role assignment. These are useful reading facts, not an unresolved claim about a missing worker capability.',
      'Making the figure exhaustive would require a different account; suppressing multiple roles would discard actual resource roles. No guard-removal repair is needed.')
group('S09', 'Exec outcome layers', 'N028', 'O06',
      'Spawn evidence and child/helper outcome are distinct observations in the owning exec contract. The present external basis is identified, so this clarification can stay without a later inference RCA.',
      'A generic executes-the-target description would obscure which result the worker publishes and make the helper-outcome inference easier.')
group('S10', 'External correlation and pre-apply receipts', 'N300 N301', 'O13',
      'The causal and application boundaries define how these useful external/pre-apply observations join the run. Precise source labels do not make the records self-interpreting.',
      'Removing the relation to the run would discard why the observations are present. Renaming association or receipt alone leaves the causal or applied-policy inference available.')

by_group = {}
for g in groups.values():
    for ident in g['sweep_ids']:
        if ident in by_group:
            raise ValueError(f'duplicate default group {ident}')
        by_group[ident] = g['id']
repair_ids = {ident:r['id'] for r in repairs for ident in r['sweep_ids']}
rca_ids = {ident:r['id'] for r in rcas for ident in r['sweep_ids']}
units = []


def add(ident, quote=None, suffix='', disposition=None, group_id=None, repair_id=None, rca_id=None, route=None, meaning=None):
    e = entries[ident]
    q = quote if quote is not None else e['quote']
    lines = source(e['path']).splitlines(keepends=True)
    assert q in ''.join(lines[e['start_line']-1:e['end_line']]), (ident, q)
    if disposition is None:
        if ident in rca_ids:
            disposition, rca_id = 'stay_pending_rca', rca_ids[ident]
        elif ident in repair_ids:
            disposition, repair_id = 'go_after_worker_repair', repair_ids[ident]
        else:
            disposition, group_id = 'stay_settled', by_group[ident]
    if disposition == 'stay_settled' and group_id is None:
        group_id = by_group[ident]
    units.append(dict(id=ident+suffix, sweep_id=ident,
        original_primary=e['bucket'], original_split=e['split'], route=route or e['split'],
        layer=e['layer'], source=dict(path=e['path'], revision=BASE, start_line=e['start_line'], end_line=e['end_line'], quote=q),
        meaning=meaning or e['proposition'], disposition=disposition,
        settled_group=group_id, repair=repair_id, rca=rca_id,
        original_trigger=e.get('trigger'), context='Full original context and associated manifest locations remain in the frozen sweep inventory by sweep_id.'))


special = {'N004','N005','N014','N017','N019','N025','N026','N028','N032','N040','N043','N044','N051','N052','N053','N122','N164','N203','N216','N266','N270'}
for ident,e in entries.items():
    if e['bucket']=='B1' and ident not in special:
        add(ident)
add('N004','Acquisition periods record call-site placement. Gating claims retain their\nobserved, source-only or unknown scope.', '.scope', 'stay_settled','S01', route='D2', meaning='Keep per-resource call-placement and evidence-basis scope.')
add('N004','Cleanup entries name calls; retained\nnative returns establish their observed outcomes where available.', '.cleanup', repair_id='R01', meaning='Requested cleanup calls and observed outcomes are different.')
add('N005','that assertion scope belongs beside\nthe source account of preparation.', meaning='Meta-instruction guarding assertion coverage inferred from preparation citations.')
add('N014','The observer used by those controls itself ignores SIGPIPE, so that observation\ncovers environment and descriptors.', meaning='The observer does not independently establish inherited signal state.')
add('N017',"fixture adapters contain those uses, so the controls establish\ncontinued host flow without claiming libc's behavior on that input.", meaning='Fixture adapter receipts do not describe libc behavior on invalid handles.')
add('N019','These controlled launches do not establish that an ordinary XPC\nhost starts with the same descriptor arrangement.', meaning='Deliberate low-descriptor fixture behavior is not an ordinary XPC starting arrangement.')
add('N025','The source\nestablishes where each call occurs and which returns are discarded; those are\nseparate from an independently observed filesystem effect.', meaning='Call placement or retained status is not independent filesystem-effect observation.')
add('N026','That is a published-source\naccount; allocation events in the installed libraries were unobserved.', '.source', meaning='Examined published allocation paths are not observations of the installed libraries.')
add('N026','Runtime allocator, locale and binding behavior remain unobserved at\nthese call sites.', '.runtime', route='D2', meaning='Runtime allocator/locale/binding scope remains unobserved; historical row 6 supplies the current reason.')
add('N028','A nonzero child exit after\nsuccessful spawn still supplies spawn evidence;', meaning='A child outcome does not erase the independent successful-spawn observation.')
add('N032','This lifetime is source-established; a live right-count measurement\nis absent.', meaning='The Mach lifetime account has source support rather than a live right-count measurement.')
add('N040','Known gap: private extension calls may allocate or retain internal state that PW\ncannot inspect.', '.private', route='D2', meaning='Private extension allocation/retention lies beyond the recorded observations.')
add('N040','Erasure observations cover PW-owned transient buffers;', '.erasure', route='D2', meaning='Observed buffer erasure is scoped to PW-owned transient buffers.')
for suffix,quote,route,meaning in [
 ('kernel','kernel extension state','C2','Native success/progress does not establish kernel extension state.'),
 ('identity','stable identity','D2','Native success/progress does not establish stable target identity across preparation and later access.'),
 ('permission','effective permissions','C2','Native success/progress does not determine effective permission.'),
 ('revocation','access revocation','C2','Native release success/progress does not establish access revocation.')]:
    add('N040',quote,'.'+suffix,route=route,meaning=meaning)
add('N043','the source-level inventory\nends at native/library call boundaries whose internals remain unobserved.', meaning='The source-level PW acquisition account stops at native/library call boundaries.')
add('N044','Earlier actions and external actors can\nchange conditions before a later attempt, even with an intact release hold.', meaning='The release hold orders observations but does not freeze later conditions.')
add('N051','use missing publication as proof of no effect', meaning='The change table repeats the missing-publication inference already refuted by the concrete control.')
add('N052','observe both the hold and its limited snapshot meaning.', meaning='Ordering controls establish the hold within its limited snapshot meaning.')
add('N053',"Source citations\nestablish locations; a check's assertions establish its coverage; recorded\nexecution establishes the configuration actually observed.",'.evidence',meaning='Keep source locations, assertions and observed executions distinct.')
add('N053','Call-site completeness is a source-review responsibility.', '.completeness',route='D2',meaning='Keep the chosen manual completeness responsibility; no automatic completeness rule is promised.')
add('N122','no universal stdio rule',meaning='A production observation does not define every worker launch stdio arrangement.')
add('N164','no mapping-identity attribution from size alone',meaning='Size alone does not identify the observed mapping as the evidence object.')
add('N203','exact child policy effects not inventoried here',meaning='Unspecified exact child-policy-effect inference needs a defined premise.')
add('N216','Source-only', '.source', 'stay_settled','S01',route='D2',meaning='Keep the evidence basis of the new-file resource fact.')
add('N216','creation not implied for existing target', '.creation', meaning='An O_CREAT/open status need not mean a new filesystem object was created.')
add('N266','no claim of byte erasure',meaning='Frame return/process exit is not presented as byte erasure; the specific reason for this warning is unresolved.')
add('N270','no claim of byte erasure',meaning='Capture/hash frame lifetime is not presented as byte erasure; the specific reason for this warning is unresolved.')

for ident in ['N258','N285','N287','N289','N291','N293']:
    e=entries[ident]
    q='Source-only' if 'Source-only' in e['quote'] else 'source-only'
    add(ident,q,'.secondary','stay_settled','S01',route='D2',meaning='Keep source-only provenance; the actual outside-worker/no-target-fd fact remains set aside as A1.')
add('N304',suffix='.secondary',disposition='stay_settled',group_id='S08',route='C2',meaning='The possible exclusive-color inference is answered by actual multiple-role descriptions; retain those facts.')
aliases=[dict(sweep_id='N008',handled_by=['N009'],reason='The private-ownership guard already has its own unit; park the actual absence of a PW destruction call.'),
         dict(sweep_id='N045',handled_by=['N299','N300'],reason='The closing contract referral remains; the concrete identity/causality guards are triaged separately.'),
         dict(sweep_id='N126',handled_by=['N012'],reason='Retain the two positive launch observations; their configuration/generalization boundary is handled with N012.')]

units.sort(key=lambda r:(int(r['sweep_id'][1:]),r['id']))
covered={u['sweep_id'] for u in units}
assert {i for i,e in entries.items() if e['bucket']=='B1'} <= covered
assert len({u['id'] for u in units})==len(units)
secondary={i for i,e in entries.items() if e['bucket']=='A1' and e.get('secondary_role')}
assert secondary == ({u['sweep_id'] for u in units if u['original_primary']=='A1'} | {a['sweep_id'] for a in aliases})
save('origins.json',dict(revision=BASE,origins=origins,search_boundary='Targeted WORKER/machinery, associated plan, git introduction history, owning contracts and relevant control documentation. No repository-wide search for negative language.'))
save('rewrite-candidates.json',dict(revision=BASE,repairs=repairs,
     common_scope='Drafts only. Apply through the owning manifest/generator for generated text. Resulting document/figure changes are confined to WORKER and worker-capabilities; shared rules and other documents remain unchanged.',
     future_checks=['python3 docs/generate_architecture.py', 'python3 docs/generate_architecture.py --check', 'PW_TEST_OUT_DIR=tests/out/runs/<fresh-name> tests/run.sh --case source_drift/architecture_documentation', 'Review generated WORKER plus DOT/SVG and prove all other generated destinations unchanged. Use targeted source_drift checks if renderer/contract verification changes.'],
     runtime_scope='No worker/native behavior, evidence contract, source identity, signing, build or runtime changes are part of these candidates.'))
save('ledger.json',dict(revision=BASE,input_inventory=str(INPUT),input_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    scope='Triage decisions and concrete WORKER-only repair candidates; not implementation or register adjudication. No pass 6.',
    counting='Decision units split when disposition or inference basis differs. Positive A1 context is preserved rather than counted again as a guard. Counts are not unique semantic-claim counts.',
    units=units,settled_groups=list(groups.values()),rca_briefs=rcas,secondary_aliases=aliases,
    parked_a1_ids=[i for i,e in entries.items() if e['bucket']=='A1'],
    prior_scope_exclusions=[e['id'] for e in inventory['excluded_entries']],
    route_note='Original sweep labels remain immutable. Clause routes expose partial C2 support and D2 secondary roles for this triage; they do not overwrite the descriptive sweep.'))


def location(r):
    return f"{r['path']}:{r['start_line']}–{r['end_line']} at {r['revision'][:7]}"


def literal(text):
    return ['```text',text,'```','']


md=['# Worker-language triage ledger','',f'Frozen revision: `{BASE}`.','',
    'The three outcomes apply to guard clauses. All 205 primary A1 occurrences remain set aside; seven secondary units and three aliases carry their guard roles into this ledger. The 23 prior scope exclusions remain excluded. Original quotations/context and manifest duplicates remain in the earlier sweep inventory by ID.','',
    'Every settled unit has an origin/basis and a reason in its named group below. Every pending unit has an RCA brief; every removable unit has a concrete repair. Drafts and full before/after text are in `rewrite-candidates.md`. No changes are applied to the underlying account.','']
counts=collections.Counter(u['disposition'] for u in units)
for outcome,title in [('stay_settled','Stay; no later inference investigation'),('stay_pending_rca','Stay pending a specified RCA'),('go_after_worker_repair','Go after the specified WORKER-only repair')]:
    md += ['## '+title,'',f"{counts[outcome]} decision units.",'', '| Unit | Sweep route | Subject | Basis / action |','| --- | --- | --- | --- |']
    for u in units:
        if u['disposition']==outcome:
            md.append('| '+u['id']+' | '+str(u['route'])+' | '+u['meaning'].replace('|','\\|')+' | '+str(u['settled_group'] or u['repair'] or u['rca'])+' |')
    md.append('')
md += ['## Settled reasons and rejected rewrite trials','']
for g in groups.values():
    md += [f"### {g['id']} — {g['title']}",'',g['settled_reason'],'', '**Origin/basis:** '+', '.join(g['origins'])+'.','', '**Why the alternative is unsatisfactory:** '+g['rejected_rewrite'],'']
md += ['## RCA briefs','']
for q in rcas:
    md += [f"### {q['id']} — {q['title']}",'', 'Units: '+', '.join(q['sweep_ids'])+'.','',
           '**Established:** '+q['established'],'', '**Question:** '+q['question'],'',
           '**Hypotheses, not findings:** '+ ' '.join(q['hypotheses']),'',
           '**Bounded work:** '+q['bounded_work'],'','**Completion condition:** '+q['completion'],'',q['interim'],'']
md += ['## Exact guard clauses','']
for u in units:
    md += [f"### {u['id']}",'', location(u['source']), '']+literal(u['source']['quote'])
    md += [u['meaning'],'',f"Outcome: **{u['disposition']}**; "+str(u['settled_group'] or u['repair'] or u['rca'])+'.','']
md += ['## Secondary aliases','']
for a in aliases:
    md += [f"- {a['sweep_id']} → {', '.join(a['handled_by'])}: {a['reason']}"]
(OUT/'ledger.md').write_text('\n'.join(md).rstrip()+'\n')

md=['# Concrete WORKER-only rewrite candidates','',f'Frozen revision: `{BASE}`. Drafts only; nothing below has been applied.','',
    'Generated edits name their owning inputs. Preserve all factual context specified below, every settled/pending guard, and all A1 facts. Other documents are read-only. No new call-site completeness enforcement or behavioral claim is introduced. Reflow surrounding whitespace after deleting a selected prose span.','']
for r in repairs:
    md += [f"## {r['id']} — {r['title']}",'','Guard units: '+', '.join(r['sweep_ids'])+'.','',r['rationale'],'']
    for edit in r['edits']:
        md += ['**Owner:** '+edit['owner']+'.','']
        if 'selector' in edit:md += ['**Selector:** `'+edit['selector']+'`.','']
        before=edit['before']
        if isinstance(before,dict) and 'quote' in before:
            md += ['**Before:** '+location(before),'']+literal(before['quote'])
        else:md += ['**Before:**','']+literal(json.dumps(before,ensure_ascii=False,indent=2) if isinstance(before,dict) else str(before))
        md += ['**After:**','']+literal('(remove this selected text/object; preserve surrounding context)' if edit['after'] is None or edit['after']=='' else edit['after'])
    md += ['**Preserved:** '+r['preserved'],'','**Read with the guard absent:** '+r['guard_absent_read'],'','**Validation at implementation:** '+r['verification'],'']
md += ['## Common implementation boundary','',
       'Render all destinations through the existing generator, then verify that only WORKER.md and worker-capabilities DOT/SVG changed. Generated captions/header labels specific to WORKER require worker-specific rendering; keep shared helper rules and other tour captions intact. Use a fresh managed output directory for source_drift/architecture_documentation. These commands are future implementation checks, not tests run by this triage.','',
       'The repair IDs are not register adjudications. Existing open/reopened findings, especially citation ownership and setup/descendant verification, retain their current state. No package closes them.']
(OUT/'rewrite-candidates.md').write_text('\n'.join(md).rstrip()+'\n')

md=['# Documentary origins and current inference bases','',
    'Historical introduction, documented motivation and present reader premise are separate kinds of evidence. A cited external contract supplies a current meaning; it does not by itself establish historical causation. No external document is proposed for editing.','']
for o in origins:
    md += [f"## {o['id']} — {o['title']}",'',o['finding'],'']
    for r in o['references']:
        md += [location(r),'']+literal(r['quote'])
(OUT/'origins.md').write_text('\n'.join(md).rstrip()+'\n')
print(json.dumps(dict(decision_units=len(units),outcomes=counts,
                     primary_b1_ids=len({u['sweep_id'] for u in units if u['original_primary']=='B1'}),
                     secondary_a1_ids=len({u['sweep_id'] for u in units if u['original_primary']=='A1'}),
                     aliases=len(aliases),parked_a1=205,repairs=len(repairs),rca_briefs=len(rcas)),indent=2))
