import { redirect } from 'next/navigation';

// Redirect root to /dashboard
export default function HomePage() {
  redirect('/dashboard');
}