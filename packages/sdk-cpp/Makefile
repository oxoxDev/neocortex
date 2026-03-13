BUILD_DIR = build

.PHONY: build test integration-test clean

build:
	@cmake -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=Debug
	@cmake --build $(BUILD_DIR) -j

test: build
	@cd $(BUILD_DIR) && ctest --test-dir test -R "^(error_test|memory_client_test)$$" --output-on-failure

integration-test: build
	@cd $(BUILD_DIR) && ctest --test-dir test -R "^integration_test$$" --output-on-failure

clean:
	@rm -rf $(BUILD_DIR)
