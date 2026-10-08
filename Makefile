# Operator entry points for PolicyWitness. This file is a thin layer over
# build.sh, tests/run.sh and the Python helpers under tests/lib/. No build or
# release logic lives here: read those for mechanism and this file for sequence.
# The procedure and its evidence format are described in docs/SIGNING.md; test
# output ownership and retention in tests/README.md.
#
# Targets
#   build     Compile, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app.
#   test      Run the default battery into tests/out/runs/default.
#   clean     Prune completed, owned, unretained test runs. Nothing else.
#   notarize  The rehearsable lower-level chain: preflight report, build, submit,
#             staple, validate, Gatekeeper, re-zip, accept the final ZIP.
#   release   The whole procedure: strict preflight, notarize, battery, archive,
#             rotate older test output. Spends one notarization submission.
#   publish   Push the tag and create the GitHub release from an archive.
#
# Variables (set on the command line, e.g. make release NOTARY_KEYCHAIN_PROFILE=...)
#   IDENTITY                 Developer ID Application identity in your keychain;
#                            build.sh refuses any other class and selects nothing.
#   NOTARY_KEYCHAIN_PROFILE  notarytool keychain profile; notarize and release need it.
#   DIST_DIR                 Where the app, ZIP, guide, evidence/ and archive/ land.
#   RELEASE_NOTES            Notes file. release archives it as evidence/release-notes.md;
#                            publish uses it in place of the archived copy.
#   VERSION                  Which archived release publish acts on. Only publish reads
#                            it; release derives the version from the annotated tag.
#
# Conventions
#   Every target is phony; make tracks no outputs here.
#   /usr/bin/python3 -B is deliberate: the system interpreter, writing no bytecode.
#   Multi-line recipes run under one `set -eu` shell so $$release_evidence, $$version
#   and $$battery survive across lines and the first failure stops the chain.
#   release calls notarize, and notarize calls build, through $(MAKE) rather than
#   prerequisites so each target's guards and preflight run before anything builds.
#   $(if $(RELEASE_NOTES),...) passes --notes only when notes were given.
#
# Boundaries
#   Acceptance, the battery, archiving and rotation each hold tests/.checkout.lock;
#   run no other battery during make release.
#   Nothing leaves the machine except the notarization submission. publish is the
#   only outward target.
.PHONY: build clean test notarize release publish

# Defaults. The header says what each one means; IDENTITY has no default.
NOTARY_KEYCHAIN_PROFILE ?=
DIST_DIR ?= dist
RELEASE_NOTES ?=
VERSION ?=

# build: one path through build.sh, which compiles (Cargo for the Rust pieces,
# Meson for the native executables), signs every embedded tool and embeds the
# generated evidence. The guard mirrors build.sh's own identity
# requirement so the message names the make invocation to use.
build:
	@if [ -z "$(IDENTITY)" ]; then \
		echo "ERROR: set IDENTITY to your Developer ID Application identity"; \
		echo "example: make build IDENTITY='Developer ID Application: ...'"; \
		exit 2; \
	fi
	@echo "==> [build] build, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app"
	DIST_DIR="$(DIST_DIR)" IDENTITY="$(IDENTITY)" ./build.sh

# clean: not rm -rf. It delegates to the pruner, which removes only completed,
# owned, unretained direct children of tests/out/runs/ and keeps release
# acceptance, retained and unfinished output. dist/ and .tmp/ are untouched.
# Older runs are otherwise retired only when a release is packaged (see release).
# The phase line goes to stderr: stdout is the pruner's JSON report, which the
# dispatcher retention control reads back.
clean:
	@echo "==> [clean] prune completed, owned, unretained runs under tests/out/runs" >&2
	@./tests/run.sh --prune --apply

# test: the default battery against the built app, into tests/out/runs/default.
# For separate evidence run tests/run.sh directly with PW_TEST_OUT_DIR set.
test:
	@echo "==> [test] run the default battery"
	@./tests/run.sh

# notarize: the lower-level chain, usable on its own as a rehearsal. The preflight
# runs in --report mode, so its findings are warnings and a rehearsal still
# records the stamp it notarized. It builds again on purpose: what this chain
# submits, staples and accepts must come from the tree the preflight just
# inspected, not from an earlier build. release_evidence.py opens the attempt
# directory; every later step runs through release_commands.py with a 60 s bound
# and leaves a receipt there. The pre-staple ZIP is removed before re-zip so
# acceptance can only ever see the stapled artifact, and the last step tests
# that actual ZIP.
notarize:
	@if [ -z "$(NOTARY_KEYCHAIN_PROFILE)" ]; then \
		echo "ERROR: set NOTARY_KEYCHAIN_PROFILE to your notarytool keychain profile name"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: ...'"; \
		exit 2; \
	fi
	@if [ -z "$(IDENTITY)" ]; then \
		echo "ERROR: set IDENTITY to your Developer ID Application identity"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: ...'"; \
		exit 2; \
	fi
	@echo "==> [notarize] preflight report for $(DIST_DIR)"
	@/usr/bin/python3 -B tests/lib/release_preflight.py --report --dist "$(DIST_DIR)"
	@$(MAKE) build
# One shell from here: the attempt directory path must reach every step.
	@set -eu; \
	  release_evidence="$$(/usr/bin/python3 -B tests/lib/release_evidence.py "$(DIST_DIR)/PolicyWitness.zip")"; \
	  echo "==> [notarize] submit $(DIST_DIR)/PolicyWitness.zip and wait once -> $$release_evidence"; \
	  /usr/bin/python3 -B notarize.py "$(DIST_DIR)/PolicyWitness.zip" "$(NOTARY_KEYCHAIN_PROFILE)" --evidence-dir "$$release_evidence"; \
	  echo "==> [notarize] staple, validate and assess $(DIST_DIR)/PolicyWitness.app"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step staple "$$release_evidence" 60 /usr/bin/xcrun stapler staple "$(DIST_DIR)/PolicyWitness.app"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step staple-validation "$$release_evidence" 60 /usr/bin/xcrun stapler validate -v "$(DIST_DIR)/PolicyWitness.app"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step gatekeeper "$$release_evidence" 60 /usr/sbin/spctl -a -vv --type execute "$(DIST_DIR)/PolicyWitness.app"; \
	  echo "==> [notarize] re-zip the stapled app and accept the final ZIP"; \
	  rm -f "$(DIST_DIR)/PolicyWitness.zip"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step re-zip "$$release_evidence" 60 /usr/bin/ditto -c -k --sequesterRsrc --keepParent "$(DIST_DIR)/PolicyWitness.app" "$(DIST_DIR)/PolicyWitness.zip"; \
	  bash tests/accept-release.sh "$(DIST_DIR)/PolicyWitness.zip" --evidence-dir "$$release_evidence"

# release: the whole procedure, in order. The strict preflight comes first so a
# dirty, untagged or already-archived tree stops here, before any build or
# notarization submission; its success report is discarded because notarize
# prints the same stamp moments later. The version comes from the annotated tag
# the preflight verified, never from VERSION. The battery runs against the
# stapled app into its own run directory; release_archive.py stages and verifies
# the archive and retains both runs; release_rotate.py then retires older
# working test output. A rotation failure leaves the release complete: resume
# with `python3 -B tests/lib/release_rotate.py $(DIST_DIR)/archive/v<version> --apply`.
# Commit the tests/RETAINED.json change afterwards either way.
release:
	@if [ -z "$(NOTARY_KEYCHAIN_PROFILE)" ]; then \
		echo "ERROR: set NOTARY_KEYCHAIN_PROFILE to your notarytool keychain profile name"; \
		echo "example: make release NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: ...' RELEASE_NOTES=notes.md"; \
		exit 2; \
	fi
# Stop before anything builds or is submitted; notarize prints the report again.
	@echo "==> [release] strict preflight for $(DIST_DIR)"
	@/usr/bin/python3 -B tests/lib/release_preflight.py --dist "$(DIST_DIR)" >/dev/null
	@$(MAKE) notarize
# One shell from here: the version and battery path must reach every step.
	@set -eu; \
	  version="$$(/usr/bin/python3 -B tests/lib/release_preflight.py --dist "$(DIST_DIR)" --format version)"; \
	  battery="tests/out/runs/release-$$version-default"; \
	  echo "==> [release] default battery against $(DIST_DIR)/PolicyWitness.app -> $$battery"; \
	  PW_APP_DIR="$(DIST_DIR)/PolicyWitness.app" PW_TEST_OUT_DIR="$$battery" ./tests/run.sh; \
	  echo "==> [release] archive $(DIST_DIR)/archive/v$$version"; \
	  /usr/bin/python3 -B tests/lib/release_archive.py --latest --dist "$(DIST_DIR)" --battery "$$battery" \
	    $(if $(RELEASE_NOTES),--notes "$(RELEASE_NOTES)",); \
	  echo "==> [release] clean up older working test output"; \
	  /usr/bin/python3 -B tests/lib/release_rotate.py "$(DIST_DIR)/archive/v$$version" --apply

# publish: the only outward step. release_publish.py verifies the archive,
# including its portable test evidence, pushes the tag if the remote lacks it,
# creates the GitHub release once with the tag verified, downloads every asset
# back and records origin only when bytes and digests match. Running it again
# verifies the existing release and creates nothing. Needs an authenticated gh.
publish:
	@if [ -z "$(VERSION)" ]; then \
		echo "ERROR: set VERSION to the archived release version"; \
		echo "example: make publish VERSION=0.2.4"; \
		exit 2; \
	fi
	@echo "==> [publish] verify and publish $(DIST_DIR)/archive/v$(VERSION)"
	@/usr/bin/python3 -B tests/lib/release_publish.py "$(DIST_DIR)/archive/v$(VERSION)" \
	  $(if $(RELEASE_NOTES),--notes "$(RELEASE_NOTES)",)
