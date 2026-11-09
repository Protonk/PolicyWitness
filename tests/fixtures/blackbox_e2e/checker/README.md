# Evidence checker fixtures

`current/constructed_run.json` is an authored ordinary current-contract model
with hypothetical process identities, copied carrier structure and unavailable
artifact verification. It supports checker and comparison interpretation controls;
it is not a live capture or signed-candidate result. Missing-path controls are
authored by `constructed_missing_path_baseline()` in the menagerie control file.
Its embedded host bytes are authored JSON, admitted only by the controls'
explicit fixture option; current production transport uses binary records.

The `response25/` and earlier directories contain unmodified historical live
captures and their exact submitted requests. Current readers refuse their versions.
Their build stamps, hashes and source identities describe only those producers.
No historical capture is upgraded by editing its version or signing evidence.

Current live evidence belongs to the selected BBX-001/002 and witness workload
run directories. Refresh a retained live fixture by copying the complete envelope
and exact submitted request from a verified candidate case, retaining its run
through the test evidence helpers. Do not replace constructed control scope with
native credit merely because its shape is accepted.
