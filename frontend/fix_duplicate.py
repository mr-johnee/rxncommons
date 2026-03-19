file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

duplicate_block = """  const [copiedId, setCopiedId] = useState<string | null>(null);

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

# Replace the first occurrence with empty string to remove duplication
# Only replace once or count first
first_idx = content.find(duplicate_block)
if first_idx != -1:
    last_idx = content.find(duplicate_block, first_idx + 1)
    if last_idx != -1:
        # It's duplicated, remove the second one.
        content = content[:last_idx] + content[last_idx + len(duplicate_block):]
    else:
        print("Only found one occurrence! Something else is wrong.")
else:
    print("Not found!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
