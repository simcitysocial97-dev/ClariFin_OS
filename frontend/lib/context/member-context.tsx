'use client';

import type { ReactNode } from 'react';
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchMembers, createMember, type Member } from '@/lib/api/client';

interface MemberContextType {
  member: string;
  setMember: (member: string) => void;
  members: Member[];
  loading: boolean;
  error: Error | null;
  addMember: (name: string, color: string) => Promise<void>;
  refetch: () => void;
}

const MemberContext = createContext<MemberContextType | undefined>(undefined);

export function MemberProvider({ children }: { children: ReactNode }) {
  const [member, setMember] = useState<string>('All');
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchMembersList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMembers();
      setMembers(result.members);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch members'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMembersList();
  }, [fetchMembersList]);

  const addMember = useCallback(async (name: string, color: string) => {
    try {
      const newMember = await createMember(name, color);
      setMembers((prev) => [...prev, newMember]);
    } catch (err) {
      throw err;
    }
  }, []);

  return (
    <MemberContext.Provider
      value={{
        member,
        setMember,
        members,
        loading,
        error,
        addMember,
        refetch: fetchMembersList,
      }}
    >
      {children}
    </MemberContext.Provider>
  );
}

export function useMember() {
  const context = useContext(MemberContext);
  if (context === undefined) {
    throw new Error('useMember must be used within a MemberProvider');
  }
  return context;
}