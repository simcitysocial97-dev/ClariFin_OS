import {
  ContextRuntime,
  ContextManager,
  ContextRegistry,
  ContextSession,
  ContextSerializer,
  ContextRestorer,
  ContextHistory,
  ContextSelection,
  ContextNavigation,
  ContextFilter,
  ContextFocus,
  ContextComparison,
  ContextWorkspace,
  ContextValidator,
} from '../src';


describe('ContextRuntime', () => {
  let manager: ContextManager;
  let registry: ContextRegistry;
  let session: ContextSession;
  let runtime: ContextRuntime; // Used in tests
  let serializer: ContextSerializer;
  let restorer: ContextRestorer;
  let history: ContextHistory;
  let selection: ContextSelection;
  let navigation: ContextNavigation;
  let filter: ContextFilter;
  let focus: ContextFocus;
  let comparison: ContextComparison;
  let workspace: ContextWorkspace;

  beforeEach(() => {
    runtime = ContextRuntime.getInstance();
    manager = new ContextManager();
    registry = new ContextRegistry();
    session = new ContextSession();
    serializer = new ContextSerializer();
    restorer = new ContextRestorer();
    history = new ContextHistory();
    selection = new ContextSelection();
    navigation = new ContextNavigation();
    filter = new ContextFilter();
    focus = new ContextFocus();
    comparison = new ContextComparison();
    workspace = new ContextWorkspace();
  });

  test('should create and retrieve a context', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    expect(context.name).toBe('Test Context');
    expect(context.type).toBe('Dashboard');
    expect(registry.getContext(context.id)).toEqual(context);
  });

  test('should serialize and deserialize a context', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const serialized = serializer.serialize(context.id);
    const deserialized = serializer.deserialize(serialized);
    expect(deserialized.name).toBe(context.name);
    expect(deserialized.id).toBe(context.id);
  });

  test('should snapshot and restore a context', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const snapshot = manager.snapshot(context.id);
    const restored = restorer.restoreFromSnapshot(snapshot.id);
    expect(restored.name).toBe(context.name);
    expect(restored.id).toBe(context.id);
  });

  test('should record and retrieve history', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const events = history.getHistory(context.id);
    expect(events.length).toBeGreaterThan(0);
    expect(events[0].type).toBe('context.created');
  });

  test('should select and clear objects', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const updated = selection.selectObjects(context.id, [{ id: 'obj1', type: 'Account' }]);
    expect(updated.selectedFinancialObjects.length).toBe(1);
    const cleared = selection.clearSelection(context.id);
    expect(cleared.selectedFinancialObjects.length).toBe(0);
  });

  test('should navigate and get navigation state', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const updated = navigation.navigate(context.id, '/test', { param1: 'value1' });
    expect(updated.navigationState.path).toBe('/test');
    const state = navigation.getNavigationState(context.id);
    expect(state.path).toBe('/test');
  });

  test('should apply and remove filters', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const updated = filter.applyFilter(context.id, { id: 'filter1', type: 'date', value: '2023-01-01' });
    expect(updated.appliedFilters.length).toBe(1);
    const removed = filter.removeFilter(context.id, 'filter1');
    expect(removed.appliedFilters.length).toBe(0);
  });

  test('should focus and clear focus', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    const updated = focus.focusObject(context.id, { id: 'obj1', type: 'Account' });
    expect(updated.focusedObject?.id).toBe('obj1');
    const cleared = focus.clearFocus(context.id);
    expect(cleared.focusedObject).toBeUndefined();
  });

  test('should start and end comparison', () => {
    const context1 = manager.createContext('Test Context 1', 'Dashboard', 'user1', 'workspace1');
    const context2 = manager.createContext('Test Context 2', 'Dashboard', 'user1', 'workspace1');
    const updated = comparison.startComparison(context1.id, [context2.id], 'side-by-side');
    expect(updated.comparisonState?.comparedContexts).toContain(context2.id);
    const ended = comparison.endComparison(context1.id);
    expect(ended.comparisonState).toBeUndefined();
  });

  test('should create and destroy workspace', () => {
    const ws = workspace.createWorkspace('workspace1', 'Test Workspace');
    expect(ws.name).toBe('Test Workspace');
    expect(() => workspace.getWorkspace('workspace1')).not.toThrow();
    workspace.destroyWorkspace('workspace1');
    expect(() => workspace.getWorkspace('workspace1')).toThrow();
  });

  test('should validate context', () => {
    const context = manager.createContext('Test Context', 'Dashboard', 'user1', 'workspace1');
    expect(ContextValidator.validateContext(context)).toBe(true);
    expect(ContextValidator.validateContextType('Dashboard')).toBe(true);
    expect(ContextValidator.validateContextType('InvalidType')).toBe(false);
  });
});