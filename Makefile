.PHONY: build clean test notarize

NOTARY_KEYCHAIN_PROFILE ?=
YOLO ?=
DIST_DIR ?= dist

build:
	@if [ -z "$(IDENTITY)" ] && [ -z "$(YOLO)" ]; then \
		echo "ERROR: set IDENTITY or opt-in to auto selection with YOLO=1"; \
		echo "example: make build IDENTITY='Developer ID Application: ...'"; \
		echo "example: make build YOLO=1"; \
		exit 2; \
	fi
	DIST_DIR="$(DIST_DIR)" IDENTITY="$(IDENTITY)" YOLO="$(YOLO)" ./build.sh

clean:
	rm -rf tests/out/*

test:
	@echo "==> [test] run all suites"
	@./tests/run.sh --all

notarize:
	@if [ -z "$(NOTARY_KEYCHAIN_PROFILE)" ]; then \
		echo "ERROR: set NOTARY_KEYCHAIN_PROFILE to your notarytool keychain profile name"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=dev-profile"; \
		exit 2; \
	fi
	@if [ -z "$(IDENTITY)" ] && [ -z "$(YOLO)" ]; then \
		echo "ERROR: set IDENTITY or opt-in to auto selection with YOLO=1"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=dev-profile IDENTITY='Developer ID Application: ...'"; \
		echo "example: make notarize NOTARY_KEYCHAIN_PROFILE=dev-profile YOLO=1"; \
		exit 2; \
	fi
	@$(MAKE) build
	@echo "==> [notarize] submit $(DIST_DIR)/PolicyWitness.zip"
	@xcrun notarytool submit "$(DIST_DIR)/PolicyWitness.zip" --keychain-profile "$(NOTARY_KEYCHAIN_PROFILE)" --wait
	@echo "==> [notarize] staple $(DIST_DIR)/PolicyWitness.app"
	@xcrun stapler staple "$(DIST_DIR)/PolicyWitness.app"
	@echo "==> [notarize] validate $(DIST_DIR)/PolicyWitness.app"
	@xcrun stapler validate -v "$(DIST_DIR)/PolicyWitness.app"
	@spctl -a -vv --type execute "$(DIST_DIR)/PolicyWitness.app"
	@echo "==> [notarize] re-zip stapled app"
	@rm -f "$(DIST_DIR)/PolicyWitness.zip"
	@/usr/bin/ditto -c -k --sequesterRsrc --keepParent "$(DIST_DIR)/PolicyWitness.app" "$(DIST_DIR)/PolicyWitness.zip"
