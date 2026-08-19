import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { ROUTE_REDIRECTS } from './lib/config/navigation';

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const redirectPath = ROUTE_REDIRECTS[path];
  if (redirectPath) {
    console.log(`Redirecting ${path} -> ${redirectPath}`);
    return NextResponse.redirect(new URL(redirectPath, request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
