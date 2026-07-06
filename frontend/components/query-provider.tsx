"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes — data does not change in real time
        gcTime: 10 * 60 * 1000, // 10 minutes — keep in cache after component unmounts
        refetchOnWindowFocus: false, // do not refetch when user switches tabs
        refetchOnMount: true, // fetch when component first mounts
        retry: 1, // retry once on failure, not 3 times (default)
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}