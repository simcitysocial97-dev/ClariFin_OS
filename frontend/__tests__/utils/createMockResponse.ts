import { type MockResponse } from './types';

export function createMockResponse<T>(data: T, status: number = 200): Response {
  const response = new Response(JSON.stringify(data), {
    status,
    statusText: status >= 400 ? 'Error' : 'OK',
    headers: { 'Content-Type': 'application/json' },
  });
  return response;
}

export function createMockErrorResponse(status: number = 500): Response {
  return createMockResponse({}, status);
}

export const MOCK_RESPONSE: typeof MockResponse = {
  createSuccess: createMockResponse,
  createError: createMockErrorResponse,
};
