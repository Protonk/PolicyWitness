.PHONY: build clean test

build:
	./build.sh

clean:
	rm -rf tests/out/*

test:
	@echo "==> [test] run all suites"
	@./tests/run.sh --all
