import { ContextRuntime } from './workspace/ContextRuntime';
import { ContextEvent } from '../models/types';


export class ContextHistory {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public getHistory(contextId: string): ContextEvent[] {
    return this.runtime.history(contextId);
  }

  public getFullHistory(): ContextEvent[] {
    return [...this.runtime['events']];
  }

  public getEventsByType(type: string): ContextEvent[] {
    return this.runtime['events'].filter(event => event.type === type);
  }

  public getEventsByContext(contextId: string): ContextEvent[] {
    return this.getHistory(contextId);
  }

  public clearHistory(): void {
    this.runtime['events'] = [];
  }
}