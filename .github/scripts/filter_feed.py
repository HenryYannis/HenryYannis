"""把小宝科技站的 RSS 过滤成只含技术文章的版本，给 blog-post-workflow 用。

用法：python3 filter_feed.py <源 RSS 地址> <输出文件>
分类在 EXCLUDE_CATEGORIES 里的文章会被去掉，其余原样保留。
另外做两道防护，避免 RSS 被篡改时往 README 注入 Markdown：
- 只保留链接以 ALLOWED_LINK_PREFIX 开头的文章；
- 去掉标题里会破坏 Markdown 链接的字符（[ ] ( ) 和换行）。
"""
import re
import sys
import urllib.request

# 非技术分类，不在主页展示
EXCLUDE_CATEGORIES = {"生活感悟", "其他"}

# 只接受本站文章链接
ALLOWED_LINK_PREFIX = "https://xbkjz.cn/"

# 标题里会破坏 "- [$title]($url)" 的字符
UNSAFE_TITLE_CHARS = re.compile(r"[\[\]()\r\n]")


def safe_link(item):
    m = re.search(r"<link>(.*?)</link>", item, re.S)
    if not m:
        return False
    link = m.group(1).strip()
    # 链接里不能有空白或括号，防止跳出 Markdown 链接
    return link.startswith(ALLOWED_LINK_PREFIX) and not re.search(r"[\s()\[\]<>]", link)


def clean_title(item):
    def fix(m):
        title = UNSAFE_TITLE_CHARS.sub("", m.group(2)).strip()
        return m.group(1) + title + m.group(3)

    if not UNSAFE_TITLE_CHARS.search(re.search(r"<title>(.*?)</title>", item, re.S).group(1)):
        return item  # 标题本来就干净，原样保留
    return re.sub(r"(<title>)(.*?)(</title>)", fix, item, count=1, flags=re.S)


def main():
    src, out = sys.argv[1], sys.argv[2]
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (blog-post-workflow feed filter)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read().decode("utf-8")

    kept = removed = unsafe = 0

    def keep_or_drop(match):
        nonlocal kept, removed, unsafe
        item = match.group(0)
        cats = {c.strip() for c in re.findall(r"<category>(.*?)</category>", item, re.S)}
        if cats & EXCLUDE_CATEGORIES:
            removed += 1
            return ""
        if not re.search(r"<title>.*?</title>", item, re.S) or not safe_link(item):
            unsafe += 1
            return ""
        kept += 1
        return clean_title(item)

    filtered = re.sub(r"[ \t]*<item>.*?</item>\s*", keep_or_drop, xml, flags=re.S)
    if kept == 0:
        sys.exit("过滤后一篇文章都没有，可能是 RSS 格式变了，先不更新 README")
    with open(out, "w", encoding="utf-8") as f:
        f.write(filtered)
    msg = f"保留 {kept} 篇，去掉 {removed} 篇非技术文章"
    if unsafe:
        msg += f"，另去掉 {unsafe} 篇链接不是本站的文章"
    print(msg)


if __name__ == "__main__":
    main()
