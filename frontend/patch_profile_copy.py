import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update icons import
content = content.replace(
    "import { KeyRound, ExternalLink } from 'lucide-react';",
    "import { KeyRound, ExternalLink, Copy, Check } from 'lucide-react';"
)

# Insert copiedId state and handleCopyShare
state_insert_point = "  const [tab, setTab] = useState<'all' | 'draft' | 'pending_review' | 'published' | 'revision_required'>('all');"
state_insert_code = """  const [tab, setTab] = useState<'all' | 'draft' | 'pending_review' | 'published' | 'revision_required'>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

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
"""

if state_insert_point in content:
    content = content.replace(state_insert_point, state_insert_code)

# Update Link to Button
old_ui = """                        <Link href={`/datasets/${ds.id}?manage=true`} className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 underline underline-offset-2 transition-colors">
                          分享管理 <ExternalLink className="w-3 h-3" />
                        </Link>"""

new_ui = """                        <button 
                          onClick={(e) => handleCopyShare(e, ds)}
                          className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 underline underline-offset-2 transition-colors"
                          title="复制免密专属链接"
                        >
                          {copiedId === ds.id ? <Check className="w-3 h-3 text-green-600" /> : <Copy className="w-3 h-3" />}
                          {copiedId === ds.id ? '已复制！' : '复制专属链接'}
                        </button>"""

if old_ui in content:
    content = content.replace(old_ui, new_ui)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("PATCH APPLIED!")
