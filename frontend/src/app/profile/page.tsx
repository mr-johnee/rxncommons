'use client';
import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Link from 'next/link';
import { KeyRound, ExternalLink, Copy, Check , Lock, Globe2} from 'lucide-react';

const STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  pending_review: '审核中',
  published: '已发布',
  revision_required: '需修改',
  archived: '已归档',
};

const STATUS_STYLE: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  pending_review: 'bg-yellow-100 text-yellow-700',
  published: 'bg-green-100 text-green-700',
  revision_required: 'bg-red-100 text-red-700',
  archived: 'bg-gray-200 text-gray-500',
};

export default function ProfilePage() {
  const { user } = useAuth();
  const router = useRouter();
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'all' | 'draft' | 'pending_review' | 'published' | 'revision_required'>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [privacyFilter, setPrivacyFilter] = useState<'all' | 'public' | 'password_protected'>('all');

  const handleTogglePrivacy = async (ds: any) => {
    const isPrivate = ds.access_level === 'password_protected';
    const actionName = isPrivate ? '公开' : '私密';
    const confirmed = confirm(`确认将「${ds.title}」设为${actionName}吗？${isPrivate ? '公开后所有人均可访问和搜索该数据集。' : '私密后仅拥有专属链接的人可访问，且不对外检索。'}`);
    if (!confirmed) return;
    
    try {
      const payload: any = { access_level: isPrivate ? 'public' : 'password_protected' };
      if (!isPrivate) {
         payload.access_password = ds.access_password || Math.random().toString(36).slice(-8);
      }
      const res = await api.put(`/datasets/${ds.id}/access-policy`, payload);

      const responseNeedsReview = Boolean(res.data?.needs_review);
      const nextDatasetStatus = typeof res.data?.dataset_status === 'string' ? res.data.dataset_status : undefined;
      let refreshedItems: any[] | null = null;

      // 始终刷新一次，避免因响应模型裁剪导致前端拿不到 needs_review 字段而状态滞后。
      if (user?.username) {
        const refreshRes = await api.get(`/datasets?owner=${user.username}&limit=100`);
        refreshedItems = refreshRes.data.items || [];
        setDatasets(refreshedItems);
      } else {
        setDatasets((prev) => prev.map((item: any) => 
          item.id === ds.id
            ? {
                ...item,
                access_level: res.data?.access_level,
                access_password: payload.access_password || item.access_password,
                dataset_status: nextDatasetStatus || item.dataset_status,
              }
            : item
        ));
      }

      const refreshedTarget = Array.isArray(refreshedItems)
        ? refreshedItems.find((item: any) => item.id === ds.id)
        : null;
      const inferredNeedsReview = Boolean(
        isPrivate &&
        (responseNeedsReview || refreshedTarget?.dataset_status === 'pending_review')
      );

      // 私密 -> 公开 会进入审核：自动切到“审核中”
      if (inferredNeedsReview) {
        setTab('pending_review');
        setPrivacyFilter('all');
        alert(res.data?.message || '访问权限变更已提交审核，已切换到“审核中”列表。');
        return;
      }
      
      // 显示状态刷新成功提示
      // 如果当前使用了筛选器，自动从当前视图消失时给予明确提示
      if (privacyFilter !== 'all') {
         alert(`操作成功！数据集已转为 ${actionName}。\n(由于当前处于筛选视图，该数据集可能会从列表中隐藏)`);
      }
    } catch (err: any) {
      alert(`操作失败：${formatErrorDetail(err.response?.data?.detail || err.message)}`);
    }
  };

  const handleCopyShare = async (e: React.MouseEvent, ds: any) => {
    e.preventDefault();
    e.stopPropagation();
    const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
    const shareUrl = `${baseUrl}/datasets/${encodeURIComponent(ds.owner?.username || '')}/${ds.slug}`;
    const directUrl = ds.access_password ? `${shareUrl}?share_token=${ds.access_password}` : shareUrl;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(directUrl);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = directUrl;
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopiedId(ds.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Copy failed', err);
    }
  };



  const formatErrorDetail = (detail: unknown): string => {
    if (!detail) return '未知错误';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join('；');
    if (typeof detail === 'object') {
      const d = detail as Record<string, unknown>;
      if (d.code === 'missing_file_description') {
        const files = Array.isArray(d.files) ? d.files.join('、') : '';
        return `有文件未填写描述：${files}`;
      }
      if (d.code === 'missing_column_description') {
        return `文件 ${String(d.file || '')} 仍有列说明未填写`;
      }
      return JSON.stringify(d);
    }
    return String(detail);
  };

  useEffect(() => {
    if (!user) { router.push('/login'); return; }
    if (user.role === 'admin') { router.replace('/admin'); return; }
    const fetchMyDatasets = async () => {
      try {
        const res = await api.get(`/datasets?owner=${user.username}&limit=100`);
        setDatasets(res.data.items || []);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchMyDatasets();
  }, [user, router]);

  if (!user || loading) return <div className="text-center py-10">加载中...</div>;

  const filtered = datasets.filter(d => {
    if (tab !== 'all' && d.dataset_status !== tab) return false;
    if (privacyFilter !== 'all') {
      const isPriv = d.access_level === 'password_protected';
      if (privacyFilter === 'password_protected' && !isPriv) return false;
      if (privacyFilter === 'public' && isPriv) return false;
    }
    return true;
  });

  const counts = datasets.reduce((acc: Record<string, number>, d: any) => {
    acc[d.dataset_status] = (acc[d.dataset_status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const formatDateTime = (value?: string | null) => {
    if (!value) return '—';
    return new Date(value).toLocaleString('zh-CN');
  };

  const renderApprovedTime = (ds: any) => {
    if (ds.latest_approved_at) return formatDateTime(ds.latest_approved_at);
    return '—';
  };

  const getPrimaryLink = (ds: any) => {
    const editableVersionNum = Number(ds.latest_editable_version_num || 0);
    if (editableVersionNum > 0) {
      const modeQuery = ds.has_published_version ? '&mode=new-version' : '';
      return `/upload?datasetId=${ds.id}&versionNum=${editableVersionNum}${modeQuery}`;
    }
    if (ds.dataset_status === 'draft' || ds.dataset_status === 'revision_required') {
      const versionQuery = ds.current_version && Number(ds.current_version) > 0
        ? `&versionNum=${Number(ds.current_version)}`
        : '';
      return `/upload?datasetId=${ds.id}${versionQuery}`;
    }
    return `/datasets/${encodeURIComponent(ds.owner?.username || '')}/${encodeURIComponent(ds.slug || '')}`;
  };

  const getManageLink = (ds: any) => {
    const editableVersionNum = Number(ds.latest_editable_version_num || 0);
    if (editableVersionNum > 0) {
      const modeQuery = ds.has_published_version ? '&mode=new-version' : '';
      return `/upload?datasetId=${ds.id}&versionNum=${editableVersionNum}${modeQuery}`;
    }
    if (ds.dataset_status === 'draft' || ds.dataset_status === 'revision_required') {
      const versionQuery = ds.current_version && Number(ds.current_version) > 0
        ? `&versionNum=${Number(ds.current_version)}`
        : '';
      return `/upload?datasetId=${ds.id}${versionQuery}`;
    }
    // For published/archived: create new version
    return `/upload?datasetId=${ds.id}&mode=new-version&versionNum=${Number(ds.current_version || 0) + 1}`;
  };

  const getPrimaryActionLabel = (ds: any) => {
    if (Number(ds.latest_editable_version_num || 0) > 0) return '继续编辑';
    if (ds.dataset_status === 'draft' || ds.dataset_status === 'revision_required') return '继续编辑';
    return '管理';
  };

  const handleDeleteDataset = async (ds: any) => {
    const ownerName = ds.owner?.username || user.username;
    if (!ownerName || !ds.slug) {
      alert('缺少数据集标识，无法删除。');
      return;
    }

    const confirmed = confirm(`确认删除数据集「${ds.title}」吗？删除后将无法恢复，请谨慎操作。`);
    if (!confirmed) return;

    try {
      await api.delete(`/datasets/${encodeURIComponent(ownerName)}/${encodeURIComponent(ds.slug)}`);
      setDatasets((prev) => prev.filter((item: any) => item.id !== ds.id));
      alert('数据集已删除。');
    } catch (e: any) {
      alert('删除失败：' + (e.response?.data?.detail || e.message));
    }
  };

  const handleSubmitDraft = async (ds: any) => {
    // Warn user to review their draft before submitting
    const editableVersionNum = Number(ds.latest_editable_version_num || 0);
    if (editableVersionNum > 0) {
      const goEdit = confirm(
        `数据集「${ds.title}」有草稿 V${editableVersionNum} 尚未提交。\n\n建议先进入编辑页面检查文件描述和列说明是否完整，再从编辑页提交审核。\n\n点击"确定"前往编辑页面，点击"取消"留在当前页面。`
      );
      if (goEdit) {
        const modeQuery = ds.has_published_version ? '&mode=new-version' : '';
        router.push(`/upload?datasetId=${ds.id}&versionNum=${editableVersionNum}${modeQuery}`);
      }
      return;
    }

    try {
      let targetVersionNum = 0;
      const vRes = await api.get(`/datasets/${ds.id}/versions`);
      const draftVersions = (vRes.data || []).filter((v: any) => v.status === 'draft');
      if (draftVersions.length === 0) {
        alert('未找到可提交的草稿版本，请先进入编辑页检查。');
        return;
      }
      targetVersionNum = draftVersions.sort((a: any, b: any) => b.version_num - a.version_num)[0].version_num;

      // Also redirect to edit page for proper review
      const goEdit = confirm(
        `找到草稿版本 V${targetVersionNum}。\n\n建议先进入编辑页面检查文件描述和列说明是否完整后再提交。\n\n点击"确定"前往编辑页面。`
      );
      if (goEdit) {
        const modeQuery = ds.has_published_version ? '&mode=new-version' : '';
        router.push(`/upload?datasetId=${ds.id}&versionNum=${targetVersionNum}${modeQuery}`);
      }
    } catch (e: any) {
      alert('查询草稿失败：' + formatErrorDetail(e.response?.data?.detail || e.message));
    }
  };

  const handleCancelReview = async (ds: any) => {
    const confirmed = confirm(`确认取消「${ds.title}」当前审核吗？取消后会恢复为可编辑状态。`);
    if (!confirmed) return;

    try {
      const res = await api.post(`/datasets/${ds.id}/cancel-review`);
      const nextStatus = res.data?.dataset_status || 'draft';
      setDatasets((prev) =>
        prev.map((item: any) =>
          item.id === ds.id
            ? { ...item, dataset_status: nextStatus, status_reason: null }
            : item
        )
      );
      alert(`已取消审核，当前状态：${STATUS_LABEL[nextStatus] || nextStatus}`);
    } catch (e: any) {
      alert('取消审核失败：' + formatErrorDetail(e.response?.data?.detail || e.message));
    }
  };

  const handleArchiveDataset = async (ds: any) => {
    const confirmed = confirm(`确认归档「${ds.title}」吗？归档后该数据集将从公开页面隐藏，但可在此页恢复。`);
    if (!confirmed) return;
    try {
      await api.put(`/datasets/${ds.id}/archive`);
      setDatasets((prev) => prev.map((item: any) => (
        item.id === ds.id ? { ...item, dataset_status: 'archived' } : item
      )));
      alert('已归档。');
    } catch (e: any) {
      alert('归档失败：' + (e.response?.data?.detail || e.message));
    }
  };

  const handleUnarchiveDataset = async (ds: any) => {
    try {
      await api.put(`/datasets/${ds.id}/unarchive`);
      const restored = ds.pre_archive_status || 'published';
      setDatasets((prev) => prev.map((item: any) => (
        item.id === ds.id ? { ...item, dataset_status: restored } : item
      )));
      alert('已取消归档。');
    } catch (e: any) {
      alert('取消归档失败：' + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">我的数据管理</h1>
        <p className="text-sm text-muted-foreground mt-1">
          管理你上传的数据集与审核状态。账户信息可在
          <Link href="/account" className="text-primary hover:underline ml-1">账户信息</Link>
          页面查看。
        </p>
      </div>

      {/* Tabs + create button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-1">
            {([['all', '全部'], ['draft', '草稿'], ['pending_review', '审核中'], ['published', '已发布'], ['revision_required', '需修改']] as const).map(([key, label]) => (
              <button key={key} onClick={() => setTab(key)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium border transition-colors ${tab === key ? 'bg-primary text-primary-foreground border-primary shadow-sm' : 'bg-background text-muted-foreground border-input hover:bg-accent hover:text-accent-foreground'}`}>
                {label} {key === 'all' ? `(${datasets.length})` : counts[key] ? `(${counts[key]})` : ''}
              </button>
            ))}
          </div>
          <div className="h-5 w-px bg-border hidden sm:block mx-1"></div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPrivacyFilter(privacyFilter === 'public' ? 'all' : 'public')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-medium transition-all ${privacyFilter === 'public' ? 'bg-emerald-50 border-emerald-200 text-emerald-700 shadow-sm' : 'bg-background border-input text-muted-foreground hover:bg-accent'}`}
            >
              <Globe2 className="w-3.5 h-3.5" />
              仅看公开
            </button>
            <button
              onClick={() => setPrivacyFilter(privacyFilter === 'password_protected' ? 'all' : 'password_protected')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-medium transition-all ${privacyFilter === 'password_protected' ? 'bg-amber-50 border-amber-200 text-amber-700 shadow-sm' : 'bg-background border-input text-muted-foreground hover:bg-accent'}`}
            >
              <Lock className="w-3.5 h-3.5" />
              仅看私密
            </button>
          </div>
        </div>
        
        {user.role === 'admin' ? (
          <Link href="/admin" className="bg-primary text-primary-foreground shadow hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap text-center">
            进入管理后台
          </Link>
        ) : (
          <Link href="/upload" className="bg-primary text-primary-foreground shadow hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap text-center">
            创建新数据集
          </Link>
        )}
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-border overflow-x-auto shadow-sm transition-all">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">暂无数据集</div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-muted/50 border-b border-border text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <th className="p-4">标题</th>
                <th className="p-4 text-center border-l border-r border-transparent">状态</th>
                <th className="p-4">上传时间</th>
                <th className="p-4">审核通过时间</th>
                <th className="p-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((ds: any) => (
                <tr key={ds.id} className="border-b border-border transition-colors hover:bg-muted/50">
                  <td className="p-4">
                    <Link href={getManageLink(ds)} className="font-medium text-primary hover:underline">{ds.title}</Link>
                    <p className="text-xs text-muted-foreground mt-0.5 mono-data">{ds.owner?.username}/{ds.slug}</p>
                    {ds.is_password_protected && (
                      <div className="flex items-center gap-2 mt-1">
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-[11px] font-medium text-amber-700">
                          <KeyRound className="w-3 h-3" />
                          私密保护 {ds.access_password ? `(口令: ${ds.access_password})` : '(已设置免密口令)'}
                        </span>
                        <button 
                          onClick={(e) => handleCopyShare(e, ds)}
                          className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 underline underline-offset-2 transition-colors"
                          title="复制免密专属链接"
                        >
                          {copiedId === ds.id ? <Check className="w-3 h-3 text-green-600" /> : <Copy className="w-3 h-3" />}
                          {copiedId === ds.id ? '已复制！' : '复制专属链接'}
                        </button>
                      </div>
                    )}
                    {ds.status_reason && (
                      <p className="text-xs text-emerald-700 mt-1">审核反馈：{ds.status_reason}</p>
                    )}
                    {Number(ds.latest_editable_version_num || 0) > 0 && !['draft', 'revision_required'].includes(ds.dataset_status) && (
                      <p className="text-xs text-amber-700 mt-1">
                        草稿箱中还有未提交内容：V{ds.latest_editable_version_num}
                        {ds.latest_editable_version_status === 'revision_required' ? '（需修改）' : '（草稿）'}
                      </p>
                    )}
                  </td>
                  <td className="p-4 align-middle">
                    <div className="flex items-center justify-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${STATUS_STYLE[ds.dataset_status] || 'bg-gray-100 text-gray-700'}`}>
                        {STATUS_LABEL[ds.dataset_status] || ds.dataset_status}
                      </span>
                      <button
                        onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }}
                        className={`relative inline-flex h-6 w-14 shrink-0 cursor-pointer items-center rounded-full border border-transparent transition-colors duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                          ds.access_level === 'password_protected' ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        role="switch"
                        title={ds.access_level === 'password_protected' ? "当前：私密。点击设为公开" : "当前：公开。点击设为私密"}
                      >
                        <span className="sr-only">切换可见度</span>
                        
                        <span className={`absolute right-0 top-0 h-full w-[34px] flex items-center justify-center text-[10px] font-bold text-white transition-opacity duration-300 ${ds.access_level === 'password_protected' ? 'opacity-0' : 'opacity-100'}`}>
                          公开
                        </span>
                        
                        <span className={`absolute left-0 top-0 h-full w-[34px] flex items-center justify-center text-[10px] font-bold text-white transition-opacity duration-300 ${ds.access_level === 'password_protected' ? 'opacity-100' : 'opacity-0'}`}>
                          私密
                        </span>
                        
                        <span
                          className={`pointer-events-none z-10 flex h-[20px] w-[20px] transform items-center justify-center rounded-full bg-white shadow-sm ring-0 transition-transform duration-300 ease-in-out`}
                          style={{ transform: ds.access_level === 'password_protected' ? 'translateX(34px)' : 'translateX(0px)' }}
                        >
                          {ds.access_level === 'password_protected' ? (
                            <Lock className="h-3 w-3 text-amber-500" />
                          ) : (
                            <Globe2 className="h-3 w-3 text-emerald-500" />
                          )}
                        </span>
                      </button>
                    </div>
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">{formatDateTime(ds.created_at)}</td>
                  <td className="p-4 text-sm text-muted-foreground">{renderApprovedTime(ds)}</td>
                  <td className="p-4 text-right space-x-2">
                    {(ds.dataset_status === 'draft' || ds.latest_editable_version_status === 'draft') && (
                      <button
                        onClick={() => handleSubmitDraft(ds)}
                        className="text-primary hover:underline text-sm"
                      >
                        提交审核
                      </button>
                    )}
                    {(ds.dataset_status === 'published' || ds.dataset_status === 'revision_required') && (
                      <button
                        onClick={() => handleArchiveDataset(ds)}
                        title="归档：从公开列表隐藏，可在管理页恢复。"
                        className="text-amber-700 hover:underline text-sm"
                      >
                        归档
                      </button>
                    )}
                    {(ds.dataset_status === 'archived') && (
                      <button
                        onClick={() => handleUnarchiveDataset(ds)}
                        title="取消归档：恢复公开展示状态。"
                        className="text-blue-700 hover:underline text-sm"
                      >
                        取消归档
                      </button>
                    )}
                    {ds.dataset_status === 'pending_review' && (
                      <button
                        onClick={() => handleCancelReview(ds)}
                        className="text-amber-700 hover:underline text-sm"
                      >
                        取消审核
                      </button>
                    )}
                    <Link href={getManageLink(ds)} className="text-primary font-medium hover:underline text-sm">
                      {getPrimaryActionLabel(ds)}
                    </Link>
                    {ds.dataset_status === 'published' && (
                      <Link 
                        href={`/datasets/${encodeURIComponent(ds.owner?.username || '')}/${encodeURIComponent(ds.slug || '')}`}
                        className="text-muted-foreground hover:underline text-sm"
                      >
                        预览
                      </Link>
                    )}
                    <button
                      onClick={() => handleDeleteDataset(ds)}
                      title="删除该数据集（不可恢复）"
                      className="text-red-600 hover:underline text-sm"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
