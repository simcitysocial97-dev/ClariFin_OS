import { ContextRuntime } from './workspace/ContextRuntime';
import { Context } from '../models/types';


export class ContextComparison {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public startComparison(
    contextId: string,
    comparedContexts: string[],
    comparisonType: string
  ): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      comparisonState: {
        comparedContexts,
        comparisonType,
      },
    });

    this.runtime['recordEvent']('comparison.started', contextId, {
      comparedContexts,
      comparisonType,
    });

    return this.runtime['cloneContext'](updatedContext);
  }

  public endComparison(contextId: string): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      comparisonState: undefined,
    });

    this.runtime['recordEvent']('comparison.ended', contextId, {});
    return this.runtime['cloneContext'](updatedContext);
  }

  public getComparisonState(contextId: string): { comparedContexts: string[]; comparisonType: string } | undefined {
    return this.runtime.compare(contextId);
  }
}