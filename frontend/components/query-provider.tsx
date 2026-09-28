"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { transientRetryPolicy } from '@/lib/api/gateway';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes — data does not change in real time
        gcTime: 10 * 60 * 1000, // 10 minutes — keep in cache after component unmounts
        refetchOnWindowFocus: false, // do not refetch when user switches tabs
        refetchOnMount: true, // fetch when component first mounts
        retry: transientRetryPolicy, // semantic: only transient errors retry (M9-C37)
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}