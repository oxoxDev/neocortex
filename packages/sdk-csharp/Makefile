.PHONY: build test integration-test clean

build:
	dotnet build

test:
	dotnet test --filter "Category!=Integration"

integration-test:
	dotnet test --filter "Category=Integration"

clean:
	dotnet clean
	rm -rf src/TinyHumans.Sdk/bin src/TinyHumans.Sdk/obj
	rm -rf test/TinyHumans.Sdk.Tests/bin test/TinyHumans.Sdk.Tests/obj
	rm -rf example/TinyHumans.Sdk.Example/bin example/TinyHumans.Sdk.Example/obj
