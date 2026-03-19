'use client';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';
import Link from 'next/link';

type ApiErrorLike = {
  code?: string;
  message?: string;
  response?: {
    status?: number;
    data?: {
      detail?: unknown;
    } | string;
  };
};

function LoginPageContent() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login } = useAuth();

  const safeNextPath = useMemo(() => {
    const rawNext = searchParams.get('next') || '/';
    if (!rawNext.startsWith('/')) return '/';
    if (rawNext.startsWith('//')) return '/';
    if (rawNext.startsWith('/login')) return '/';
    return rawNext;
  }, [searchParams]);

  const registerHref = safeNextPath !== '/' ? `/register?next=${encodeURIComponent(safeNextPath)}` : '/register';

  useEffect(() => {
    if (user) {
      router.replace(safeNextPath);
    }
  }, [user, router, safeNextPath]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/login', { email, password });
      login(res.data.access_token, res.data.refresh_token || null, res.data.user);
      router.push(safeNextPath);
    } catch (err: unknown) {
      const e = err as ApiErrorLike;
      const responseData = e?.response?.data;
      const detail =
        typeof responseData === 'object' && responseData !== null
          ? responseData.detail
          : (typeof responseData === 'string' ? responseData : undefined);
      if (detail) {
        if (detail === 'auth_invalid_credentials') {
          setError('邮箱或密码错误。');
        } else if (String(detail).includes('Internal Server Error')) {
          setError('登录服务异常（500）。请检查后端服务与日志后重试。');
        } else {
          if (Array.isArray(detail)) {
            const text = detail
              .map((item) => {
                if (item && typeof item === 'object' && 'msg' in item) {
                  return String((item as { msg?: unknown }).msg ?? '');
                }
                return String(item);
              })
              .filter(Boolean)
              .join(', ');
            setError(text || '登录失败，请检查输入后重试。');
          } else {
            setError(String(detail));
          }
        }
      } else if (e?.response?.status === 500) {
        setError('登录服务异常（500）。若后端未启动，请先启动后端后重试。');
      } else if (
        e?.code === 'ERR_NETWORK' ||
        /ECONNREFUSED|Network Error/i.test(String(e?.message || ''))
      ) {
        setError('无法连接后端服务（127.0.0.1:8001），请先启动后端后重试。');
      } else {
        setError(e?.message || '登录失败，请稍后重试。');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="w-full max-w-md space-y-8 rounded-xl border border-border bg-card p-8 shadow-sm">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">登录 RxnCommons</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            欢迎回来，继续管理你的反应数据集
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground">
                邮箱
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                placeholder="name@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground">
                密码
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 rounded border-input text-primary focus:ring-primary"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-muted-foreground">
                记住我
              </label>
            </div>
            <div className="text-sm">
              <Link href="#" className="font-medium text-primary hover:text-primary/80">
                忘记密码?
              </Link>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <p className="mt-2 text-center text-sm text-muted-foreground">
          还没有账号？{' '}
          <Link href={registerHref} className="font-medium text-primary hover:text-primary/80">
            立即注册
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="text-center py-20 text-muted-foreground">加载中...</div>}>
      <LoginPageContent />
    </Suspense>
  );
}
