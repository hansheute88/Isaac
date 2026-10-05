# Isaac — Third-Party Replacement Strategy

## Short answer

Isaac can implement **native alternatives for many third-party capabilities**, but "reimplementing the capability" is not the same as copying a third party's implementation.

### Generally possible

1. **Open-source libraries**  
   Isaac can replace a dependency with Isaac-owned code if the replacement is independently implemented and the relevant license obligations are respected.

2. **Public APIs / protocols**  
   Isaac can implement its own client or protocol implementation where the protocol/API terms permit it.

3. **Service capabilities**  
   A capability currently obtained from an external service can often be moved into a local Isaac subsystem, for example local memory, local search, local browser control, local task scheduling, local model routing or local audit storage.

4. **Own abstractions**  
   Isaac's interfaces should isolate providers so that a provider can be replaced without changing the cognitive kernel.

### Not automatically possible

Isaac may not simply copy proprietary source code, proprietary SDK internals, copyrighted assets, confidential algorithms or contractual functionality that is restricted by the provider's terms.

Patents, trademarks, database rights, API terms and license conditions must also be considered separately.

## Strategic objective

The preferred acquisition architecture is:

**Isaac Kernel → Isaac-owned Port/Adapter → provider OR Isaac-native implementation**

rather than:

**Isaac Kernel → hard dependency on one provider**

## Recommended replacement priorities

### Tier 1 — already suitable for native ownership

- governance / constitution
- task lifecycle
- goal engine
- motivation
- audit / decision trace
- memory model
- provenance
- policy engine
- MCP governance
- computer-use policy
- Windows integration
- bounded Git operations

### Tier 2 — practical to replace

- simple HTTP clients
- search adapters
- local persistence
- provider routing
- browser-control wrappers
- notification adapters
- lightweight observability

### Tier 3 — expensive but possible

- vector database
- knowledge graph
- full web index/search engine
- hosted browser infrastructure
- advanced multimodal inference
- frontier LLMs

These are usually better treated as replaceable provider capabilities rather than recreated wholesale.

## Evolution 2.0 alignment

The supplied theory describes Evolution 2.0 in terms of root transparency, controlled write access, auditability, reversibility and controlled growth. That argues for **replaceable external adapters around a stable, inspectable Isaac kernel**, rather than embedding provider-specific behavior into the kernel.

The goal is not to remove every dependency. The goal is to ensure that no dependency owns Isaac's identity, governance or cognitive control plane.
