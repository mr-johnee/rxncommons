import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx', 'r') as f:
    content = f.read()

# in getPrimaryLink: change "ds.dataset_status === 'draft' || ds.dataset_status === 'revision_required'" to checking length of published version
# Actually, wait. It's better to always send user to /datasets/${ds.id}?manage=true if there's any published version. But `ds` in /profile is just the dataset basic info. It doesn't have version count easily. 
# But wait, we can just send everyone to `/datasets/${ds.id}?manage=true` and let them hit "+新版本" or continue draft from there!
content = re.sub(
    r"  const getPrimaryLink = \(ds: any\) => \{\n    if \(ds\.dataset_status === 'draft' \|\| ds\.dataset_status === 'revision_required'\) \{\n      return `/upload\?datasetId=\$\{ds\.id\}`;\n    \}\n    return `/datasets/\$\{ds\.id\}\?manage=true`;\n  \};",
    r"  const getPrimaryLink = (ds: any) => {\n    if (ds.dataset_status === 'draft' || ds.dataset_status === 'revision_required') {\n      // If it has ever been published, send them to dataset details page to see diff or manage version.\n      if (ds.current_version && Number(ds.current_version) > 0) return `/datasets/${ds.id}?manage=true`;\n      return `/upload?datasetId=${ds.id}`;\n    }\n    return `/datasets/${ds.id}?manage=true`;\n  };",
    content
)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx', 'w') as f:
    f.write(content)
