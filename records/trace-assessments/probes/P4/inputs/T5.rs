        fn capture_for(input: &str, status: &str) -> PolicyCheckCapture {
            PolicyCheckCapture {
                status: status.into(),
                tool_exit_code: if status == "ok" { 0 } else { 1 },
                output: crate::utils::TextOutputCapture::unavailable(
                    String::new(),
                    crate::utils::HELPER_CAPTURE_BYTES,
                ),
                envelope: Some(json!({
                    "build": {"contract": json_contract::BUILD_CONTRACT},
                    "kind": "sbpl_check",
                    "result": {"normalized_outcome": status},
                    "data": {"controlled_input_sha256": crate::digest::sha256_hex(input)},
                })),
            }
        }

        fn wire_capture(capture: PolicyCheckCapture) -> Value {
            serde_json::to_value(capture).unwrap()
        }

        fn run_held(
            app: &Path,
            path: &Path,
            capture: (RunnerClientRun, Option<PWRunnerRunResult>),
            answer: &dyn Fn(&str) -> Result<PolicyCheckCapture, String>,
        ) -> Held {
            let pending = RefCell::new(Some(capture));
            let client_inputs = RefCell::new(Vec::new());
            let helper_inputs = RefCell::new(Vec::new());
            let client =
                |_: &str, held: &str, _: u64, _: &RunnerConnectionKind, _: Option<&str>| {
                    client_inputs.borrow_mut().push(held.to_owned());
                    write(path, REPLACEMENT);
                    Ok(pending.borrow_mut().take().expect("one client invocation"))
                };
            let helper = |input: &str| {
                helper_inputs.borrow_mut().push(input.to_owned());
                answer(input)
            };
            let deps = RunDependencies {
                app_root: &|| Ok(app.to_path_buf()),
                load_manifest: &evidence::load_manifest,
                registry_path: None,
                client: &client,
                policy_check: &helper,
            };
            let output = run(&[path.as_os_str().to_owned()], Form::Run, &deps).unwrap();
            assert_eq!(fs::read(path).unwrap(), REPLACEMENT);
            let (wire, exit_code) = envelope_of(&output);
            Held {
                client_inputs: client_inputs.into_inner(),
                helper_inputs: helper_inputs.into_inner(),
                wire,
                exit_code,
            }
        }

        fn ordinary_fallback_receives_the_held_request_after_the_file_is_replaced() {
            // The ordinary form through production orchestration with client
            // and helper callbacks. The request file is replaced inside the
            // client callback, before any helper call. This compares what the
            // controller hands the helper with what it handed the client; it
            // does not show that the shipped client reaches this capture or
            // that the shipped helper compiles this input.
            let root = scratch("ordinary-fallback-held");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            write(
                &app.join("Contents/Resources/Augments/read_control.sb"),
                b"(deny file-read-data)",
            );
            let request = json!({
                "contract": json_contract::BUILD_CONTRACT,
                "specimen_id": "ordinary-fallback", "runner": {"mode": "standard"},
                "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)",
                    "augments": ["read_control"]},
                "probe_plan": [],
            });
            // Authored independently of the resolver and of the delivered
            // request: the selector removed and the augment spliced.
            let expected = json!({
                "contract": json_contract::BUILD_CONTRACT, "specimen_id": "ordinary-fallback",
                "policy": {"format": "sbpl",
                    "sbpl_source": "(version 1) (allow default)\n(deny file-read-data)"},
                "probe_plan": [],
            });
            let path = root.join("request.json");
            let answer = |input: &str| -> Result<PolicyCheckCapture, String> {
                Ok(capture_for(input, "ok"))
            };

            write(&path, request.to_string().as_bytes());
            let held = run_held(&app, &path, (client_run(None), None), &answer);
            let (wire, inputs) = (&held.wire, &held.client_inputs);
            assert_eq!(inputs.len(), 1, "one client invocation");
            assert_eq!(serde_json::from_str::<Value>(&inputs[0]).unwrap(), expected);
            // The helper is given the client's input, byte for byte.
            assert!(!held.helper_inputs.is_empty());
            for input in &held.helper_inputs {
                assert_eq!(input.as_bytes(), inputs[0].as_bytes());
            }
            // The envelope's capture is the one returned for that input.
            assert_eq!(
                wire["data"].get("policy_check"),
                Some(&wire_capture(capture_for(&inputs[0], "ok")))
            );
            assert!(wire["data"].get("actor_policy_checks").is_none());
            assert_eq!(held.exit_code, 1);
            assert_eq!(wire["result"]["normalized_outcome"], "xpc_error");
            for key in ["runner_result", "runner_sandbox_diagnostics"] {
                assert_eq!(wire["data"].get(key), Some(&Value::Null), "{key}");
            }

            // The same request with a delivered host reply: no helper input.
            write(&path, request.to_string().as_bytes());
            let reply = controlled_reply();
            let held = run_held(
                &app,
                &path,
                (client_run(Some(&reply)), Some(fixture_reply(reply.clone()))),
                &answer,
            );
            assert_eq!(held.client_inputs, *inputs);
            assert!(held.helper_inputs.is_empty());
            assert_eq!(held.wire["data"].get("policy_check"), Some(&Value::Null));
            assert_eq!(held.wire["result"]["normalized_outcome"], "finished");
            assert_eq!(held.exit_code, 0);
            fs::remove_dir_all(&root).unwrap();
        }
