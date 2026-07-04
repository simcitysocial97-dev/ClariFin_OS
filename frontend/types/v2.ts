/**
 * V2 API Types
 */

// Import List Response
export interface ImportListResponse {
  imports: Array<{
    id: number;
    filename: string;
    bank: string;
    status: string;
    transaction_count: number;
    created_at: string;
    template_id: number | null;
  }>;
  total: number;
  page: number;
  per_page: number;
}