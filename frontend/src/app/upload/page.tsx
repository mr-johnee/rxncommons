'use client';
import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api, { getCoverImageUrl } from '@/lib/api';
import { LICENSE_OPTIONS, SOURCE_TYPE_OPTIONS, normalizeSourceTypeCode } from '@/lib/dataset-meta';
const TASK_TAG_PRESETS = ['yield_prediction', 'condition_prediction', 'retrosynthesis', 'forward_prediction', 'reaction_classification'];
const META_TEXT_LIMIT = 500;

type VersionFile = {
  id: string;
  filename: string;
  file_size: number;
  created_at?: string;
  upload_status?: string;
  row_count?: number | null;
  error_message?: string | null;
};

type FileColumnDraft = {
  column_name: string;
  column_type?: string;
  description: string;
};

type FileMetaDraftEntry = {
  description: string;
  upload_status?: string;
  row_count?: number | null;
  error_message?: string | null;
  columns: FileColumnDraft[];
};

type FilePreview = {
  preview_type: 'table' | 'text';
  columns: string[];
  rows: Array<Record<string, unknown>>;
  truncated: boolean;
  error?: string;
};

type UploadedFileRecord = {
  id: string;
  filename: string;
  upload_status?: string;
};

function mergeFileMetaDraft(
  previous: Record<string, FileMetaDraftEntry>,
  incoming: Record<string, FileMetaDraftEntry>,
) {
  const next: Record<string, FileMetaDraftEntry> = {};

  Object.entries(incoming).forEach(([fileId, incomingEntry]) => {
    const existing = previous[fileId];
    const existingColumnDescriptionMap = new Map(
      (existing?.columns || []).map((column) => [column.column_name, String(column.description || '').trim()])
    );

    next[fileId] = {
      description: String(existing?.description || '').trim() ? existing.description : incomingEntry.description,
      upload_status: incomingEntry.upload_status,
      row_count: incomingEntry.row_count,
      error_message: incomingEntry.error_message,
      columns: incomingEntry.columns.map((column) => ({
        ...column,
        description: existingColumnDescriptionMap.get(column.column_name) || column.description || '',
      })),
    };
  });

  return next;
}

function orderColumnsByPreview(columns: FileColumnDraft[], previewColumns: string[]) {
  if (!previewColumns.length || !columns.length) return columns;
  const orderMap = new Map(previewColumns.map((columnName, index) => [columnName, index]));
  return [...columns].sort((a, b) => {
    const left = orderMap.get(a.column_name) ?? Number.MAX_SAFE_INTEGER;
    const right = orderMap.get(b.column_name) ?? Number.MAX_SAFE_INTEGER;
    return left - right;
  });
}

function slugifyDatasetTitle(raw: string) {
  const trimmed = raw.trim().toLowerCase();
  let slug = trimmed
    .replace(/[\s\-.]+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 90);
  if (!slug) slug = 'dataset';
  return slug;
}

function UploadPageContent() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const editDatasetId = searchParams.get('datasetId') || '';
  const mode = searchParams.get('mode') || '';
  const queryVersionNum = Number(searchParams.get('versionNum') || '1');
  const targetVersionNum = Number.isFinite(queryVersionNum) && queryVersionNum > 0 ? queryVersionNum : 1;
  const [step, setStep] = useState(0); // 0 = confirm dialog, 1 = files, 2 = info
  const [datasetId, setDatasetId] = useState('');
  const [initLoading, setInitLoading] = useState(false);
  const [workingVersionNum, setWorkingVersionNum] = useState<number>(targetVersionNum);
  const [targetReleaseVersionNum, setTargetReleaseVersionNum] = useState<number | null>(null);

  // Step 1: File state
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  // Step 2: Meta state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [license, setLicense] = useState('CC BY 4.0');
  const [sourceType, setSourceType] = useState<string[]>(['lab']);
  const [sourceRef, setSourceRef] = useState('');
  const [accessLevel, setAccessLevel] = useState<'public' | 'password_protected'>('public');
  const [initialAccessLevel, setInitialAccessLevel] = useState<'public' | 'password_protected' | null>(null);
  const [workingVersionStatus, setWorkingVersionStatus] = useState<string>('draft');
  const [accessPassword, setAccessPassword] = useState('');
  const [hasExistingAccessPassword, setHasExistingAccessPassword] = useState(false);
  const [versionNote, setVersionNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [versionFiles, setVersionFiles] = useState<VersionFile[]>([]);
  const [fileMetaDraft, setFileMetaDraft] = useState<Record<string, FileMetaDraftEntry>>({});
  const [previewByFileId, setPreviewByFileId] = useState<Record<string, FilePreview>>({});
  const [deletingFileId, setDeletingFileId] = useState('');
  const [taskTags, setTaskTags] = useState<string[]>([]);
  const [customTagInput, setCustomTagInput] = useState('');
  const [confirmSmilesChecked, setConfirmSmilesChecked] = useState(false);
  const [confirmColumnNamingChecked, setConfirmColumnNamingChecked] = useState(false);
  const [processingFiles, setProcessingFiles] = useState(false);
  const [hasSaved, setHasSaved] = useState(false);
  const [existingDrafts, setExistingDrafts] = useState<any[]>([]);
  const [showDraftPicker, setShowDraftPicker] = useState(false);
  const [showClearDraftConfirm, setShowClearDraftConfirm] = useState(false);
  const [draftCheckDone, setDraftCheckDone] = useState(!!editDatasetId); // skip check if editing existing
  const [slugConflict, setSlugConflict] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{ msg: string; onConfirm: () => void; onCancel: () => void } | null>(null);
  const isNewlyCreatedRef = useRef(false);

  // Cover image state
  const [coverImageFile, setCoverImageFile] = useState<File | null>(null);
  const [coverImagePreview, setCoverImagePreview] = useState<string>('');
  const [coverImageUploading, setCoverImageUploading] = useState(false);
  const [existingCoverImageKey, setExistingCoverImageKey] = useState<string | null>(null);
  const [coverImageMarkedForDeletion, setCoverImageMarkedForDeletion] = useState(false);
  const coverImageObjectUrlRef = useRef<string | null>(null);

  const askConfirm = (msg: string): Promise<boolean> =>
    new Promise(resolve => {
      setConfirmDialog({
        msg,
        onConfirm: () => { setConfirmDialog(null); resolve(true); },
        onCancel:  () => { setConfirmDialog(null); resolve(false); },
      });
    });
  const datasetIdRef = useRef('');
  const newDatasetSlugRef = useRef('');
  const workingVersionNumRef = useRef(targetVersionNum);

  const revokeCoverImageObjectUrl = useCallback(() => {
    if (coverImageObjectUrlRef.current) {
      URL.revokeObjectURL(coverImageObjectUrlRef.current);
      coverImageObjectUrlRef.current = null;
    }
  }, []);

  const clearCoverImagePreview = useCallback(() => {
    revokeCoverImageObjectUrl();
    setCoverImagePreview('');
  }, [revokeCoverImageObjectUrl]);

  const setCoverImagePreviewFromFile = useCallback((file: File) => {
    revokeCoverImageObjectUrl();
    const nextObjectUrl = URL.createObjectURL(file);
    coverImageObjectUrlRef.current = nextObjectUrl;
    setCoverImagePreview(nextObjectUrl);
  }, [revokeCoverImageObjectUrl]);

  const setCoverImagePreviewFromServer = useCallback((targetDatasetId: string, cacheKey?: string) => {
    revokeCoverImageObjectUrl();
    setCoverImagePreview(getCoverImageUrl(targetDatasetId, cacheKey));
  }, [revokeCoverImageObjectUrl]);

  const mapErrorCode = (code: string) => {
    if (code === 'dataset_status_conflict') {
      return '当前数据集状态不允许提交审核（可能存在状态冲突）。请刷新页面后重试。';
    }
    if (code === 'dataset_under_review_locked') {
      return '当前已有版本处于审核中，请等待审核结果后再继续操作。';
    }
    if (code === 'missing_version_note') {
      return '请先填写版本说明。';
    }
    if (code === 'missing_task_tag') {
      return '请至少添加 1 个任务类标签后再提交审核。';
    }
    if (code === 'missing_files') {
      return '当前版本暂无文件，请先上传文件后再提交审核。';
    }
    if (code === 'version_not_editable') {
      return '此版本已提交或已发布，无法重复提交。请刷新页面查看最新版本状态，或从数据集页面进入"新增版本"流程。';
    }
    if (code === 'only_csv_excel_supported' || code === 'only_csv_xlsx_supported') {
      return '仅支持上传 CSV、XLS、XLSX 文件。';
    }
    if (code === 'description_too_short') {
      return '数据集描述至少需要 10 个字。';
    }
    if (code === 'missing_access_password') {
      return '已启用密码保护，请设置访问密码（至少 6 位）。';
    }
    if (code === 'access_password_too_short') {
      return '访问密码至少需要 6 位。';
    }
    if (code === 'invalid_access_level') {
      return '访问权限配置不正确，请重新选择。';
    }
    if (code === 'access_policy_endpoint_not_available') {
      return '当前后端尚未启用“访问权限”接口，请重启后端服务后重试。';
    }
    if (code === 'dataset_meta_endpoint_not_available') {
      return '当前后端元信息保存接口不可用，请重启后端后再试。';
    }
    if (code === 'has_pending_review') {
      return '有版本正在审核中，请先等待审核完成或取消审核后再修改访问权限。';
    }
    if (code === 'has_pending_access_review') {
      return '有访问权限变更正在审核中，请等待审核完成后再修改。';
    }
    return code;
  };

  const formatErrorDetail = (detail: unknown): string => {
    if (!detail) return '未知错误';
    if (typeof detail === 'string') return mapErrorCode(detail);
    if (Array.isArray(detail)) {
      return detail.map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join('；');
    }
    if (typeof detail === 'object') {
      const d = detail as Record<string, unknown>;
      if (d.code === 'missing_file_description') {
        const files = Array.isArray(d.files) ? d.files.join('、') : '';
        return `以下文件还没填写“文件描述”：${files}。请补全后重新提交。`;
      }
      if (d.code === 'missing_column_description') {
        return `文件 ${String(d.file || '')} 仍有列说明未填写，请补全后保存。`;
      }
      if (d.code === 'duplicate_filename') {
        return `上传失败：当前版本中已存在同名文件 ${String(d.filename || '')}，请重命名后再上传。`;
      }
      if (typeof d.code === 'string') {
        return mapErrorCode(d.code);
      }
      return JSON.stringify(d);
    }
    return String(detail);
  };

  const normalizeFilename = (name: string) => name.trim().toLowerCase();

  const isRouteNotFound = (err: any) => {
    const status = err?.response?.status;
    const detail = err?.response?.data?.detail;
    return status === 404 && (
      detail === 'Not Found' ||
      detail === 'Owner not found' ||
      detail === 'Dataset not found' ||
      (typeof detail === 'string' && /not found/i.test(detail))
    );
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;

    const incoming = Array.from(e.target.files);
    const existingNames = new Set(files.map((f) => normalizeFilename(f.name)));
    const versionNames = new Set(versionFiles.map((f: any) => normalizeFilename(String(f.filename || ''))));

    const accepted: File[] = [];
    const rejected: string[] = [];

    for (const f of incoming) {
      const key = normalizeFilename(f.name);
      if (existingNames.has(key) || versionNames.has(key)) {
        rejected.push(f.name);
        continue;
      }
      existingNames.add(key);
      accepted.push(f);
    }

    if (accepted.length > 0) {
      setFiles((prev) => [...prev, ...accepted]);
    }
    if (rejected.length > 0) {
      setMessage(`以下文件因同名被忽略：${rejected.join('、')}。同一版本内不允许重名文件。`);
    }

    // Reset input so user can select same file again after rename/remove.
    e.target.value = '';
  };

  const handleCoverImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = '';
    if (!f) return;

    if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(f.type)) {
      alert('仅支持上传 jpg/jpeg/png/gif/webp 格式的图片');
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      alert('图片大小不能超过 5 MB');
      return;
    }

    setCoverImageFile(f);
    setCoverImageMarkedForDeletion(false);
    setCoverImagePreviewFromFile(f);
  };

  const handleRemoveCoverImage = () => {
    if (coverImageFile) {
      setCoverImageFile(null);
      if (existingCoverImageKey && datasetIdRef.current) {
        setCoverImageMarkedForDeletion(false);
        setCoverImagePreviewFromServer(datasetIdRef.current, existingCoverImageKey);
      } else {
        clearCoverImagePreview();
      }
      return;
    }

    if (existingCoverImageKey) {
      setCoverImageMarkedForDeletion(true);
    }
    clearCoverImagePreview();
  };

  const restoreExistingCoverImage = () => {
    if (!datasetIdRef.current || !existingCoverImageKey) return;
    setCoverImageMarkedForDeletion(false);
    setCoverImageFile(null);
    setCoverImagePreviewFromServer(datasetIdRef.current, existingCoverImageKey);
  };

  const removeFile = (idx: number) => setFiles(prev => prev.filter((_, i) => i !== idx));

  const loadVersionFilesSnapshot = useCallback(async (targetDatasetId: string, targetVersionNum: number) => {
    const filesRes = await api.get(`/datasets/${targetDatasetId}/versions/${targetVersionNum}/files`);
    const nextFiles = (filesRes.data || []) as VersionFile[];

    const draft: Record<string, FileMetaDraftEntry> = {};
    const previewDraft: Record<string, FilePreview> = {};
    if (nextFiles.length > 0) {
      await Promise.all(
        nextFiles.map(async (f: VersionFile) => {
          let previewColumns: string[] = [];
          try {
            const previewRes = await api.get(`/datasets/${targetDatasetId}/files/${f.id}/preview`);
            previewDraft[f.id] = {
              preview_type: previewRes.data?.preview_type === 'text' ? 'text' : 'table',
              columns: Array.isArray(previewRes.data?.columns) ? previewRes.data.columns.map((column: unknown) => String(column)) : [],
              rows: Array.isArray(previewRes.data?.rows) ? previewRes.data.rows : [],
              truncated: Boolean(previewRes.data?.truncated),
            };
            previewColumns = previewDraft[f.id].columns;
          } catch {
            previewDraft[f.id] = {
              preview_type: 'text',
              columns: [],
              rows: [],
              truncated: false,
              error: '样例数据预览加载失败，请稍后重试。',
            };
          }

          try {
            const metaRes = await api.get(`/datasets/${targetDatasetId}/files/${f.id}/metadata`);
            draft[f.id] = {
              description: metaRes.data.description || '',
              upload_status: metaRes.data.upload_status || f.upload_status || 'pending',
              row_count: metaRes.data.row_count,
              error_message: metaRes.data.error_message || f.error_message || '',
              columns: orderColumnsByPreview((metaRes.data.columns || []).map((c: any) => ({
                column_name: c.column_name,
                column_type: c.column_type,
                description: c.description || ''
              })), previewColumns)
            };
          } catch {
            draft[f.id] = {
              description: '',
              upload_status: f.upload_status || 'pending',
              row_count: f.row_count,
              error_message: f.error_message || '',
              columns: [],
            };
          }
        })
      );
    }

    return { nextFiles, draft, previewDraft };
  }, []);

  const applyVersionFilesSnapshot = useCallback((snapshot: {
    nextFiles: VersionFile[];
    draft: Record<string, FileMetaDraftEntry>;
    previewDraft: Record<string, FilePreview>;
  }) => {
    setVersionFiles(snapshot.nextFiles);
    setFileMetaDraft((prev) => mergeFileMetaDraft(prev, snapshot.draft));
    setPreviewByFileId(() => {
      const nextPreviewState: Record<string, FilePreview> = {};
      snapshot.nextFiles.forEach((file) => {
        if (snapshot.previewDraft[file.id]) {
          nextPreviewState[file.id] = snapshot.previewDraft[file.id];
        }
      });
      return nextPreviewState;
    });
  }, []);

  const waitForUploadedFilesToBeDisplayReady = useCallback(async (
    targetDatasetId: string,
    uploadedRecords: UploadedFileRecord[],
    maxWaitMs = 60000,
  ) => {
    if (uploadedRecords.length === 0) {
      return { timedOut: false };
    }

    const deadline = Date.now() + maxWaitMs;
    while (Date.now() < deadline) {
      const results = await Promise.all(
        uploadedRecords.map(async (file) => {
          try {
            const metaRes = await api.get(`/datasets/${targetDatasetId}/files/${file.id}/metadata`);
            const metaColumns = Array.isArray(metaRes.data?.columns) ? metaRes.data.columns : [];
            const uploadStatus = metaRes.data?.upload_status || file.upload_status || 'pending';
            return uploadStatus === 'error' || metaColumns.length > 0;
          } catch {
            return false;
          }
        })
      );

      if (results.every(Boolean)) {
        return { timedOut: false };
      }

      await new Promise((resolve) => window.setTimeout(resolve, 800));
    }

    return { timedOut: true };
  }, []);

  const refreshVersionFilesAndMeta = useCallback(async () => {
    if (!datasetId) return;
    const snapshot = await loadVersionFilesSnapshot(datasetId, workingVersionNum);
    applyVersionFilesSnapshot(snapshot);
  }, [datasetId, workingVersionNum, loadVersionFilesSnapshot, applyVersionFilesSnapshot]);

  // Keep refs in sync
  useEffect(() => { datasetIdRef.current = datasetId; }, [datasetId]);
  useEffect(() => { workingVersionNumRef.current = workingVersionNum; }, [workingVersionNum]);
  useEffect(() => () => revokeCoverImageObjectUrl(), [revokeCoverImageObjectUrl]);

  // Slug conflict detection: debounce check if title-derived slug is already taken
  // Only checks published/archived datasets — drafts do NOT block a slug.
  useEffect(() => {
    const slug = slugifyDatasetTitle(title);
    const currentDsId = editDatasetId || datasetId;
    if (!user?.username || !slug || slug === 'dataset') {
      setSlugConflict(false);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams();
        if (currentDsId) params.set('exclude_id', currentDsId);
        const res = await api.get(
          `/datasets/${encodeURIComponent(user.username)}/${encodeURIComponent(slug)}/slug-check?${params.toString()}`
        );
        setSlugConflict(res.data?.conflict === true);
      } catch {
        setSlugConflict(false);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [title, user?.username, editDatasetId, datasetId]);

  // beforeunload: warn + cleanup newly created draft via fetch keepalive
  useEffect(() => {
    if (!datasetId || hasSaved) return;
    const handler = (e: BeforeUnloadEvent) => {
      // Try to cleanup newly created drafts when tab closes
      if (isNewlyCreatedRef.current && newDatasetSlugRef.current && user?.username) {
        const slug = newDatasetSlugRef.current;
        const owner = user.username;
        const baseUrl = String(api.defaults?.baseURL || '/api/v1').replace(/\/$/, '');
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        const deleteUrl = `${baseUrl}/datasets/${encodeURIComponent(owner)}/${encodeURIComponent(slug)}`;
        try {
          fetch(deleteUrl, {
            method: 'DELETE',
            keepalive: true,
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          }).catch(() => {});
        } catch {}
      }
      e.preventDefault();
      e.returnValue = '您有未保存的数据，确定要离开吗？';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [datasetId, hasSaved, user]);

  useEffect(() => {
    if (!datasetId) return;
    if (step === 1 || step === 2) {
      refreshVersionFilesAndMeta().catch(() => {});
    }
  }, [step, datasetId, refreshVersionFilesAndMeta]);

  useEffect(() => {
    if (step !== 2 || !datasetId || versionFiles.length === 0) return;
    const hasPendingFiles = versionFiles.some((file) => {
      const draft = fileMetaDraft[file.id];
      const uploadStatus = draft?.upload_status || file.upload_status || 'pending';
      if (uploadStatus === 'pending') return true;
      if (uploadStatus === 'error') return false;
      return draft?.columns?.length === 0 && !draft?.error_message;
    });
    if (!hasPendingFiles) return;

    const timer = window.setTimeout(() => {
      refreshVersionFilesAndMeta().catch(() => {});
    }, 2000);

    return () => window.clearTimeout(timer);
  }, [step, datasetId, versionFiles, fileMetaDraft, refreshVersionFilesAndMeta]);

  useEffect(() => {
    const initEditMode = async () => {
      if (!user || !editDatasetId) return;
      setInitLoading(true);
      try {
        const dsRes = await api.get(`/datasets/by-id/${editDatasetId}`);
        const ds = dsRes.data;
        if (ds.owner_id !== user.id) {
          setMessage('无权限编辑该数据集。');
          setInitLoading(false);
          return;
        }

        setDatasetId(ds.id);
        setWorkingVersionNum(targetVersionNum);
        setTitle(ds.title || '');
        setDescription(ds.description || '');
        setLicense(ds.license || 'CC BY 4.0');
        setSourceType(ds.source_type ? ds.source_type.split(',').map((s: string) => normalizeSourceTypeCode(s.trim()) || s.trim()).filter(Boolean) : ['lab']);
        setSourceRef(ds.source_ref || '');
        setCoverImageFile(null);
        setCoverImageUploading(false);
        setCoverImageMarkedForDeletion(false);
        if (ds.cover_image_key) {
          setExistingCoverImageKey(ds.cover_image_key);
          setCoverImagePreviewFromServer(ds.id, ds.cover_image_key);
        } else {
          setExistingCoverImageKey(null);
          clearCoverImagePreview();
        }
        try {
          const policyRes = await api.get(`/datasets/${ds.id}/access-policy`);
          const level = policyRes.data?.access_level === 'password_protected' ? 'password_protected' : 'public';
          setAccessLevel(level);
          setInitialAccessLevel(level);
          setHasExistingAccessPassword(Boolean(policyRes.data?.has_password));
          setAccessPassword('');
        } catch {
          setAccessLevel('public');
          setInitialAccessLevel('public');
          setHasExistingAccessPassword(false);
          setAccessPassword('');
        }

        const vRes = await api.get(`/datasets/${ds.id}/versions`);
        const allVersions = vRes.data || [];
        const targetVersion = allVersions.find((v: any) => v.version_num === targetVersionNum);
        setVersionNote(targetVersion?.version_note || '');
        const publishedVersionsAsc = [...allVersions]
          .filter((v: any) => v.status === 'published')
          .sort((a: any, b: any) => a.version_num - b.version_num);
        const publishedDisplayNoMap = new Map<number, number>(
          publishedVersionsAsc.map((v: any, idx: number) => [v.version_num, idx + 1])
        );
        const nextDisplayNo = targetVersion?.status === 'published'
          ? (publishedDisplayNoMap.get(targetVersion.version_num) ?? null)
          : (publishedVersionsAsc.length + 1);
        setTargetReleaseVersionNum(nextDisplayNo);

        try {
          const tagsRes = await api.get(`/datasets/${ds.id}/tags`);
          const tags = (tagsRes.data || []) as Array<{ tag: string; tag_type?: string }>;
          setTaskTags(tags.filter((t) => t.tag_type === 'task').map((t) => t.tag));
        } catch {
          setTaskTags([]);
        }

        let nextStep = mode === 'new-version' ? 1 : 2;
        if (mode === 'new-version') {
          // Ensure the draft version actually exists in the backend.
          // If targetVersion is null OR it's already published/pending (e.g. user navigated back after
          // auto-publish), create a fresh draft so uploads and file listings work correctly.
          let actualVersionNum = targetVersionNum;
          let actualVersionStatus = targetVersion?.status ?? 'draft';
          if (!targetVersion || targetVersion.status !== 'draft') {
            try {
              const latestPublished = publishedVersionsAsc[publishedVersionsAsc.length - 1];
              const createRes = await api.post(`/datasets/${ds.id}/versions`, {
                base_version_num: latestPublished?.version_num ?? null,
                reset_existing_draft: false,
              });
              actualVersionNum = createRes.data.version_num;
              actualVersionStatus = createRes.data.status ?? 'draft';
              setWorkingVersionNum(actualVersionNum);
            } catch (createErr: any) {
              const detail = createErr?.response?.data?.detail;
              if (detail?.code === 'existing_unapproved_version') {
                // An unapproved version already exists – use it (may be pending_review)
                actualVersionNum = detail.version_num ?? targetVersionNum;
                actualVersionStatus = detail.status ?? 'draft';
                setWorkingVersionNum(actualVersionNum);
              } else {
                throw createErr;
              }
            }
          }
          setWorkingVersionStatus(actualVersionStatus);
          try {
            const snapshot = await loadVersionFilesSnapshot(ds.id, actualVersionNum);
            applyVersionFilesSnapshot(snapshot);
            if (snapshot.nextFiles.length > 0) {
              setMessage('已加载当前草稿文件（含继承文件），可继续上传或删除，再进入下一步填写信息。');
            }
          } catch {
            // version or files not ready yet, just start from step 1
          }
        }

        // For edit mode (non new-version), track the actual version status
        if (mode !== 'new-version' && targetVersion) {
          setWorkingVersionStatus(targetVersion.status || 'draft');
        }

        setStep(nextStep);
      } catch (err: any) {
        setMessage(`加载草稿失败: ${formatErrorDetail(err.response?.data?.detail || err.message)}`);
      } finally {
        setInitLoading(false);
      }
    };
    initEditMode();
  }, [editDatasetId, user, targetVersionNum, mode, loadVersionFilesSnapshot, applyVersionFilesSnapshot, clearCoverImagePreview, setCoverImagePreviewFromServer]);

  const handleClearDraft = () => {
    if (!datasetId || uploading) return;
    setShowClearDraftConfirm(true);
  };

  const confirmClearDraft = async () => {
    if (!datasetId) return;
    setShowClearDraftConfirm(false);
    try {
      setUploading(true);
      await Promise.all(versionFiles.map(f => api.delete(`/datasets/${datasetId}/files/${f.id}`)));
      setVersionFiles([]);
      setFileMetaDraft({});
      setPreviewByFileId({});
      alert('草稿文件已清空。');
    } catch (e: any) {
      alert('清空失败: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  };

  const deleteVersionFile = async (fileId: string) => {
    if (!datasetId) return;
    if (!(await askConfirm('确认从当前版本删除这个文件吗？该操作只影响当前版本。'))) return;
    setDeletingFileId(fileId);
    try {
      await api.delete(`/datasets/${datasetId}/files/${fileId}`);
      setMessage('文件已从当前版本删除。');
      await refreshVersionFilesAndMeta();
    } catch (err: any) {
      setMessage(`删除文件失败: ${formatErrorDetail(err.response?.data?.detail || err.message)}`);
    } finally {
      setDeletingFileId('');
    }
  };

  const autofillColumnDescriptions = (targetFileId: string) => {
    const target = fileMetaDraft[targetFileId];
    if (!target || !target.columns.length) {
      alert('目标文件暂无可填充的列信息。');
      return;
    }

    const targetNames = target.columns.map((c) => c.column_name.trim()).join('||');
    const sourceEntry = Object.entries(fileMetaDraft).find(([fileId, meta]) => {
      if (fileId === targetFileId) return false;
      if (!meta?.columns?.length) return false;
      const sourceNames = meta.columns.map((c) => c.column_name.trim()).join('||');
      if (sourceNames !== targetNames) return false;
      return meta.columns.some((c) => String(c.description || '').trim());
    });

    if (!sourceEntry) {
      alert('未找到可复用的同字段文件（列名和顺序需一致，且已有列说明）。');
      return;
    }

    const [, sourceMeta] = sourceEntry;
    const sourceMap = new Map(sourceMeta.columns.map((c) => [c.column_name, c.description || '']));
    const nextColumns = target.columns.map((c) => {
      const current = String(c.description || '').trim();
      if (current) return c;
      const fill = sourceMap.get(c.column_name) || '';
      return { ...c, description: fill };
    });

    setFileMetaDraft((prev) => ({
      ...prev,
      [targetFileId]: {
        ...target,
        columns: nextColumns,
      }
    }));
    setMessage('已按同字段文件自动填充可复用列说明，请检查后保存。');
  };

  // Cleanup: delete newly-created draft dataset if user abandons
  const cleanupNewDraft = async () => {
    if (!isNewlyCreatedRef.current) return;
    const slug = newDatasetSlugRef.current;
    const owner = user?.username;
    if (!slug || !owner) return;
    try {
      await api.delete(`/datasets/${encodeURIComponent(owner)}/${encodeURIComponent(slug)}`);
    } catch {
      // Silently ignore cleanup errors
    }
  };

  // Navigation guard: confirm before leaving with unsaved data
  const confirmLeave = async (destination?: string) => {
    if (!datasetId || hasSaved) {
      if (destination) router.push(destination);
      else router.back();
      return;
    }
    const msg = isNewlyCreatedRef.current
      ? '您有未保存的新数据集，离开后草稿将被删除。\n\n确定要放弃当前操作吗？'
      : '您有未保存的修改，离开后未保存的内容将丢失。\n\n确定要放弃当前操作吗？';
    if (await askConfirm(msg)) {
      setHasSaved(true); // prevent double prompt from beforeunload
      cleanupNewDraft().finally(() => {
        if (destination) router.push(destination);
        else router.back();
      });
    }
  };

  if (!user) {
    return <div className="text-center py-20">请先 <a href="/login" className="text-blue-600 underline">登录</a> 后再上传数据。</div>;
  }

  if (initLoading) {
    return <div className="py-20 text-center text-slate-500">正在加载草稿...</div>;
  }

  // Step 0: Confirmation dialog
  if (step === 0) {
    const canContinue = confirmSmilesChecked && confirmColumnNamingChecked;
    return (
      <div className="mx-auto mt-10 max-w-xl rounded-[1.25rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.94),rgba(255,255,255,0.98))] p-8 shadow-[0_18px_40px_-38px_rgba(15,23,42,0.34)]">
        <h2 className="text-xl font-bold mb-4">上传前请确认</h2>
        <div className="mb-6 space-y-3 text-sm text-slate-700">
          <label className="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={confirmSmilesChecked}
              onChange={(e) => setConfirmSmilesChecked(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span>
              我已对 SMILES 相关列进行了基本标准化，并检查了其有效性
              <span className="block mt-1 text-xs text-slate-500">
                例如统一表示形式、排查明显错误值，并确认关键列中的 SMILES 可正常解析。
              </span>
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={confirmColumnNamingChecked}
              onChange={(e) => setConfirmColumnNamingChecked(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span>我的列名命名清晰，便于他人理解</span>
          </label>
        </div>
        <div className="mb-6 space-y-2 rounded-xl border border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-700">
          <p className="font-semibold text-slate-800">建议列名参考：</p>
          <div className="flex flex-wrap gap-2">
            {[
              'reactants', 'products', 'solvent', 'catalyst', 'ligand', 'base', 
              'yield_pct', 'temperature_c', 'reaction_smiles', 'reagent'
            ].map(name => (
              <span key={name} className="inline-flex items-center rounded-md border border-slate-200 bg-white/85 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">
                {name}
              </span>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <button 
            onClick={() => confirmLeave('/profile')} 
            className="rounded-xl border border-slate-200 bg-white/85 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-800"
          >
            取消
          </button>
          <button 
            onClick={async () => {
              // If editing existing dataset, go straight to step 1
              if (editDatasetId) {
                setStep(1);
                return;
              }
              // Check for existing drafts before proceeding
              try {
                const draftsRes = await api.get(`/datasets?owner=${encodeURIComponent(user!.username)}&status_filter=draft&limit=20`);
                const drafts = (draftsRes.data?.items || []) as any[];
                if (drafts.length > 0) {
                  setExistingDrafts(drafts);
                  setShowDraftPicker(true);
                  return;
                }
              } catch {}
              setDraftCheckDone(true);
              setStep(1);
            }}
            disabled={!canContinue}
            className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              canContinue
                ? 'bg-primary text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring'
                : 'cursor-not-allowed bg-slate-200 text-slate-500'
            }`}
          >
            确认并继续上传
          </button>
        </div>

        {/* Draft picker overlay */}
        {showDraftPicker && existingDrafts.length > 0 && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="flex max-h-[80vh] w-full max-w-lg flex-col overflow-hidden rounded-[1.25rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.98))] shadow-xl">
              <div className="border-b border-slate-200 p-6">
                <h3 className="text-lg font-bold text-slate-900">检测到已有草稿</h3>
                <p className="mt-1 text-sm text-slate-500">
                  您有 {existingDrafts.length} 个草稿数据集。可以继续编辑已有草稿，或创建全新数据集。
                </p>
              </div>
              <div className="overflow-y-auto flex-1 p-4 space-y-2">
                {existingDrafts.map((draft: any) => (
                  <button
                    key={draft.id}
                    onClick={() => {
                      setHasSaved(true); // prevent beforeunload warning
                      const vNum = Number(draft.latest_editable_version_num || draft.current_version || 1);
                      const modeQ = draft.has_published_version ? '&mode=new-version' : '';
                      router.push(`/upload?datasetId=${draft.id}&versionNum=${vNum}${modeQ}`);
                    }}
                    className="group w-full rounded-xl border border-slate-200 bg-white/80 p-3 text-left transition-colors hover:border-primary/40 hover:bg-primary/5"
                  >
                    <div className="text-sm font-medium text-slate-900 group-hover:text-primary">{draft.title}</div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      {draft.owner?.username}/{draft.slug} · 创建于 {new Date(draft.created_at).toLocaleString('zh-CN')}
                    </div>
                  </button>
                ))}
              </div>
              <div className="flex justify-between border-t border-slate-200 p-4">
                <button
                  onClick={() => { setShowDraftPicker(false); }}
                  className="px-4 py-2 text-sm text-slate-600 transition hover:text-slate-900"
                >
                  返回
                </button>
                <button
                  onClick={() => {
                    setShowDraftPicker(false);
                    setDraftCheckDone(true);
                    setStep(1);
                  }}
                  className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md shadow hover:bg-primary/90"
                >
                  创建全新数据集
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  const handleUploadFiles = async () => {
    if (workingVersionStatus && workingVersionStatus !== 'draft') {
      alert(`当前版本不可编辑 (${workingVersionStatus})。请点击"创建新版本"或刷新页面重试。`);
      return;
    }
    
    if (files.length === 0) {
      if (versionFiles.length > 0) {
        setStep(2);
        return;
      }
      alert('请至少上传一个文件');
      return;
    }

    setUploading(true);
    const existingDatasetId = datasetId || editDatasetId;
    setMessage(existingDatasetId ? '正在上传到当前草稿版本...' : '正在创建数据集...');
    try {
      let dsId = existingDatasetId;
      let targetVersionNum = dsId === existingDatasetId ? workingVersionNum : 1;

      if (!dsId) {
        const dsRes = await api.post('/datasets', { title: files[0].name.replace(/\.[^/.]+$/, ''), description: '(待补充)' });
        dsId = dsRes.data.id;
        setDatasetId(dsId);
        isNewlyCreatedRef.current = true;
        newDatasetSlugRef.current = dsRes.data.slug || '';
        setWorkingVersionNum(1);
        setTitle(dsRes.data.title);
        targetVersionNum = 1;
      }

      // Upload each file
      const uploaded: string[] = [];
      const uploadedRecords: UploadedFileRecord[] = [];
      const duplicated: string[] = [];
      for (const file of files) {
        setMessage(`正在上传 ${file.name}...`);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('version_num', String(targetVersionNum));
        try {
          const uploadRes = await api.post(`/datasets/${dsId}/files`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          uploaded.push(file.name);
          uploadedRecords.push({
            id: String(uploadRes.data?.id),
            filename: file.name,
            upload_status: uploadRes.data?.upload_status || 'pending',
          });
        } catch (uploadErr: any) {
          const detail = uploadErr?.response?.data?.detail;
          if (detail?.code === 'duplicate_filename') {
            duplicated.push(file.name);
            continue;
          }
          throw uploadErr;
        }
      }
      setUploadedFiles(uploaded);

      if (duplicated.length > 0) {
        setMessage(`以下文件上传失败（同名已存在于当前版本）：${duplicated.join('、')}。其余文件已成功上传。`);
      } else {
        setMessage('文件已上传，正在解析列名和样例数据...');
      }

      if (uploadedRecords.length > 0) {
        setProcessingFiles(true); // Start processing UI
        // Wait up to 5 minutes
        const waitResult = await waitForUploadedFilesToBeDisplayReady(dsId, uploadedRecords, 300000);
        
        const snapshot = await loadVersionFilesSnapshot(dsId, targetVersionNum);
        applyVersionFilesSnapshot(snapshot);
        
        setProcessingFiles(false); // End processing UI

        if (waitResult.timedOut) {
          const force = await askConfirm('文件解析耗时很久（超过5分钟），部分列信息可能尚未就绪。\n是否强行进入下一步？\n(建议取消并稍后刷新页面查看)');
          if (!force) {
             setMessage('解析超时，请稍后刷新页面查看。');
             setFiles([]); // Clear selection
             return; // Stop here
          }
        } else if (duplicated.length === 0) {
          setMessage('');
        }
      } else if (dsId) {
        const snapshot = await loadVersionFilesSnapshot(dsId, targetVersionNum);
        applyVersionFilesSnapshot(snapshot);
      }

      setFiles([]);
      setStep(2);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (detail === 'auth_email_not_verified') {
        setMessage('上传失败：当前账号邮箱尚未验证，请先完成邮箱验证。');
      } else {
        setMessage(`上传失败: ${formatErrorDetail(detail || err.message)}`);
      }
    } finally {
      setUploading(false);
    }
  };

  const addTaskTag = (raw: string) => {
    const tag = raw.trim().toLowerCase();
    if (!tag) return;
    if (!/^[a-z0-9_]+$/.test(tag)) {
      alert('标签仅支持小写字母、数字和下划线');
      return;
    }
    if (taskTags.includes(tag)) return;
    setTaskTags((prev) => [...prev, tag]);
  };

  const removeTaskTag = (tag: string) => {
    setTaskTags((prev) => prev.filter((t) => t !== tag));
  };

  const syncTags = async () => {
    if (!datasetId) return;
    const res = await api.get(`/datasets/${datasetId}/tags`).catch(() => ({ data: [] }));
    const current = ((res.data || []) as Array<{ tag: string; tag_type?: string }>).filter((t) => t.tag_type === 'task').map((t) => t.tag);

    const toDelete = current.filter((t) => !taskTags.includes(t));
    const toAdd = taskTags.filter((t) => !current.includes(t));

    await Promise.all(toDelete.map((t) => api.delete(`/datasets/${datasetId}/tags/${t}`)));
    await Promise.all(toAdd.map((t) => api.post(`/datasets/${datasetId}/tags`, { tag: t, tag_type: 'task' })));
  };

  const persistAllFileMetadata = async () => {
    if (!datasetId || versionFiles.length === 0) return;

    await Promise.all(
      versionFiles.map((f) => {
        const draft = fileMetaDraft[f.id] || { description: '', columns: [] as Array<{ column_name: string; description: string }> };
        return api.put(`/datasets/${datasetId}/files/${f.id}/metadata`, {
          description: draft.description,
          columns: (draft.columns || []).map((c) => ({
            column_name: c.column_name,
            description: c.description,
          })),
        });
      })
    );
  };

  const saveDatasetMeta = async () => {
    const payload = {
      title,
      description,
      license,
      source_type: sourceType.join(','),
      source_ref: sourceRef || undefined,
    };

    try {
      await api.put(`/datasets/by-id/${datasetId}/meta`, payload);
      return;
    } catch (err: any) {
      if (!isRouteNotFound(err)) {
        throw err;
      }
    }

    const dsRes = await api.get(`/datasets/by-id/${datasetId}`);
    const ownerUsername = dsRes.data?.owner?.username || user?.username;
    const slug = dsRes.data?.slug;
    if (!ownerUsername || !slug) {
      throw { response: { data: { detail: 'dataset_meta_endpoint_not_available' } } };
    }
    await api.put(`/datasets/${encodeURIComponent(ownerUsername)}/${encodeURIComponent(slug)}`, payload);
  };

  const saveAccessPolicy = async (): Promise<{needsReview?: boolean; message?: string}> => {
    try {
      // 随机生成一个6位提取码
      const generatedToken = Math.random().toString(36).substring(2, 8).toLowerCase();
      const payloadPassword = accessLevel === 'password_protected' 
        ? (!hasExistingAccessPassword ? generatedToken : undefined) // 新增私密时自动给一个Token，已有则保留原Token/不覆盖
        : undefined;

      const policyRes = await api.put(`/datasets/${datasetId}/access-policy`, {
        access_level: accessLevel,
        access_password: payloadPassword,
      });
      setHasExistingAccessPassword(Boolean(policyRes.data?.has_password));
      return {
        needsReview: Boolean(policyRes.data?.needs_review),
        message: policyRes.data?.message,
      };
    } catch (err: any) {
      if (!isRouteNotFound(err)) {
        throw err;
      }
      if (accessLevel === 'public') {
        setHasExistingAccessPassword(false);
        return {};
      }
      throw { response: { data: { detail: 'access_policy_endpoint_not_available' } } };
    }
  };

  const syncCoverImage = async (targetDatasetId: string) => {
    if (coverImageFile) {
      setCoverImageUploading(true);
      try {
        const formData = new FormData();
        formData.append('file', coverImageFile);
        const uploadRes = await api.post(`/datasets/by-id/${targetDatasetId}/cover-image`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        const nextCoverKey = String(uploadRes.data?.cover_image_key || '').trim() || null;
        setExistingCoverImageKey(nextCoverKey);
        setCoverImageMarkedForDeletion(false);
        setCoverImageFile(null);
        if (nextCoverKey) {
          setCoverImagePreviewFromServer(targetDatasetId, nextCoverKey);
        } else {
          clearCoverImagePreview();
        }
      } finally {
        setCoverImageUploading(false);
      }
      return;
    }

    if (coverImageMarkedForDeletion && existingCoverImageKey) {
      setCoverImageUploading(true);
      try {
        await api.delete(`/datasets/by-id/${targetDatasetId}/cover-image`);
        setExistingCoverImageKey(null);
        setCoverImageMarkedForDeletion(false);
        clearCoverImagePreview();
      } finally {
        setCoverImageUploading(false);
      }
    }
  };

  const handleSubmitInfo = async (action: 'draft' | 'review') => {
    // 隐藏掉原本强校验“自己输密码”的逻辑，改为静默由后台或固定方案处理
    // 以实现只选权限，不用写密码顺滑体验

    if (action === 'review') {
      // Guard: prevent submitting already-published or pending-review versions
      if (workingVersionStatus === 'published') {
        alert('此版本已经发布，无需再次提交。\n如需添加新版本，请从数据集详情页点击"新增版本"。');
        return;
      }
      if (workingVersionStatus === 'pending_review') {
        alert('此版本正在审核中，无法重复提交。\n如需修改，请先在数据集详情页撤回审核申请。');
        return;
      }

      if (description.trim().length < 10) {
        alert('数据集描述至少需要 10 个字。');
        return;
      }
      if (taskTags.length === 0) {
        alert('请至少添加 1 个任务类标签。');
        return;
      }
      const incomplete = versionFiles.find((f) => {
        const meta = fileMetaDraft[f.id];
        if (!meta || !meta.description.trim()) return true;
        if (!meta.columns || meta.columns.length === 0) return true;
        return meta.columns.some((c) => !String(c.description || '').trim());
      });
      if (incomplete) {
        const meta = fileMetaDraft[incomplete.id];
        const uploadStatus = meta?.upload_status || incomplete.upload_status || 'pending';
        if (uploadStatus === 'pending') {
          alert('部分文件仍在读取列名和样例数据，请稍候自动完成后再提交审核。');
          return;
        }
        if (uploadStatus === 'error') {
          alert('部分文件解析失败，请检查文件格式后重新上传。');
          return;
        }
        alert('提交审核前，请先补全每个文件的描述与列说明。');
        return;
      }
      if (!versionNote.trim()) {
        alert('请填写版本说明。');
        return;
      }
    }

    setSubmitting(true);
    try {
      setMessage('正在保存文件说明...');
      await persistAllFileMetadata();

      await saveDatasetMeta();
      const targetDatasetId = datasetIdRef.current;
      if (!targetDatasetId) {
        throw new Error('数据集 ID 丢失，请刷新页面后重试');
      }
      if (coverImageFile || (coverImageMarkedForDeletion && existingCoverImageKey)) {
        setMessage(coverImageFile ? '正在上传封面图...' : '正在删除封面图...');
        await syncCoverImage(targetDatasetId);
      }

      const policyResult = await saveAccessPolicy();
      await syncTags();

      setHasSaved(true);
      isNewlyCreatedRef.current = false; // no longer needs cleanup

      // 如果权限切换（私密→公开）触发了审核流程，直接跳转，不再继续提交审核
      if (policyResult?.needsReview) {
        setMessage(policyResult.message || '访问权限已变更为公开，数据集已提交管理员审核。');
        setTimeout(() => router.push(`/datasets/${datasetId}`), 1500);
        return;
      }

      if (action === 'review') {
        const reviewRes = await api.post(`/datasets/${datasetId}/submit-review`, { version_num: workingVersionNum, version_note: versionNote.trim() });
        const autoPublished = Boolean(reviewRes.data?.auto_published);
        if (autoPublished) {
          setMessage('密码保护数据集已发布，无需管理员审核。');
          setTimeout(() => router.push(`/datasets/${datasetId}`), 1200);
        } else {
          setMessage('数据集已提交审核！');
          setTimeout(() => router.push('/profile'), 1200);
        }
      } else {
        setMessage('草稿已保存！');
        setTimeout(() => router.push(`/upload?datasetId=${datasetId}&versionNum=${workingVersionNum}${mode ? `&mode=${mode}` : ''}`), 800);
      }
    } catch (err: any) {
      setMessage(`提交失败: ${formatErrorDetail(err.response?.data?.detail || err.message)}`);
    } finally {
      setSubmitting(false);
    }
  };

  const previewSlug = slugifyDatasetTitle(title);
  const previewDatasetPath = user?.username
    ? `/datasets/${encodeURIComponent(user.username)}/${previewSlug}`
    : '';
  const canEnterInfoStep = step === 2 || files.length > 0 || versionFiles.length > 0;
  const paperPanelClass = 'rounded-[1.25rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.94),rgba(255,255,255,0.98))] shadow-[0_18px_40px_-38px_rgba(15,23,42,0.34)]';
  const softInputClass = 'mt-1 w-full rounded-xl border border-slate-200 bg-slate-50/75 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 transition focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15';
  const softPlainInputClass = 'w-full rounded-xl border border-slate-200 bg-slate-50/75 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 transition focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15';

  return (
    <div className={`mx-auto max-w-3xl p-8 ${paperPanelClass}`}>
      <h1 className="text-2xl font-bold mb-6">
        {mode === 'new-version' ? '新增版本（草稿）' : editDatasetId ? '编辑草稿数据集' : '上传数据集'}
      </h1>
      {mode === 'new-version' && (
        <p className="-mt-4 mb-6 text-sm text-slate-500">
          当前为未发布草稿，{accessLevel === 'password_protected' ? '保存后' : '审核通过后'}{targetReleaseVersionNum ? `将发布为 V${targetReleaseVersionNum}` : '将生成正式版本号'}。
        </p>
      )}

      {workingVersionStatus && workingVersionStatus !== 'draft' && (
        <div className="mb-6 flex items-start gap-3 rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 110 20A10 10 0 0112 2z" />
          </svg>
          <div>
            <div className="font-semibold mb-0.5">此版本{workingVersionStatus === 'pending_review' ? '正在审核中' : '已发布'}</div>
            <div className="text-amber-700">
              {workingVersionStatus === 'pending_review'
                ? <>当前版本正在审核，无法修改或添加文件。如需修改，请先前往<a href={`/datasets/${editDatasetId || datasetId}`} className="underline font-medium">数据集详情页</a>取消审核，再重新编辑。</>
                : <>当前版本已发布，无法修改。如需添加文件或修改信息，请前往<a href={`/datasets/${editDatasetId || datasetId}`} className="underline font-medium">数据集详情页</a>创建新版本。</>
              }
            </div>
          </div>
        </div>
      )}

      {/* Steps indicator */}
      <div className="flex mb-8 border-b pb-4">
        <button
          type="button"
          onClick={() => setStep(1)}
          className={`flex-1 text-center font-semibold transition-colors ${step === 1 ? 'text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}
        >
          步骤 1/2：上传文件
        </button>
        <button
          type="button"
          onClick={() => canEnterInfoStep && setStep(2)}
          disabled={!canEnterInfoStep}
          className={`flex-1 text-center font-semibold transition-colors ${step === 2 ? 'text-blue-600' : 'text-slate-400'} ${canEnterInfoStep ? 'hover:text-slate-600' : 'cursor-not-allowed opacity-60'}`}
        >
          步骤 2/2：填写信息
        </button>
      </div>

      {step === 1 && (
        <div className="space-y-6 relative">
          {processingFiles && (
            <div className="absolute inset-0 z-10 bg-white/80 backdrop-blur-sm flex flex-col items-center justify-center rounded-lg border border-primary/20 shadow-sm">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mb-4"></div>
                <p className="text-lg font-semibold text-primary">正在解析文件内容...</p>
                <p className="mt-2 max-w-sm text-center text-sm text-slate-500">系统正在自动提取列名并生成预览数据。<br/>通常只需数秒到几十秒，请保持页面开启。</p>
            </div>
          )}
          {versionFiles.length > 0 && (
            <div className="rounded-[1.1rem] border border-slate-200 bg-slate-50/85 p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-slate-800">当前版本文件</h3>
                <button
                  onClick={handleClearDraft}
                  disabled={uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft')}
                  className="text-xs text-red-600 bg-red-50 hover:bg-red-100 px-2 py-1 rounded border border-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? '处理中...' : '⚠️ 清空草稿'}
                </button>
              </div>
              <div className="space-y-2">
                {versionFiles.map((f: any) => (
                  <div key={f.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white/80 p-3">
                    <span className="text-sm text-slate-700">📄 {f.filename} <span className="ml-2 font-mono text-slate-400">{((f.file_size || 0) / 1024 / 1024).toFixed(2)} MB</span></span>
                    <button
                      onClick={() => deleteVersionFile(f.id)}
                      disabled={deletingFileId === f.id || (workingVersionStatus !== '' && workingVersionStatus !== 'draft')}
                      className="text-destructive text-sm hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deletingFileId === f.id ? '删除中...' : '从当前版本删除'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div 
            className={`flex flex-col items-center justify-center rounded-[1.2rem] border-2 border-dashed p-10 text-center transition-colors ${
              uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft')
                ? 'cursor-not-allowed border-slate-200 bg-slate-100/70' 
                : 'border-slate-300 bg-slate-50/70 hover:border-primary/40 hover:bg-white'
            }`}
          >
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              disabled={uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft')}
              className="hidden"
              id="file-upload"
              accept=".csv,.xls,.xlsx"
            />
            <label 
              htmlFor={uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft') ? undefined : "file-upload"} 
              className={`${uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft') ? 'cursor-not-allowed' : 'cursor-pointer'} flex flex-col items-center justify-center gap-2 w-full h-full`}
            >
              <div className="p-4 rounded-full bg-primary/5 text-primary mb-2">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <span className="text-lg font-medium text-slate-800">
                {uploading 
                  ? '上传处理中...' 
                  : workingVersionStatus && workingVersionStatus !== 'draft' 
                    ? `不可上传 (${workingVersionStatus})` 
                    : '点击或拖拽上传文件 (支持CSV/XLSX)'}
              </span>
              <span className="mt-1 text-sm text-slate-500">
                {workingVersionStatus && workingVersionStatus !== 'draft' 
                  ? '请点击右上角"创建新版本"后再进行上传' 
                  : '支持拖拽上传，单文件最大2GB，压缩文件需提前解压'}
              </span>
            </label>
          </div>

          {files.length > 0 && (
            <div>
              <h3 className="mb-2 font-medium text-slate-800">已选文件：</h3>
              {files.map((f, i) => (
                <div key={i} className="mb-2 flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/75 p-3">
                  <span className="text-sm text-slate-700">📊 {f.name} <span className="text-slate-400">({(f.size / 1024 / 1024).toFixed(2)} MB)</span></span>
                  <button onClick={() => removeFile(i)} className="text-destructive text-sm hover:underline">移除</button>
                </div>
              ))}
            </div>
          )}

          {message && <div className="text-blue-600 text-sm font-medium">{message}</div>}

          <div className="flex justify-end">
            <button onClick={handleUploadFiles} disabled={(files.length === 0 && versionFiles.length === 0) || uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft')}
                    className={`px-6 py-2 rounded-md font-medium text-primary-foreground transition-colors ${
                      (files.length === 0 && versionFiles.length === 0) || uploading || (workingVersionStatus !== '' && workingVersionStatus !== 'draft') ? 'cursor-not-allowed bg-slate-200 text-slate-500' : 'bg-primary shadow hover:bg-primary/90'
                    }`}>
              {uploading ? '上传中...' : files.length === 0 ? '下一步，填写信息 →' : '上传并下一步 →'}
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-5">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="text-sm text-primary hover:underline"
            >
              ← 返回步骤1：上传/管理文件
            </button>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50/85 p-4 text-sm text-slate-700">
            <span className="font-semibold text-primary mr-2">文件已上传：</span>
            {(uploadedFiles.length > 0 ? uploadedFiles : versionFiles.map((f) => f.filename)).join(', ') || '暂无'}
             <span className="ml-2 text-slate-500">请完善以下信息。</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">数据集标题 *</label>
            <input type="text" required value={title} onChange={e => setTitle(e.target.value)}
                   className={softInputClass} />
            {previewDatasetPath && (
              <p className="mt-2 break-all text-xs text-slate-500">
                数据集链接预览：<span className="mono-data text-slate-700">{previewDatasetPath}</span>
                {slugConflict && (
                  <span className="ml-2 text-amber-600">⚠ 此链接已被占用，建议修改标题避免自动追加后缀</span>
                )}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">数据集描述 *（至少10字，最多500字）</label>
            <textarea required value={description} onChange={e => setDescription(e.target.value)}
                      maxLength={META_TEXT_LIMIT}
                      className={`${softInputClass} h-32 resize-none`} placeholder="请详细描述数据集的来源、范围和用途..." />
            <p className="mt-1 text-xs text-slate-400">已输入 {description.length}/{META_TEXT_LIMIT} 字，至少 10 字</p>
          </div>
          <div>
              <label className="block text-sm font-medium text-slate-700">
              {accessLevel === 'password_protected'
                ? `版本说明（保存后${targetReleaseVersionNum ? `发布为 V${targetReleaseVersionNum}` : '生成正式版本号'}，最多500字）*`
                : `版本说明（审核通过后${targetReleaseVersionNum ? `发布为 V${targetReleaseVersionNum}` : '生成正式版本号'}，最多500字）*`}
              </label>
            <textarea value={versionNote} onChange={e => setVersionNote(e.target.value)}
                   maxLength={META_TEXT_LIMIT}
                   placeholder="如：2024.03-2025.12 从文献与实验记录整理；剔除缺失产率样本"
                   className={`${softInputClass} h-24 resize-none`} />
            <p className="mt-1 text-xs text-slate-400">已输入 {versionNote.length}/{META_TEXT_LIMIT} 字</p>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">数据来源类型 *</label>
            <div className="grid grid-cols-4 gap-1.5">
              {SOURCE_TYPE_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setSourceType(prev =>
                    prev.includes(t.value) ? prev.filter(v => v !== t.value) : [...prev, t.value]
                  )}
                  className={`px-2 py-1.5 rounded-md border text-xs text-center transition ${
                    sourceType.includes(t.value)
                      ? 'border-primary/40 bg-primary/[0.08] text-primary font-semibold'
                      : 'border-slate-200 bg-slate-50/70 text-slate-700 hover:border-slate-300 hover:bg-white'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">License *</label>
            <select value={license} onChange={e => setLicense(e.target.value)} className={softPlainInputClass}>
              {LICENSE_OPTIONS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">任务类标签 *（至少 1 个）</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {taskTags.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50/85 px-3 py-1 text-xs font-medium text-slate-700 mono-data">
                  {tag}
                  <button type="button" onClick={() => removeTaskTag(tag)} className="ml-1 text-slate-400 transition hover:text-slate-700">×</button>
                </span>
              ))}
              {taskTags.length === 0 && <span className="text-xs text-slate-400">暂未添加</span>}
            </div>
            <div className="flex flex-wrap gap-2 mb-2">
              {TASK_TAG_PRESETS.map((tag) => (
                <button key={tag} type="button" onClick={() => addTaskTag(tag)} className="rounded-md border border-slate-200 bg-slate-50/70 px-2 py-1 text-xs text-slate-700 transition hover:bg-white mono-data">
                  + {tag}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={customTagInput}
                onChange={(e) => setCustomTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addTaskTag(customTagInput);
                    setCustomTagInput('');
                  }
                }}
                placeholder="自定义任务类标签（如 reaction_yield_benchmark）"
                className={`flex-1 ${softPlainInputClass}`}
              />
              <button type="button" className="rounded-xl border border-slate-200 bg-white/85 px-3 py-2 text-sm text-slate-600 transition hover:bg-slate-50 hover:text-slate-800" onClick={() => {
                addTaskTag(customTagInput);
                setCustomTagInput('');
              }}>添加</button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">来源链接/DOI（建议填写）</label>
            <input type="text" value={sourceRef} onChange={e => setSourceRef(e.target.value)}
                   maxLength={META_TEXT_LIMIT}
                   placeholder="如：10.1021/jacs.xxxxxxx"
                   className={softInputClass} />
            <p className="mt-1 text-xs text-slate-400">最多 {META_TEXT_LIMIT} 字</p>
          </div>

          {/* Cover Image (ToC image) */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">封面图</label>
            <p className="mb-2 text-xs text-slate-400">上传一张展示该数据集主体内容样式的图片，支持 jpg/png/gif/webp（≤5MB）</p>
            <input
              id="cover-image-upload"
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              className="hidden"
              onChange={handleCoverImageChange}
              disabled={submitting || coverImageUploading}
            />
            {coverImagePreview ? (
              <div className="space-y-3">
                <div className="relative inline-block">
                  <img
                    src={coverImagePreview}
                    alt="封面图预览"
                    className="max-h-48 rounded-xl border border-slate-200 bg-slate-50/75 object-contain p-2"
                  />
                  {coverImageUploading && (
                    <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-white/70 text-xs text-slate-600">
                      处理中...
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <label
                    htmlFor={submitting || coverImageUploading ? undefined : 'cover-image-upload'}
                    className={`inline-flex items-center rounded-md border px-3 py-1.5 text-sm transition ${
                      submitting || coverImageUploading
                        ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
                        : 'cursor-pointer border-slate-200 bg-white/85 text-slate-700 hover:border-primary/40 hover:text-primary'
                    }`}
                  >
                    更换图片
                  </label>
                  <button
                    type="button"
                    onClick={handleRemoveCoverImage}
                    disabled={submitting || coverImageUploading}
                    className="inline-flex items-center rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-sm text-red-600 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    移除图片
                  </button>
                </div>
                <p className="text-xs text-slate-400">
                  {coverImageFile ? '新的封面图将在保存后替换当前图片。' : '当前封面图已保存，可继续更换或移除。'}
                </p>
              </div>
            ) : (
              <label
                htmlFor={submitting || coverImageUploading ? undefined : 'cover-image-upload'}
                className={`flex h-32 w-full flex-col items-center justify-center rounded-[1.1rem] border-2 border-dashed transition ${
                  submitting || coverImageUploading
                    ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
                    : 'cursor-pointer border-slate-300 bg-slate-50/75 hover:border-primary/40 hover:bg-white'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="mb-1 h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-sm text-slate-500">点击上传封面图</span>
              </label>
            )}
            {coverImageMarkedForDeletion && existingCoverImageKey && !coverImageFile && (
              <div className="mt-2 flex flex-wrap items-center gap-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                <span>当前封面图已标记为删除，点击保存后才会真正生效。</span>
                <button
                  type="button"
                  onClick={restoreExistingCoverImage}
                  disabled={submitting || coverImageUploading}
                  className="font-medium underline decoration-amber-400 underline-offset-2 disabled:no-underline disabled:opacity-60"
                >
                  恢复当前封面图
                </button>
              </div>
            )}
          </div>

          <div className="rounded-[1.15rem] border border-slate-200 bg-slate-50/85 p-4">
            <h3 className="mb-3 font-semibold text-slate-900">文件信息（提交审核前必填）</h3>
            {versionFiles.length === 0 && <div className="text-sm text-slate-500">暂无文件，请返回上一步上传。</div>}
            <div className="space-y-4">
              {versionFiles.map((f) => {
                const draft = fileMetaDraft[f.id] || { description: '', columns: [], upload_status: f.upload_status, row_count: f.row_count, error_message: f.error_message };
                const preview = previewByFileId[f.id];
                const uploadStatus = draft.upload_status || f.upload_status || 'pending';
                const statusLabel = uploadStatus === 'pending'
                  ? '解析中'
                  : uploadStatus === 'error'
                    ? '解析失败'
                    : '待完善';
                const complete = draft.description.trim() && draft.columns.length > 0 && !draft.columns.some((c) => !String(c.description || '').trim());
                const badgeText = uploadStatus === 'ready' && complete ? '已完成' : statusLabel;
                const badgeClass = uploadStatus === 'pending'
                  ? 'bg-blue-100 text-blue-700'
                  : uploadStatus === 'error'
                    ? 'bg-red-100 text-red-700'
                    : complete
                      ? 'bg-green-100 text-green-700'
                      : 'bg-yellow-100 text-yellow-700';
                const previewRows = Array.isArray(preview?.rows) ? preview.rows.slice(0, 5) : [];
                const previewColumns = Array.isArray(preview?.columns) ? preview.columns : [];
                const recognizedColumns = draft.columns.length > 0
                  ? draft.columns.map((column) => column.column_name)
                  : previewColumns;
                return (
                  <div key={f.id} className="rounded-[1rem] border border-slate-200 bg-white/85 p-3 shadow-[0_16px_36px_-34px_rgba(15,23,42,0.22)]">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="break-all text-sm font-medium text-slate-900">{f.filename}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {typeof draft.row_count === 'number' ? `${draft.row_count.toLocaleString()} 行数据` : '正在统计行数'}
                          {recognizedColumns.length > 0 ? ` · ${recognizedColumns.length} 列` : ''}
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${badgeClass}`}>
                        {badgeText}
                      </span>
                    </div>

                    <div className="mb-3 overflow-hidden rounded-xl border border-slate-200 bg-slate-50/75">
                      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 text-xs text-slate-600">
                        <span>文件预览</span>
                        {preview?.truncated ? <span>仅展示前 5 行</span> : null}
                      </div>
                      {preview?.preview_type === 'table' && previewColumns.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-slate-200 text-xs">
                            <thead className="bg-white/80">
                              <tr>
                                {previewColumns.map((columnName) => (
                                  <th key={`${f.id}-${columnName}`} className="whitespace-nowrap px-3 py-2 text-left font-medium text-slate-600">
                                    {columnName}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 bg-white/90">
                              {previewRows.map((row, rowIndex) => (
                                <tr key={`${f.id}-row-${rowIndex}`}>
                                  {previewColumns.map((columnName) => (
                                    <td key={`${f.id}-${columnName}-${rowIndex}`} className="max-w-[180px] px-3 py-2 align-top text-slate-700">
                                      <div className="truncate">{String(row?.[columnName] ?? '') || '-'}</div>
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : uploadStatus === 'pending' ? (
                        <div className="px-3 py-3 text-xs text-slate-500">正在读取样例数据和列名，页面会自动刷新。</div>
                      ) : preview?.error ? (
                        <div className="px-3 py-3 text-xs text-red-600">{preview.error}</div>
                      ) : (
                        <div className="px-3 py-3 text-xs text-slate-500">
                          {preview?.preview_type === 'text'
                            ? (previewRows.map((row) => String(row?.content ?? '')).join('\n') || '文件内容为空。')
                            : '暂未获取到样例数据。'}
                        </div>
                      )}
                    </div>

                    <label className="mb-1 block text-xs font-medium text-slate-600">文件描述 *（最多500字）</label>
                    <textarea
                      value={draft.description}
                      onChange={(e) => setFileMetaDraft((prev) => ({
                        ...prev,
                        [f.id]: { ...draft, description: e.target.value }
                      }))}
                      maxLength={META_TEXT_LIMIT}
                      onBlur={() => persistAllFileMetadata()}
                      className="mb-3 h-20 w-full rounded-xl border border-slate-200 bg-slate-50/75 p-2 text-sm text-slate-700 placeholder:text-slate-400 transition focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15"
                      placeholder="说明该文件包含的数据内容、来源与用途..."
                    />
                    <div className="mb-3 text-right text-[11px] text-slate-400">{draft.description.length}/{META_TEXT_LIMIT}</div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-xs font-medium text-slate-600">列说明 *（每项最多500字）</div>
                        <button
                          onClick={() => autofillColumnDescriptions(f.id)}
                          className="text-xs text-blue-600 hover:underline"
                          type="button"
                        >
                          同字段自动填充
                        </button>
                      </div>
                      <div className="space-y-2 max-h-56 overflow-auto pr-1">
                        {draft.columns.map((c, idx) => (
                          <div key={`${f.id}-${c.column_name}`} className="grid grid-cols-1 md:grid-cols-3 gap-2">
                            <div className="break-all rounded-xl border border-slate-200 bg-slate-50/80 px-2 py-2 text-xs text-slate-700">{c.column_name}</div>
                            <input
                              value={c.description}
                              onChange={(e) => {
                                const nextCols = [...draft.columns];
                                nextCols[idx] = { ...nextCols[idx], description: e.target.value };
                                setFileMetaDraft((prev) => ({
                                  ...prev,
                                  [f.id]: { ...draft, columns: nextCols }
                                }));
                              }}
                              maxLength={META_TEXT_LIMIT}
                              onBlur={() => persistAllFileMetadata()}
                              className="md:col-span-2 rounded-xl border border-slate-200 bg-slate-50/75 px-2 py-2 text-xs text-slate-700 placeholder:text-slate-400 transition focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15"
                              placeholder="请填写该列含义与单位..."
                            />
                          </div>
                        ))}
                        {draft.columns.length === 0 && previewColumns.length > 0 && (
                          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/75 px-3 py-3 text-xs text-slate-600">
                            <div className="mb-2">已识别到以下列名，正在同步为可编辑列说明：</div>
                            <div className="flex flex-wrap gap-2">
                              {previewColumns.map((columnName) => (
                                <span key={`${f.id}-preview-${columnName}`} className="rounded-md border border-slate-200 bg-white/85 px-2 py-1 text-slate-700">
                                  {columnName}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {draft.columns.length === 0 && previewColumns.length === 0 && uploadStatus === 'pending' && (
                          <div className="text-xs text-slate-400">列信息正在生成，页面会自动刷新。</div>
                        )}
                        {draft.columns.length === 0 && uploadStatus === 'error' && (
                          <div className="text-xs text-red-600">列信息读取失败：{draft.error_message || '请重新上传或稍后重试。'}</div>
                        )}
                        {draft.columns.length === 0 && previewColumns.length === 0 && uploadStatus === 'ready' && !draft.error_message && (
                          <div className="text-xs text-slate-400">暂未读取到列信息，请稍后重试。</div>
                        )}
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          </div>

          {message && <div className="text-blue-600 text-sm font-medium">{message}</div>}

          <div className="mt-4 mb-2 rounded-[1.1rem] border border-slate-200 bg-slate-50/85 p-4">
            <label className="mb-2 block text-sm font-semibold text-slate-800">设置访问权限 *</label>
            {initialAccessLevel === 'password_protected' && accessLevel === 'public' && (
              <div className="mb-3 flex items-start gap-2 rounded-md bg-blue-50 border border-blue-200 px-3 py-2 text-xs text-blue-800">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 110 20A10 10 0 0112 2z" />
                </svg>
                <span>您正在将数据集从<strong>私有</strong>切换为<strong>公开</strong>。保存后将提交管理员审核，审核期间数据集仍保持私有状态。审核通过后所有已发布版本将可被所有用户搜索和下载。</span>
              </div>
            )}
            <div className="space-y-2 text-sm text-slate-700">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="accessLevel"
                  checked={accessLevel === 'public'}
                  onChange={() => setAccessLevel('public')}
                  className="mt-0.5"
                />
                <span><strong>公开分享</strong>：审核通过后可被所有人搜索、展示并下载。</span>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="accessLevel"
                  checked={accessLevel === 'password_protected'}
                  onChange={() => setAccessLevel('password_protected')}
                  className="mt-0.5"
                />
                <span><strong>私有链接</strong>：不会出现在公开网络，需通过您后续生成的免密邀请链接才能访问。</span>
              </label>
            </div>
            
            {/* 保留旧版的状态兼容以防接口未通。这里不强制要输入密码了，改为后台自动分配Token或默认填一个。为了平滑过渡现隐藏原先繁琐的自己想密码的流程，改为自动。但这块稍后需要配后端Token接口 */}
          </div>

          <div className="flex items-center justify-between border-t border-slate-200 pt-4">
            <button onClick={() => confirmLeave('/profile')} disabled={submitting}
                    className="px-4 py-2 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50 font-medium transition-colors">
              放弃并离开
            </button>
            <div className="flex gap-3">
              <button onClick={() => handleSubmitInfo('draft')} disabled={submitting}
                      className="rounded-xl border border-slate-200 bg-white/85 px-6 py-2 font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-800">
                保存草稿
              </button>
              <button onClick={() => handleSubmitInfo('review')} disabled={submitting || workingVersionStatus === 'pending_review' || workingVersionStatus === 'published'}
                      className="px-6 py-2 bg-primary text-primary-foreground rounded shadow hover:bg-primary/90 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                {workingVersionStatus === 'pending_review' ? '审核中（不可提交）' : workingVersionStatus === 'published' ? '已发布' : accessLevel === 'password_protected' ? '保存并发布（密码保护）' : '提交上线审核'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showClearDraftConfirm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-[1.2rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.98))] p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-900">确认清空草稿</h3>
            <p className="mt-2 text-sm text-slate-600">
              清空当前版本（V{workingVersionNum}）的草稿文件？
            </p>
            <p className="text-xs text-red-600 mt-1">此操作不可恢复。</p>
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowClearDraftConfirm(false)}
                className="rounded-xl border border-slate-200 bg-white/85 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={confirmClearDraft}
                className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                确认清空
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 通用确认对话框 */}
      {confirmDialog && (
        <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-[1.2rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.98))] p-6 shadow-2xl">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{confirmDialog.msg}</p>
            <div className="flex justify-end gap-3 mt-5">
              <button
                onClick={confirmDialog.onCancel}
                className="rounded-xl border border-slate-200 bg-white/85 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
              >
                取消
              </button>
              <button
                onClick={confirmDialog.onConfirm}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md shadow hover:bg-primary/90"
              >
                确认
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function UploadPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-slate-500">加载中...</div>}>
      <UploadPageContent />
    </Suspense>
  );
}
