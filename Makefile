.PHONY: build clean test

build:
	./build.sh

clean:
	rm -rf tests/out/*

test:
	./tests/run.sh --all
