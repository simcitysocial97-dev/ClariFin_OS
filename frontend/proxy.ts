import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { ROUTE_REDIRECTS } from './lib/config/navigation';

export function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // Check if this path needs redirection
  const redirectPath = ROUTE_REDIRECTS[path];
  if (redirectPath) {
    console.log(`Redirecting ${path} → ${redirectPath}`);
    
    return NextResponse.redirect(new URL(redirectPath, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};