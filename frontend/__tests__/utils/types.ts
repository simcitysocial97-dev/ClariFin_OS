export interface MockResponse {
  createSuccess: <T>(data: T, status?: number) => Response;
  createError: (status?: number) => Response;
}
