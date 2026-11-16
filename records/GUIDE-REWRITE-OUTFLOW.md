# Guide rewrite outflow

Disposition record for `DOCUMENTATION-TRACE-PLAN.md`, prepared on 2026-11-15.
The user guide is frozen at the reconciled starting commit
`2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc`. This work changes the developer
reading paths; it moves no material into or out of the guide. This record
credits source and document inspection, not a new guide workflow, specimen,
build or test execution. Final freeze and staging verification belongs to the
plan's acceptance evidence.

## Developer pointers and surface history

The guide's [Public contract surfaces](../docs/PolicyWitness.md#public-contract-surfaces)
links to the `v0.3.8` release's `docs/CONTRACT.md` and says that document defines
the fields, applicability and obligations behind the surfaces. The link remains
useful as an entry point, but its description understates the resulting
arrangement. [REQUEST](../docs/REQUEST.md) holds declaration and admission
statements, [RESPONSE](../docs/RESPONSE.md) holds returned records and their
interpretation, and [ARCHITECTURE](../docs/ARCHITECTURE.md) states the named
cross-process protocols. [CONTRACT](../docs/CONTRACT.md) supplies identity,
history, shared definitions, support detail and indexes to those statements.
The authored surface tree still owns public meaning regardless of rendering.

**Disposition:** the frozen sentence and release link remain unchanged. The
guide rewrite receives this corrected account of the developer destinations.
The surface set, IDs, artifact descriptions and guide stamp table are preserved;
moving statements does not itself rename the user artifacts or establish
compatibility between builds. Historical links continue to refer to their
matching releases rather than being redirected to current files.

## Statements inspected against the new reading paths

The guide's [Specimen format](../docs/PolicyWitness.md#specimen-format) and
[Output envelope](../docs/PolicyWitness.md#output-envelope) remain its user
account. The new developer documents do not depend on those sections for a
definition. This bounded review established no direct guide/tree contradiction
in the publication, result, incomplete-evidence and actor-scheduling passages
read below. It did identify the following understatements and useful extensions.

| Guide location | Finding and disposition |
| --- | --- |
| [Common flags](../docs/PolicyWitness.md#common-flags), `example` row | The row correctly distinguishes a request from an envelope and requires discarding output after exit 2. It does not explicitly state the full [build admission promise](../docs/REQUEST.md#contract-request-specimen-emit_example): this build's own `run` admits its published example, while emission performs no host admission and establishes no successful attempt. This distinction is available to the guide rewrite; it is not a claim that the existing row promises native success. |
| [Receiver evidence](../docs/PolicyWitness.md#receiver-evidence) | The guide already distinguishes admitted `not_invoked`, `invoked` and unknown submission, and preserves the no-replay rule. Its sentence that `runner_client` is null when the client was not invoked gives one cause, not the full [payload field meaning](../docs/RESPONSE.md#contract-envelope-data-runner_client), which also permits launch failure before a capture returns. The rewrite receives that fuller explanation without treating a missing capture as evidence of nonexecution. |
| [What success means](../docs/PolicyWitness.md#what-success-means) | The guide already allows failed attempts and integrity findings beside finished/true/0. RESPONSE adds an envelope-first reading path and an explicit comparison with the independently captured process status. This is an explanatory path to reuse, not a correction of the guide's success rule. |
| [Reading path and object observations](../docs/PolicyWitness.md#reading-path-and-object-observations) | The guide already separates submitted paths, descriptor observations and host path diagnostics, and says no reply field identifies the object a native query consulted. RESPONSE's saved-input replacement and suffix examples add concrete ways to read those limits with independent samples. Their workload expectations are not captured results or general promises about native behavior. |

`test-input` does not appear in the frozen guide. It is a build-bound developer
publisher, so that absence is not by itself a user-guide defect or a requirement
to add the command. The disposition is to carry its useful distinction into any
user explanation that discusses it: complete publication with positional target
binding is separate from host admission, fixture preparation and native results.
The publisher supplies no answer key. Its [developer rule](../docs/REQUEST.md#contract-request-specimen-emit_test_input)
and the [controlled-read exercise](../docs/RESPONSE.md#follow-one-saved-read-input)
retain those boundaries.

## Actor advancement correction and its guide relevance

The corrected [phase scheduling rule](../docs/REQUEST.md#contract-actors-phase-order)
distinguishes ordinary completion-based advance from actor scheduling. The actor
schedule can skip unavailable actors or visits and continue to another usable
actor after a failed active actor is reaped. Unresolved termination, exhausted
execution allowance, lost wait ownership and a failed evaluated termination
dependency retain their cancellation consequences. This corrects the public
account to the existing scheduler; it changes no runtime behavior.

The guide's sentence that the next collection begins after phase completion
occurs in [Ordered phases](../docs/PolicyWitness.md#ordered-phases), explaining
the ordinary form and its one retained worker. It is not an established conflict
with that corrected actor rule. The guide already says setup-failed or unlaunched
actors remain unavailable, distinguishes a never-evaluated gate from a failed
evaluated gate, and says a termination dependency does not require final phase
completion. Those statements remain consistent.

**Disposition:** the guide rewrite receives the fuller skip/reap/continue account
as a useful qualification of actor progression. The ordinary phase explanation
is not marked wrong, and the guide's description of actors staying alive across
visits is not treated as a guarantee that every declared visit executes. A user
account can make that distinction through phase status, activation, ending and
reap observations, without reproducing scheduler symbols or test names.

## Material that needs a user explanation

These developer statements have user-relevant consequences, but their source
citations and constructed-check discussions are not a substitute for prose a
reader can use with the shipped app:

- The [REQUEST opening](../docs/REQUEST.md) distinguishes declaration,
  controller preparation, host admission and contingent execution. For a user,
  the consequence is to retain the asserted identity and submitted input while
  treating an identity match as one boundary, not a certificate of validity or
  effects.
- The [publication comparison](../docs/REQUEST.md) and
  [example exercise](../docs/RESPONSE.md#read-the-published-example) separate
  complete output, the build's admission promise and independent native
  expectations. The flat and actor derivatives belong to the test harness;
  they are not additional forms that `example` publishes. The constructed actor
  fixture is not a transcript suitable for presenting as an observed run.
- The [absence reading](../docs/RESPONSE.md#read-absence-and-incomplete-execution-precisely)
  distinguishes omitted keys, explicit null, withheld assessments, unpublished
  actions and incomplete collection. A user needs the corresponding field and
  supported conclusion, including the possibility of effects after a lost
  reply, rather than implementation type names.
- The [controlled-read exercise](../docs/RESPONSE.md#follow-one-saved-read-input)
  distinguishes a new inode at the same path, an unchanged bounded prefix with
  a changed suffix, and a full-bound read that establishes no EOF. Independent
  before/after samples establish their sampled relationship, not continuous
  stability; an observer reading the whole file does not mean the worker did.
- [Collection before release](../docs/ARCHITECTURE.md#one-run-in-time),
  [once-only invocation](../docs/ARCHITECTURE.md#contract-transport-delivery) and
  [extension custody](../docs/ARCHITECTURE.md#contract-extensions-custody) provide
  complete developer accounts. Their user consequences are bounded ordering,
  uncertainty before repeating an effect, and the distinct evidence for issue,
  transfer, consumption, release and subsequent access. The guide already
  explains substantial parts of these and need not acquire the developer
  protocol notation or trace indexes.

CONTRACT's changed-item index, partial interface associations and support grades
serve developers reviewing changes. They are retained as developer material;
there is no disposition to transplant those indexes into the standalone guide.

## Shared content retained by the freeze

The copied regions in [LIMITS](../docs/LIMITS.md),
[QUESTIONS](../docs/QUESTIONS.md), [EXTENSIONS](../docs/EXTENSIONS.md) and the
[failure-propagation contract](../tests/FAILURE-PROPAGATION-CONTRACT.md) were
left unchanged, as were the guide's stamp-table carriers. The navigation sweep
found no relocated `CONTRACT#contract-*` link inside those copied regions that
required a deferred edit. No additional shared-region correction was identified
and withheld during this review.

The actor coverage region already preserves setup, equipment, gate and
unavailable-actor distinctions. The actor advancement clarification above is
recorded as additional explanation available to the guide rewrite, not as an
unmade fix to an identified contradictory shared sentence. Shared-region
ownership, standalone link usability and the guide's executable workflows remain
with their existing owners.
