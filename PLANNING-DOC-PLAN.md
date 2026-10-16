# Planning guidance in CONTRIBUTING

Add a roughly 500–600 word section, **Planning a change**, to
[CONTRIBUTING.md](CONTRIBUTING.md), after **How to help** and before
**Development environment**. Help agents make their first draft their best
executable proposal: sufficient for a fresh agent to execute, and disposable
once the work is complete. Human contributors should be able to use the same
guidance.

Status: ready for drafting; the section has not been written.

## Writing brief

Address a reader familiar with the relevant repository code and documentation,
but without the originating conversation or memory of earlier changes. Explain
how to turn that understanding into a considered recommendation. Preserve the
existing welcome to people bringing an unresolved question: this standard
applies when preparing a plan for execution, not to every issue or contribution.

Develop these six ideas into concise, connected guidance:

- Choose a coherent course and justify consequential decisions. Alternatives
  should help reach a recommendation; routine implementation detail can remain
  with the executor.
- Do the inspection or reproduction needed to support that recommendation before
  handoff. Distinguish this preparation from work that genuinely belongs in the
  proposed implementation or investigation.
- Give a successor the problem, intended behavior, decisions, scope, actions,
  dependencies and evidence of completion. Put lasting contracts and operating
  instructions in their proper homes so the completed plan can be removed.
- Make each unresolved question actionable: identify the missing fact, why it
  cannot be settled now, how to resolve it and what depends on the answer.
- Challenge the weakest premise and whether the proposed checks distinguish
  success from a plausible failure. Scale the effort to the change.
- Present a proposal ready to act on within the task's authorization. If a
  decision belongs to someone else, identify it and bring a recommendation.
  Anticipated review is no reason to leave ordinary design unfinished.

These are obligations for the guidance's author, not six required headings or
steps for every plan. Combine related ideas and use a brief example where it
makes an instruction usable. Explain enough to elicit judgment rather than
merely listing desirable qualities. Keep detailed repository rules with their
existing owners; no architecture recap, mandatory template, commit cadence or
new approval process is needed.

## Work

### 1. Draft the section

Read CONTRIBUTING as a whole and develop the explanations and example before
compressing them to the word target. Organize around preparing and choosing,
handing off executable work, handling genuine unknowns, and challenging the
proposal. Let the prose connect these responsibilities rather than reproducing
this plan's structure.

Use an example that shows preparation earning a decision or an experiment making
a dependency executable. Include only the facts needed to understand that
choice. The published section should stand on its own, with no historical
survey, account of its development or references to temporary plans.

### 2. Check what the guidance elicits

Use the draft to prepare short proposals for a small settled repair, a repair
with a known reproduction across a component boundary, and a capability with an
unresolved feasibility premise. Supply the necessary context and vary the
problems from the section's example. These are writing exercises, not requests
to implement changes or conduct product experiments.

Inspect the resulting proposals: can a successor recover the recommendation,
its basis, next actions, real dependencies and acceptance evidence? Does the
small repair stay small? Does the uncertain case specify useful work without
inventing an answer or waiting for routine review? Would completion leave the
necessary contracts and instructions usable after deleting the plan?

Revise guidance that encourages omissions, excess or deferral, then recheck the
affected proposal. Use any available reader feedback, but do not make obtaining
an external reviewer a prerequisite. Distinguish author rehearsal from independent
review; neither word count nor coverage of the six ideas establishes usefulness.
Keep only actionable findings and remaining work in this plan. Replace resolved
discussion with the resulting instructions; exercise drafts and assessment
transcripts need not become part of it or of the published section.

### 3. Integrate and finish

Add one planning link in [AGENTS.md](AGENTS.md)'s quick router to
`CONTRIBUTING.md#planning-a-change`. README already links CONTRIBUTING; no new
standalone document or documentation-index entry is needed. Limit surrounding
edits to transitions or wording required for the section to fit.

Check the section's word count, rendered Markdown and links. Use the existing
`broken_links` helper in
[generators.py](tests/suites/source_drift/generators.py) explicitly on CONTRIBUTING
and AGENTS: CONTRIBUTING is outside its default document scan. Run
`git diff --check` on the changed files. This prose and link change requires no
app build or live test run.

Read the whole CONTRIBUTING document again. The new section should retain the
welcoming tone while making the responsibility for a strong first proposal clear.
Confirm that its instructions support all six ideas without demanding ceremony,
repeated orientation or unnecessary detail.

Complete the work when the section fits the length and purpose, the exercises'
material findings are resolved, and the router and documentation checks pass.
Commit the section and router change, report the checks and the scope of the
writing assessment, and retire this plan without leaving references to it.
