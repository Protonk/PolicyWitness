# Complete actor example control

`constructed_actor_run.json` is an authored hypothetical run envelope for
`witness_contract/example_round_trip_controls`, read by
`example_form_controls.py`. It describes one applied `selected` actor, two
visits with a 2+1 action partition, and the three example roles. It supplies
full setup, equipment, application, collection, worker disposition, reap,
controller dossier and diagnostic records. There is no termination dependency,
extension operation or authority-region requirement.

The file is identity-free. The control binds its explicit test producer and
transport context with `blackbox.bind_constructed_envelope`, then updates the
JSON host carrier with `recapture_host_reply`. Only the consumer's existing
`allow_fixture_json` option admits that constructed carrier. The entire
envelope must pass the consumer and each case expectation before mutations
are tested; it is never projected into an ordinary reply.

The action and ordinary lifecycle syntax reuse the existing authored
`blackbox_e2e/checker/current/constructed_run.json` model and the scalar
example control's fresh-read model. Actor process numbers (51000/51001),
validator numbers, equipment hashes, paths, timestamps, application and setup
observations are authored values, not captured native observations. Target
samples come from the independent scalar control's `CONTENT` and `IDENTITY`
tables. No live capture or production classifier generated expected results.

Maintain this fixture by editing the hypothetical observations deliberately,
keeping all dependent ownership and carrier fields coherent, and running
`tests/run.sh --case witness_contract/example_round_trip_controls`. The case
never refreshes the file or downloads replacement material. It establishes
reader sensitivity, not native execution or signature verification.
