export function createMockResponse<T>(data: T, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    statusText: status >= 400 ? 'Error' : 'OK',
    headers: { 'Content-Type': 'application/json' },
  });
}

export function createMockErrorResponse(status: number = 500): Response {
  return createMockResponse<Record<string, unknown>>({}, status);
}
