#pragma once

#include "types.hpp"
#include <string>

namespace alphahuman {

class AlphahumanMemoryClient {
public:
    explicit AlphahumanMemoryClient(const std::string& token, const std::string& base_url = "");
    ~AlphahumanMemoryClient();

    // Non-copyable
    AlphahumanMemoryClient(const AlphahumanMemoryClient&) = delete;
    AlphahumanMemoryClient& operator=(const AlphahumanMemoryClient&) = delete;

    // Movable
    AlphahumanMemoryClient(AlphahumanMemoryClient&& other) noexcept;
    AlphahumanMemoryClient& operator=(AlphahumanMemoryClient&& other) noexcept;

    InsertMemoryResponse insert_memory(const InsertMemoryParams& params);
    RecallMemoryResponse recall_memory(const RecallMemoryParams& params = {});
    DeleteMemoryResponse delete_memory(const DeleteMemoryParams& params = {});
    QueryMemoryResponse query_memory(const QueryMemoryParams& params);
    RecallMemoriesResponse recall_memories(const RecallMemoriesParams& params = {});

private:
    json post(const std::string& path, const json& body);
    json handle_response(long http_code, const std::string& response_body);
    static size_t write_callback(char* ptr, size_t size, size_t nmemb, void* userdata);

    std::string base_url_;
    std::string token_;
    void* curl_ = nullptr;
};

} // namespace alphahuman
