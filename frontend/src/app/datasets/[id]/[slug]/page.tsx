'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';

export default function DatasetCanonicalPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const owner = params.id as string;
  const slug = params.slug as string;
  const router = useRouter();
  const [error, setError] = useState('');
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [password, setPassword] = useState(searchParams?.get('share_token') || '');
  const [unlocking, setUnlocking] = useState(false);

  const canonicalKey = `dataset_access_owner_slug_${owner}/${slug}`;

  const withCanonicalToken = () => {
    if (typeof window === 'undefined') return {};
    const token = sessionStorage.getItem(canonicalKey);
    if (!token) return {};
    return { headers: { 'X-Dataset-Access-Token': token } };
  };

  const resolveDataset = async () => {
    try {
      const res = await api.get(`/datasets/${encodeURIComponent(owner)}/${encodeURIComponent(slug)}`, withCanonicalToken());
      if (typeof window !== 'undefined') {
        const token = sessionStorage.getItem(canonicalKey);
        if (token) {
          sessionStorage.setItem(`dataset_access_token_${res.data.id}`, token);
        }
      }
      const isManage = searchParams?.get('manage') === 'true';
      router.replace(`/datasets/${res.data.id}${isManage ? '?manage=true' : ''}`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 403 && detail?.code === 'dataset_access_password_required') {
        const shareToken = searchParams?.get('share_token');
        if (shareToken) {
          try {
            const res = await api.post(`/datasets/${encodeURIComponent(owner)}/${encodeURIComponent(slug)}/access/unlock`, {
              password: shareToken,
            });
            const token = res.data?.access_token;
            const datasetId = res.data?.dataset_id;
            if (token && datasetId) {
              if (typeof window !== 'undefined') {
                sessionStorage.setItem(canonicalKey, token);
                sessionStorage.setItem(`dataset_access_token_${datasetId}`, token);
              }
              // include manage parameter if present
              const isManage = searchParams?.get('manage') === 'true';
              router.replace(`/datasets/${datasetId}${isManage ? '?manage=true' : ''}`);
              return;
            }
          } catch (autoErr) {
            setError('链接中的访问口令已失效或错误，请重新输入。');
            setPassword(shareToken);
          }
        }
        setPasswordRequired(true);
        return;
      }
      setError(typeof detail === 'string' ? detail : '数据集不存在或你暂无访问权限。');
    }
  };

  const handleUnlock = async () => {
    if (!password.trim()) {
      setError('请输入访问密码。');
      return;
    }
    setUnlocking(true);
    setError('');
    try {
      const res = await api.post(`/datasets/${encodeURIComponent(owner)}/${encodeURIComponent(slug)}/access/unlock`, {
        password: password.trim(),
      });
      const token = res.data?.access_token;
      const datasetId = res.data?.dataset_id;
      if (!token || !datasetId) {
        throw new Error('missing_unlock_data');
      }
      if (typeof window !== 'undefined') {
        sessionStorage.setItem(canonicalKey, token);
        sessionStorage.setItem(`dataset_access_token_${datasetId}`, token);
      }
      const isManage = searchParams?.get('manage') === 'true';
      router.replace(`/datasets/${datasetId}${isManage ? '?manage=true' : ''}`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (detail === 'invalid_dataset_password') {
        setError('访问密码错误，请重试。');
      } else {
        setError('解锁失败，请稍后重试。');
      }
    } finally {
      setUnlocking(false);
    }
  };

  useEffect(() => {
    if (owner && slug) {
      resolveDataset();
    }
  }, [owner, slug]);

  if (passwordRequired) {
    return (
      <div className="max-w-md mx-auto py-16 px-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <h1 className="text-lg font-semibold text-amber-900 mb-2">此数据集受密码保护</h1>
          <p className="text-sm text-amber-800 mb-4">请输入访问密码以继续进入该数据集页面。</p>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="输入访问密码"
            className="w-full border rounded-md p-2 text-sm mb-3"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleUnlock();
              }
            }}
          />
          {error && <p className="text-xs text-red-600 mb-2">{error}</p>}
          <button
            onClick={handleUnlock}
            disabled={unlocking}
            className="w-full rounded-md bg-primary text-primary-foreground py-2 text-sm font-medium disabled:opacity-60"
          >
            {unlocking ? '验证中...' : '解锁并进入'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-16 px-4 text-center text-sm text-muted-foreground">
      {error || '正在跳转到数据集详情...'}
    </div>
  );
}
