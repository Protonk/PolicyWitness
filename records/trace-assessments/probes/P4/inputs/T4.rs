        fn compiled_profile_status_and_labels_alone_decide_run_admission() {
            // The receipt corpus through production orchestration with a
            // supplied client result: two admitted rows and seventeen refused.
            // Reply admission reads a receipt's status and its two labels and
            // nothing else; nine refused rows are refused there, with the
            // decoded reply retained. The other eight carry a non-string or
            // absent status or label, and this test's typed JSON reader
            // refuses them first, as host bytes that supply no typed record.
            // The admitted `captured` row deliberately disagrees with the
            // request, which asks for no capture: its nonce, source and
            // parameter fields correspond to nothing submitted here, and
            // admission compares none of them.
            let root = scratch("profile-label-outcomes");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            let request = request_file(&root, None);
            let args = [request.to_str().unwrap()];
            let cases: Value = serde_json::from_str(include_str!(
                "../../tests/fixtures/contract/compiled_profile.json"
            ))
            .unwrap();
            let (mut admitted, mut by_admission, mut by_reader) = (Vec::new(), 0, 0);
            for case in cases.as_array().unwrap() {
                let mut reply = worker("finished", None);
                reply["compiled_profile"] = case["receipt"].clone();
                let retained = serde_json::from_value::<PWRunnerRunResult>(reply.clone()).ok();
                let observed = observe_reply(&app, None, &args, reply);
                let (wire, exit_code) = envelope_of(&observed.output);
                let valid = case["valid"].as_bool().unwrap();
                let label = case["name"].as_str().unwrap();
                assert_eq!(observed.calls.len(), 1, "{label}");
                assert!(!observed.calls[0].request.contains("capture"), "{label}");
                assert!(observed.helper_inputs.is_empty(), "{label}");
                assert_eq!(exit_code, if valid { 0 } else { 1 }, "{label}");
                assert_eq!(wire["result"]["exit_code"], exit_code, "{label}");
                assert_eq!(wire["result"]["ok"], valid, "{label}");
                assert_eq!(
                    wire["result"]["normalized_outcome"],
                    if valid {
                        "finished"
                    } else {
                        "malformed_runner_response"
                    },
                    "{label}"
                );
                assert_eq!(
                    serde_json::from_value::<Option<PWRunnerRunResult>>(
                        wire["data"]["runner_result"].clone()
                    )
                    .unwrap(),
                    retained,
                    "{label}: structurally decoded reports remain available"
                );
                assert_eq!(
                    wire["data"].get("policy_check"),
                    Some(&Value::Null),
                    "{label}"
                );
                let diagnostics = wire["data"]
                    .get("runner_sandbox_diagnostics")
                    .unwrap_or_else(|| panic!("{label}: the diagnostics key is absent"));
                let reply_error = &wire["data"]["runner_client"]["runner_reply_error"];
                if valid {
                    assert!(diagnostics.is_object(), "{label}");
                    assert!(wire["result"]["error"].is_null(), "{label}");
                    admitted.push(label);
                } else if retained.is_some() {
                    // Refused by reply admission: a decoded reply, the
                    // admission diagnostic and an explicit null diagnostics.
                    assert_eq!(*diagnostics, Value::Null, "{label}");
                    assert!(reply_error.is_null(), "{label}");
                    assert_eq!(
                        wire["result"]["error"],
                        if label == "status_future" {
                            "unsupported or malformed compiled_profile"
                        } else {
                            "compiled_profile context is inconsistent"
                        },
                        "{label}"
                    );
                    by_admission += 1;
                } else {
                    // Refused by this test's typed reader: no decoded reply.
                    assert_eq!(*diagnostics, Value::Null, "{label}");
                    assert_eq!(
                        wire["data"].get("runner_result"),
                        Some(&Value::Null),
                        "{label}"
                    );
                    assert!(reply_error.is_string(), "{label}");
                    assert_eq!(wire["result"]["error"], *reply_error, "{label}");
                    by_reader += 1;
                }
            }
            assert_eq!(admitted, ["captured", "unavailable"]);
            assert_eq!((by_admission, by_reader), (9, 8));
            fs::remove_dir_all(&root).unwrap();
        }
