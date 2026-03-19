'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { getSourceTypeLabel } from '@/lib/dataset-meta';
import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Columns3,
  Database,
  Download,
  Eye,
  FileSearch,
  FileText,
  FlaskConical,
  LayoutPanelTop,
  ShieldCheck,
  Trash2,
  XCircle,
} from 'lucide-react';

interface ReviewHistoryItem {
  id: string;
  status: string;
  submitted_at: string;
  reviewed_at?: string;
  result_reason?: string;
  version_num?: number;
}

interface ReviewDetail {
  history?: ReviewHistoryItem[];
  request: {
    id: string;
    status: string;
    submitted_at: string;
    submitted_by: string;
    requested_version_num?: number | null;
    reviewed_at?: string;
    reviewed_by?: string;
    result_reason?: string;
  };
  dataset: {
    id: string;
    title: string;
    slug: string;
    dataset_status: string;
    description: string;
    source_type?: string;
    source_ref?: string;
    license?: string;
    status_reason?: string;
  };
  version: {
    version_num: number | null;
    version_note?: string;
    status?: string;
  };
  files: Array<{
    id: string;
    filename: string;
    file_size: number;
    description?: string;
    row_count?: number;
    columns: Array<{ column_name: string; column_type?: string; description?: string }>;
  }>;
}

type FilePreview = {
  preview_type: 'table' | 'text';
  columns: string[];
  rows: Array<Record<string, any>>;
  truncated?: boolean;
  error?: string;
};

const REQUEST_STATUS_META: Record<string, { label: string; chip: string; icon: any }> = {
  pending: {
    label: '待审核',
    chip: 'bg-amber-50 border-amber-200 text-amber-700',
    icon: Clock3,
  },
  approved: {
    label: '已通过',
    chip: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    icon: CheckCircle2,
  },
  rejected: {
    label: '已拒绝',
    chip: 'bg-red-50 border-red-200 text-red-700',
    icon: XCircle,
  },
  revision_required: {
    label: '建议修改',
    chip: 'bg-orange-50 border-orange-200 text-orange-700',
    icon: AlertTriangle,
  },
  canceled_by_user: {
    label: '用户取消',
    chip: 'bg-slate-100 border-slate-200 text-slate-700',
    icon: Ban,
  },
};

const DATASET_STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  pending_review: '审核中',
  published: '已发布',
  revision_required: '需修改',
  archived: '已归档',
  takedown: '下架',
  deleted: '已删除',
};

export default function AdminReviewDetailPage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionReason, setActionReason] = useState('');
  const [decisionType, setDecisionType] = useState<'approve' | 'suggest' | 'reject'>('approve');
  const [acting, setActing] = useState(false);
  const [deletingDataset, setDeletingDataset] = useState(false);
  const [previewByFileId, setPreviewByFileId] = useState<Record<string, FilePreview>>({});

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push('/admin/login');
      return;
    }
    if (user.role !== 'admin') {
      setLoading(false);
      return;
    }
    api.get(`/admin/review-requests/${id}`)
      .then((res) => setDetail(res.data))
      .catch((err) => alert(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [id, user, authLoading, router]);

  const reload = async () => {
    const res = await api.get(`/admin/review-requests/${id}`);
    setDetail(res.data);
  };

  const submitDecision = async () => {
    const reason = actionReason.trim();

    if (decisionType !== 'approve' && reason.length === 0) {
      alert(decisionType === 'suggest' ? '请填写修改建议。' : '请填写拒绝原因。');
      return;
    }

    const confirmText = decisionType === 'approve'
      ? '确认直接通过该审核请求吗？'
      : decisionType === 'suggest'
        ? '确认将该请求标记为建议修改吗？'
        : '确认拒绝该审核请求吗？';

    if (!confirm(confirmText)) return;

    setActing(true);
    try {
      if (decisionType === 'approve') {
        await api.post(`/admin/review-requests/${id}/approve`, { result_reason: reason || undefined });
        alert('已通过并发布。');
      } else if (decisionType === 'suggest') {
        await api.post(`/admin/review-requests/${id}/suggest`, { result_reason: reason });
        alert('已提交修改建议。');
      } else {
        await api.post(`/admin/review-requests/${id}/reject`, { result_reason: reason });
        alert('已拒绝该请求。');
      }
      await reload();
      setActionReason('');
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    } finally {
      setActing(false);
    }
  };

  const rollbackApproval = async () => {
    const reason = actionReason.trim();
    if (reason.length === 0) {
      alert('请填写转待修订原因。');
      return;
    }
    setActing(true);
    try {
      await api.post(`/admin/review-requests/${id}/rollback-approval`, { result_reason: reason });
      await reload();
      alert('已转为待修订。');
      setActionReason('');
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    } finally {
      setActing(false);
    }
  };

  const handleDownloadFile = (fileId: string) => {
    if (!detail) return;
    const a = document.createElement('a');
    a.href = `/api/datasets/${detail.dataset.id}/files/${fileId}/download`;
    a.click();
  };

  const handleDownloadAll = () => {
    if (!detail) return;
    const versionNum = detail.request.requested_version_num || detail.request.version_num || detail.dataset.current_version || 1;
    const a = document.createElement('a');
    a.href = `/api/datasets/${detail.dataset.id}/versions/${versionNum}/download-all`;
    a.click();
  };

  const handleDeleteDataset = async () => {
    if (!detail) return;
    const confirmed = confirm(
      `确认将数据集「${detail.dataset.title}」移入回收站吗？移入后普通列表中将隐藏，但管理员仍可恢复。`
    );
    if (!confirmed) return;

    setDeletingDataset(true);
    try {
      await api.delete(`/admin/datasets/${detail.dataset.id}`);
      alert('数据集已移入回收站。');
      router.push('/admin');
    } catch (err: any) {
      const detailMessage = err.response?.data?.detail || err.message;
      if (err.response?.status === 404 && detailMessage === 'Not Found') {
        alert('删除失败：当前后端尚未加载管理员回收站接口，请重启后端后重试。');
      } else {
        alert('删除失败：' + detailMessage);
      }
    } finally {
      setDeletingDataset(false);
    }
  };

  useEffect(() => {
    if (!detail || !detail.files?.length) {
      setPreviewByFileId({});
      return;
    }
    let cancelled = false;

    const loadPreviews = async () => {
      const results = await Promise.all(
        detail.files.map(async (f) => {
          try {
            const res = await api.get(`/datasets/${detail.dataset.id}/files/${f.id}/preview`);
            return [f.id, res.data as FilePreview] as const;
          } catch {
            return [f.id, {
              preview_type: 'text',
              columns: ['content'],
              rows: [{ content: '预览加载失败，请稍后重试。' }],
              error: 'preview_failed',
            } as FilePreview] as const;
          }
        })
      );
      if (!cancelled) {
        setPreviewByFileId(Object.fromEntries(results));
      }
    };

    loadPreviews();
    return () => {
      cancelled = true;
    };
  }, [detail]);

  useEffect(() => {
    if (detail?.request.status === 'pending') {
      setDecisionType('approve');
    }
  }, [detail?.request.id, detail?.request.status]);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (authLoading || loading) return <div className="text-center py-10">加载中...</div>;
  if (!user || user.role !== 'admin') return <div className="text-center py-10 text-red-600">仅管理员可访问</div>;
  if (!detail) return <div className="text-center py-10 text-gray-500">未找到审核请求</div>;
  const versionDisplayLabel = detail.version.status === 'published'
    ? `V${detail.version.version_num ?? '-'}`
    : '待发布草稿（未发布编号）';
  const requestMeta = REQUEST_STATUS_META[detail.request.status] || {
    label: detail.request.status,
    chip: 'bg-slate-100 border-slate-200 text-slate-700',
    icon: LayoutPanelTop,
  };
  const RequestStatusIcon = requestMeta.icon;
  const datasetStatusLabel = DATASET_STATUS_LABEL[detail.dataset.dataset_status] || detail.dataset.dataset_status;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <div className="mb-6 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">审核详情</h1>
          <p className="mt-1 text-sm text-slate-500">查看数据集内容与审核上下文后再执行处理动作。</p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <button
            onClick={handleDeleteDataset}
            disabled={deletingDataset}
            className="inline-flex items-center gap-1.5 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-sm text-red-700 hover:bg-red-100 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Trash2 className="h-4 w-4" />
            {deletingDataset ? '处理中...' : '移入回收站'}
          </button>
          <button
            onClick={() => router.push('/admin')}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            <ArrowLeft className="h-4 w-4" />
            返回列表
          </button>
        </div>
      </div>

      <div className="mb-6 rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-white to-slate-50 p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h2 className="text-xl font-semibold text-slate-900 break-words">{detail.dataset.title}</h2>
          <div className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${requestMeta.chip}`}>
            <RequestStatusIcon className="h-3.5 w-3.5" />
            {requestMeta.label}
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-slate-700">
            <ShieldCheck className="h-3.5 w-3.5" />
            数据集状态 {datasetStatusLabel}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-slate-700">
            <LayoutPanelTop className="h-3.5 w-3.5" />
            版本 {versionDisplayLabel}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-slate-700">
            <FlaskConical className="h-3.5 w-3.5" />
            来源 {getSourceTypeLabel(detail.dataset.source_type)}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-slate-700">
            License {detail.dataset.license || '—'}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1">
            <CalendarClock className="h-3.5 w-3.5 text-slate-500" />
            提交 {new Date(detail.request.submitted_at).toLocaleString('zh-CN')}
          </span>
          {detail.request.reviewed_at && (
            <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1">
              <CalendarClock className="h-3.5 w-3.5 text-slate-500" />
              处理 {new Date(detail.request.reviewed_at).toLocaleString('zh-CN')}
            </span>
          )}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
              <FileText className="h-4 w-4 text-primary" />
              数据集描述
            </h3>
            <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{detail.dataset.description || '暂无描述'}</p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
            <h3 className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-primary">
              <FileSearch className="h-4 w-4 text-primary" />
              版本说明（提交人填写）
            </h3>
            <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{detail.version.version_note || '—'}</p>
          </div>
        </div>

        {detail.request.result_reason ? (
          <div className="mt-4 rounded-xl border border-orange-200 bg-orange-50 p-3 text-sm text-orange-900 whitespace-pre-wrap">
            <span className="font-medium">本次处理补充说明：</span>{detail.request.result_reason}
          </div>
        ) : null}
      </div>

      {/* 审核操作历史时间线 */}
      {detail.history && detail.history.length > 0 && (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="mb-4 text-lg font-semibold text-slate-900">审核操作历史</h3>
          <div className="relative pl-6 border-l-2 border-slate-200 space-y-4">
            {detail.history.map((h, idx) => {
              const hMeta = REQUEST_STATUS_META[h.status];
              const HIcon = hMeta?.icon || Clock3;
              const isLatest = idx === 0;
              const dotColor =
                h.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                h.status === 'rejected' ? 'bg-red-100 text-red-700' :
                h.status === 'revision_required' ? 'bg-orange-100 text-orange-700' :
                h.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                'bg-slate-100 text-slate-700';
              return (
                <div key={h.id} className="relative">
                  <div className={`absolute -left-[calc(0.75rem+1px)] top-1 w-5 h-5 rounded-full flex items-center justify-center ${dotColor}`}>
                    <HIcon className="h-3 w-3" />
                  </div>
                  <div className={`rounded-lg border p-3 ${isLatest ? 'border-primary/30 bg-primary/5' : 'border-slate-200 bg-slate-50/40'}`}>
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-medium ${hMeta?.chip || 'bg-slate-100 border-slate-200 text-slate-700'}`}>
                        {hMeta?.label || h.status}
                      </span>
                      {h.version_num != null && (
                        <span className="text-slate-500">版本 V{h.version_num}</span>
                      )}
                      <span className="text-slate-500">提交于 {new Date(h.submitted_at).toLocaleString('zh-CN')}</span>
                      {h.reviewed_at && (
                        <span className="text-slate-400">→ 处理于 {new Date(h.reviewed_at).toLocaleString('zh-CN')}</span>
                      )}
                    </div>
                    {h.result_reason && (
                      <div className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">{h.result_reason}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">文件与列说明</h3>
            {detail.files.length > 0 && (
              <button
                onClick={handleDownloadAll}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary hover:bg-primary/20 transition-colors"
                title="下载该版本所有文件"
              >
                <Download className="h-4 w-4" />
                下载全部
              </button>
            )}
          </div>
          <div className="space-y-4">
            {detail.files.map((f) => (
              <article key={f.id} className="rounded-xl border border-slate-200 bg-slate-50/40 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="inline-flex items-center gap-3 text-slate-900 font-medium min-w-0">
                    <div className="inline-flex items-center gap-2">
                      <FileText className="h-4 w-4 text-primary shrink-0" />
                      <span className="break-all">{f.filename}</span>
                    </div>
                    <button
                      onClick={() => handleDownloadFile(f.id)}
                      className="inline-flex items-center justify-center rounded-md p-1.5 text-slate-400 hover:bg-white hover:text-primary hover:shadow-sm border border-transparent hover:border-slate-200 transition-all"
                      title="下载此文件"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2 text-[11px] text-slate-700">
                    <span className="inline-flex items-center gap-1 rounded-full bg-white border border-slate-200 px-2 py-1">
                      <Database className="h-3.5 w-3.5" />
                      大小 {formatSize(Number(f.file_size || 0))}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-white border border-slate-200 px-2 py-1">
                      <FlaskConical className="h-3.5 w-3.5" />
                      条目 {f.row_count ?? '-'}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-white border border-slate-200 px-2 py-1">
                      <Columns3 className="h-3.5 w-3.5" />
                      列数 {f.columns.length}
                    </span>
                  </div>
                </div>

                <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-700">
                  文件描述：{f.description || '（未填写）'}
                </div>

                <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                  <div className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
                      <Eye className="h-4 w-4 text-primary" />
                      文件内容预览
                    </div>
                    {previewByFileId[f.id] ? (
                      previewByFileId[f.id].preview_type === 'table' && previewByFileId[f.id].columns?.length ? (
                        <div className="max-h-64 overflow-auto rounded border border-slate-200 bg-white">
                          <table className="min-w-max text-xs border-collapse">
                            <thead className="sticky top-0 z-10 bg-slate-100">
                              <tr>
                                {previewByFileId[f.id].columns.map((c) => (
                                  <th key={`${f.id}-${c}`} className="px-2.5 py-2 text-left border-b border-r border-slate-200 whitespace-nowrap">{c}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {previewByFileId[f.id].rows.map((row, idx) => (
                                <tr key={`${f.id}-${idx}`} className="odd:bg-white even:bg-slate-50/60">
                                  {previewByFileId[f.id].columns.map((c) => (
                                    <td key={`${f.id}-${idx}-${c}`} className="px-2.5 py-1.5 border-b border-r border-slate-100 whitespace-nowrap">{String(row[c] ?? '')}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <pre className="max-h-64 overflow-auto rounded border border-slate-200 bg-white p-3 text-xs whitespace-pre">
                          {(previewByFileId[f.id].rows || []).map((r) => String((r as any).content || '')).join('\n')}
                        </pre>
                      )
                    ) : (
                      <div className="text-xs text-slate-500">预览加载中...</div>
                    )}
                  </div>

                  <div className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
                      <Columns3 className="h-4 w-4 text-primary" />
                      列说明
                    </div>
                    <div className="max-h-64 overflow-auto rounded border border-slate-200">
                      <table className="w-full text-xs border-collapse bg-white">
                        <thead className="bg-slate-50 sticky top-0 z-10">
                          <tr className="border-b border-slate-200">
                            <th className="text-left p-2">列名</th>
                            <th className="text-left p-2">列说明</th>
                          </tr>
                        </thead>
                        <tbody>
                          {f.columns.map((c) => (
                            <tr key={`${f.id}-${c.column_name}`} className="border-b border-slate-100">
                              <td className="p-2 whitespace-nowrap">{c.column_name}</td>
                              <td className="p-2">{c.description || '（未填写）'}</td>
                            </tr>
                          ))}
                          {f.columns.length === 0 && (
                            <tr>
                              <td className="p-2 text-gray-500" colSpan={2}>暂无列信息</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </article>
            ))}
            {detail.files.length === 0 && <div className="text-sm text-gray-500">该版本暂无文件。</div>}
          </div>
        </div>

        <aside className="xl:sticky xl:top-20 h-fit rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="mb-3 text-lg font-semibold text-slate-900">审核操作</h3>
          <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
            当前请求状态：<span className="font-medium text-slate-800">{requestMeta.label}</span>
          </div>

          {detail.request.status === 'pending' && (
            <>
              <div className="text-sm text-slate-600 mb-3">处理方式（单次只能执行一种）</div>
              <div className="grid grid-cols-1 gap-2 mb-3">
                {[
                  { value: 'approve', label: '通过发布', activeCls: 'border-emerald-300 text-emerald-700 bg-emerald-50' },
                  { value: 'suggest', label: '建议修改', activeCls: 'border-amber-300 text-amber-700 bg-amber-50' },
                  { value: 'reject', label: '拒绝请求', activeCls: 'border-red-300 text-red-700 bg-red-50' },
                ].map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setDecisionType(option.value as 'approve' | 'suggest' | 'reject')}
                    className={`px-3 py-2 rounded-md border text-sm text-left transition-colors ${
                      decisionType === option.value
                        ? option.activeCls
                        : 'border-slate-200 text-slate-600 bg-white hover:bg-slate-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                className="w-full border border-input rounded-md p-2.5 h-28 text-sm mb-3"
                placeholder={
                  decisionType === 'approve'
                    ? '可选：填写通过意见（留空也可通过）...'
                    : decisionType === 'suggest'
                      ? '填写需要作者修改的内容...'
                      : '填写拒绝原因...'
                }
              />
              <button
                disabled={acting}
                onClick={submitDecision}
                className={`w-full px-4 py-2 text-white rounded-md disabled:opacity-50 ${
                  decisionType === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : decisionType === 'suggest'
                      ? 'bg-amber-600 hover:bg-amber-700'
                      : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {decisionType === 'approve' ? '确认通过' : decisionType === 'suggest' ? '提交修改建议' : '确认拒绝'}
              </button>
            </>
          )}

          {detail.request.status === 'approved' && (
            <>
              <div className="rounded-lg border border-orange-200 bg-orange-50 p-3 text-xs text-orange-800 mb-3">
                当前已通过。若发现问题，可填写原因并转为待修订。
              </div>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                className="w-full border border-input rounded-md p-2.5 h-28 text-sm mb-3"
                placeholder="填写纠偏原因，将该审核结果转为待修订..."
              />
              <button
                disabled={acting}
                onClick={rollbackApproval}
                className="w-full px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50"
              >
                转为待修订
              </button>
            </>
          )}

          {detail.request.status !== 'pending' && detail.request.status !== 'approved' && (
            <div className="text-sm text-slate-500">当前状态无需额外审核操作。</div>
          )}
        </aside>
      </div>
    </div>
  );
}
