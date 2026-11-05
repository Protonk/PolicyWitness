# Final reader preparation and isolation

Candidate identity is the corrected documentation patch recorded in
`documentation/verification-02.json`, relative to this record directory's
parent. Validation completed before final document exposure. The three source
hashes, image hashes and complete artifact hashes are recorded in
`rendering/artifact-manifest.json`.

## Materials

ARCHITECTURE is a 24-page self-contained vector PDF; WORKER is a 27-page
self-contained vector PDF. LIMITS is complete flat Markdown. Non-visible
generation comments were removed while retaining scalar values. Visible prose,
headings, examples, captions, qualifications, tables and their order remain.
PDF details blocks are expanded so the entire document is available. That
conversion can make reference inventories more prominent than a collapsed
browser view; assess density concerns with this difference in mind.

The four ARCHITECTURE SVGs and the detailed WORKER SVG are embedded. Tall
inventory figures occupy appropriately sized PDF pages and retain vector zoom.
The one WORKER Mermaid diagram was rendered with the recorded Graphviz
translation: all nine nodes, four nested groups, eight directed relationships
and labels were checked against the source. Conversion introduces no new
explanation or annotation. A neutral page number is the only added visible
navigation element.

All 51 PDF pages were inspected as contact sheets; the conceptual diagram and
representative wide tables were also inspected at full raster width. No
out-of-page text boxes, clipped tables or missing diagrams were found.
Extracted visible-token comparison initially named source symbols split by
table wrapping; all were recovered at their full source counts after whitespace
normalization. This supports content preservation alongside visual inspection;
it is not proof that every reader will navigate the layout easily. Internal
heading-link destinations were also checked in the rendered HTML.

Conversion used Pandoc GFM, WeasyPrint 70.0 and Poppler. Supporting libraries
were installed in an isolated temporary environment. The PDF skill marker ran
once before authoring. Renderer warnings about unavailable font-cache write
locations did not prevent rendering; the resulting pages, text and glyphs were
inspected. Scripts and derivatives remain in `rendering/`. The PDFs, rather
than extracted text, own the reading experience; corresponding page images and
text extraction are permitted reading aids.

## Staging

The first three readers started fresh with Astra, no conversation fork and no
prior findings. Coordinator preparation replaces broad repository orientation.
Each received only their bounded onramp and the existing illustrative actor
example, then a consequential task for a need checkpoint, then their artifact
for a <=150-word first impression. Work result and whole-document account were
captured before targeted questions. Individual transcripts retain tasks,
materials actually read and responses; no target-source or outside links may
be followed.

Onramp teaches actor/setup vocabulary, schedule and reference reading. It does
not supply numeric capacities, timing or failure semantics, implementation or
authority protocol. The WORKER reader reasoned generally about pre-opened
descriptors and revocation before seeing its document; those principles are
not credited as newly taught by the target. The source state, intended
familiarity and overlap are in the artifact manifest.

`COORDINATOR-TAKEAWAYS.md` was written before any reader response and is withheld
from both reader roles. Skeptical assessors receive only their artifact,
first-reader report and full task/intervention transcript. They assess the
report in either direction; they do not count as independent first impressions.
Neither role receives earlier investigation conclusions or intended answers.
