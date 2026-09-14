# runner_filter_iokit_user_client_class

Exercises `(iokit-open-user-client, iokit_user_client_class)` with a policy denying
`IOSurfaceRootUserClient`. The response must contain exactly the requested `iosurfaceroot_uc`
step and report `prediction_unavailable` for that operation.

The suite uses the [shared filter contract](../runner_filter_sysctl_name/README.md#shared-filter-contract):
a successful run envelope, explicit nullable evidence, integer prediction
`rc=-1`, null `filter_type_id`, null prediction `errno`, and null `drift`.
The paired file `open_read` of `/etc/hosts` must report a supported outcome
(`ok` or `open_failed`) and an integer `attempt.rc` agreeing with `exit_code`.
The checker continues attempt validation even when prediction evidence is broken.

The file attempt is a placeholder. It exercises supported attempt reporting and
does not establish IOKit enforcement. The suite does not require the file open
to succeed or assert internal prediction dispatch behavior.

## Fixtures and artifacts

`run.sh` generates the specimen inline. Artifacts under
`tests/out/suites/runner_filter_iokit_user_client_class/<test_id>/artifacts/`
retain the specimen, raw `run.json`, `pw.stderr`, and assertion log.
Independent checker controls for all three filter callers run in
`runner_filter_sysctl_name`, including valid file failures and rejection of
unsupported or missing attempt evidence alongside unavailable predictions.

```sh
./tests/run.sh --suite runner_filter_iokit_user_client_class
```
