// Shared association for step assembly and the worker disposition account.
// A duplicate identifier cannot choose an arbitrary slot as its evidence.
func uniquelyAssociatedWorkerSlots(_ slots: [CWorkerSlotResult]) -> [String: CWorkerSlotResult] {
    Dictionary(grouping: slots, by: { $0.stepId }).compactMapValues { $0.count == 1 ? $0[0] : nil }
}
