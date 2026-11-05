# Bounded reader onramp

Reviewed source state: `lookback-ea64218b`, commit `ea64218b`. Your role is a specimen author or someone interpreting PolicyWitness results. Assume ordinary knowledge of processes, file descriptors, IPC and sandbox policies, but no prior PolicyWitness internals.

PolicyWitness accepts a JSON specimen describing policy and operations and emits a JSON result envelope. This packet supplies one existing request example, not a new execution or an observed successful result. Read only this packet and `actor-example.json` beside it. Do not inspect the repository, target document, other records, implementation, tests or external sources yet. Do not execute the specimen or edit any files. Return your answer to the coordinator and wait for the next task; this same conversation continues.

The example is the actor request in `docs/PolicyWitness.md` at this baseline, with its shell substitutions expanded to a fixed illustrative path. The shell creation/run commands and surrounding explanation are deliberately omitted. The target file need not exist for this reading exercise.

Task: prepare a short inventory for a teammate: the actors and declared setup modes, the schedule in order, the number of ordinary query/attempt actions and each kind of extension action, and which references connect actions. State what you can read directly and what terms or behavior you cannot determine from the request alone. Do not infer runtime success from the request. You are not yet evaluating documentation or proposing changes.
