import { ContextRuntime } from './workspace/ContextRuntime';
import { Context } from '../models/types';


export class ContextSerializer {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public serialize(contextId: string): string {
    return this.runtime.serialize(contextId);
  }

  public deserialize(serializedContext: string): Context {
    return this.runtime.deserialize(serializedContext);
  }

  public serializeToObject(contextId: string): Context {
    const context = this.runtime['contexts'].get(contextId);
    if (!context) {
      throw new Error(`Context ${contextId} not found`);
    }
    return this.runtime['cloneContext'](context);
  }

  public deserializeFromObject(contextObj: Context): Context {
    return this.runtime.deserialize(JSON.stringify(contextObj));
  }
}