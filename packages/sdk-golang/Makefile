.PHONY: build vet example clean test

build:
	go build ./...

vet:
	go vet ./...

test:
	go test ./... -v -count=1

test-race:
	go test ./... -race

test-cover:
	go test ./... -cover

example:
	go build ./example/

clean:
	go clean ./...

check: build vet test
