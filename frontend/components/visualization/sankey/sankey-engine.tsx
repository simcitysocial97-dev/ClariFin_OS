/**
 * Sankey Engine - Stage 8C Financial OS Visual System
 *
 * Financial flow visualization using @nivo/sankey.
 * Shows income → expenses → transfers flow.
 */

'use client';

import { ResponsiveSankey } from '@nivo/sankey';
import { useMemo } from 'react';
import { financialColors } from '@/lib/design-system/colors';

// ===== Sankey Data Types =====
export interface SankeyNode {
  id: string;
  name: string;
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
}

export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

// ===== Props =====
interface SankeyEngineProps {
  data: SankeyData;
  className?: string;
}

// ===== Sankey Engine Component =====
export function SankeyEngine({
  data,
  className,
}: SankeyEngineProps) {
  // Transform data for nivo
  const sankeyData = useMemo(() => ({
    nodes: data.nodes.map(node => ({
      id: node.id,
      name: node.name,
    })),
    links: data.links.map(link => ({
      source: link.source,
      target: link.target,
      value: link.value,
    })),
  }), [data]);

  // Color scheme for different node types
  const nodeColors = useMemo(() => {
    return financialColors;
  }, []);

  if (!data.nodes.length || !data.links.length) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No cashflow data available</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveSankey
        data={sankeyData}
        margin={{ top: 20, right: 120, bottom: 20, left: 120 }}
        align="justify"
        colors={[
          nodeColors.positive[500],
          nodeColors.negative[500],
          nodeColors.neutral[500],
          nodeColors.info[500],
        ]}
        nodeOpacity={1}
        nodeHoverOpacity={0.8}
        nodeBorderWidth={1}
        nodeBorderColor={{
          from: 'color',
          modifiers: [['darker', 0.3]],
        }}
        linkOpacity={0.5}
        linkHoverOpacity={0.8}
        linkBlendMode="multiply"
        animate={true}
        motionConfig="gentle"
        labelTextColor={{
          from: 'color',
          modifiers: [['darker', 1]],
        }}
      />
    </div>
  );
}