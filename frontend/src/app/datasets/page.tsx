'use client';
import { useEffect, useState } from 'react';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import api, { getCoverImageUrl } from '@/lib/api';
import CoverImageCard from '@/components/CoverImageCard';
import { useAuth } from '@/context/AuthContext';
import { Filter, Database, FlaskConical, Download, Eye, ThumbsUp } from 'lucide-react';
import { SOURCE_TYPE_OPTIONS, normalizeSourceTypeCode } from '@/lib/dataset-meta';

function truncateText(text: string | null | undefined, maxLength: number) {
  const normalized = String(text || '').trim();
  if (!normalized) return '暂无描述';
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength)}...` : normalized;
}

function DatasetsPageContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [datasets, setDatasets] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [appliedSearch, setAppliedSearch] = useState(searchParams.get('search') || '');
  const [sourceTypeFilter, setSourceTypeFilter] = useState(normalizeSourceTypeCode(searchParams.get('source_type') || ''));
  const [rangeMin, setRangeMin] = useState(0);
  const [rangeMax, setRangeMax] = useState(0);
  const [minRows, setMinRows] = useState(0);
  const [maxRows, setMaxRows] = useState(0);
  const [appliedMinRows, setAppliedMinRows] = useState(0);
  const [appliedMaxRows, setAppliedMaxRows] = useState(0);
  const [rangeReady, setRangeReady] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const fetchRowsRange = async (q: string, sourceType: string) => {
    const params = new URLSearchParams();
    if (q) params.set('search', q);
    if (sourceType) params.set('source_type', sourceType);
    const res = await api.get(`/datasets/rows-range?${params.toString()}`);
    const nextMin = Number(res.data?.min_rows || 0);
    const nextMaxRaw = Number(res.data?.max_rows || 0);
    const nextMax = Math.max(nextMaxRaw, nextMin);

    setRangeMin(nextMin);
    setRangeMax(nextMax);
    setMinRows(nextMin);
    setMaxRows(nextMax);
    setAppliedMinRows(nextMin);
    setAppliedMaxRows(nextMax);
    setPage(1);
    setRangeReady(true);
  };

  const fetchDatasets = async (
    q: string,
    p: number,
    sourceType: string,
    minRowNum: number,
    maxRowNum: number,
    lowerBound: number,
    upperBound: number,
  ) => {
    try {
      setLoading(true);
      const skip = (p - 1) * pageSize;
      const params = new URLSearchParams();
      if (q) params.set('search', q);
      if (sourceType) params.set('source_type', sourceType);
      if (minRowNum > lowerBound) params.set('min_rows', String(minRowNum));
      if (maxRowNum < upperBound) params.set('max_rows', String(maxRowNum));
      params.set('limit', String(pageSize));
      params.set('skip', String(skip));
      const res = await api.get(`/datasets?${params.toString()}`);
      setDatasets(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRowsRange(appliedSearch, sourceTypeFilter).catch(console.error);
  }, [appliedSearch, sourceTypeFilter]);

  useEffect(() => {
    if (!rangeReady) return;
    fetchDatasets(appliedSearch, page, sourceTypeFilter, appliedMinRows, appliedMaxRows, rangeMin, rangeMax);
  }, [rangeReady, appliedSearch, page, sourceTypeFilter, appliedMinRows, appliedMaxRows, rangeMin, rangeMax]);

  useEffect(() => {
    const q = searchParams.get('search') || '';
    const st = normalizeSourceTypeCode(searchParams.get('source_type') || '');
    if (q !== search) {
      setSearch(q);
      setAppliedSearch(q);
    }
    if (st !== sourceTypeFilter) {
      setSourceTypeFilter(st);
    }
  }, [searchParams]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setAppliedSearch(search);
  };

  const span = Math.max(rangeMax - rangeMin, 1);
  const sliderStep = Math.max(1, Math.floor(span / 300));
  const minPct = ((minRows - rangeMin) / span) * 100;
  const maxPct = ((maxRows - rangeMin) / span) * 100;

  const applyRangeFilter = () => {
    setPage(1);
    setAppliedMinRows(minRows);
    setAppliedMaxRows(maxRows);
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold text-foreground">数据集广场</h1>
        {user?.role !== 'admin' && (
          <Link 
            href="/upload" 
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            上传数据集
          </Link>
        )}
      </div>

      {/* Search + Filters */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input 
          type="text" 
          placeholder="搜索数据集标题..."
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          value={search} 
          onChange={(e) => setSearch(e.target.value)} 
        />
        <button 
          type="submit" 
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
          搜索
        </button>
      </form>
      <div className="mb-6 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span>共找到 {total} 个数据集</span>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-20 text-muted-foreground">加载中...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <aside className="lg:col-span-1 bg-card border border-border rounded-lg p-5 h-fit shadow-sm">
              <h3 className="font-semibold text-foreground mb-4 inline-flex items-center gap-2">
                <Filter className="h-4 w-4 text-primary" />
                筛选条件
              </h3>

              <div className="mb-4">
                <label className="block text-xs font-semibold tracking-wider text-muted-foreground mb-2 inline-flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" />
                  数据来源类型
                </label>
                <select 
                  value={sourceTypeFilter} 
                  onChange={(e) => { setPage(1); setSourceTypeFilter(e.target.value); }} 
                  className="w-full rounded-md border border-input bg-muted/20 px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="">全部来源</option>
                  {SOURCE_TYPE_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>

              <div className="mb-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#666666] mb-1">数据条目数</label>
                <div className="space-y-2">
                  <div className="text-xs text-[#666666]">
                    当前范围：{minRows.toLocaleString()} - {maxRows.toLocaleString()}
                  </div>
                  <div className="relative h-8">
                    <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1.5 bg-gray-200 rounded" />
                    <div
                      className="absolute top-1/2 -translate-y-1/2 h-1.5 bg-primary rounded"
                      style={{ left: `${minPct}%`, right: `${100 - maxPct}%` }}
                    />
                    <input
                      type="range"
                      min={rangeMin}
                      max={rangeMax}
                      step={sliderStep}
                      value={minRows}
                      onInput={(e) => {
                        const next = Number((e.target as HTMLInputElement).value);
                        setMinRows(Math.min(next, maxRows));
                      }}
                      onMouseUp={applyRangeFilter}
                      onTouchEnd={applyRangeFilter}
                      className="range-slider absolute inset-0 w-full z-20"
                    />
                    <input
                      type="range"
                      min={rangeMin}
                      max={rangeMax}
                      step={sliderStep}
                      value={maxRows}
                      onInput={(e) => {
                        const next = Number((e.target as HTMLInputElement).value);
                        setMaxRows(Math.max(next, minRows));
                      }}
                      onMouseUp={applyRangeFilter}
                      onTouchEnd={applyRangeFilter}
                      className="range-slider absolute inset-0 w-full z-30"
                    />
                  </div>
                </div>
              </div>
            </aside>

            <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
            {datasets.map((ds: any) => (
              (() => {
                const briefDescription = truncateText(ds.description, 36);
                const hasCoverImage = Boolean(ds.cover_image_key);
                const totalRows = Number(ds.total_rows ?? ds.row_count ?? 0);
                const content = (
                  <div className={`flex h-full flex-col justify-between ${hasCoverImage ? 'py-0.5 sm:py-1' : 'p-5 sm:p-6'}`}>
                    <div>
                      <h2 className="mb-2 line-clamp-2 text-lg font-semibold text-slate-900 transition-colors hover:text-primary">
                        {ds.title}
                      </h2>
                      <p className="min-h-[1.5rem] text-sm leading-6 text-slate-600">
                        {briefDescription}
                      </p>
                    </div>
                    <div className="mt-4">
                      <div className="grid grid-cols-4 gap-2 text-[11px] sm:text-xs">
                        <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
                          <FlaskConical className="h-3.5 w-3.5" />
                          <span className="truncate">{totalRows.toLocaleString()}</span>
                        </span>
                        <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
                          <ThumbsUp className="h-3.5 w-3.5" />
                          <span className="truncate">{Number(ds.upvote_count || 0)}</span>
                        </span>
                        <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
                          <Download className="h-3.5 w-3.5" />
                          <span className="truncate">{Number(ds.download_count || 0)}</span>
                        </span>
                        <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
                          <Eye className="h-3.5 w-3.5" />
                          <span className="truncate">{Number(ds.view_count || 0)}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                );

                return (
              <Link key={ds.id} href={`/datasets/${ds.id}`}
                    className="overflow-hidden rounded-[1.35rem] border border-slate-200/90 bg-white/95 shadow-[0_18px_40px_-38px_rgba(15,23,42,0.26)] transition-all hover:border-slate-300 hover:shadow-[0_24px_52px_-38px_rgba(15,23,42,0.32)]">
                {hasCoverImage ? (
                  <div className="flex h-full flex-col gap-2.5 p-4 sm:flex-row sm:items-center sm:gap-3 sm:p-[1.125rem]">
                    <div className="sm:w-[118px] sm:shrink-0">
                      <CoverImageCard
                        src={getCoverImageUrl(ds.id, ds.cover_image_key)}
                        alt={`${ds.title} cover image`}
                        variant="list"
                      />
                    </div>
                    {content}
                  </div>
                ) : content}
              </Link>
                );
              })()
            ))}
            {datasets.length === 0 && (
              <div className="col-span-full text-center py-10 text-[#666666]">没有找到匹配的数据集。</div>
            )}
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-8">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                      className="px-4 py-2 border border-gray-300 rounded-md bg-white disabled:opacity-40">← 上一页</button>
                    <span className="text-sm text-[#666666]">第 {page} / {totalPages} 页</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                      className="px-4 py-2 border border-gray-300 rounded-md bg-white disabled:opacity-40">下一页 →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function DatasetsPage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto py-8 px-4 text-[#666666]">加载中...</div>}>
      <DatasetsPageContent />
    </Suspense>
  );
}
