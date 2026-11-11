# Corrected stage-four guide attempt: copy-inventory failure

The completed guide case remains failed. It reached the displayed `cp -R` with
exit 0, then failed at workflow line 475 because the copied bundle's inventory
was compared for exact equality with the source inventory. The source of the
comparison includes full `st_mode`, regular-file SHA256 and symlink target,
keyed by relative path; it excludes inode/timestamps. The local macOS `cp(1)`
manual states that new regular-file permissions are modified by umask and that
`-R` directory permissions are preserved. The guide deliberately sets umask 077.
This supports repairing the harness's mode expectation. The failed destination
inventory was not retained, so the precise observed difference in this attempt
remains unknown. A successful copy command alone does not establish equal bytes.

Canonical `20261111T181408Z_78d9824e` completed 13/13 cases, 12 pass and this one
failure, no skipped/unrun cases, zero sleep in this guide case, valid/unchanged
app. Root owns whole-run accounting. The source/staged/retained guide all hash to
`31944ef9cd04d131e1cf2314ba1bb3e0f67322a4f58a5a828bcb08136f3fa3a4`.
Build is 1337, commit `5c1c63dc7bbcf07188f83924be1367423ea188b3`, dirty describe,
contract `development:84448fb421a5a0e4acdbce236dae143e04df6d425c7a258c12df447e9b762444`,
worker identity `52bbda618677886b6c59dcf5dd999e2b2a5021cbd2c8dc4f08aa0ba66ef2dd38`.

Eight full source fences and the setup/copy prefix of a ninth were executed as
19 source fragments, plus the existing-target guard: 20 shell captures. Their
bytes reconstruct the retained guide portions with only APP/IDENTITY/ENT setup
substitutions. Every captured shell fragment returned 0 without timeout. The
refusal invocations separately retain their intended native exit 1.

The four submitted request hashes agree with durable invocation entries and
retained work-record hashes. The spelling correction and added nonce each change
exactly their intended policy field. Ordinary worker 27314 created an initially
absent regular empty mode-0600 file (inode 198618602); capture worker 27354 did so
for a different target (inode 198618709). Both were reaped with exit 0. Their
actual queries are synthetic `prediction_unavailable`/`query_not_requested`,
null native result, and path-unresolved planning diagnostics. Comparisons retain
succeeded/completed_worker_status, unestablished order, unresolved operation
relation, same_submitted target relation and the path-planning limitation.

The two refusals are exact `unknown_field` at
`policy.capture_compiled_profiel` and `invalid_capture_nonce` at
`policy.capture_nonce`, with empty steps/phases, no worker subprocess and absent
targets. All four client captures are accepted, granted once, invoked and end in
runner_reply, with client exit 0 and no delivery/truncation/parse errors. The host
refusals happened after interface invocation and before worker launch.

Positive capture binds worker 27354, nonce
`7925f4ed8b6b595fe498040434283c63`, source length 27/SHA
`c3f48dc83eca4ac705acbf9094416e239dda782b96cab885e8f7151c653474b3`,
parameter count 0, and 492 decoded bytes/SHA
`b2056ef25b6c4e72bcd45bb018452bde93d05afcbdb9813fee8698551cf397e0`.
Direct helper compilation passed and both preexisting effects retain unchanged
file observations. Guard bytes/mtimes/effect observations were preserved.

The corrected `runner_registry` and reconcile outputs passed the initial empty
installed/pending prerequisite. Independent selected-worker entitlement readback
returned an empty dictionary. The workflow armed exact stage ownership before
copy; rename, signing, install, status, verify, service-selected run, validate
and removal remained unreached. The nested receipt has install_attempted=false,
install_finished=false, removed=true, no cleanup error. Outer ownership has
cleanup_verified=true, removed=true, no uncertain command/error. The stage and
work paths are absent at audit; the recorded plist is absent. Original source
inventories before/after match. The four cleanup witnesses are the two worker
reaps and two exact admission refusals. These receipts establish cleanup of an
uninstalled staged copy; no native installed-service cleanup is credited here.

All ten constructed ownership groups completed before the native sequence;
six fake-command receipts retain 19 calls. Their real file effects, rejected
foreign owners, uncertainty retention, individual absence failures and recovery
remain scoped to constructed command/OS inputs. Disposition controls explicitly
inject consumer admission. They establish no native interruption occurrence.

The private `guide-copy-mode.patch` changes only the test owner. It records source
and copied inventories, differences and source aliases; requires exact paths,
file types, hashes/link targets; preserves the no-hardlink check; masks only
regular-file mode by 077 and retains other modes exactly. Three small controls
construct a 0755-to-0700 copy, then reject changed bytes and a missing owner
execute bit. Candidate source SHA is
`9cefe93310f0699923274d54e4a4c6265506d04a6204ec8e9a74058f304c037d`;
patch SHA is `b0fd9e7b06f25d236fa211ad7561ce97c0aea04ec8e8e00d6783cca289e41ae9`.
Only AST parsing was performed by this auditor; root owns applying and executing
the replacement. The guide command remains unchanged.

I reused the already reviewed unchanged ownership/cleanup/control source and
read the corrected three literals, current retained commands/results, inventory
implementation and local cp manual. Mechanical inspection recomputed request,
profile and fragment identities and hashed 175 source/artifact inputs. Exact
sources and hashes are in source-artifact-manifest.json; detailed compact values
are in observations.json. No product modules were imported, no app/test/build
commands or resource cleanup were run, and no shared file was edited. The
original failed audit remains untouched. Original tests/out and private files
are local/gitignored and follow ordinary retention. The complete later guide
run requires a separate audit and receipt.
