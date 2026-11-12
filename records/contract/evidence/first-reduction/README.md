# First-reduction evidence

`reduction-manifest.json.gz` lists what the first contract reduction removed
from the prepared `v0.3.8` account at `b83b2e2e` and where each meaning
remains:

- `sentence_cuts`: 148 entries, each with its node, the removed sentences, any
  replacement, and the retained statement with its node.
- `node_removals`: the 15 removed nodes with their former text, the stage-two
  gap each definition replaced, the node its support now qualifies and the
  sentence or clause moved to that home.
- `owner_context_removals`: the two generic context strings removed from 14
  source-read owners.
- `surfaces`: each surface's canonical hash before and after, its changed and
  removed node counts and whether it changed through its own content.

`readings/` holds the six delegated readings of the generated document, one
per line range. Each is that reader's reading. It includes candidates the
coordinator declined and the look-alikes the reader found distinct; the
account states which candidates were taken and why others stay.

Files use deterministic gzip with an empty header name and zero modification
time. `manifest.json` gives stored and decoded SHA-256 values. Line numbers in
the readings refer to the baseline document. The associated
CONTRACT-STAGING-PLAN.md owns inbound links.
