'use client';
import { usePathname } from 'next/navigation';

export default function Footer() {
  const pathname = usePathname();
  
  if (pathname === '/') return null;

  return (
    <footer className="bg-background border-t border-border mt-auto">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 flex justify-center">
        <p className="text-center text-xs leading-5 text-muted-foreground">
          &copy; {new Date().getFullYear()} RxnCommons Chemistry Data Hub. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
