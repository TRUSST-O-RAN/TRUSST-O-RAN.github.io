// SPDX-License-Identifier: MIT
// Optional Task 1 instrumentation. Never included in the portable baseline build.
#pragma once
#include "ocudu/support/async/async_task.h"
#include "ocudu/support/async/async_timer.h"
#include <chrono>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
#include <mutex>
#include <string>
#include <unistd.h>
#include <vector>

namespace ocudu::trusst_lab {
struct snapshot {
  int64_t local, cu, du;
  bool present, releasing;
  int rrc; // DU F1 configuration state only; -1 means unavailable on CU.
};
template <typename T> snapshot cu(const T& c) {
  return {int64_t(c.ue_ids.ue_index), int64_t(c.ue_ids.cu_ue_f1ap_id),
          c.ue_ids.du_ue_f1ap_id ? int64_t(*c.ue_ids.du_ue_f1ap_id) : -1,
          true, c.marked_for_release, -1};
}
template <typename T> snapshot du(const T& c) {
  return {int64_t(c.ue_index), int64_t(c.gnb_cu_ue_f1ap_id), int64_t(c.gnb_du_ue_f1ap_id),
          true, c.marked_for_release, int(c.rrc_state)};
}
inline int64_t mono_ns() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline bool safe_token(const std::string& s) {
  return !s.empty() && s.size() <= 80 && s.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") == std::string::npos;
}
class writer {
  std::mutex mutex;
  FILE* file = nullptr;
  FILE* inventories = nullptr;
  std::string run, component, process;
  std::string boot, clock_namespace;
  int64_t monotonic_offset_ns = 0;
  uint64_t sequence = 0, next_epoch = 0;
  uint64_t inventory_sequence = 0;
  std::map<int64_t, uint64_t> epochs;
public:
  writer() {
    const char* r = std::getenv("TRUSST_RUN_ID");
    const char* c = std::getenv("TRUSST_COMPONENT");
    if (!r || !c) return;
    run = r; component = c;
    if (!safe_token(run) || (component != "CU" && component != "DU")) std::abort();
    std::ifstream uuid("/proc/sys/kernel/random/uuid");
    uuid >> process;
    if (!safe_token(process)) std::abort();
    std::string path = "/traces/" + component + "-state.jsonl";
    file = std::fopen(path.c_str(), "ax"); // Refuse stale trace files.
    if (!file) { std::perror("TRUSST state trace"); std::abort(); }
    path = "/traces/" + component + "-inventory.jsonl";
    inventories = std::fopen(path.c_str(), "ax");
    if (!inventories) { std::perror("TRUSST inventory trace"); std::abort(); }
    std::ifstream boot_file("/proc/sys/kernel/random/boot_id");
    boot_file >> boot;
    char name[128];
    auto length = ::readlink("/proc/self/ns/time", name, sizeof(name));
    if (!safe_token(boot) || length <= 0 || size_t(length) >= sizeof(name)) std::abort();
    clock_namespace.assign(name, size_t(length));
    std::ifstream offsets("/proc/self/timens_offsets");
    std::string clock;
    int64_t seconds, nanoseconds;
    bool found = false;
    while (offsets >> clock >> seconds >> nanoseconds) {
      if (clock == "monotonic") {
        monotonic_offset_ns = seconds * 1000000000LL + nanoseconds;
        found = true;
      }
    }
    if (!found) std::abort();
  }
  void emit(snapshot s, const char* event, const char* procedure, int outcome, int delay_ms) {
    if (!file) return;
    std::lock_guard<std::mutex> guard(mutex);
    if (std::string(event) == "context_created") epochs[s.local] = ++next_epoch;
    auto epoch = epochs.find(s.local);
    int64_t wall = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    int result = std::fprintf(file,
      "{\"schema\":\"trusst.f1-state.v1\",\"run_id\":\"%s\",\"component\":\"%s\","
      "\"process_epoch\":\"%s\",\"sequence\":%llu,\"timestamp_ns\":%lld,\"monotonic_ns\":%lld,"
      "\"context_epoch\":%llu,\"local_ue_id\":%lld,\"cu_ue_id\":%lld,\"du_ue_id\":%lld,"
      "\"context_present\":%s,\"marked_for_release\":%s,\"du_rrc_state\":%d,"
      "\"event\":\"%s\",\"procedure\":\"%s\",\"outcome\":%d,\"delay_ms\":%d}\n",
      run.c_str(), component.c_str(), process.c_str(), (unsigned long long)++sequence,
      (long long)wall, (long long)mono_ns(), (unsigned long long)(epoch == epochs.end() ? 0 : epoch->second),
      (long long)s.local, (long long)s.cu, (long long)s.du, s.present ? "true" : "false",
      s.releasing ? "true" : "false", s.rrc, event, procedure, outcome, delay_ms);
    if (result < 0 || std::fflush(file) != 0) { std::perror("TRUSST state write"); std::abort(); }
    if (std::string(event) == "context_deleted") epochs.erase(s.local);
  }
  void inventory(const std::vector<snapshot>& contexts, uint64_t repository, uint64_t association) {
    if (!inventories) return;
    std::lock_guard<std::mutex> guard(mutex);
    auto wall = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    std::fprintf(inventories,
        "{\"schema\":\"trusst.f1-inventory.v1\",\"run_id\":\"%s\",\"component\":\"%s\","
        "\"process_epoch\":\"%s\",\"boot_id\":\"%s\",\"clock_namespace\":\"%s\",\"monotonic_offset_ns\":%lld,"
        "\"sequence\":%llu,\"timestamp_ns\":%lld,\"monotonic_ns\":%lld,"
        "\"repository_epoch\":%llu,\"association_epoch\":%llu,\"contexts\":[",
        run.c_str(), component.c_str(), process.c_str(), boot.c_str(), clock_namespace.c_str(), (long long)monotonic_offset_ns,
        (unsigned long long)++inventory_sequence, (long long)wall, (long long)mono_ns(),
        (unsigned long long)repository, (unsigned long long)association);
    bool first = true;
    for (const auto& s : contexts) {
      auto epoch = epochs.find(s.local);
      if (epoch == epochs.end()) std::abort();
      std::fprintf(inventories,
          "%s{\"local_ue_id\":%lld,\"cu_ue_id\":%lld,\"du_ue_id\":%lld,\"context_epoch\":%llu}",
          first ? "" : ",", (long long)s.local, (long long)s.cu, (long long)s.du,
          (unsigned long long)epoch->second);
      first = false;
    }
    if (std::fprintf(inventories, "]}\n") < 0 || std::fflush(inventories) != 0 || std::ferror(inventories)) {
      std::perror("TRUSST inventory write"); std::abort();
    }
  }
};
inline writer& sink() { static writer instance; return instance; }
inline void emit(snapshot s, const char* event, const char* procedure = "", int outcome = -1, int delay_ms = 0) {
  sink().emit(s, event, procedure, outcome, delay_ms);
}
inline void inventory(const std::vector<snapshot>& contexts, uint64_t repository, uint64_t association) {
  sink().inventory(contexts, repository, association);
}
inline uint64_t next_repository_epoch() { static std::atomic<uint64_t> value{0}; return ++value; }
inline unsigned hook_delay(const char* procedure) {
  std::string key = "TRUSST_HOOK_" + std::string(procedure) + "_MS";
  const char* value = std::getenv(key.c_str());
  std::string text = value ? value : "0";
  std::ifstream control("/traces/hooks/" + std::string(procedure) + ".ms");
  if (control) std::getline(control, text);
  if (!text.empty() && text.back() == '\r') text.pop_back();
  if (text.empty() || text.size() > 4 || text.find_first_not_of("0123456789") != std::string::npos) std::abort();
  unsigned delay = std::stoul(text);
  if (delay > 2000) std::abort();
  return delay;
}
// Suspend only this procedure; the executor remains available for other work.
inline async_task<void> delay(timer_factory timers, snapshot s, const char* procedure) {
  return launch_async([timers, s, procedure, ms = hook_delay(procedure)](coro_context<async_task<void>>& ctx) mutable {
    CORO_BEGIN(ctx);
    emit(s, "hook_enter", procedure, -1, ms);
    CORO_AWAIT(async_wait_for(timers.create_timer(), std::chrono::milliseconds(ms)));
    emit(s, "hook_resume", procedure, -1, ms);
    CORO_RETURN();
  });
}
} // namespace ocudu::trusst_lab
