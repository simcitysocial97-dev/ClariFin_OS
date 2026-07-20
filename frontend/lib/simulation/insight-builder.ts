/**
 * Simulation Insight Builder - Stage 7 Simulation & Forecast Engine
 *
 * Utility for building evidence chains, calculation steps, and simulation objects.
 * Ensures every projection includes assumptions, inputs, outputs, evidence, confidence,
 * and related graph nodes.
 */

import type {
  SimulationEvidenceChain,
  SimulationEvidenceItem,
  SimulationCalculationStep,
  SimulationSourceReference,
  SimulationAssumption,
  Projection,
  Scenario,
  SimulationResult,
  SimulationType,
  SimulationInput,
  SimulationOutput,
} from './types';

// ===== Simulation Insight Builder =====
/**
 * Builder for creating explainable simulation results.
 */
export class SimulationInsightBuilder {
  /**
   * Build an evidence chain from evidence items and calculation steps.
   */
  buildEvidenceChain(
    summary: string,
    evidence: SimulationEvidenceItem[],
    calculationSteps: SimulationCalculationStep[],
    sourceReferences: SimulationSourceReference[],
    confidenceScore: number,
  ): SimulationEvidenceChain {
    return {
      summary,
      evidence,
      calculation_steps: calculationSteps,
      source_references: sourceReferences,
      confidence_score: Math.max(0, Math.min(100, confidenceScore)),
    };
  }

  /**
   * Create an evidence item.
   */
  createEvidence(
    type: string,
    summary: string,
    source: string,
    confidence?: number,
  ): SimulationEvidenceItem {
    return {
      type,
      summary,
      source,
      ...(confidence !== undefined ? { confidence: Math.max(0, Math.min(100, confidence)) } : {}),
    };
  }

  /**
   * Create a calculation step.
   */
  createCalculationStep(
    name: string,
    description: string,
    inputs: Record<string, unknown>,
    outputs: Record<string, unknown>,
  ): SimulationCalculationStep {
    return {
      name,
      description,
      inputs,
      outputs,
    };
  }

  /**
   * Create a source reference.
   */
  createSourceReference(
    id: string,
    type: string,
    label: string,
    timestamp: string,
  ): SimulationSourceReference {
    return {
      id,
      type,
      label,
      timestamp,
    };
  }

  /**
   * Create an assumption.
   */
  createAssumption(
    id: string,
    description: string,
    category: SimulationAssumption['category'],
    value?: number,
    confidence: number = 80,
    source: string = 'simulation-engine',
  ): SimulationAssumption {
    return {
      id,
      description,
      category,
      ...(value !== undefined ? { value } : {}),
      confidence: Math.max(0, Math.min(100, confidence)),
      source,
    };
  }

  /**
   * Create a projection.
   */
  createProjection(
    id: string,
    type: Projection['type'],
    date: string,
    valuePaise: number,
    confidence: number,
    relatedNodes: string[],
    options?: {
      lowerBoundPaise?: number;
      upperBoundPaise?: number;
    },
  ): Projection {
    return {
      id,
      type,
      date,
      value_paise: valuePaise,
      confidence: Math.max(0, Math.min(100, confidence)),
      related_nodes: relatedNodes,
      ...(options?.lowerBoundPaise !== undefined ? { lower_bound_paise: options.lowerBoundPaise } : {}),
      ...(options?.upperBoundPaise !== undefined ? { upper_bound_paise: options.upperBoundPaise } : {}),
    };
  }

  /**
   * Create a scenario.
   */
  createScenario(
    id: string,
    name: string,
    description: string,
    probabilityBps: number,
    projections: Projection[],
    assumptions: SimulationAssumption[],
    evidence: SimulationEvidenceChain,
  ): Scenario {
    return {
      id,
      name,
      description,
      probability_bps: Math.max(0, Math.min(10000, probabilityBps)),
      projections,
      assumptions,
      evidence,
    };
  }

  /**
   * Create a simulation result.
   */
  createSimulationResult(
    type: SimulationType,
    scenario: Scenario,
    timeline: Projection[],
    outputs: SimulationOutput[],
    evidence: SimulationEvidenceChain,
    relatedNodes: string[],
  ): SimulationResult {
    return {
      type,
      scenario,
      timeline,
      outputs,
      evidence,
      related_nodes: relatedNodes,
    };
  }

  /**
   * Create a simulation input.
   */
  createInput(
    name: string,
    value: number | string | boolean,
    description: string,
    source: SimulationInput['source'] = 'default',
  ): SimulationInput {
    return {
      name,
      value,
      description,
      source,
    };
  }

  /**
   * Create a simulation output.
   */
  createOutput(
    name: string,
    description: string,
    options?: {
      valuePaise?: number;
      value?: number | string | boolean;
      unit?: string;
    },
  ): SimulationOutput {
    return {
      name,
      description,
      ...(options?.valuePaise !== undefined ? { value_paise: options.valuePaise } : {}),
      ...(options?.value !== undefined ? { value: options.value } : {}),
      ...(options?.unit ? { unit: options.unit } : {}),
    };
  }

  /**
   * Generate a date string for a given month offset.
   */
  generateDateFromOffset(baseDate: string, monthOffset: number): string {
    const date = new Date(baseDate);
    date.setMonth(date.getMonth() + monthOffset);
    return date.toISOString().split('T')[0] ?? baseDate;
  }

  /**
   * Calculate confidence bounds based on confidence score.
   */
  calculateConfidenceBounds(
    valuePaise: number,
    confidence: number,
    volatilityBps: number = 1000, // 10% default volatility
  ): { lowerBoundPaise: number; upperBoundPaise: number } {
    // For 80% confidence, use ~1.28 standard deviations
    // Volatility is expressed in basis points
    const stdDev = (valuePaise * volatilityBps) / 10000;
    const zScore = confidence >= 90 ? 1.645 : confidence >= 80 ? 1.28 : 1.0;

    return {
      lowerBoundPaise: Math.max(0, Math.round(valuePaise - stdDev * zScore)),
      upperBoundPaise: Math.round(valuePaise + stdDev * zScore),
    };
  }
}

/** Convenience export */
export const simulationBuilder = new SimulationInsightBuilder();