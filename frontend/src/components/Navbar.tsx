'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { useState, useRef, useEffect } from 'react';
import { User, ChevronDown, LogOut, LayoutDashboard, Upload } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const canUpload = !!user && user.role !== 'admin';
  const isAdmin = user?.role === 'admin';
  const hideUploadEntry =
    pathname === '/' ||
    pathname === '/upload' ||
    pathname === '/datasets' ||
    pathname.startsWith('/datasets/') ||
    pathname === '/profile' ||
    pathname === '/account';
  const showUploadEntry = canUpload && !hideUploadEntry;

  const linkClass = (active: boolean) =>
    `px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors duration-200 ${
      active
        ? 'text-primary-foreground bg-primary shadow-sm'
        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
    }`;

  const isDatasetsActive = pathname === '/datasets' || pathname.startsWith('/datasets/');

  // Handle outside click to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [dropdownRef]);

  // Close dropdown on route change (optional, but good UX)
  useEffect(() => {
    setDropdownOpen(false);
  }, [pathname]);

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Logo & Main Nav */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-primary">
                RxnCommons
              </span>
            </Link>
            
            <div className="hidden md:flex items-center space-x-1">
              <Link href="/datasets" className={linkClass(isDatasetsActive)}>
                数据集
              </Link>
            </div>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-2">
                {showUploadEntry && (
                  <Link
                    href="/upload"
                    className="hidden sm:inline-flex items-center justify-center gap-1.5 rounded-full bg-gradient-to-r from-teal-600 to-primary px-5 py-1.5 text-sm font-semibold text-white shadow-md transition-all hover:from-teal-500 hover:to-primary/90 hover:shadow-lg hover:-translate-y-0.5 active:scale-95 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    <Upload className="h-4 w-4" />
                    <span>上传数据</span>
                  </Link>
                )}
                
                {/* User Dropdown */}
                <div className="relative" ref={dropdownRef}>
                  <button 
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="flex items-center gap-2 px-2.5 py-1 rounded-full hover:bg-muted/50 transition-colors focus:outline-none border border-transparent hover:border-border/50"
                  >
                    <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground shadow-sm">
                      <span className="text-sm font-bold">{user.username.charAt(0).toUpperCase()}</span>
                    </div>
                    <span className="text-sm font-medium text-foreground max-w-[100px] truncate hidden sm:block">
                      {user.username}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {dropdownOpen && (
                    <div className="absolute right-0 top-full mt-2 w-56 bg-popover border border-border rounded-xl shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right">
                      <div className="px-4 py-3 border-b border-border/50 mb-1">
                         <p className="text-sm font-medium text-foreground truncate">{user.username}</p>
                         <p className="text-xs text-muted-foreground truncate opacity-80">{user.email}</p>
                      </div>
                      
                      <div className="px-1 py-1">
                        {!isAdmin ? (
                          <>
                            <Link href="/account" className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted rounded-md transition-colors w-full">
                              <User className="w-4 h-4 text-muted-foreground" />
                              账户信息
                            </Link>
                            <Link href="/profile" className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted rounded-md transition-colors w-full">
                              <LayoutDashboard className="w-4 h-4 text-muted-foreground" />
                              我的数据
                            </Link>
                          </>
                        ) : (
                          <Link href="/admin" className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted rounded-md transition-colors w-full">
                            <LayoutDashboard className="w-4 h-4 text-muted-foreground" />
                            后台管理
                          </Link>
                        )}
                      </div>
                      
                      <div className="border-t border-border/50 my-1"></div>

                      <div className="px-1 py-1">
                        <button 
                          onClick={logout}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 rounded-md transition-colors text-left"
                        >
                          <LogOut className="w-4 h-4" />
                          退出登录
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link 
                  href="/login" 
                  className="rounded-full px-3.5 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground hover:bg-muted/50"
                  // Clean rounded hover area for login
                >
                  登录
                </Link>
                <Link 
                  href="/register" 
                  className="inline-flex items-center justify-center rounded-full bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground shadow transition-all hover:bg-primary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
