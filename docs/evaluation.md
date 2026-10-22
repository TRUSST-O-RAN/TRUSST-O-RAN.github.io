# Evaluation

No attack is confirmed. The current implementation can measure F1 lifecycle
timing, sampled CU/DU context presence, and basic UE connectivity.

## Next evidence

1. Repeat controls and timeout cases with the native state checker.
2. Add actual bearer, RLC/MAC, and CU/UE security exports.
3. Implement NR RLF, valid overlap/reset scenarios, and multiple UE sources.
4. Measure duration, recovery, impact on other UEs, and control detection.
5. Compare useful cases with a separate monolithic RAN.

For every campaign, retain software/configuration hashes, capability assumptions,
timing, seeds, source identities, native state, traffic, and collection status.
Exclude startup/capture failures and synthetic fixtures from attack success rates.

The generic latest-value checker and old metrics/corpus utilities are prototypes;
their mismatch heuristics are not validated research labels. Use native procedure
boundaries and the settled inventory check for the current experiments.

[Results](validation.md) · [Full requirements](plans/task-1.md)
