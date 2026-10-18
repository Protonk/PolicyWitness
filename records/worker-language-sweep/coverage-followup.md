# Coverage follow-up

This follow-up compares the coordinator's 243 mechanical candidate cells with the first inventory by **owning `worker_capabilities` item and field**, including exact manifest locations. It does not revise any first classification or use reviewer work. Source revision remains `2d63c983224907b109b4349d216c03471a8b1f0c`.

Of the 243 cells, **231 already have exact owning-manifest references** in the first inventory. Among the remaining 12, this follow-up records **6 omitted limiting occurrences**, **4 positive-context exclusions**, and **2 propositions already covered elsewhere**. The coordinator's initial 13 mismatches included one rendering mismatch: `s22.label` is already N302; the manifest's newline becomes a space in Markdown.

## Six additional occurrences

All six additions are A1 descriptions of actual resource bounds or behavior. They are kept in this separate artifact and do not change the first totals. They are additional occurrences, not necessarily new unique semantic families.

| Follow-up ID | Manifest item / field | WORKER line | Exact clause |
| --- | --- | ---: | --- |
| F001 | s4b / Held across | 78 | Through bounded policy transfer |
| F002 | s12a / Released | 91 | I bounded erase then free; oversized tail caveat |
| F003 | s12b / Acquired by | 92 | I: memcpy on bounded accepted token |
| F004 | s24 / Acquired by | 116 | W: memcpy from bounded shared parameters |
| F005 | s36a / Released | 133 | Wait observation, conditional group kill, bounded nonblocking reap |
| F006 | n4 / Authority | 139 | Read EOF/write discard |

F001, F003 and F004 supply actual lifetime/input bounds. F005 adds the bounded nonblocking reap constraint, which is not stated by the already-collected unconfirmed-reap observations. F006 records the issuer endpoints' EOF/discard behavior under the first inventory's stated apparatus-inclusive boundary. F002 records bounded erasure as actual behavior; its secondary oversized-tail evidence limitation is already the authored B1 N038 and remains unchanged. The weaker granularity choices—bounded-copy descriptions and issuer-apparatus inclusion—retain medium confidence in JSON.

## Remaining flagged cells

| Item / field | Decision | Explanation |
| --- | --- | --- |
| s22 / label | Already covered, N302 | Exact owning value exists; only JSON-newline/Markdown-space rendering differed. |
| s31b / label | Positive context | “Newly created filesystem object, if absent” names the acquired resource and target precondition. N023/N216 already collect create semantics and the existing-target qualification. |
| W34 / label | Positive context | “Successful create-open can create absent file” states a positive capability; `absent` describes the target. Related semantics are N023/N216. |
| n11 / When | Positive context | “After apply outside an attempt” gives protocol placement. N043/N277/N278 already collect the relevant storage and no-child limits. |
| n11 / label | Positive context | The automatic-diagnostics/seam-timespec label names the same resource and placement; it adds no separate negative proposition. |
| x1 / When | Covered proposition | Query collection outside the worker is already N002/N297/N303. |
| x4 / When | Covered proposition | External evidence ownership is already N045; surrounding execution adds positive timing context, not a new causality/completeness guard. |

The JSON records exact WORKER and manifest citations for all 13 flagged decisions, the six addition entries, and a status for all 243 candidate pairs. The mechanical candidate list remains a coverage aid, not proof of semantic completeness.

Static validation passed the six entries and 42 nested quoted references. No runtime or generator execution occurred. Hash checks confirmed both first artifacts unchanged: inventory `c76ea2386a01400bca779aa434f457cb60cde0fd3ba59cf3d2882822390320f4`; report `4060ebfacda513898f1d354c71bf242c9bd565abff6363ab2f078dfcec56e929`.
