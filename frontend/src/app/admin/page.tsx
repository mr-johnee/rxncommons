'use client';
import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';
import Link from 'next/link';
import {
  AlertTriangle,
  Ban,
  CalendarClock,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Eye,
  EyeOff,
  ListChecks,
  LockKeyhole,
  RotateCcw,
  Search,
  Star,
  StarOff,
  Trash2,
  UserRound,
  XCircle,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface ReviewRequest {
  id: string;
  dataset_id: string;
  submitted_by: string;
  status: string;
  submitted_at: string;
  version_num?: number;
  dataset?: {
    title: string;
    dataset_status?: string;
    access_level?: string;
    is_password_protected?: boolean;
    owner?: { username: string };
  };
}

interface FeaturedItem {
  dataset_id: string;
  title: string;
  dataset_status: string;
  sort_order: number;
}

interface DeletedDatasetItem {
  id: string;
  title: string;
  slug: string;
  deleted_at: string;
  owner?: {
    username?: string | null;
  };
}

const STATUS_FILTER_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'all', label: '全部状态' },
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'revision_required', label: '建议修改' },
  { value: 'canceled_by_user', label: '用户取消' },
];

const STATUS_META: Record<string, { label: string; badge: string; chip: string; selected_chip: string; icon: LucideIcon }> = {
  pending: {
    label: '待审核',
    badge: 'bg-amber-100 text-amber-800 border-amber-200',
    chip: 'bg-amber-50 text-amber-700 border-amber-200',
    selected_chip: 'bg-amber-500 text-white border-amber-600',
    icon: Clock3,
  },
  approved: {
    label: '已通过',
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    chip: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    selected_chip: 'bg-emerald-600 text-white border-emerald-700',
    icon: CheckCircle2,
  },
  rejected: {
    label: '已拒绝',
    badge: 'bg-red-100 text-red-800 border-red-200',
    chip: 'bg-red-50 text-red-700 border-red-200',
    selected_chip: 'bg-red-500 text-white border-red-600',
    icon: XCircle,
  },
  revision_required: {
    label: '建议修改',
    badge: 'bg-orange-100 text-orange-800 border-orange-200',
    chip: 'bg-orange-50 text-orange-700 border-orange-200',
    selected_chip: 'bg-orange-500 text-white border-orange-600',
    icon: AlertTriangle,
  },
  canceled_by_user: {
    label: '用户取消',
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    chip: 'bg-slate-100 text-slate-700 border-slate-200',
    selected_chip: 'bg-slate-600 text-white border-slate-700',
    icon: Ban,
  },
};

const safeStringify = (value: unknown): string => {
  try {
    return JSON.stringify(value);
  } catch {
    // JSON.stringify 通常只在循环引用时抛出，避免使用 String() 产生 "[object Object]"
    return '(序列化失败)';
  }
};

const formatErrorDetail = (detail: unknown): string => {
  if (detail == null) return '';
  if (typeof detail === 'string') return detail;
  if (typeof detail === 'number' || typeof detail === 'boolean') return String(detail);

  if (Array.isArray(detail)) {
    return detail
      .map((item) => formatErrorDetail(item))
      .filter(Boolean)
      .join('；');
  }

  if (typeof detail === 'object') {
    const d = detail as Record<string, unknown>;
    if (typeof d.message === 'string' && d.message.trim()) return d.message.trim();
    if (typeof d.code === 'string' && d.code.trim()) return d.code.trim();

    const loc = Array.isArray(d.loc) ? d.loc.map((item) => String(item)).join('.') : '';
    const msg = typeof d.msg === 'string' ? d.msg : '';
    if (loc && msg) return `${loc}: ${msg}`;
    if (msg) return msg;
    if (loc) return loc;

    return safeStringify(d);
  }

  return String(detail);
};

type ApiErrorLike = {
  response?: {
    status?: number;
    data?: {
      detail?: unknown;
    };
  };
  message?: unknown;
};

const getErrorMessage = (err: unknown): string => {
  try {
    const e = err as ApiErrorLike;
    const detailText = formatErrorDetail(e.response?.data?.detail);
    if (detailText) return detailText;
    // 直接取 message 字符串，避免将整个 error 对象传入 formatErrorDetail
    if (typeof e.message === 'string' && e.message.trim()) return e.message.trim();
    return '未知错误';
  } catch {
    return '未知错误';
  }
};

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const [requests, setRequests] = useState<ReviewRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [rollbackId, setRollbackId] = useState<string | null>(null);
  const [rollbackReason, setRollbackReason] = useState('');
  const [featured, setFeatured] = useState<FeaturedItem[]>([]);
  const [search, setSearch] = useState('');
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>(['all']);
  const [visibilityFilter, setVisibilityFilter] = useState<'all' | 'public_visible' | 'password_protected' | 'hidden_from_public'>('all');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({});
  const [deletingDatasetId, setDeletingDatasetId] = useState<string | null>(null);
  const [deletedDatasets, setDeletedDatasets] = useState<DeletedDatasetItem[]>([]);
  const [deletedTotal, setDeletedTotal] = useState(0);
  const [restoringDatasetId, setRestoringDatasetId] = useState<string | null>(null);
  const [clearingTrash, setClearingTrash] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    if (authLoading) return;
    if (user?.role === 'admin') {
      fetchRequests();
      fetchFeatured();
      fetchDeletedDatasets();
    } else {
      setLoading(false);
    }
  }, [user, authLoading]);

  const fetchRequests = async () => {
    try {
      const skip = (page - 1) * pageSize;
      const params = new URLSearchParams();
      if (search.trim()) params.set('search', search.trim());
      const statuses = selectedStatuses.includes('all') ? [] : selectedStatuses;
      if (statuses.length > 0) params.set('status_filter', statuses.join(','));
      if (visibilityFilter !== 'all') params.set('visibility_filter', visibilityFilter);
      params.set('sort_by', 'submitted_at');
      params.set('sort_order', sortOrder);
      params.set('skip', String(skip));
      params.set('limit', String(pageSize));

      const res = await api.get(`/admin/review-requests?${params.toString()}`);
      setRequests(res.data.items || []);
      setTotal(res.data.total || 0);
      setStatusCounts(res.data.status_counts || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user || user.role !== 'admin') return;
    fetchRequests();
    fetchDeletedDatasets();
  }, [user, page, search, selectedStatuses, visibilityFilter, sortOrder]);

  const toggleStatus = (status: string) => {
    setPage(1);
    setSelectedStatuses((prev) => {
      if (status === 'all') return ['all'];

      const withoutAll = prev.filter((x) => x !== 'all');
      const exists = withoutAll.includes(status);
      const next = exists ? withoutAll.filter((x) => x !== status) : [...withoutAll, status];
      return next.length > 0 ? next : ['all'];
    });
  };

  const fetchFeatured = async () => {
    try {
      const res = await api.get('/admin/home-featured');
      setFeatured(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchDeletedDatasets = async () => {
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set('search', search.trim());
      params.set('limit', '10');
      const query = params.toString();
      const res = await api.get(`/admin/datasets/deleted${query ? `?${query}` : ''}`);
      setDeletedDatasets(res.data.items || []);
      setDeletedTotal(res.data.total || 0);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleFeatured = async (datasetId: string, nextFeatured: boolean) => {
    try {
      if (nextFeatured) {
        await api.post(`/admin/home-featured/${datasetId}`);
      } else {
        await api.delete(`/admin/home-featured/${datasetId}`);
      }
      await fetchFeatured();
    } catch (err: unknown) {
      alert((nextFeatured ? '设为精选失败：' : '取消精选失败：') + getErrorMessage(err));
    }
  };

  const handleRollbackApproval = async () => {
    if (!rollbackId || !rollbackReason.trim()) {
      alert('请输入转待修订原因');
      return;
    }
    try {
      await api.post(`/admin/review-requests/${rollbackId}/rollback-approval`, { result_reason: rollbackReason });
      await fetchRequests();
      setRollbackId(null);
      setRollbackReason('');
      alert('已转为待修订。');
    } catch (err: unknown) {
      alert('操作失败：' + getErrorMessage(err));
    }
  };

  const handleDeleteDataset = async (req: ReviewRequest) => {
    const title = req.dataset?.title || `数据集 ${req.dataset_id.slice(0, 8)}...`;
    const confirmed = confirm(
      `确认将数据集「${title}」移入回收站吗？移入后普通列表中将隐藏，但管理员仍可恢复。`
    );
    if (!confirmed) return;

    setDeletingDatasetId(req.dataset_id);
    try {
      await api.delete(`/admin/datasets/${req.dataset_id}`);
      await Promise.all([fetchRequests(), fetchFeatured(), fetchDeletedDatasets()]);
      alert('数据集已移入回收站。');
    } catch (err: unknown) {
      const error = err as ApiErrorLike;
      const detail = getErrorMessage(err);
      if (error.response?.status === 404 && detail === 'Not Found') {
        alert('删除失败：当前后端尚未加载管理员回收站接口，请重启后端后重试。');
      } else {
        alert('删除失败：' + detail);
      }
    } finally {
      setDeletingDatasetId(null);
    }
  };

  const handleRestoreDataset = async (item: DeletedDatasetItem) => {
    const confirmed = confirm(`确认恢复数据集「${item.title}」吗？`);
    if (!confirmed) return;

    setRestoringDatasetId(item.id);
    try {
      await api.put(`/admin/datasets/${item.id}/restore`);
      await Promise.all([fetchRequests(), fetchFeatured(), fetchDeletedDatasets()]);
      alert('数据集已恢复。');
    } catch (err: unknown) {
      alert('恢复失败：' + getErrorMessage(err));
    } finally {
      setRestoringDatasetId(null);
    }
  };

  const handleClearTrash = async () => {
    if (deletedTotal === 0) return;
    const confirmed = confirm(
      `确认永久清空回收站吗？当前共有 ${deletedTotal} 个数据集将被彻底删除，且无法恢复。`
    );
    if (!confirmed) return;

    setClearingTrash(true);
    try {
      const res = await api.delete('/admin/datasets/deleted/clear');
      await Promise.all([fetchRequests(), fetchFeatured(), fetchDeletedDatasets()]);
      alert(`已永久清空回收站，共清除 ${res.data?.purged_count ?? 0} 个数据集。`);
    } catch (err: unknown) {
      console.error('[清空回收站] 错误详情:', err);
      alert('清空失败：' + getErrorMessage(err));
    } finally {
      setClearingTrash(false);
    }
  };

  if (authLoading) return <div className="text-center py-10">加载中...</div>;

  if (!user) {
    return (
      <div className="max-w-xl mx-auto mt-16 bg-white border rounded-lg p-8 text-center">
        <h2 className="text-xl font-bold mb-2">管理员登录</h2>
        <p className="text-gray-600 mb-6">请先登录管理员账号后再进入审核后台。</p>
        <Link href="/admin/login" className="inline-block px-5 py-2.5 bg-primary text-primary-foreground rounded hover:bg-primary/90 shadow">前往管理员登录</Link>
      </div>
    );
  }

  if (user.role !== 'admin') {
    return <div className="text-center py-20 text-red-500 font-bold">权限不足，仅管理员可访问。</div>;
  }
  if (loading) return <div className="text-center py-10">加载中...</div>;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const totalCount = Object.values(statusCounts).reduce((a, b) => a + b, 0);

  const summaryCards = [
    { key: 'total', label: '总数', count: totalCount, icon: ListChecks, cls: 'bg-slate-50 text-slate-800 border-slate-200' },
    { key: 'pending', label: '待审核', count: statusCounts.pending || 0, icon: Clock3, cls: 'bg-amber-50 text-amber-800 border-amber-200' },
    { key: 'approved', label: '已通过', count: statusCounts.approved || 0, icon: CheckCircle2, cls: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
    { key: 'rejected', label: '已拒绝', count: statusCounts.rejected || 0, icon: XCircle, cls: 'bg-red-50 text-red-800 border-red-200' },
    { key: 'revision_required', label: '建议修改', count: statusCounts.revision_required || 0, icon: AlertTriangle, cls: 'bg-orange-50 text-orange-800 border-orange-200' },
    { key: 'canceled_by_user', label: '用户取消', count: statusCounts.canceled_by_user || 0, icon: Ban, cls: 'bg-slate-100 text-slate-700 border-slate-200' },
  ];

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="mb-5">
        <h1 className="text-2xl font-bold text-slate-900">管理后台 · 审核工作台</h1>
        <p className="text-sm text-slate-500 mt-1">统一处理数据集审核请求、精选推荐与纠偏操作。</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 mb-5">
        {summaryCards.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.key} className={`rounded-xl border p-3 ${item.cls}`}>
              <div className="inline-flex items-center gap-1.5 text-xs font-medium">
                <Icon className="h-3.5 w-3.5" />
                {item.label}
              </div>
              <div className="mt-2 text-2xl font-bold">{item.count}</div>
            </div>
          );
        })}
      </div>
      <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
        统计口径：上方状态数按“审核请求记录”统计（一次提交/重提/处理都会生成一条记录），并受当前搜索关键词影响；下方状态筛选仅决定列表展示哪些记录。
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-4 mb-4 shadow-sm">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
          <div className="lg:col-span-2 relative">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={search}
              onChange={(e) => { setPage(1); setSearch(e.target.value); }}
              placeholder="按数据集标题或提交者检索"
              className="w-full border border-input bg-background rounded-lg pl-9 pr-3 py-2 text-sm"
            />
          </div>
          <div className="relative">
            <Eye className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <select
              value={visibilityFilter}
              onChange={(e) => { setPage(1); setVisibilityFilter(e.target.value as 'all' | 'public_visible' | 'password_protected'); }}
              className="w-full border border-input bg-background rounded-lg pl-9 pr-3 py-2 text-sm appearance-none"
            >
              <option value="all">所有权限状态</option>
              <option value="public_visible">对外公开展示</option>
              <option value="password_protected">已设为私密 (密码保护)</option>
            </select>
          </div>
          <div className="relative">
            <CalendarClock className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
              className="w-full border border-input bg-background rounded-lg pl-9 pr-3 py-2 text-sm appearance-none"
            >
              <option value="desc">提交时间：从新到旧</option>
              <option value="asc">提交时间：从旧到新</option>
            </select>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 pt-3">
          {STATUS_FILTER_OPTIONS.map((option) => {
            const active = selectedStatuses.includes(option.value);
            const count = option.value === 'all' ? totalCount : (statusCounts[option.value] || 0);
            const meta = STATUS_META[option.value];
            const Icon = meta?.icon || ListChecks;
            return (
              <button
                key={option.value}
                onClick={() => toggleStatus(option.value)}
                className={`px-3 py-1.5 text-xs rounded-full border transition-colors inline-flex items-center gap-1.5 ${
                  active
                    ? (meta ? `${meta.selected_chip} shadow-sm` : 'bg-primary text-primary-foreground border-primary shadow-sm')
                    : 'bg-background text-muted-foreground border-input hover:bg-slate-100 hover:text-slate-800'
                }`}
                type="button"
              >
                <Icon className="h-3 w-3" />
                {option.label}
                <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${active ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'}`}>{count}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-3">
        {requests.map((req) => {
          const meta = STATUS_META[req.status];
          const StatusIcon = meta?.icon || ListChecks;
          const isProtected = req.dataset?.is_password_protected || req.dataset?.access_level === 'password_protected';
          const isPublicVisible = !isProtected && req.dataset?.dataset_status === 'published';
          const isFeatured = featured.some((f) => f.dataset_id === req.dataset_id);
          const canReviewNow = req.status === 'pending';
          const primaryActionLabel = canReviewNow ? '进入审核' : '查看记录';
          const primaryActionClassName = canReviewNow
            ? 'bg-primary text-primary-foreground shadow hover:bg-primary/90'
            : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50';
          return (
            <div key={req.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                  <Link href={`/admin/review-requests/${req.id}`} className="font-semibold text-primary hover:underline break-words">
                    {req.dataset?.title || `数据集 ${req.dataset_id.slice(0, 8)}...`}
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
                      <UserRound className="h-3 w-3" />
                      提交者 {req.dataset?.owner?.username || req.submitted_by}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
                      <CalendarClock className="h-3 w-3" />
                      {new Date(req.submitted_at).toLocaleString('zh-CN')}
                    </span>
                    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 ${meta?.badge || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                      <StatusIcon className="h-3 w-3" />
                      {meta?.label || req.status}
                    </span>
                    {req.version_num != null && (
                      <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-1 text-slate-600">
                        版本 V{req.version_num}
                      </span>
                    )}
                    {(() => {
                      if (isProtected) {
                        return (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
                            <LockKeyhole className="h-3 w-3" />
                            隐私数据集
                          </span>
                        );
                      }
                      
                      if (req.status === 'approved') {
                        return isPublicVisible ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-sky-200 bg-sky-50 px-2 py-1 text-sky-700">
                            <Eye className="h-3 w-3" />
                            已发布可见
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-slate-700">
                            <EyeOff className="h-3 w-3" />
                            数据集全局不可见
                          </span>
                        );
                      }
                      
                      if (req.status === 'pending') {
                        return req.dataset?.dataset_status === 'published' ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
                            <Clock3 className="h-3 w-3" />
                            新版本审核中
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-slate-700">
                            <EyeOff className="h-3 w-3" />
                            首次提审，普通用户不可见
                          </span>
                        );
                      }
                      
                      // rejected 等
                      return (
                        <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-slate-700">
                          <EyeOff className="h-3 w-3" />
                          该版本不可见
                        </span>
                      );
                    })()}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    href={`/admin/review-requests/${req.id}`}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors inline-flex items-center gap-1 ${primaryActionClassName}`}
                  >
                    <Eye className="h-3.5 w-3.5" />
                    {primaryActionLabel}
                  </Link>
                  {req.status === 'approved' && isPublicVisible && (
                    <button
                      onClick={() => toggleFeatured(req.dataset_id, !isFeatured)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors inline-flex items-center gap-1 ${
                        isFeatured
                          ? 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                          : 'bg-primary text-primary-foreground shadow hover:bg-primary/90'
                      }`}
                    >
                      {isFeatured ? <StarOff className="h-3.5 w-3.5" /> : <Star className="h-3.5 w-3.5" />}
                      {isFeatured ? '取消精选' : '设为精选'}
                    </button>
                  )}
                  {req.status === 'approved' && (
                    <button
                      onClick={() => { setRollbackId(req.id); setRollbackReason(''); }}
                      className="px-3 py-1.5 text-xs font-medium rounded-md bg-orange-100 text-orange-700 hover:bg-orange-200 inline-flex items-center gap-1"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      转待修订
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteDataset(req)}
                    disabled={deletingDatasetId === req.dataset_id}
                    className="px-3 py-1.5 text-xs font-medium rounded-md bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-60 disabled:cursor-not-allowed inline-flex items-center gap-1"
                    title="移入回收站：从普通列表隐藏，但管理员可恢复。"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    {deletingDatasetId === req.dataset_id ? '处理中...' : '移入回收站'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
        {requests.length === 0 && (
          <div className="text-center text-slate-500 py-12 bg-white border border-slate-200 rounded-xl">
            没有匹配的审核记录。
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-3 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 border border-slate-300 rounded-md bg-white disabled:opacity-40 inline-flex items-center gap-1 text-sm"
          >
            <ChevronLeft className="h-4 w-4" />
            上一页
          </button>
          <span className="text-sm text-slate-600">第 {page} / {totalPages} 页</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 border border-slate-300 rounded-md bg-white disabled:opacity-40 inline-flex items-center gap-1 text-sm"
          >
            下一页
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">回收站</h2>
            <p className="mt-1 text-sm text-slate-500">移入回收站的数据集会从普通列表隐藏，但保留版本与文件，可由管理员恢复。</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              共 {deletedTotal} 项
            </span>
            <button
              type="button"
              onClick={handleClearTrash}
              disabled={deletedTotal === 0 || clearingTrash}
              className="inline-flex items-center justify-center gap-1 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {clearingTrash ? '清空中...' : '一键清空回收站'}
            </button>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {deletedDatasets.map((item) => (
            <div key={item.id} className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="font-medium text-slate-900 break-words">{item.title}</div>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 border border-slate-200">
                    作者 {item.owner?.username || '—'}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-1 border border-slate-200">
                    删除于 {new Date(item.deleted_at).toLocaleString('zh-CN')}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleRestoreDataset(item)}
                disabled={restoringDatasetId === item.id}
                className="inline-flex items-center justify-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                {restoringDatasetId === item.id ? '恢复中...' : '恢复数据集'}
              </button>
            </div>
          ))}
          {deletedDatasets.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-4 py-8 text-center text-sm text-slate-500">
              当前回收站为空。
            </div>
          )}
        </div>
      </div>

      {rollbackId && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-md border border-slate-200">
            <h3 className="text-lg font-bold mb-2">转为待修订</h3>
            <p className="text-sm text-slate-500 mb-3">请填写纠偏原因，系统将通知作者进行修订。</p>
            <textarea
              value={rollbackReason}
              onChange={(e) => setRollbackReason(e.target.value)}
              className="w-full border border-input rounded-lg p-2 h-28 text-sm"
              placeholder="例如：检测到关键字段定义不清晰，请补充列说明并重新提交。"
            />
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setRollbackId(null)} className="px-4 py-2 border rounded-md hover:bg-gray-50 text-sm">取消</button>
              <button onClick={handleRollbackApproval} className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 text-sm">确认转待修订</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
