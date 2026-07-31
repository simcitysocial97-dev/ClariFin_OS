import { ContextRuntime } from './workspace/ContextRuntime';
import { Context, ContextSnapshot } from '../models/types';


export class ContextRestorer {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public restoreFromSnapshot(snapshotId: string): Context {
    return this.runtime.restore(snapshotId);
  }

  public restoreFromSerialized(serializedContext: string): Context {
    return this.runtime.deserialize(serializedContext);
  }

  public restoreFromObject(contextObj: Context): Context {
    return this.runtime.deserialize(JSON.stringify(contextObj));
  }

  public listSnapshots(): ContextSnapshot[] {
    return Array.from(this.runtime['snapshots'].values());
  }

  public getSnapshot(snapshotId: string): ContextSnapshot | undefined {
    return this.runtime['snapshots'].get(snapshotId);
  }
}