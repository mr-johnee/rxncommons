'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import api, { getCoverImageUrl } from '@/lib/api';
import CoverImageCard from '@/components/CoverImageCard';
import { useAuth } from '@/context/AuthContext';
import { Search, ArrowRight, Database, FlaskConical, Users, Sparkles, ThumbsUp, ArrowDownToLine, Upload, Eye, type LucideIcon } from 'lucide-react';
import { parseSourceTypes } from '@/lib/dataset-meta';

function truncateText(text: string | null | undefined, maxLength: number) {
  const normalized = String(text || '').trim();
  if (!normalized) return '暂无描述';
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength)}...` : normalized;
}

export default function Home() {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [featured, setFeatured] = useState<any[]>([]);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const lockingRef = useRef(false);

  const getSectionNodes = () =>
    Array.from(
      (scrollRef.current?.querySelectorAll<HTMLElement>('[data-home-section="true"]') || [])
    );

  const getCurrentSectionIndex = (sections: HTMLElement[]) => {
    const container = scrollRef.current;
    if (!container || sections.length === 0) return 0;
    const currentTop = container.scrollTop;
    return sections.reduce((bestIdx, section, idx) => {
      const bestDist = Math.abs(sections[bestIdx].offsetTop - currentTop);
      const nextDist = Math.abs(section.offsetTop - currentTop);
      return nextDist < bestDist ? idx : bestIdx;
    }, 0);
  };

  const scrollToSectionIndex = (targetIndex: number) => {
    const container = scrollRef.current;
    const sections = getSectionNodes();
    if (!container || sections.length === 0) return;
    if (targetIndex < 0 || targetIndex >= sections.length) return;
    lockingRef.current = true;
    container.scrollTo({ top: sections[targetIndex].offsetTop, behavior: 'smooth' });
    window.setTimeout(() => {
      lockingRef.current = false;
    }, 520);
  };

  useEffect(() => {
    api.get('/stats/overview').then(res => setStats(res.data)).catch(() => {});
    api.get('/datasets/featured?limit=2')
      .then(res => setFeatured(res.data.items || []))
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    const onWheel = (event: WheelEvent) => {
      if (Math.abs(event.deltaY) < 20) return;
      if (lockingRef.current) {
        event.preventDefault();
        return;
      }

      const sections = getSectionNodes();
      if (sections.length === 0) return;

      const currentIndex = getCurrentSectionIndex(sections);

      const targetIndex = event.deltaY > 0
        ? Math.min(sections.length - 1, currentIndex + 1)
        : Math.max(0, currentIndex - 1);

      if (targetIndex === currentIndex) return;

      event.preventDefault();
      scrollToSectionIndex(targetIndex);
    };

    container.addEventListener('wheel', onWheel, { passive: false });
    return () => {
      container.removeEventListener('wheel', onWheel);
    };
  }, []);

  const handleSectionClick = (event: React.MouseEvent<HTMLElement>) => {
    if (lockingRef.current) return;
    const target = event.target as HTMLElement | null;
    if (
      target?.closest('a,button,input,textarea,select,label,[role="button"],[data-no-section-jump="true"]')
    ) {
      return;
    }

    const sectionEl = event.currentTarget as HTMLElement;
    const idxRaw = sectionEl.dataset.sectionIndex;
    const currentIndex = Number.isFinite(Number(idxRaw)) ? Number(idxRaw) : -1;
    if (currentIndex < 0) return;

    const sections = getSectionNodes();
    if (currentIndex >= sections.length - 1) return;
    scrollToSectionIndex(currentIndex + 1);
  };

  const statCards: Array<{
    label: string;
    value: string;
    icon: LucideIcon;
    accentBar: string;
    cardSurfaceClassName: string;
    iconWrapClassName: string;
    iconClassName: string;
  }> = stats
    ? [
        {
          label: '活跃数据集',
          value: String(stats.dataset_count ?? 0),
          icon: Database,
          accentBar: 'from-teal-400 via-emerald-400 to-cyan-400',
          cardSurfaceClassName: 'from-white via-white to-teal-50/70',
          iconWrapClassName: 'border-teal-200 bg-teal-50 text-teal-700',
          iconClassName: 'text-teal-700',
        },
        {
          label: '总反应条目',
          value: stats.total_reactions ? stats.total_reactions.toLocaleString() : '0',
          icon: FlaskConical,
          accentBar: 'from-emerald-400 via-lime-300 to-amber-300',
          cardSurfaceClassName: 'from-white via-white to-emerald-50/70',
          iconWrapClassName: 'border-emerald-200 bg-emerald-50 text-emerald-700',
          iconClassName: 'text-emerald-700',
        },
        {
          label: '注册用户',
          value: String(stats.user_count ?? 0),
          icon: Users,
          accentBar: 'from-sky-400 via-cyan-300 to-blue-300',
          cardSurfaceClassName: 'from-white via-white to-sky-50/70',
          iconWrapClassName: 'border-sky-200 bg-sky-50 text-sky-700',
          iconClassName: 'text-sky-700',
        },
      ]
    : [];

  const featuredCollectionCardCopy = {
    eyebrow: '进一步检索',
    title: '公开数据集总览',
    description: '浏览平台当前可访问的数据集，按标题、描述与关键词开展系统检索，快速定位相关化学反应数据。',
    cta: '查看数据总览',
  };

  const featureCards: Array<{
    title: string;
    description: string;
    icon: LucideIcon;
  }> = [
    {
      title: '分散反应数据的系统汇聚',
      description: '论文正文、补充材料与本地实验文件中的反应信息长期分散存放。平台以统一数据集框架进行汇聚，形成可检索、可浏览、可下载的研究资源。',
      icon: Database,
    },
    {
      title: '标准化元数据描述',
      description: '通过列名规范、字段说明与实验条件补充，对原始文件实施结构化描述，降低语义歧义，提升数据质量与跨研究复用能力。',
      icon: FlaskConical,
    },
    {
      title: '受控共享与版本治理',
      description: '支持公开、私有与受控共享模式，并保留版本迭代和审核记录，使数据发布、修订与追溯过程具备明确依据。',
      icon: Users,
    },
  ];

  const renderFeaturedDatasetCard = (ds: any, compact = false) => {
    const briefDescription = truncateText(ds.description, 30);
    const totalRows = Number(ds.total_rows ?? ds.row_count ?? 0);

    return (
      <article
        key={ds.id}
        className={`group flex flex-col rounded-[1.6rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.9))] p-4 shadow-[0_20px_45px_-38px_rgba(15,23,42,0.28)] transition-all hover:-translate-y-1 hover:border-slate-300 hover:shadow-[0_24px_52px_-38px_rgba(15,23,42,0.34)] ${compact ? 'min-h-[236px] min-w-[230px] snap-start' : 'mx-auto min-h-[252px] w-full max-w-[320px]'}`}
      >
        <div className="mb-3 flex items-start justify-between gap-2">
          <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary text-primary">
            <Sparkles className="h-4 w-4" />
          </span>
          <div className="flex flex-wrap justify-end gap-1">
            {parseSourceTypes(ds.source_type).map(({ code, label, colorClass }) => (
              <span key={code} className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${colorClass}`}>{label}</span>
            ))}
          </div>
        </div>

        <div className="relative flex-1">
          <h3 className={`font-semibold leading-6 text-foreground group-hover:text-primary ${compact ? 'text-base' : 'text-lg'}`}>
            <Link href={`/datasets/${ds.id}`}>
              <span className="absolute inset-0" />
              {ds.title}
            </Link>
          </h3>

          {ds.cover_image_key ? (
            <div className="mt-3">
              <CoverImageCard
                src={getCoverImageUrl(ds.id, ds.cover_image_key)}
                alt={`${ds.title} cover image`}
                variant="featured"
              />
            </div>
          ) : null}

          <p className="mt-3 text-sm leading-6 text-muted-foreground">{briefDescription}</p>
        </div>

        <div className="mt-4 grid grid-cols-4 gap-2 text-[11px] sm:text-xs">
          <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
            <FlaskConical className="h-3.5 w-3.5" />
            <span className="truncate">{totalRows.toLocaleString()}</span>
          </span>
          <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
            <ThumbsUp className="h-3.5 w-3.5" />
            <span className="truncate">{Number(ds.upvote_count || 0)}</span>
          </span>
          <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
            <ArrowDownToLine className="h-3.5 w-3.5" />
            <span className="truncate">{Number(ds.download_count || 0)}</span>
          </span>
          <span className="inline-flex min-w-0 items-center justify-center gap-1 rounded-full bg-slate-100/90 px-2 py-1.5 text-slate-700">
            <Eye className="h-3.5 w-3.5" />
            <span className="truncate">{Number(ds.view_count || 0)}</span>
          </span>
        </div>
      </article>
    );
  };



  return (
    <div ref={scrollRef} className="h-[calc(100svh-3.5rem)] overflow-y-auto overscroll-y-contain snap-y snap-mandatory scroll-smooth relative">
      <style dangerouslySetInnerHTML={{ __html: `body { overflow: hidden !important; }` }} />
      <style dangerouslySetInnerHTML={{ __html: `body { overflow: hidden !important; }` }} />
      {/* Part 1: Brand + Search */}
      <section data-home-section="true" data-section-index="0" onClick={handleSectionClick} className="snap-start snap-always min-h-full border-b border-slate-200 bg-gradient-to-br from-emerald-50 via-white to-slate-50 px-6 py-10 lg:px-8">
        <div className="mx-auto flex min-h-full max-w-4xl flex-col items-center justify-start pt-[14vh] md:pt-[17vh] text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
            化学反应数据开放共享平台
          </h1>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            面向化学研究的数据汇聚、规范标引、审核发布与版本追踪平台。
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              const q = (e.target as any).q.value;
              window.location.href = `/datasets?search=${encodeURIComponent(q)}`;
            }}
            className="mx-auto mt-12 flex w-full max-w-2xl flex-col items-center"
          >
            <div className="relative flex w-full flex-col shadow sm:flex-row overflow-hidden rounded-full bg-white/90 backdrop-blur ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-primary/40 focus-within:shadow-md transition-all">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-6">
                <Search className="h-5 w-5 text-slate-400" aria-hidden="true" />
              </div>
              <input
                name="q"
                type="text"
                autoComplete="off"
                className="block w-full border-none bg-transparent py-4 pl-14 pr-4 sm:pr-32 text-slate-800 placeholder:text-slate-400 focus:ring-0 text-base outline-none"
                placeholder="搜索化学反应数据集标题、描述或关键词..."
              />
              <button
                type="submit"
                className="hidden sm:inline-flex absolute right-1.5 top-1.5 bottom-1.5 rounded-full bg-primary px-8 items-center text-sm font-medium text-primary-foreground hover:bg-primary/95 transition-all shadow-sm active:scale-95"
              >
                搜索
              </button>
            </div>
            {/* Mobile Submit */}
            <button
                type="submit"
                className="sm:hidden mt-4 w-full rounded-full bg-primary py-3.5 text-base font-medium text-primary-foreground hover:bg-primary/95 transition-all shadow-sm active:scale-95"
            >
              搜索
            </button>
          </form>

          <div className="mt-8 flex w-full flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/datasets"
              className="group flex w-full items-center justify-center gap-2 rounded-full bg-slate-100 px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-200 hover:shadow hover:-translate-y-0.5 sm:w-auto"
            >
              <Database className="h-4 w-4 text-slate-500 group-hover:text-slate-700 transition-colors" />
              浏览数据集
            </Link>
            {user?.role === 'admin' ? (
              <Link href="/admin" className="flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                进入管理后台
              </Link>
            ) : (
              <Link href="/upload" className="flex w-full items-center justify-center gap-2 rounded-full border border-teal-200 bg-teal-50/50 px-8 py-3 text-sm font-medium text-teal-700 shadow-sm transition-all hover:bg-teal-100 hover:text-teal-800 hover:border-teal-300 sm:w-auto hover:-translate-y-0.5">
                <Upload className="h-4 w-4" /> 上传数据集
              </Link>
            )}
          </div>

          <button 
            type="button"
            title="查看下一模块"
            onClick={(e) => {
              e.preventDefault();
              document.querySelector('[data-section-index="1"]')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="group mt-16 inline-flex h-9 w-6 items-start justify-center rounded-[999px] border border-slate-300/80 bg-white/60 pt-1.5 shadow-sm backdrop-blur-md transition-all duration-300 hover:-translate-y-0.5 hover:border-slate-400/90 hover:bg-white/80 hover:shadow-md active:scale-95"
          >
            <span className="relative flex h-4 w-2 items-start justify-center overflow-hidden rounded-full border border-slate-200/70 bg-white/70">
              <span className="mt-0.5 h-1.5 w-[3px] rounded-full bg-primary/80 animate-bounce" style={{ animationDuration: '1.8s' }} />
            </span>
          </button>
        </div>
      </section>

      {/* Part 2: Dataset Metrics + Featured */}
      <section data-home-section="true" data-section-index="1" onClick={handleSectionClick} className="snap-start snap-always min-h-full border-b border-slate-200 bg-white px-6 py-10 lg:px-8">
        <div className="mx-auto flex min-h-full max-w-7xl flex-col justify-center">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">平台概览与代表性数据</h2>
            <p className="mt-2 text-lg leading-8 text-muted-foreground">
              汇总当前公开数据规模与代表性数据集，帮助研究者快速判断平台覆盖范围与资源特征。
            </p>
          </div>

          {statCards.length > 0 && (
            <div className="mx-auto mt-10 w-full max-w-4xl" data-no-section-jump="true">
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {statCards.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.label}
                      className={`group relative mx-auto w-full max-w-[220px] overflow-hidden rounded-[1.5rem] border border-slate-200 bg-gradient-to-br ${item.cardSurfaceClassName} px-5 py-4 text-center shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg`}
                    >
                      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${item.accentBar}`} />
                      <div className="relative flex justify-center">
                        <dt className="inline-flex items-center justify-center gap-2.5 text-sm font-medium tracking-wide text-slate-500">
                          <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${item.iconWrapClassName}`}>
                            <Icon className={`h-4 w-4 ${item.iconClassName}`} />
                          </span>
                          {item.label}
                        </dt>
                      </div>
                      <dd className="relative mt-4 text-4xl font-semibold tracking-tight text-slate-900 sm:text-[2.8rem]">
                        {item.value}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </div>
          )}

          {featured.length > 0 && (
            <>
              <div className="md:hidden mt-8 -mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-1">
                {featured.map((ds: any) => renderFeaturedDatasetCard(ds, true))}
                <Link
                  href="/datasets"
                  className="relative overflow-hidden group min-w-[220px] snap-start flex min-h-[220px] flex-col justify-between rounded-2xl bg-primary/5 border border-primary/20 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md hover:bg-primary/10"
                >
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        <p className="text-xs font-medium tracking-widest text-primary">{featuredCollectionCardCopy.eyebrow}</p>
                    </div>
                    <h3 className="mt-2 text-2xl font-bold tracking-tight text-foreground">{featuredCollectionCardCopy.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {featuredCollectionCardCopy.description}
                    </p>
                  </div>
                  <div className="relative z-10 mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition-colors group-hover:bg-primary/20">
                    {featuredCollectionCardCopy.cta}
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Link>
              </div>

              <div className="mt-10 hidden grid-cols-3 gap-5 md:mx-auto md:grid md:max-w-5xl">
                {featured.map((ds: any) => renderFeaturedDatasetCard(ds))}
                <Link
                  href="/datasets"
                  className="relative overflow-hidden group mx-auto flex min-h-[220px] w-full max-w-[320px] flex-col justify-between rounded-2xl bg-primary/5 border border-primary/20 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md hover:bg-primary/10"
                >
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        <p className="text-xs font-medium tracking-widest text-primary">{featuredCollectionCardCopy.eyebrow}</p>
                    </div>
                    <h3 className="mt-2 text-2xl font-bold tracking-tight text-foreground">{featuredCollectionCardCopy.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {featuredCollectionCardCopy.description}
                    </p>
                  </div>
                  <div className="relative z-10 mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition-colors group-hover:bg-primary/20">
                    {featuredCollectionCardCopy.cta}
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Link>
              </div>
            </>
          )}
        </div>
      </section>

      {/* Part 3: Advantages */}
      <section data-home-section="true" data-section-index="2" onClick={handleSectionClick} className="snap-start snap-always min-h-full bg-slate-50 flex flex-col">
        <div className="mx-auto flex flex-1 w-full max-w-7xl flex-col justify-start pt-[8vh] md:pt-[10vh] px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">面向化学研究的数据基础设施</p>
            <p className="mt-5 text-lg leading-8 text-muted-foreground">
              围绕数据汇聚、语义规范、审核发布与受控共享，构建支持长期积累、持续修订与学术复用的化学反应数据体系。
            </p>
          </div>

          <div className="md:hidden mt-8 -mx-1 flex snap-x snap-mandatory gap-4 overflow-x-auto px-1 pb-4">
            {featureCards.map((item) => {
              const Icon = item.icon;
              return (
                <article key={item.title} className="min-w-[260px] snap-start rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/5 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mb-3 text-lg font-bold tracking-tight text-foreground">{item.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground/90">
                    {item.description}
                  </p>
                </article>
              );
            })}
          </div>

          <div className="mt-16 hidden grid-cols-3 gap-8 md:mx-auto md:grid md:max-w-5xl">
            {featureCards.map((item) => {
              const Icon = item.icon;
              return (
                <article key={item.title} className="group mx-auto w-full max-w-[320px] rounded-3xl border border-slate-100 bg-white p-8 shadow-sm transition-all hover:-translate-y-2 hover:shadow-xl hover:border-primary/20">
                  <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/5 text-primary transition-colors group-hover:bg-primary group-hover:text-white">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mb-4 text-xl font-bold tracking-tight text-foreground">{item.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground/90">
                    {item.description}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
        
        {/* 简化的版权底部 */}
        <div className="mt-auto w-full pb-6 pt-12 text-center text-xs leading-5 text-slate-400">
          &copy; {new Date().getFullYear()} RxnCommons Chemistry Data Hub. All rights reserved.
        </div>
      </section>
    </div>
  );
}
