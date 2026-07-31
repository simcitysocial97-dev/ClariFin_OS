export * from './models/types';
export * from './workspace/ContextRuntime';
export * from './workspace/ContextManager';
export * from './workspace/ContextRegistry';
export * from './workspace/ContextSession';
export * from './serialization/ContextSerializer';
export * from './serialization/ContextRestorer';
export * from './history/ContextHistory';
export * from './selection/ContextSelection';
export * from './navigation/ContextNavigation';
export * from './selection/ContextFilter';
export * from './selection/ContextFocus';
export * from './selection/ContextComparison';
export * from './workspace/ContextWorkspace';
export * from './validation/ContextValidator';

// Public API
import { ContextRuntime } from './workspace/ContextRuntime';
const runtime = ContextRuntime.getInstance();

export default {
  create: runtime.createContext.bind(runtime),
  destroy: runtime.destroyContext.bind(runtime),
  activate: runtime.activateContext.bind(runtime),
  snapshot: runtime.snapshot.bind(runtime),
  restore: runtime.restore.bind(runtime),
  history: runtime.history.bind(runtime),
  workspace: runtime.workspace.bind(runtime),
  selection: runtime.selection.bind(runtime),
  focus: runtime.focus.bind(runtime),
  navigation: runtime.navigation.bind(runtime),
  filters: runtime.filters.bind(runtime),
  compare: runtime.compare.bind(runtime),
  serialize: runtime.serialize.bind(runtime),
  deserialize: runtime.deserialize.bind(runtime),
  validate: runtime.validate.bind(runtime),
};