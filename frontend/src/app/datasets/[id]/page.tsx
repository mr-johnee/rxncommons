'use client';
import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';
import { FlaskConical, Download, Eye, ArrowDownToLine, FileText, Columns3, FileSearch, LayoutPanelTop, UserRound, CalendarClock, ThumbsUp, Share2, Copy, Check, X, RefreshCw, KeyRound, ChevronDown } from 'lucide-react';
import { getSourceTypeLabel, parseSourceTypes } from '@/lib/dataset-meta';

export default function DatasetDetailPage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const searchParams = useSearchParams();
  const isManage = searchParams?.get('manage') === 'true';
  const { user, loading: authLoading } = useAuth();
  const [dataset, setDataset] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [tags, setTags] = useState<any[]>([]);
  const [showShareModal, setShowShareModal] = useState(false);
  const [sharePassword, setSharePassword] = useState('');
  const [copiedAction, setCopiedAction] = useState<string | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<string>('');
  const [filePreview, setFilePreview] = useState<string>('请选择右侧文件查看内容预览。');
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  const [previewRows, setPreviewRows] = useState<Array<Record<string, string | number>>>([]);
  const [previewType, setPreviewType] = useState<'table' | 'text'>('text');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [selectedFileMeta, setSelectedFileMeta] = useState<{ description?: string; columns: Array<{ column_name: string; column_type?: string; description?: string }> }>({ columns: [] });
  const [creatingVersion, setCreatingVersion] = useState(false);
  const [versionHint, setVersionHint] = useState('');
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [unlockPassword, setUnlockPassword] = useState(searchParams?.get('share_token') || '');
  const [unlocking, setUnlocking] = useState(false);
  const [unlockError, setUnlockError] = useState('');
  const [reloadNonce, setReloadNonce] = useState(0);
  const viewTrackedRef = useRef<string | null>(null);
  const [reviewHistory, setReviewHistory] = useState<Array<{id:string;status:string;submitted_at:string;reviewed_at?:string;result_reason?:string;version_num?:number}>>([]);
  const [isUpvoted, setIsUpvoted] = useState(false);
  const [versionsOpen, setVersionsOpen] = useState(true);
  const [filesOpen, setFilesOpen] = useState(true);
  const [previewOpen, setPreviewOpen] = useState(true);

  const getDatasetAccessToken = () => {
    if (typeof window === 'undefined') return '';
    return sessionStorage.getItem(`dataset_access_token_${id}`) || '';
  };

  const withDatasetAccess = (config: any = {}) => {
    const token = getDatasetAccessToken();
    if (!token) return config;
    return {
      ...config,
      headers: {
        ...(config.headers || {}),
        'X-Dataset-Access-Token': token,
      },
    };
  };

  const datasetAccessQuery = () => {
    const token = getDatasetAccessToken();
    return token ? `?dataset_access_token=${encodeURIComponent(token)}` : '';
  };

  const isPasswordRequiredError = (err: any) => {
    const detail = err?.response?.data?.detail;
    return err?.response?.status === 403 && (detail?.code === 'dataset_access_password_required' || detail === 'dataset_access_password_required');
  };

  const formatCreateVersionError = (detail: any) => {
    if (!detail) return '未知错误';
    if (typeof detail === 'string') return detail;
    if (detail.code === 'existing_unapproved_version') {
      const v = detail.version_num ? `V${detail.version_num}` : '当前草稿';
      return `当前已有未审核通过的版本（${v}），请先完成该版本流程后再新建。`;
    }
    return JSON.stringify(detail);
  };

  useEffect(() => {
    viewTrackedRef.current = null;
  }, [id]);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await api.get(`/datasets/by-id/${id}`, withDatasetAccess());
        setDataset(res.data);
        setPasswordRequired(false);
        setUnlockError('');

        const viewKey = `dataset_view_track_${id}`;
        const now = Date.now();
        const lastTs = Number(sessionStorage.getItem(viewKey) || '0');
        const shouldTrack = viewTrackedRef.current !== id && (now - lastTs > 30_000);
        if (shouldTrack) {
          viewTrackedRef.current = id;
          sessionStorage.setItem(viewKey, String(now));
          api.post(`/datasets/${id}/view`, {}, withDatasetAccess())
            .then((viewRes) => {
              setDataset((prev: any) => prev ? { ...prev, view_count: viewRes.data.view_count } : prev);
            })
            .catch(() => {});
        }

        const [vRes, tRes] = await Promise.all([
          api.get(`/datasets/${id}/versions`, withDatasetAccess()),
          api.get(`/datasets/${id}/tags`, withDatasetAccess()).catch(() => ({ data: [] }))
        ]);
        const nextVersions = vRes.data || [];
        setVersions(nextVersions);
        setTags(tRes.data || []);

        // 获取当前用户点赞状态（登录时）
        if (user) {
          api.get(`/datasets/${id}/upvote-status`, withDatasetAccess())
            .then((r) => setIsUpvoted(r.data.is_upvoted ?? false))
            .catch(() => {});
        }
      } catch (err: any) {
        if (isPasswordRequiredError(err)) {
          if (typeof window !== 'undefined') {
            sessionStorage.removeItem(`dataset_access_token_${id}`);
          }
          const shareToken = searchParams.get('share_token');
          if (shareToken) {
            try {
              const res = await api.post(`/datasets/${id}/access/unlock`, { password: shareToken });
              const accessToken = res.data?.access_token;
              if (accessToken) {
                if (typeof window !== 'undefined') {
                  sessionStorage.setItem(`dataset_access_token_${id}`, accessToken);
                }
                setReloadNonce((v) => v + 1);
                return;
              }
            } catch (autoUnlockErr) {
              setUnlockError('链接中的访问口令已失效或错误，请重新输入。');
              setUnlockPassword(shareToken);
            }
          }
          setPasswordRequired(true);
          setDataset(null);
          setVersions([]);
          setTags([]);
        } else {
          console.error(err);
        }
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchDetails();
  }, [id, reloadNonce]);

  useEffect(() => {
    if (!versions.length) {
      setSelectedVersion(null);
      return;
    }

    const isOwner = Boolean(user && user.id === dataset?.owner_id);
    const canViewUnpublished = Boolean(user && isManage && (user.role === 'admin' || isOwner));
    const currentPublishedVersion = Number(dataset?.current_version || 0);
    const publishedVersions = versions.filter((v: any) => v.status === 'published');

    if (canViewUnpublished) {
      const inReviewOrDraft = versions
        .filter((v: any) =>
          (v.status === 'pending_review' || v.status === 'draft' || v.status === 'revision_required') &&
          v.version_num > currentPublishedVersion
        )
        .sort((a: any, b: any) => b.version_num - a.version_num)[0];
      if (inReviewOrDraft) {
        setSelectedVersion(inReviewOrDraft.version_num);
        return;
      }
    }

    const highestPublished = publishedVersions.length > 0
      ? Math.max(...publishedVersions.map((v: any) => v.version_num))
      : null;
    if (highestPublished) {
      setSelectedVersion(highestPublished);
      return;
    }

    const highestAny = Math.max(...versions.map((v: any) => v.version_num));
    setSelectedVersion(Number.isFinite(highestAny) ? highestAny : null);
  }, [versions, dataset?.current_version, dataset?.owner_id, user?.id, user?.role, isManage]);

  useEffect(() => {
    if (!dataset || !user || !isManage) { setReviewHistory([]); return; }
    const isOwnerOrAdmin = user.role === 'admin' || user.id === dataset.owner_id;
    if (!isOwnerOrAdmin) { setReviewHistory([]); return; }
    api.get(`/datasets/${id}/review-history`, withDatasetAccess())
      .then((res) => setReviewHistory(res.data || []))
      .catch(() => setReviewHistory([]));
  }, [dataset?.id, user?.id, user?.role, isManage, reloadNonce]);

  useEffect(() => {
    const fetchFiles = async () => {
      if (!selectedVersion) return;
      try {
        const fRes = await api.get(`/datasets/${id}/versions/${selectedVersion}/files`, withDatasetAccess());
        const nextFiles = fRes.data.items || fRes.data || [];
        setFiles(nextFiles);
        if (nextFiles.length > 0) {
          setSelectedFileId(nextFiles[0].id);
        } else {
          setSelectedFileId('');
          setFilePreview('该版本下暂无可用文件。');
          setPreviewColumns([]);
          setPreviewRows([]);
        }
      } catch {
        setFiles([]);
        setSelectedFileId('');
        setFilePreview('文件加载失败，请稍后重试。');
        setPreviewColumns([]);
        setPreviewRows([]);
      }
    };
    fetchFiles();
  }, [id, selectedVersion, reloadNonce]);

  useEffect(() => {
    const previewFile = async () => {
      const selectedFile = files.find((f) => f.id === selectedFileId);
      if (!selectedFile) return;

      try {
        setPreviewLoading(true);
        const res = await api.get(`/datasets/${id}/files/${selectedFileId}/preview`, withDatasetAccess());
        const data = res.data;
        if (data.preview_type === 'table') {
          setPreviewType('table');
          setPreviewColumns(Array.isArray(data.columns) ? data.columns : []);
          setPreviewRows(Array.isArray(data.rows) ? data.rows : []);
          setFilePreview('');
        } else {
          setPreviewType('text');
          setPreviewColumns([]);
          setPreviewRows([]);
          const txt = Array.isArray(data.rows) ? data.rows.map((r: any) => r.content).join('\n') : '文件内容为空。';
          setFilePreview(txt || '文件内容为空。');
        }
      } catch {
        setFilePreview('预览加载失败，请稍后重试。');
        setPreviewColumns([]);
        setPreviewRows([]);
      } finally {
        setPreviewLoading(false);
      }
    };

    if (selectedFileId) {
      previewFile();
    }
  }, [id, selectedFileId, files, reloadNonce]);

  useEffect(() => {
    const fetchFileMeta = async () => {
      if (!selectedFileId) {
        setSelectedFileMeta({ columns: [] });
        return;
      }
      try {
        const res = await api.get(`/datasets/${id}/files/${selectedFileId}/metadata`, withDatasetAccess());
        setSelectedFileMeta({
          description: res.data.description,
          columns: Array.isArray(res.data.columns) ? res.data.columns : []
        });
      } catch {
        setSelectedFileMeta({ columns: [] });
      }
    };
    fetchFileMeta();
  }, [id, selectedFileId, reloadNonce]);

  const ensureLoggedInForDownload = () => {
    if (dataset?.is_password_protected) return true;

    if (authLoading) {
      alert('正在确认登录状态，请稍后重试。');
      return false;
    }
    if (user) return true;

    const shouldLogin = window.confirm('下载功能需要先登录。是否现在前往登录？');
    if (!shouldLogin) return false;

    const nextPath = `${window.location.pathname}${window.location.search}`;
    router.push(`/login?next=${encodeURIComponent(nextPath)}`);
    return false;
  };

  const handleUnlockDataset = async () => {
    const pwd = unlockPassword.trim();
    if (!pwd) {
      setUnlockError('请输入访问密码。');
      return;
    }
    setUnlocking(true);
    setUnlockError('');
    try {
      const res = await api.post(`/datasets/${id}/access/unlock`, { password: pwd });
      const accessToken = res.data?.access_token;
      if (!accessToken) {
        throw new Error('missing_access_token');
      }
      if (typeof window !== 'undefined') {
        sessionStorage.setItem(`dataset_access_token_${id}`, accessToken);
      }
      setUnlockPassword('');
      setPasswordRequired(false);
      setLoading(true);
      setReloadNonce((v) => v + 1);
    } catch (err: any) {
      if (err?.response?.data?.detail === 'invalid_dataset_password') {
        setUnlockError('访问密码错误，请重试。');
      } else {
        setUnlockError('解锁失败，请稍后重试。');
      }
    } finally {
      setUnlocking(false);
    }
  };

  const handleDownloadZip = () => {
    if (!ensureLoggedInForDownload()) return;
    if (!selectedVersion) return;
    window.location.href = `/api/datasets/${id}/versions/${selectedVersion}/download-all${datasetAccessQuery()}`;
  };

  const handleSingleFileDownload = (fileId: string) => {
    if (!ensureLoggedInForDownload()) return;
    const a = document.createElement('a');
    a.href = `/api/datasets/${id}/files/${fileId}/download${datasetAccessQuery()}`;
    a.click();
  };

  const handleUpvote = async () => {
    try {
      const res = await api.post(`/datasets/${id}/upvote`, {}, withDatasetAccess());
      setDataset((prev: any) => prev ? { ...prev, upvote_count: res.data.upvote_count } : prev);
      setIsUpvoted(res.data.is_upvoted ?? !isUpvoted);
    } catch {
      alert('请先登录后再点赞。');
    }
  };

  const handleCancelReview = async () => {
    const confirmed = confirm('确认取消当前审核吗？取消后会恢复为可编辑状态。');
    if (!confirmed) return;
    try {
      await api.post(`/datasets/${id}/cancel-review`, {}, withDatasetAccess());
      const [dsRes, vRes] = await Promise.all([
        api.get(`/datasets/by-id/${id}`, withDatasetAccess()),
        api.get(`/datasets/${id}/versions`, withDatasetAccess()),
      ]);
      setDataset(dsRes.data);
      setVersions(vRes.data || []);
      alert('已取消审核。');
    } catch (err: any) {
      alert(`取消审核失败：${err.response?.data?.detail || err.message}`);
    }
  };

  const handleCreateNewVersion = async () => {
    if (dataset?.dataset_status === 'pending_review') {
      alert('当前有版本正在审核中，暂不可新增版本。');
      return;
    }
    if (!selectedVersion) {
      alert('请先选择一个已发布版本作为基准版本。');
      return;
    }
    setCreatingVersion(true);
    try {
      const res = await api.post(`/datasets/${id}/versions`, {
        base_version_num: selectedVersion,
        reset_existing_draft: false,
      }, withDatasetAccess());
      const newVersionNum = res.data?.version_num;
      if (!newVersionNum) {
        throw new Error('创建新版本失败：未返回版本号');
      }
      const existingDraft = versions.find((v: any) => v.status === 'draft');
      if (existingDraft && existingDraft.version_num === newVersionNum) {
        setVersionHint('已进入草稿编辑页。');
      }
      router.push(`/upload?datasetId=${id}&versionNum=${newVersionNum}&mode=new-version`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (detail?.code === 'existing_unapproved_version') {
        const targetVersionNum = detail?.version_num;
        if (targetVersionNum) {
          const shouldContinue = window.confirm(`当前已有未审核通过版本 V${targetVersionNum}。是否前往继续编辑该版本？`);
          if (shouldContinue) {
            router.push(`/upload?datasetId=${id}&versionNum=${targetVersionNum}&mode=new-version`);
            return;
          }
        }
      }
      alert(`创建新版本失败：${formatCreateVersionError(detail || err.message)}`);
    } finally {
      setCreatingVersion(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  if (loading) return <div className="text-center py-20 text-gray-500">加载中...</div>;

  if (passwordRequired && !dataset) {
    return (
      <div className="max-w-md mx-auto py-16 px-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <h1 className="text-lg font-semibold text-amber-900 mb-2">此数据集受密码保护</h1>
          <p className="text-sm text-amber-800 mb-4">
            该数据集不会出现在公开搜索和统计中。请输入访问密码后继续浏览。
          </p>
          <input
            type="password"
            value={unlockPassword}
            onChange={(e) => setUnlockPassword(e.target.value)}
            placeholder="输入访问密码"
            className="w-full border rounded-md p-2 text-sm mb-3"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleUnlockDataset();
              }
            }}
          />
          {unlockError && <p className="text-xs text-red-600 mb-2">{unlockError}</p>}
          <button
            onClick={handleUnlockDataset}
            disabled={unlocking}
            className="w-full rounded-md bg-primary text-primary-foreground py-2 text-sm font-medium disabled:opacity-60"
          >
            {unlocking ? '验证中...' : '解锁并访问'}
          </button>
        </div>
      </div>
    );
  }

  if (!dataset) return <div className="text-center py-20 text-gray-500">数据集不存在</div>;

  const isOwner = Boolean(user && dataset.owner_id === user.id);
  const showManageButtons = Boolean(isOwner && isManage);
  const canViewUnpublishedVersion = Boolean(user && isManage && (user.role === 'admin' || isOwner));
  const inProgressVersion = versions
    .filter((v: any) => v.status !== 'published' && (!dataset.current_version || v.version_num > Number(dataset.current_version)))
    .sort((a: any, b: any) => b.version_num - a.version_num)[0] || null;
  const publishedVersions = versions.filter((v: any) => v.status === 'published');
  const latestUnpublishedVersion = versions
    .filter((v: any) =>
      (v.status === 'pending_review' || v.status === 'draft' || v.status === 'revision_required') &&
      (!dataset.current_version || v.version_num > Number(dataset.current_version))
    )
    .sort((a: any, b: any) => b.version_num - a.version_num)[0] || null;
  const displayVersions = canViewUnpublishedVersion && latestUnpublishedVersion
    ? [latestUnpublishedVersion, ...publishedVersions]
    : publishedVersions;
  const currentVInfo = displayVersions.find((v: any) => v.version_num === selectedVersion);
  const selectedFile = files.find((f) => f.id === selectedFileId);
  const revisionTargetVersionNum = inProgressVersion?.status === 'revision_required'
    ? inProgressVersion.version_num
    : (dataset.dataset_status === 'revision_required' && dataset.current_version
      ? Number(dataset.current_version)
      : null);
  const revisionTargetHref = revisionTargetVersionNum
    ? `/upload?datasetId=${id}&versionNum=${revisionTargetVersionNum}${publishedVersions.length > 0 ? '&mode=new-version' : ''}`
    : `/upload?datasetId=${id}`;
  const publishedVersionsAsc = [...publishedVersions]
    .sort((a: any, b: any) => a.version_num - b.version_num);
  const publishedDisplayNoMap = new Map<number, number>(
    publishedVersionsAsc.map((v: any, idx: number) => [v.version_num, idx + 1])
  );
  const getVersionOptionLabel = (v: any) => {
    const publishedNo = publishedDisplayNoMap.get(v.version_num);
    if (v.status === 'published' && publishedNo) return `V${publishedNo}（已发布）`;
    if (v.status === 'pending_review') return `V${v.version_num}（审核中，待发布）`;
    if (v.status === 'draft') return `V${v.version_num}（草稿，待发布）`;
    if (v.status === 'revision_required') return `V${v.version_num}（需修改，待发布）`;
    return `V${v.version_num}`;
  };

  const displayStatus = (dataset.dataset_status !== 'archived' && currentVInfo)
    ? currentVInfo.status
    : ((!canViewUnpublishedVersion && (dataset.dataset_status === 'pending_review' || dataset.dataset_status === 'draft' || dataset.dataset_status === 'revision_required') && publishedVersions.length > 0)
      ? 'published' 
      : dataset.dataset_status);

  const handleCopyShare = async (actionType: 'top_copy' | 'generate' | 'bottom_copy' = 'top_copy') => {
    const generateNew = actionType === 'generate';
    try {
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
      const shareUrl = `${baseUrl}/datasets/${encodeURIComponent(dataset.owner?.username || '')}/${dataset.slug}`;
      
      let text = ``;
      let updateTokenPromise = null;

      if (dataset.is_password_protected) {
        if (generateNew) {
          const newToken = Math.random().toString(36).substring(2, 8).toLowerCase();
          setSharePassword(newToken);
          const directUrl = `${shareUrl}?share_token=${newToken}`;
          text = `我在 RxnCommons 分享了私密数据集「${dataset.title}」\n点击专属邀请链接，免密直达访问：\n👉 ${directUrl}`;
          
          updateTokenPromise = api.put(`/datasets/${id}/access-policy`, {
            access_level: 'password_protected',
            access_password: newToken
          }, withDatasetAccess()).catch(() => {});
        } else {
          // 只复制基础链接（如果没有输入或者就是不想生成新的）
          const effectiveToken = sharePassword.trim() || dataset.access_password;
          const currentTokenUrlSnippet = effectiveToken ? `?share_token=${effectiveToken}` : '';
          if (currentTokenUrlSnippet) {
            text = `我在 RxnCommons 分享了私密数据集「${dataset.title}」\n点击专属邀请链接，免密直达访问：\n👉 ${shareUrl}${currentTokenUrlSnippet}`;
          } else {
            text = `我在 RxnCommons 分享了私密数据集「${dataset.title}」\n👉 基础链接：${shareUrl} \n(需手动输入有效访问口令)`;
          }
        }
      } else {
        text = `我在 RxnCommons 分享了公开数据集「${dataset.title}」\n👉 访问链接：${shareUrl}`;
      }

      const safelyWriteClipboard = async (content: string) => {
        if (navigator.clipboard && window.isSecureContext) {
          try {
            await navigator.clipboard.writeText(content);
            return true;
          } catch (e) {
            console.warn("Clipboard API failed, falling back", e);
          }
        }
        
        // Fallback for non-HTTPS or failed clipboard API
        try {
          const textArea = document.createElement("textarea");
          textArea.value = content;
          // Avoid scrolling to bottom
          textArea.style.top = "0";
          textArea.style.left = "0";
          textArea.style.position = "fixed";
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          const successful = document.execCommand('copy');
          document.body.removeChild(textArea);
          return successful;
        } catch (err) {
          console.error('Fallback copy failed', err);
          return false;
        }
      };

      const copiedOk = await safelyWriteClipboard(text);
      
      if (!copiedOk) {
        throw new Error("Copy command failed");
      }

      setCopiedAction(actionType);
      setTimeout(() => setCopiedAction(null), 2000);

      // If we had a token update, await it after the synchronous copy has successfully executed
      if (updateTokenPromise) {
        await updateTokenPromise;
      }

    } catch (err) {
      alert('无法获取剪贴板权限或环境受限，请在下方文本框中手动全选并复制。');
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-white to-slate-50 p-6 mb-6 shadow-sm transition hover:shadow-md">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between mb-4">
          <div className="min-w-0">
            <h1 className="text-3xl font-bold text-gray-900 break-words">{dataset.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-600">
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1">
                <UserRound className="h-3.5 w-3.5 text-slate-500" />
                {dataset.owner?.username ?? '—'}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1">
                <CalendarClock className="h-3.5 w-3.5 text-slate-500" />
                {new Date(dataset.created_at).toLocaleString('zh-CN')}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1">
                <FlaskConical className="h-3.5 w-3.5 text-slate-500" />
                条目 {Number(dataset.total_rows || 0).toLocaleString()}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1">
                <Download className="h-3.5 w-3.5 text-slate-500" />
                下载 {Number(dataset.download_count || 0).toLocaleString()}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1">
                <Eye className="h-3.5 w-3.5 text-slate-500" />
                浏览 {Number(dataset.view_count || 0).toLocaleString()}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {showManageButtons && (dataset.dataset_status === 'published' || dataset.dataset_status === 'revision_required') && !inProgressVersion && (
              <button
                onClick={handleCreateNewVersion}
                disabled={creatingVersion}
                className="bg-primary text-primary-foreground shadow px-4 py-2 rounded-md text-sm hover:bg-primary/90 disabled:opacity-60 transition-colors"
              >
                {creatingVersion ? '创建中...' : '+ 新版本'}
              </button>
            )}
            {showManageButtons && inProgressVersion?.status === 'draft' && (
              <button
                onClick={() => router.push(`/upload?datasetId=${id}&versionNum=${inProgressVersion.version_num}&mode=new-version`)}
                className="bg-primary text-primary-foreground shadow px-4 py-2 rounded-md text-sm hover:bg-primary/90 transition-colors"
              >
                继续当前草稿
              </button>
            )}
            {showManageButtons && (dataset.dataset_status === 'revision_required' || inProgressVersion?.status === 'revision_required') && (
              <button
                onClick={() => router.push(revisionTargetHref)}
                className="bg-primary text-primary-foreground shadow px-4 py-2 rounded-md text-sm hover:bg-primary/90 transition-colors"
              >
                去修改
              </button>
            )}
            {showManageButtons && (dataset.dataset_status === 'pending_review' || inProgressVersion?.status === 'pending_review') && (
              <button
                onClick={handleCancelReview}
                className="border border-amber-300 bg-amber-50 text-amber-700 px-4 py-2 rounded-md text-sm hover:bg-amber-100 transition-colors"
              >
                取消审核
              </button>
            )}
            {selectedVersion && (
              <button
                onClick={handleDownloadZip}
                disabled={files.length === 0}
                className={`border border-input px-4 py-2 rounded-md inline-flex items-center gap-2 font-medium text-sm transition-colors ${
                  files.length > 0
                    ? 'text-primary hover:bg-accent hover:text-accent-foreground'
                    : 'text-muted-foreground bg-muted/50 cursor-not-allowed opacity-70'
                }`}
                title="下载"
              >
                <Download className="h-4 w-4" />
                下载
              </button>
            )}
            <button
              onClick={handleUpvote}
              className={`border px-4 py-2 rounded-md inline-flex items-center gap-2 font-medium text-sm transition-colors ${
                isUpvoted
                  ? 'border-primary bg-primary/10 text-primary hover:bg-primary/20'
                  : 'border-input text-primary hover:bg-accent hover:text-accent-foreground'
              }`}
              aria-label={`点赞数 ${dataset.upvote_count}`}
            >
              <ThumbsUp className={`h-4 w-4 ${isUpvoted ? 'fill-primary' : ''}`} />
              {dataset.upvote_count}
            </button>
            <button
              onClick={() => {
                // 不再每次随机生成覆盖，避免误切覆盖历史密码
                setSharePassword('');
                setCopiedAction(null);
                setShowShareModal(true);
              }}
              className="border border-input text-primary px-4 py-2 rounded-md inline-flex items-center gap-2 hover:bg-accent hover:text-accent-foreground font-medium text-sm transition-colors"
              title="分享数据集"
            >
              <Share2 className="h-4 w-4" />
              分享
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className={`px-3 py-1 rounded-md text-xs font-medium ${
            displayStatus === 'published' ? 'bg-green-100 text-green-700' :
            displayStatus === 'archived' ? 'bg-gray-200 text-gray-600' :
            displayStatus === 'revision_required' ? 'bg-orange-100 text-orange-700' :
            displayStatus === 'pending_review' ? 'bg-yellow-100 text-yellow-700' :
            'bg-gray-100 text-gray-600'
          }`}>{displayStatus === 'draft' ? '草稿' : displayStatus === 'pending_review' ? '审核中' : displayStatus === 'published' ? '已发布' : displayStatus === 'revision_required' ? '需修改' : '已归档'}</span>
          {dataset.is_password_protected && (
            <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-md text-xs">密码保护</span>
          )}
          {parseSourceTypes(dataset.source_type).map(({ code, label, colorClass }) => (
            <span key={code} className={`px-3 py-1 rounded-md text-xs font-medium mono-data ${colorClass}`}>{label}</span>
          ))}
          {dataset.license && <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-md text-xs font-medium mono-data">{dataset.license}</span>}
          {dataset.source_ref && (
            <a
              href={dataset.source_ref.startsWith('http') ? dataset.source_ref : `https://doi.org/${dataset.source_ref}`}
              target="_blank" rel="noreferrer"
              className="bg-slate-100 text-primary hover:bg-slate-200 px-3 py-1 rounded-md text-xs font-medium mono-data truncate max-w-[220px] transition-colors"
              title={dataset.source_ref}
            >{dataset.source_ref}</a>
          )}
          {tags.map((t: any) => (
            <span key={t.tag} className={`px-2 py-1 rounded-md text-xs mono-data ${
              t.tag_type === 'task' ? 'bg-secondary text-secondary-foreground' :
              t.tag_type === 'field' ? 'bg-secondary text-secondary-foreground' :
              'bg-muted text-muted-foreground'
            }`}>#{t.tag}</span>
          ))}
        </div>
        <div className="mb-5 rounded-xl border border-slate-200 bg-white/80 p-4">
          <h2 className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
            <FileText className="h-4 w-4 text-primary" />
            数据集描述
          </h2>
          <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {dataset.description || '暂无描述'}
          </p>
        </div>
      </div>

      {versionHint && (
        <div className="mb-4 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">{versionHint}</div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div>
          {selectedVersion && (
            <div className="bg-white rounded-xl border border-gray-200 hover:shadow-md hover:border-gray-300 transition">
              <button
                onClick={() => setPreviewOpen((v) => !v)}
                className="w-full flex items-center justify-between px-5 py-4 text-left"
              >
                <h3 className="font-bold text-lg">文件内容预览</h3>
                <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform ${previewOpen ? '' : '-rotate-90'}`} />
              </button>
              {previewOpen && (
              <div className="px-5 pb-5">
              <div className="space-y-4">
                <div className="rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white p-4">
                  <h4 className="font-semibold mb-2 text-gray-900 text-sm flex items-center gap-2">
                    <FileSearch className="h-4 w-4 text-primary" />
                    文件描述与列说明
                  </h4>
                  <p className="text-xs text-gray-500 mb-3">先查看字段语义，再看表格数据，会更容易理解数据结构。</p>
                  
                {selectedFile ? (
                  <>
                    <div className="text-xs text-gray-600 mb-2">文件：<span className="font-medium text-gray-900">{selectedFile.filename}</span></div>
                    <div className="text-sm text-gray-800 bg-white border border-slate-200 rounded-lg p-3 mb-3">{selectedFileMeta.description || '暂无文件描述'}</div>
                    <div className="max-h-52 overflow-auto border border-slate-200 rounded-lg bg-white">
                      <table className="w-full text-xs border-collapse">
                        <thead className="bg-slate-50 sticky top-0 z-10">
                          <tr className="border-b border-slate-200">
                            <th className="text-left p-2.5 w-1/3">
                              <span className="inline-flex items-center gap-1.5">
                                <Columns3 className="h-3.5 w-3.5 text-slate-500" />
                                列名
                              </span>
                            </th>
                            <th className="text-left p-2.5">说明</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedFileMeta.columns.map((c) => (
                            <tr key={c.column_name} className="border-b border-slate-100">
                              <td className="p-2.5 break-all text-slate-700">{c.column_name}</td>
                              <td className="p-2.5 text-slate-600">{c.description || '—'}</td>
                            </tr>
                          ))}
                          {selectedFileMeta.columns.length === 0 && (
                            <tr><td className="p-3 text-slate-400" colSpan={2}>暂无列说明</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-gray-400">请选择文件以查看描述与列说明。</div>
                )}
                </div>

                <div className="rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white p-4">
                  <h4 className="font-semibold mb-1.5 text-gray-900 text-sm flex items-center gap-2">
                    <LayoutPanelTop className="h-4 w-4 text-primary" />
                    文件内容预览
                  </h4>
                  <p className="text-xs text-gray-500 mb-3">仅展示抽样数据行，用于快速核对字段与内容格式。</p>
                  <div className="max-h-[360px] overflow-auto">
                    {previewLoading ? (
                      <div className="p-4 text-sm text-gray-500">正在加载预览...</div>
                    ) : previewType === 'table' && previewColumns.length > 0 ? (
                      <table className="min-w-max text-xs border-collapse">
                        <thead className="sticky top-0 bg-slate-100 z-10">
                          <tr>
                            {previewColumns.map((c) => (
                              <th key={c} className="px-3 py-2 text-left border-b border-r border-slate-200 text-gray-700 font-semibold whitespace-nowrap">{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewRows.map((row, idx) => (
                            <tr key={idx} className="odd:bg-white even:bg-slate-50/60">
                              {previewColumns.map((c) => (
                                <td key={`${idx}-${c}`} className="px-2.5 py-1.5 border-b border-r border-slate-100 text-gray-700 align-top whitespace-nowrap">{String(row[c] ?? '')}</td>
                              ))}
                            </tr>
                          ))}
                          {previewRows.length === 0 && (
                            <tr>
                              <td colSpan={previewColumns.length} className="p-6 text-sm text-gray-500">该文件暂无可预览内容。</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    ) : (
                      <pre className="p-3 text-xs leading-5 text-gray-800 whitespace-pre mono-data">{filePreview}</pre>
                    )}
                  </div>
                </div>
              </div>
              </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-4">
          {displayVersions.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 hover:shadow-md hover:border-gray-300 transition">
              <button
                onClick={() => setVersionsOpen((v) => !v)}
                className="w-full flex items-center justify-between px-4 py-3 text-left"
              >
                <span className="text-sm font-bold text-gray-900">版本选择</span>
                <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${versionsOpen ? '' : '-rotate-90'}`} />
              </button>
              {versionsOpen && (
              <div className="px-4 pb-4">
                <div className="space-y-1.5 mb-3">
                  {displayVersions.map(v => {
                    const isSelected = selectedVersion === v.version_num;
                    const publishedNo = publishedDisplayNoMap.get(v.version_num);
                    const vLabel = publishedNo != null ? `V${publishedNo}` : `V${v.version_num}`;
                    const statusText = v.status === 'published' ? '已发布'
                      : v.status === 'pending_review' ? '审核中'
                      : v.status === 'draft' ? '草稿'
                      : v.status === 'revision_required' ? '需修改'
                      : v.status;
                    const statusColor = v.status === 'published'
                      ? 'bg-emerald-100 text-emerald-700'
                      : v.status === 'pending_review'
                      ? 'bg-blue-100 text-blue-700'
                      : v.status === 'draft'
                      ? 'bg-gray-100 text-gray-500'
                      : v.status === 'revision_required'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-gray-100 text-gray-500';
                    return (
                      <button
                        key={v.version_num}
                        onClick={() => setSelectedVersion(v.version_num)}
                        className={`w-full flex items-center gap-3 rounded-lg border px-3 py-2 text-left transition ${
                          isSelected
                            ? 'border-primary/40 bg-primary/5'
                            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <span className={`text-sm font-bold flex-none w-8 ${isSelected ? 'text-primary' : 'text-gray-800'}`}>{vLabel}</span>
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium flex-none ${statusColor}`}>{statusText}</span>
                        <span className="text-xs text-gray-400 ml-auto flex-none">{new Date(v.created_at).toLocaleDateString()}</span>
                      </button>
                    );
                  })}
                </div>
                {currentVInfo && currentVInfo.version_note && (
                  <div className="text-sm border-t border-gray-100 pt-3">
                    <div className="text-gray-500 text-xs mb-1.5">版本说明</div>
                    <div className="text-gray-800 bg-gray-50 p-2.5 rounded text-xs leading-relaxed">{currentVInfo.version_note}</div>
                  </div>
                )}
              </div>
              )}
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 hover:shadow-md hover:border-gray-300 transition">
            <button
              onClick={() => setFilesOpen((v) => !v)}
              className="w-full flex items-center justify-between px-3.5 py-3 text-left"
            >
              <span className="font-bold text-gray-900 text-sm">
                当前版本文件
                {files.length > 0 && <span className="ml-1.5 text-xs font-normal text-gray-400">({files.length})</span>}
              </span>
              <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${filesOpen ? '' : '-rotate-90'}`} />
            </button>
            {filesOpen && (
            <div className="px-3.5 pb-3.5">
            <div className="space-y-2 mb-3 max-h-64 overflow-auto pr-1">
              {files.map((f) => (
                <div key={f.id}
                     className={`border rounded-lg p-2 ${selectedFileId === f.id ? 'border-primary/40 bg-primary/5' : 'border-gray-200 bg-white'}`}>
                  <div className="flex items-center gap-2 min-w-0">
                    <button
                      onClick={() => setSelectedFileId(f.id)}
                      className="text-left flex items-center gap-2 min-w-0 flex-1"
                      title={f.filename}
                    >
                      <FileText className="h-4 w-4 text-slate-500 shrink-0" />
                      <span className="font-medium text-xs text-gray-900 truncate">{f.filename}</span>
                      <span className="text-[11px] text-gray-500 shrink-0">{formatSize(f.file_size)}</span>
                    </button>
                    <button
                      onClick={() => handleSingleFileDownload(f.id)}
                      title="下载文件"
                      className="inline-flex items-center justify-center rounded-md border border-slate-200 bg-slate-50 p-1.5 text-slate-700 hover:bg-slate-100 shrink-0"
                    >
                      <ArrowDownToLine className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
              {files.length === 0 && <div className="text-sm text-gray-400">该版本下暂无可用文件。</div>}
            </div>

            </div>
            )}
          </div>

          {/* 审核历史 — 仅数据集所有者/管理员在管理模式可见 */}
          {isManage && reviewHistory.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-3.5 hover:shadow-md hover:border-gray-300 transition">
              <h3 className="font-bold mb-3 text-gray-900 text-sm">审核操作历史</h3>
              <div className="relative pl-4 border-l-2 border-slate-200 space-y-3 max-h-80 overflow-auto pr-1">
                {reviewHistory.map((h, idx) => {
                  const isLatest = idx === 0;
                  const statusLabel =
                    h.status === 'approved' ? '已通过' :
                    h.status === 'rejected' ? '已拒绝' :
                    h.status === 'revision_required' ? '建议修改' :
                    h.status === 'pending' ? '待审核' :
                    h.status === 'canceled_by_user' ? '已取消' : h.status;
                  const dotColor =
                    h.status === 'approved' ? 'bg-emerald-500' :
                    h.status === 'rejected' ? 'bg-red-500' :
                    h.status === 'revision_required' ? 'bg-orange-500' :
                    h.status === 'pending' ? 'bg-amber-500' :
                    'bg-slate-400';
                  const chipColor =
                    h.status === 'approved' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                    h.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200' :
                    h.status === 'revision_required' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                    h.status === 'pending' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    'bg-slate-50 text-slate-700 border-slate-200';
                  return (
                    <div key={h.id} className="relative">
                      <div className={`absolute -left-[calc(0.5rem+1px)] top-1.5 w-2.5 h-2.5 rounded-full ${dotColor}`} />
                      <div className={`rounded-lg border p-2.5 ${isLatest ? 'border-primary/30 bg-primary/5' : 'border-slate-100 bg-slate-50/40'}`}>
                        <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                          <span className={`inline-flex items-center rounded-full border px-1.5 py-0.5 font-medium ${chipColor}`}>
                            {statusLabel}
                          </span>
                          {h.version_num != null && <span className="text-slate-500">V{h.version_num}</span>}
                          <span className="text-slate-400">{new Date(h.submitted_at).toLocaleString('zh-CN')}</span>
                        </div>
                        {h.result_reason && (
                          <div className="mt-1.5 text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">{h.result_reason}</div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Share Modal */}
      {showShareModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
          onClick={() => setShowShareModal(false)}
        >
          <div 
            className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Share2 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">分享数据集</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{dataset.title}</p>
                </div>
              </div>
              <button 
                onClick={() => setShowShareModal(false)}
                className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-colors"
                aria-label="关闭"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6 overflow-hidden">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {!dataset.is_password_protected 
                    ? '公开直达链接' 
                    : (dataset.access_password || sharePassword.trim()) 
                      ? '免密专属链接' 
                      : '基础链接 (需对方手动输入口令)'}
                </label>
                <div className="flex items-stretch max-w-full">
                  <div className={`bg-gray-50 flex-1 p-3 text-sm text-gray-600 break-all border border-gray-200 select-all font-mono ${dataset.is_password_protected ? 'rounded-lg' : 'rounded-l-lg border-r-0'}`}>
                    {typeof window !== 'undefined' ? window.location.origin : ''}/datasets/{encodeURIComponent(dataset.owner?.username || '')}/{dataset.slug}
                    {(dataset.is_password_protected && (dataset.access_password || sharePassword.trim())) 
                      ? `?share_token=${sharePassword.trim() || dataset.access_password}`
                      : ''}
                  </div>
                  {!dataset.is_password_protected && (
                    <button
                      onClick={() => handleCopyShare('top_copy')}
                      className="px-4 py-3 min-h-[46px] border border-gray-200 border-l-0 rounded-r-lg bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors flex items-center shrink-0"
                      title="复制上方链接"
                    >
                      {copiedAction === 'top_copy' ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                    </button>
                  )}
                </div>
              </div>

              {dataset.is_password_protected && (
                <div className="relative overflow-hidden rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50/30">
                  <div className="p-5">
                    <div className="flex items-start gap-3">
                      <div className="p-1.5 bg-amber-100 rounded-md text-amber-700 mt-0.5 shadow-sm shrink-0">
                        <KeyRound className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-3 gap-2">
                          <h4 className="text-[15px] font-semibold text-amber-900 truncate">私密数据集专属邀请</h4>
                          {(dataset.access_password || sharePassword.trim()) && (
                            <div className="px-2.5 py-1 bg-white border border-amber-200 rounded text-xs font-mono text-amber-700 shadow-sm shrink-0">
                              当前口令: {sharePassword.trim() || dataset.access_password}
                            </div>
                          )}
                        </div>
                        <p className="text-[13px] leading-relaxed text-amber-800/80 mb-4">
                          通过专属链接，访客可免密直接访问此数据集。重新生成将使旧口令失效。
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3">
                          <button 
                            onClick={() => handleCopyShare('generate')}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md"
                          >
                            {copiedAction === 'generate' ? <Check className="h-4 w-4" /> : <RefreshCw className="h-4 w-4" />}
                            {copiedAction === 'generate' ? '已生成并复制！' : '生成新口令'}
                          </button>
                          <button 
                            onClick={() => handleCopyShare('bottom_copy')}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600/10 text-amber-800 border border-amber-600/20 hover:bg-amber-600/20 rounded-lg transition-all flex items-center justify-center gap-2"
                          >
                            {copiedAction === 'bottom_copy' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                            {copiedAction === 'bottom_copy' ? '链接已复制！' : '复制专属链接'}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
