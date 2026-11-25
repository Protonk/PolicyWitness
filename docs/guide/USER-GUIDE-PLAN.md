# Guide work after 0.3.8

Use the guide's seven worked cases for the next reader's pass. The extension case starts from `example extension` and moves the file grant between readers. Runner help should let a reader decide what to keep after removal. The release plan stages both in 0.3.9 and the `guide` command in the 0.4.0 transition. [Worked cases](README.md#worked-cases) · [Release staging](../../CLI-TRANSITION-PLAN.md)

## Deliver one authored guide

Keep [PolicyWitness.md](../PolicyWitness.md) as the Markdown people read on the web,
download with the release and retrieve from the app. Give each of the five main
verbs one level-two heading consisting of its literal name, such as `## run`.
Within it, keep headings like “Why couldn't my app open this file?” and give
the author room to choose the questions and their order. The introduction and
the release stamp table can stand outside the verb sections. Keep internal
links to setup that several cases share. Preserve used anchors when regrouping
the stories, or repair the links at their owners.

Bare `guide` writes the entire document byte for byte. `guide <verb>` writes
the bytes from the start of that verb's heading up to the next heading of
level two or higher, or the end of the document. This includes the selected
heading, its subheadings, examples and original spacing. Have the build
locate the five unique headings with the repository Markdown reader and
retain their byte ranges. Missing or duplicate sections refuse the build.
A heading inside a fenced specimen is content. Use the verb declarations
for topic selection. Give an unknown topic or an extra argument a usage
diagnostic, empty stdout and exit 2. List the five choices in `help guide`.

Package the checked guide as a resource before sealing the app. Use the same
source bytes for section ranges, the signed publication receipt and the
standalone staged file. Include the resource and range inputs in build and
release verification. Preserve the guide's existing generated scalar spans
and stamp table. All explanations, including the selected passages, come
directly from the author's document. [Publication binding](../publication.py) · [Build and release checks](../SIGNING.md#release-procedure)

On the extracted release app, compare bare stdout with the tagged document
and staged release asset, including the final newline. Verify the digest and
build contract against the signed receipt. Compare each topic, including
`guide guide`, with an independently delimited slice of those bytes. Check
the adjacent heading, end of the last section, a heading-like line inside a
fence, and invalid topics and tails. Exercise delivery away from the checkout
and sidecar with no usable runner, registry, specimen or network. Check that
a failed write or flush reports failure. Publication read-back checks the
downloadable asset.

## Review the teaching

Run the worked blocks in order with the staged release and independently
prepared fixtures. Use the case table to check the asserted relationships
and the existing workflow controls for the operations they actually exercise.
Then give a reader a *nearby* question without its answer. For example, after
the absent/present failed-open lesson, give them a result in which the query
and attempted open name different files. Can they identify the file the
worker tried, say what the prediction covers and choose a control before
attributing the failure? Record their conclusion or next action and what
justifies it. Revise the passage, the example or the interface where the
reader needed an observation or choice they could not obtain. [Case table](README.md#worked-cases) · [Guide review procedure](../AGENTS.md#editing-the-guides-worked-cases)

## Ways to make progress

- **Press on an instruction.** Pick a choice the caller has to make. Try simplifying the instruction against two cases the reader still needs to distinguish. For instance, can an author check a repair to the exact specimen before authorizing its file effects? [User responsibilities](../REQUIREMENTS.md) · [Admission investigation](../../runner/Sources/ADMISSION-CHECK-PLAN.md)
- **Read a saved run as its recipient.** Give a reader the symptom and one envelope. Before showing the fixture notes or a second run, ask which explanations the worker's observation resolves and which need another observation. For a proposed field, identify who could observe it, when, and how it would change the reader's decision. [Failed-open passage](../PolicyWitness.md#why-couldnt-my-app-open-this-file) · [Four file-open trials and fixture account](../../tests/atlas/COMPARE-PLAN.md#fixture-account)
- **Try the lesson with the shipped app.** Start from what the build prints, edit the field that carries the lesson, and compare the results with independently prepared fixtures. Give build-specific lookups to the executable where it can answer them. Update the case table and rerun the guide when changing a worked case. [Guide editing rules](../AGENTS.md#editing-the-guides-worked-cases)

## Paired inputs

These original specimens come from direct runs of development build 1634 (`e7937ecc`) with the built-in runner on macOS build 25G241. Their contracts and absolute scratch paths belong to those trials. To repeat a pair, review both requests against the selected build, set its contract in working copies and replace every occurrence of the scratch target, including policy literals. Keep the original inputs intact. [Request admission](../REQUEST.md)

- **Move the grant.** Both readers use the same policy and sample the same file before and after consumption. The unapplied issuer transfers to Alice in one input and Bob in the other. Prepare a file with known bytes and compare the recipient's fresh read with the other reader's. Transfer equality answers the separate question of delivery. Use the pair to choose the edits for the extension passage. [Alice receives](experiment-inputs/ab_Alice.json) · [Bob receives](experiment-inputs/ab_Bob.json)
- **Move the queries in time.** Start with a fresh absent name for each trial. Create, read, unlink, read, create and read the same name in one worker. Grouping all six actions into one plan or putting each in its own phase changes when a path query is possible. Read the query and the worker result separately after creation and after removal. This pair is available to challenge a simplification that changes what the caller can ask. [One plan](experiment-inputs/spec_single.json) · [Six phases](experiment-inputs/spec_phases.json)
