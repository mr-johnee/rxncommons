export const SOURCE_TYPE_OPTIONS = [
  { value: 'lab', label: '实验室实验' },
  { value: 'literature', label: '文献整理' },
  { value: 'patent', label: '专利提取' },
  { value: 'database', label: '公共数据库' },
  { value: 'simulation', label: '计算模拟' },
  { value: 'benchmark', label: '基准评测集' },
  { value: 'industrial', label: '工业流程' },
  { value: 'other', label: '其他' },
] as const;

export const LICENSE_OPTIONS = [
  'CC0 1.0',
  'CC BY 4.0',
  'CC BY-SA 4.0',
  'CC BY-NC 4.0',
  'CC BY-NC-SA 4.0',
  'ODC-BY 1.0',
  'ODbL 1.0',
  'MIT',
  'Apache-2.0',
  'BSD-3-Clause',
  'GPL-3.0-only',
  'LGPL-3.0-only',
  'Proprietary',
  'Other',
] as const;

const SOURCE_TYPE_ALIAS_TO_CODE: Record<string, string> = {
  实验室自测: 'lab',
  实验室实验: 'lab',
  文献提取: 'literature',
  文献整理: 'literature',
  专利提取: 'patent',
  数据库导出: 'database',
  公共数据库: 'database',
  计算模拟: 'simulation',
  基准评测集: 'benchmark',
  工业流程: 'industrial',
  其他: 'other',
};

const SOURCE_TYPE_LABEL_MAP: Record<string, string> = Object.fromEntries(
  SOURCE_TYPE_OPTIONS.map((item) => [item.value, item.label])
);

export function normalizeSourceTypeCode(raw?: string | null): string {
  if (!raw) return '';
  const v = String(raw).trim();
  return SOURCE_TYPE_ALIAS_TO_CODE[v] || v;
}

export function getSourceTypeLabel(raw?: string | null): string {
  const code = normalizeSourceTypeCode(raw);
  if (!code) return '未标注';
  return SOURCE_TYPE_LABEL_MAP[code] || String(raw);
}

const SOURCE_TYPE_COLOR_MAP: Record<string, string> = {
  lab:        'bg-emerald-100 text-emerald-700',
  literature: 'bg-blue-100 text-blue-700',
  patent:     'bg-purple-100 text-purple-700',
  database:   'bg-indigo-100 text-indigo-700',
  simulation: 'bg-cyan-100 text-cyan-700',
  benchmark:  'bg-orange-100 text-orange-700',
  industrial: 'bg-amber-100 text-amber-700',
  other:      'bg-slate-100 text-slate-600',
};

/** 返回该 source_type code 对应的 Tailwind colorClass */
export function getSourceTypeColor(code?: string | null): string {
  return SOURCE_TYPE_COLOR_MAP[code || ''] ?? 'bg-slate-100 text-slate-600';
}

/**
 * 将逗号分隔的 source_type 字符串解析为 { code, label, colorClass }[] 数组，
 * 方便渲染多个独立 badge。
 */
export function parseSourceTypes(raw?: string | null): { code: string; label: string; colorClass: string }[] {
  if (!raw) return [{ code: '', label: '未标注', colorClass: SOURCE_TYPE_COLOR_MAP.other }];
  return String(raw)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => {
      const code = normalizeSourceTypeCode(s) || s;
      return {
        code,
        label: SOURCE_TYPE_LABEL_MAP[code] || s,
        colorClass: SOURCE_TYPE_COLOR_MAP[code] ?? 'bg-slate-100 text-slate-600',
      };
    });
}
