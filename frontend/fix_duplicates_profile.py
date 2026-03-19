import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix duplicates in imports
content = content.replace("Globe2, Lock, Globe2", "Lock, Globe2")
content = content.replace("Globe2, Lock", "Lock, Globe2")
content = re.sub(r'Lock, Globe2.*?, Lock, Globe2', 'Lock, Globe2', content)

# Remove the duplicated privacyFilter state block
duplicates = re.findall(r"(  const \[privacyFilter, setPrivacyFilter\] = useState<'all' \| 'public' \| 'password_protected'>\('all'\);.*?  };)", content, flags=re.DOTALL)
if len(duplicates) > 1:
    content = content.replace(duplicates[0], "", 1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("DUPLICATES CLEANED!")
