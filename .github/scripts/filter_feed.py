"""把小宝科技站的 RSS 过滤成只含技术文章的版本，给 blog-post-workflow 用。

用法：python3 filter_feed.py <源 RSS 地址> <输出文件>
分类在 EXCLUDE_CATEGORIES 里的文章会被去掉，其余原样保留。
"""
import re
import sys
import urllib.request

# 非技术分类，不在主页展示
EXCLUDE_CATEGORIES = {"生活感悟", "其他"}


def main():
    src, out = sys.argv[1], sys.argv[2]
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (blog-post-workflow feed filter)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read().decode("utf-8")

    kept = removed = 0

    def keep_or_drop(match):
        nonlocal kept, removed
        cats = {c.strip() for c in re.findall(r"<category>(.*?)</category>", match.group(0), re.S)}
        if cats & EXCLUDE_CATEGORIES:
            removed += 1
            return ""
        kept += 1
        return match.group(0)

    filtered = re.sub(r"[ \t]*<item>.*?</item>\s*", keep_or_drop, xml, flags=re.S)
    if kept == 0:
        sys.exit("过滤后一篇文章都没有，可能是 RSS 格式变了，先不更新 README")
    with open(out, "w", encoding="utf-8") as f:
        f.write(filtered)
    print(f"保留 {kept} 篇，去掉 {removed} 篇非技术文章")


if __name__ == "__main__":
    main()
