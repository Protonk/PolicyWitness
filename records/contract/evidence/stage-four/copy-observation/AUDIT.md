# Third guide attempt: observed directory permissions

Canonical run `20261111T182501Z_840a2a11` completed the one selected guide case as
failed, with zero sleep and a valid/unchanged app. It failed in
`check_guide_copy` line 88 after the displayed copy returned zero. The retained
inventory supplies the evidence missing from the second attempt: all 21 paths
and file types matched, all ten regular files retained their hashes and expected
masked modes, and no source alias was observed. All eleven directories changed
from 0755 to 0700. The first repair incorrectly required unchanged directory
permissions and therefore remained insufficient.

The local `/usr/share/man/man1/cp.1` says recursive directory modes are preserved;
this attempt's recorded copy differs. The historical shell capture did not
record PATH or resolved cp executable. A later read-only lookup in the auditor's
shell resolves `/bin/cp` and finds no other cp among its PATH candidates; that
lookup is not provenance for the historical command. The evidence establishes
the actual mode difference without requiring a universal account of cp behavior.

The guide/staged/snapshot SHA remains
`31944ef9cd04d131e1cf2314ba1bb3e0f67322a4f58a5a828bcb08136f3fa3a4`.
The app remains build1337/source5c1c63dc dirty,
`development:84448fb421a5a0e4acdbce236dae143e04df6d425c7a258c12df447e9b762444`,
worker `52bbda618677886b6c59dcf5dd999e2b2a5021cbd2c8dc4f08aa0ba66ef2dd38`.
The executed workflow preimage SHA is
`9cefe93310f0699923274d54e4a4c6265506d04a6204ec8e9a74058f304c037d`.

Eight whole guide fences and a ninth setup/copy prefix again produced twenty
shell captures including the repeated existing-target guard. Exact source
fragments, all four submitted request hashes, correction relations and source
preservation were rejoined independently. Workers38609 and38645 completed the
ordinary/capture creates, each with an independently observed absent-to-empty
mode0600 file and confirmed reap. The two exact host refusals again have no
worker, steps or phases. Positive capture bytes/nonce/source/PID agree, helper
compilation succeeds with earlier effects unchanged, and both successful query
records remain synthetic prediction_unavailable with unresolved-path planning
limitations. Every admitted client capture is granted/invoked/runner_reply with
no delivery or retained-frame error. These are partial observations from a failed
case; the later external lifecycle was still unreached.

The nested copied stage was durably owned before cp, and install_attempted and
install_finished both remain false. Outer cleanup_verified/removed and nested
removed are true, with no cleanup errors; work and stage are absent. The original
app inventory remains unchanged. This is cleanup of an uninstalled copy. The
four worker disposition witnesses and ten existing constructed ownership groups
completed. New copy-control receipts independently show a passing 0755-directory,
0700-regular-file input, rejection of a changed worker hash, and rejection of
worker mode0600 in place of0700.

The narrow successor `guide-copy-mode-v2.patch` keeps exact copied path/type/hash/
link-target requirements and source-alias rejection. Regular modes remain exactly
source masked by077. A directory may have exactly source mode or exactly source
mode masked by077; both preserve its source owner permissions. Symlink modes stay
exact. Independently specified directory0755 and0700 positive inputs accompany
the retained changed-content and missing-worker-execute negatives. The same-shell
harness prefix records `type -a cp` beside the subsequent native copy capture;
the displayed guide fragment and substitutions stay unchanged. This predicate
expresses coherent contents and usable owner permissions, not a universal cp
permission guarantee.

Successor patch SHA
`e4744b31e613becb33a003cffc304756994385fe67a2a618bcc3aab25b302c78`,
candidate SHA `2316b88e5813c0343c6b115d0a0d8b75e8bbe95bb6b3268cd81581e099ce8858`.
The candidate was AST-parsed privately, with execution owned by root in a new
run. Original failed audit/patch bytes are unchanged. This audit read the exact
new comparison/inventory and copy-control receipts, full failure trace and
canonical terminal fields, plus the earlier reviewed sources and actual repeated
request/result/cleanup receipts. The derived observations and 183-input hash
manifest carry exact joins. No test/build/app commands, product imports, shared
edits or resource cleanup were performed by the auditor. Tests/out and private
paths remain local/gitignored, under ordinary retention.
