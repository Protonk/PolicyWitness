.PHONY: build clean test notarize release publish

NOTARY_KEYCHAIN_PROFILE ?=
YOLO ?=
DIST_DIR ?= dist
RELEASE_NOTES ?=
VERSION ?=

build:
	@if [ -z "$(IDENTITY)" ] && [ -z "$(YOLO)" ]; then \
		echo "ERROR: set IDENTITY or opt-in to auto selection with YOLO=1"; \
		echo "example: make build IDENTITY='Developer ID Application: ...'"; \
		echo "example: make build YOLO=1"; \
		exit 2; \
	fi
	DIST_DIR="$(DIST_DIR)" IDENTITY="$(IDENTITY)" YOLO="$(YOLO)" ./build.sh

clean:
	@./tests/run.sh --prune --apply

test:
	@echo "==> [test] run the default battery"
	@./tests/run.sh

notarize:
	@if [ -z "$(NOTARY_KEYCHAIN_PROFILE)" ]; then \
		echo "ERROR: set NOTARY_KEYCHAIN_PROFILE to your notarytool keychain profile name"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail YOLO=1"; \
		exit 2; \
	fi
	@if [ -z "$(IDENTITY)" ] && [ -z "$(YOLO)" ]; then \
		echo "ERROR: set IDENTITY or opt-in to auto selection with YOLO=1"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY='Developer ID Application: ...'"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail YOLO=1"; \
		exit 2; \
	fi
	@/usr/bin/python3 -B tests/lib/release_preflight.py --report --dist "$(DIST_DIR)"
	@$(MAKE) build
	@set -eu; \
	  release_evidence="$$(/usr/bin/python3 -B tests/lib/release_evidence.py "$(DIST_DIR)/PolicyWitness.zip")"; \
	  /usr/bin/python3 -B notarize.py "$(DIST_DIR)/PolicyWitness.zip" "$(NOTARY_KEYCHAIN_PROFILE)" --evidence-dir "$$release_evidence"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step staple "$$release_evidence" 60 /usr/bin/xcrun stapler staple "$(DIST_DIR)/PolicyWitness.app"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step staple-validation "$$release_evidence" 60 /usr/bin/xcrun stapler validate -v "$(DIST_DIR)/PolicyWitness.app"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step gatekeeper "$$release_evidence" 60 /usr/sbin/spctl -a -vv --type execute "$(DIST_DIR)/PolicyWitness.app"; \
	  rm -f "$(DIST_DIR)/PolicyWitness.zip"; \
	  /usr/bin/python3 -B tests/lib/release_commands.py --step re-zip "$$release_evidence" 60 /usr/bin/ditto -c -k --sequesterRsrc --keepParent "$(DIST_DIR)/PolicyWitness.app" "$(DIST_DIR)/PolicyWitness.zip"; \
	  bash tests/accept-release.sh "$(DIST_DIR)/PolicyWitness.zip" --evidence-dir "$$release_evidence"

release:
	@if [ -z "$(NOTARY_KEYCHAIN_PROFILE)" ]; then \
		echo "ERROR: set NOTARY_KEYCHAIN_PROFILE to your notarytool keychain profile name"; \
		echo "example: make release NOTARY_KEYCHAIN_PROFILE=entitlement-jail YOLO=1 RELEASE_NOTES=notes.md"; \
		exit 2; \
	fi
	@/usr/bin/python3 -B tests/lib/release_preflight.py --dist "$(DIST_DIR)" >/dev/null
	@$(MAKE) notarize
	@set -eu; \
	  version="$$(/usr/bin/python3 -B tests/lib/release_preflight.py --dist "$(DIST_DIR)" --format version)"; \
	  battery="tests/out/runs/release-$$version-default"; \
	  echo "==> [release] default battery against $(DIST_DIR)/PolicyWitness.app -> $$battery"; \
	  PW_APP_DIR="$(DIST_DIR)/PolicyWitness.app" PW_TEST_OUT_DIR="$$battery" ./tests/run.sh; \
	  echo "==> [release] archive $(DIST_DIR)/archive/v$$version"; \
	  /usr/bin/python3 -B tests/lib/release_archive.py --latest --dist "$(DIST_DIR)" --battery "$$battery" \
	    $(if $(RELEASE_NOTES),--notes "$(RELEASE_NOTES)",)

publish:
	@if [ -z "$(VERSION)" ]; then \
		echo "ERROR: set VERSION to the archived release version"; \
		echo "example: make publish VERSION=0.2.4"; \
		exit 2; \
	fi
	@/usr/bin/python3 -B tests/lib/release_publish.py "$(DIST_DIR)/archive/v$(VERSION)" \
	  $(if $(RELEASE_NOTES),--notes "$(RELEASE_NOTES)",)
