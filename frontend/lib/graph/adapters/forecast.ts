/**
 * Forecast Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts ForecastViewModel into GraphResult.
 * Maps projections, scenarios, and confidence intervals to graph nodes and edges.
 *
 * Architecture: ForecastViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { ForecastViewModel } from '@/types/forecast-view-model';

const WORKSPACE = 'forecast';

/**
 * Adapter for the Forecast Intelligence Workspace
 */
export class ForecastGraphAdapter extends BaseAdapter<ForecastViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: ForecastViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    // Net worth projection nodes
    for (const proj of viewModel.net_worth_projections) {
      nodes.push({
        id: scopedId(WORKSPACE, `projection:nw:${proj.date}`),
        type: 'forecast_projection',
        label: `Net Worth Projection ${proj.date}`,
        workspace: WORKSPACE,
        value_paise: proj.projected_paise,
        date: proj.date,
        metadata: {
          projection_type: 'net_worth',
          lower_bound_paise: proj.lower_bound_paise,
          upper_bound_paise: proj.upper_bound_paise,
        },
        deep_link: `/forecast?date=${proj.date}`,
      });
    }

    // Cashflow projection nodes
    for (const proj of viewModel.cashflow_projections) {
      nodes.push({
        id: scopedId(WORKSPACE, `projection:cf:${proj.month}`),
        type: 'forecast_projection',
        label: `Cashflow Projection ${proj.month}`,
        workspace: WORKSPACE,
        value_paise: proj.net_paise,
        date: proj.month,
        metadata: {
          projection_type: 'cashflow',
          income_paise: proj.income_paise,
          expenses_paise: proj.expenses_paise,
        },
        deep_link: `/forecast?month=${proj.month}`,
      });
    }

    // Scenario nodes
    for (const scenario of viewModel.scenarios) {
      nodes.push({
        id: scopedId(WORKSPACE, `scenario:${scenario.name}`),
        type: 'forecast_scenario',
        label: `Scenario: ${scenario.name}`,
        workspace: WORKSPACE,
        metadata: {
          description: scenario.description,
          probability_bps: scenario.probability_bps,
        },
        deep_link: `/forecast?scenario=${encodeURIComponent(scenario.name)}`,
      });
    }

    return nodes;
  }

  buildEdges(viewModel: ForecastViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    // Connect net worth projections sequentially
    const sortedNwProjections = [...viewModel.net_worth_projections].sort((a, b) =>
      a.date.localeCompare(b.date),
    );
    for (let i = 1; i < sortedNwProjections.length; i++) {
      const prevId = scopedId(WORKSPACE, `projection:nw:${sortedNwProjections[i - 1].date}`);
      const currId = scopedId(WORKSPACE, `projection:nw:${sortedNwProjections[i].date}`);
      if (nodeIds.has(prevId) && nodeIds.has(currId)) {
        edges.push({
          id: edgeId(prevId, currId, 'related_to'),
          source: prevId,
          target: currId,
          type: 'related_to',
          label: 'Projection sequence',
          weight: 1,
          metadata: {},
        });
      }
    }

    // Scenario → Projections
    for (const scenario of viewModel.scenarios) {
      const scenarioNodeId = scopedId(WORKSPACE, `scenario:${scenario.name}`);
      if (!nodeIds.has(scenarioNodeId)) continue;

      for (const proj of scenario.net_worth_projections) {
        const projNodeId = scopedId(WORKSPACE, `projection:nw:${proj.date}`);
        if (nodeIds.has(projNodeId)) {
          edges.push({
            id: edgeId(scenarioNodeId, projNodeId, 'projects'),
            source: scenarioNodeId,
            target: projNodeId,
            type: 'projects',
            label: `Projects ${proj.date}`,
            weight: 1,
            metadata: {},
          });
        }
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const forecastGraphAdapter = new ForecastGraphAdapter();