'use client';
import { Suspense, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

type ApiErrorLike = {
  message?: string;
  response?: {
    data?: {
      detail?: unknown;
    };
  };
};

function RegisterPageContent() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [position, setPosition] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  const safeNextPath = useMemo(() => {
    const rawNext = searchParams.get('next') || '/';
    if (!rawNext.startsWith('/')) return '/';
    if (rawNext.startsWith('//')) return '/';
    if (rawNext.startsWith('/register')) return '/';
    return rawNext;
  }, [searchParams]);

  const loginHref = safeNextPath !== '/' ? `/login?next=${encodeURIComponent(safeNextPath)}` : '/login';

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/register', {
        username,
        email,
        password,
        research_area: position || undefined
      });
      setSuccess(true);
      setTimeout(() => router.push(loginHref), 2000);
    } catch (err: unknown) {
      const e = err as ApiErrorLike;
      if (e.response?.data?.detail) {
        if (Array.isArray(e.response.data.detail)) {
          const msg = e.response.data.detail
            .map((d) => {
              if (d && typeof d === 'object' && 'msg' in d) {
                return String((d as { msg?: unknown }).msg ?? '');
              }
              return String(d);
            })
            .filter(Boolean)
            .join(', ');
          setError(msg || '注册失败，请检查输入后重试。');
        } else {
          setError(String(e.response.data.detail));
        }
      } else {
        setError(e.message || '注册失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="w-full max-w-lg space-y-8 rounded-xl border border-border bg-card p-8 shadow-sm">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">创建 RxnCommons 账号</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            注册后即可上传并管理你的数据集版本
          </p>
        </div>

        {success ? (
          <div className="rounded-md bg-green-50 p-4 text-center text-green-700">
            <h3 className="text-md font-medium">注册成功！</h3>
            <p className="mt-2 text-sm">正在跳转到登录页面...</p>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleRegister}>
             {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">用户名 *</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                  minLength={3}
                  maxLength={50}
                  className="block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                  placeholder="3~50字符，字母/数字/下划线"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">邮箱 *</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  className="block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                  placeholder="your.email@example.com"
                />
              </div>

               <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">密码 *</label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={8}
                    className="block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                    placeholder="至少8位"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">确认密码 *</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    required
                    className="block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                  />
                </div>
              </div>

              <div className="border-t border-border pt-4 mt-4">
                <p className="text-sm font-semibold text-muted-foreground mb-4">补充信息 (可选)</p>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">职位</label>
                  <input
                    type="text"
                    value={position}
                    onChange={e => setPosition(e.target.value)}
                    className="block w-full rounded-md border border-input bg-transparent px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary sm:text-sm"
                    placeholder="例如：研究生 / 博士后 / 教师 / 研究员"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-4">
                <button
                type="submit"
                disabled={loading}
                className="flex w-full justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                {loading ? '注册中...' : '注册'}
                </button>
                <div className="text-center">
                    <Link href={loginHref} className="text-sm font-medium text-primary hover:text-primary/80 flex items-center justify-center gap-1">
                        <ArrowLeft className="h-4 w-4" /> 返回登录
                    </Link>
                </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="text-center py-20 text-muted-foreground">加载中...</div>}>
      <RegisterPageContent />
    </Suspense>
  );
}
