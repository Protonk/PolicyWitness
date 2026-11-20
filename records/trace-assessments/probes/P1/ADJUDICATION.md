# P1 adjudication: envelope interpretation

**Run.** Workflow `wf_c2f2cf78-611`, 2026-11-20, at `2bcdfeb8`. Four readers
ran as `Explore` agents: three Sonnet and one Opus control. Every reader
reported opening only `inputs/` and `docs/RESPONSE.md`. `Explore` agents do
not receive the repository's `CLAUDE.md`, whose core ideas state several of
the interpretations under test. Raw answers are in `answers.json`; the key
is in `KEY.md`.

## Result

On every (b) question, all four readers gave the key's answer. Sonnet did not
differ from Opus on any of them. The interpretations most open to over-reading
were each read with their stated limit, and each reader cited the governing
`RESPONSE.md` sentence:

| Envelope | Question | Limit every reader kept |
| --- | --- | --- |
| E1 | Sandbox cause | An EPERM-shaped failure is a failure class, not a cause. |
| E1, E5 | `query_first` | An ordering claim, not agreement or causation. |
| E1, E5 | Deny or allow beside the attempt | The two channels are separate; no agreement claim. |
| E2 | `validator_unavailable` | The attempts remain reported. |
| E3 | Fallback `policy_check: ok` | An independent compilation, not worker progress. |
| E3 | Lost reply | Whether anything ran stays unestablished. |
| E4 | `text_exact: false` | The text is a lossy rendering, and nothing was truncated. |
| E6 | `captured` | Neither the enforced bytes nor imported files are identified. |
| E7 | `unavailable` | It does not say whether the copy was made. |
| E7 | Signal 9 | No host kill was recorded; the cause is `unknown`. |
| E8 | Requested hang control | Not shown to have taken effect. |
| E9 | `cleanup_trigger: completion` | Restates the scheduler's `schedule_complete`; the actor did not end cleanly. |
| E10 | `inapplicable_field` | Applicability, not the value. |

The (c) answers named valid non-conclusions in every case. Several are not
in the key and the coordinator confirms them:

- E1: `result.ok: true` and exit 0 do not mean the read succeeded.
- E5: `open_read` with no content does not show the file was read.
- E6: the created file need not still exist.
- E10: the refusal came from host admission, not from the controller
  locally.

## Leads and verdicts

**L1, Pass 4 entry.** The `test_overrides` echo states no limit. Its
definition in `30-reply.surface.md` (rendered in `RESPONSE.md` `:397`) says
it is "Accepted instrumentation echoed by orchestration … It identifies the
selected execution configuration." It does not say that the echo records
supplied controls and does not establish that any control took effect.
`runner/AGENTS.md` ("Reading control evidence") and the acceptance plan's
seam comparison hold that limit. One Sonnet reader looked for the controls'
meaning in `RESPONSE.md` and did not find it.

No reader over-read the echo in E8, but nothing in the definition stops a
reader from doing so. Add the limit to the owner, stated as current
behavior: the echo is built from the admitted request's controls, whether or
not a later boundary ran.

**No action.** Query `rc` (`RESPONSE.md` `:975`) already says the host
supplies 0 with an error outcome when there is no associated verdict. A
Sonnet reader cited it correctly in E2.

## Destinations

- Pass 4 entries: L1.
- User-duty draft: none. P1 found no misreading that would create or support
  a user duty.
- Guide-rewrite note: none.
