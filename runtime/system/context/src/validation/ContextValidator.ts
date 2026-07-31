import { Context } from '../models/types';


export class ContextValidator {
  public static validateContext(context: Context): boolean {
    return (
      !!context.id &&
      !!context.name &&
      !!context.type &&
      !!context.createdTime &&
      !!context.updatedTime &&
      !!context.owner &&
      !!context.workspace &&
      !!context.currentTimeScope &&
      Array.isArray(context.selectedFinancialObjects) &&
      Array.isArray(context.appliedFilters) &&
      !!context.navigationState &&
      Array.isArray(context.pinnedObjects) &&
      Array.isArray(context.temporaryObjects) &&
      Array.isArray(context.historyStack) &&
      !!context.metadata &&
      Array.isArray(context.evidenceReferences) &&
      Array.isArray(context.explainabilityReferences)
    );
  }

  public static validateContextType(type: string): boolean {
    const validTypes = [
      'Dashboard', 'Account', 'Transaction', 'Loan', 'Investment', 'Goal',
      'Budget', 'CashFlow', 'NetWorth', 'Forecast', 'Investigation',
      'Comparison', 'Simulation', 'Search', 'Command', 'Workspace'
    ];
    return validTypes.includes(type);
  }
}