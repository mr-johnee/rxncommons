'use client';
import Link from 'next/link';
import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function AccountPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push('/login');
      return;
    }
    if (user.role === 'admin') {
      router.replace('/admin');
    }
  }, [user, loading, router]);

  if (loading || !user) return <div className="text-center py-10">加载中...</div>;

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">账户信息</h1>
        <p className="text-sm text-muted-foreground mt-1">
          查看你的基本信息。数据集管理请前往
          <Link href="/profile" className="text-primary hover:underline ml-1">我的数据</Link>
          。
        </p>
      </div>

      <div className="bg-card p-6 rounded-lg border border-border shadow-sm">
        <h2 className="text-xl font-semibold mb-4 text-foreground">{user.username}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-sm">
          <div>
            <span className="text-muted-foreground block mb-1">邮箱</span>
            <span className="text-foreground font-medium">{user.email}</span>
          </div>
          <div>
            <span className="text-muted-foreground block mb-1">注册时间</span>
            <span className="text-foreground font-medium">{new Date((user as any).created_at || Date.now()).toLocaleDateString('zh-CN')}</span>
          </div>
          <div>
            <span className="text-muted-foreground block mb-1">所属机构</span>
            <span className="text-foreground font-medium">{(user as any).institution || '—'}</span>
          </div>
          <div>
            <span className="text-muted-foreground block mb-1">研究方向</span>
            <span className="text-foreground font-medium">{(user as any).research_area || '—'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
