# Can one bounded read answer a footer question?

Two 65-byte documents shared their first 64 bytes and differed at the last byte. Two successive `read_fresh` attempts returned the same prefix. The experiment needed a helper only to distinguish a newline from `!`. [Saved byte observations under `last_byte`](../../../records/guide/work/evidence/file-repeats/observations.json) · [Current worker read](pw_probe_runner.c)

1. Reuse the pair and add the shorter common prefix and an empty file. Compare today's prefix read, a one-byte read at offset 64, and a one-byte read relative to the end of the opened regular file. Use the known fixture bytes as the independent answer. Which distinctions would each request let the author make?
2. For the end-relative case, record descriptor identity, sampled length, chosen offset, returned count and bytes. Shorten the file between size sampling and reading in a controlled trial. Can a reader distinguish an empty file, a short read after shrinkage and an open failure? Check the current stream read on a FIFO separately. [Fresh-read contract](../../../docs/contract/12-probes.surface.md)

Return the smallest request and observation that answer the footer question under the existing byte cap. Compare their cost with the helper's startup requirements. If the question is whether the importer accepts the file, record what running the importer adds.
