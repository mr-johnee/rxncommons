'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

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

export default function AdminLoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const res = await api.post('/auth/login', { email, password });
      const user = res.data.user;
      if (user.role !== 'admin') {
        setError('该账号不是管理员，无法进入后台。');
        setSubmitting(false);
        return;
      }
      login(res.data.access_token, res.data.refresh_token || null, user);
      router.push('/admin');
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
          setError(String(detail));
        }
      } else if (e?.response?.status === 500) {
        setError('登录服务异常（500）。若后端未启动，请先启动后端后重试。');
      } else if (
        e?.code === 'ERR_NETWORK' ||
        /ECONNREFUSED|Network Error/i.test(String(e?.message || ''))
      ) {
        setError('无法连接后端服务（127.0.0.1:8001），请先启动后端后重试。');
      } else {
        setError(e?.message || '登录失败');
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 bg-white border rounded-lg p-8 shadow-sm">
      <h1 className="text-2xl font-bold mb-6 text-center">管理员登录</h1>
      {error && <div className="mb-4 p-3 rounded bg-red-50 text-red-700 text-sm">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">邮箱</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full border border-input bg-background rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">密码</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full border border-input bg-background rounded px-3 py-2" />
        </div>
        <button disabled={submitting} type="submit" className="w-full bg-primary text-primary-foreground shadow py-2 rounded hover:bg-primary/90 disabled:opacity-50">
          {submitting ? '登录中...' : '登录管理后台'}
        </button>
      </form>
    </div>
  );
}
