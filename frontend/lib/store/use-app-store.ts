'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Transaction } from '@/types/transaction';
import type { CreditCard } from '@/types/card';

interface AppState {
  // Data
  cards: CreditCard[];
  transactions: Transaction[];
  paidBills: string[]; // Array of card IDs that have been marked as paid
  
  // UI State
  selectedCardId: string | null;
  sidebarCollapsed: boolean;
  
  // Filters
  filters: {
    search: string;
    category: string;
    type: 'all' | 'debit' | 'credit';
    cardId: string;
    dateRange: { from: Date | null; to: Date | null };
  };
  
  // Actions
  addCard: (card: CreditCard) => void;
  removeCard: (cardId: string) => void;
  addTransactions: (transactions: Transaction[]) => void;
  updateTransaction: (id: string, updates: Partial<Transaction>) => void;
  deleteTransaction: (id: string) => void;
  setFilters: (filters: Partial<AppState['filters']>) => void;
  clearFilters: () => void;
  toggleSidebar: () => void;
  selectCard: (cardId: string | null) => void;
  clearAllData: () => void;
  markBillAsPaid: (cardId: string) => void;
  markBillAsUnpaid: (cardId: string) => void;
  isBillPaid: (cardId: string) => boolean;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      cards: [],
      transactions: [],
      paidBills: [],
      selectedCardId: null,
      sidebarCollapsed: false,
      filters: {
        search: '',
        category: 'All',
        type: 'all',
        cardId: 'all',
        dateRange: { from: null, to: null }
      },
      
      // Actions
      addCard: (card) => set((state) => ({
        cards: [...state.cards, card]
      })),
      
      removeCard: (cardId) => set((state) => ({
        cards: state.cards.filter(c => c.id !== cardId),
        transactions: state.transactions.filter(t => t.cardId !== cardId),
        selectedCardId: state.selectedCardId === cardId ? null : state.selectedCardId
      })),
      
      addTransactions: (transactions) => set((state) => ({
        transactions: [...state.transactions, ...transactions]
      })),
      
      updateTransaction: (id, updates) => set((state) => ({
        transactions: state.transactions.map(t => 
          t.id === id ? { ...t, ...updates } : t
        )
      })),
      
      deleteTransaction: (id) => set((state) => ({
        transactions: state.transactions.filter(t => t.id !== id)
      })),
      
      setFilters: (filters) => set((state) => ({
        filters: { ...state.filters, ...filters }
      })),
      
      clearFilters: () => set({
        selectedCardId: null,
        filters: {
          search: '',
          category: 'All',
          type: 'all',
          cardId: 'all',
          dateRange: { from: null, to: null }
        }
      }),
      
      toggleSidebar: () => set((state) => ({
        sidebarCollapsed: !state.sidebarCollapsed
      })),
      
      selectCard: (cardId) => set({ selectedCardId: cardId }),
      
      clearAllData: () => set({
        cards: [],
        transactions: [],
        paidBills: [],
        selectedCardId: null,
        filters: {
          search: '',
          category: 'All',
          type: 'all',
          cardId: 'all',
          dateRange: { from: null, to: null }
        }
      }),
      
      markBillAsPaid: (cardId) => set((state) => ({
        paidBills: [...state.paidBills, cardId]
      })),
      
      markBillAsUnpaid: (cardId) => set((state) => ({
        paidBills: state.paidBills.filter(id => id !== cardId)
      })),
      
      isBillPaid: (cardId) => {
        return get().paidBills.includes(cardId);
      }
    }),
    {
      name: 'bank-parser-storage'
    }
  )
);
