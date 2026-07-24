/**
 * useEvidence Hook - Stage 3 Transaction Intelligence Workspace
 *
 * React hook for evidence state management.
 */

'use client';

import { useState, useCallback } from 'react';
import type { EvidenceState, EvidenceItem } from './types';

/**
 * useEvidence Hook
 * Provides evidence state management for the Transaction Intelligence Workspace
 */
export function useEvidence(): EvidenceState & {
  toggleEvidence: (transactionId: string, evidence: EvidenceItem[]) => void;
  openEvidence: (transactionId: string, evidence: EvidenceItem[]) => void;
  closeEvidence: () => void;
} {
  const [state, setState] = useState<EvidenceState>({
    isOpen: false,
    transactionId: null,
    evidence: [],
    loading: false,
    error: null,
  });

  const toggleEvidence = useCallback((transactionId: string, evidence: EvidenceItem[]) => {
    setState(prev => ({
      ...prev,
      isOpen: !prev.isOpen || prev.transactionId !== transactionId,
      transactionId,
      evidence,
    }));
  }, []);

  const openEvidence = useCallback((transactionId: string, evidence: EvidenceItem[]) => {
    setState({
      isOpen: true,
      transactionId,
      evidence,
      loading: false,
      error: null,
    });
  }, []);

  const closeEvidence = useCallback(() => {
    setState({
      isOpen: false,
      transactionId: null,
      evidence: [],
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    toggleEvidence,
    openEvidence,
    closeEvidence,
  };
}