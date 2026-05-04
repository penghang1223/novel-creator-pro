#!/bin/bash
OUTPUT="/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/article_urls.txt"
TMP="/tmp/xbookcn_page.html"
> "$OUTPUT"

fetch_page() {
    local URL="$1"
    curl -s -L "$URL" > "$TMP"
    grep -o "href='https://blog\.xbookcn\.net/[^']*blog-post[^']*'" "$TMP" | sed "s/href='//;s/'$//" >> "$OUTPUT"
    grep "blog-pager-older-link" "$TMP" | grep -o "href='[^']*'" | sed "s/href='//;s/'$//" | head -1
}

echo "Fetching page 1..."
NEXT=$(fetch_page "https://blog.xbookcn.net/search/label/%E7%B2%BE%E9%80%89%E4%BD%9C%E5%93%81")
echo "  Next: $NEXT"

PAGE=2
while [ -n "$NEXT" ] && [ $PAGE -le 15 ]; do
    echo "Fetching page $PAGE..."
    sleep 2
    NEXT=$(fetch_page "$NEXT")
    echo "  Next: $NEXT"
    PAGE=$((PAGE + 1))
done

sort -u "$OUTPUT" -o "$OUTPUT"
TOTAL=$(wc -l < "$OUTPUT" | tr -d ' ')
echo "Total unique article URLs: $TOTAL"
