.PHONY: build clean test notarize

NOTARY_KEYCHAIN_PROFILE ?=
YOLO ?=
BUILD_ARGS ?=

ifneq ($(strip $(YOLO)),)
BUILD_ARGS += --yolo
endif

build:
	@if [ -z "$(IDENTITY)" ] && [ -z "$(YOLO)" ]; then \
		echo "ERROR: set IDENTITY or opt-in to auto selection with YOLO=1"; \
		echo "example: make build IDENTITY='Developer ID Application: ...'"; \
		echo "example: make build YOLO=1"; \
		exit 2; \
	fi
	./build.sh $(BUILD_ARGS)

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
	@echo "==> [notarize] submit PolicyWitness.zip"
	@xcrun notarytool submit "PolicyWitness.zip" --keychain-profile "$(NOTARY_KEYCHAIN_PROFILE)" --wait
	@echo "==> [notarize] staple PolicyWitness.app"
	@xcrun stapler staple "PolicyWitness.app"
	@echo "==> [notarize] validate PolicyWitness.app"
	@xcrun stapler validate -v "PolicyWitness.app"
	@spctl -a -vv --type execute "PolicyWitness.app"
	@echo "==> [notarize] re-zip stapled app"
	@rm -f "PolicyWitness.zip"
	@/usr/bin/ditto -c -k --sequesterRsrc --keepParent "PolicyWitness.app" "PolicyWitness.zip"
