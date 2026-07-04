import { redirect } from 'next/navigation';

/**
 * Root Page - Redirects to Dashboard
 * ==================================
 * 
 * The canonical dashboard route is `/dashboard`.
 * This page redirects all root `/` requests to `/dashboard`.
 */

export default function RootPage() {
  redirect('/dashboard');
}
