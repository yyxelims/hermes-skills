#!/usr/bin/env bash
# 给交付文件留带时间戳的快照（明文版/自用版默认没有 git 历史，别等用户问"回退到几点那版"）
#
# 用法:
#   snapshot_deliverable.sh <文件> [标签]
#   snapshot_deliverable.sh ~/Downloads/SendFenhang-明文版/SendFenhang.py 1547
#
# 产物: <文件所在目录>/snapshots/<名>-<标签|HHMM>.<扩展名>
# 建议标签用"当时的时间点"或"驱动版本/页面版本"，让"哪一版"可指认。
set -euo pipefail

f="${1:-}"
label="${2:-}"
if [ -z "$f" ] || [ ! -f "$f" ]; then
    echo "用法: $(basename "$0") <文件> [标签]" >&2
    echo "错误: 文件不存在: ${f:-<空>}" >&2
    exit 1
fi

dir="$(cd "$(dirname "$f")" && pwd)"
base="$(basename "$f")"
stem="${base%.*}"
ext="${base##*.}"
[ "$stem" = "$base" ] && ext=""
stamp="${label:-$(date +%H%M)}"

if [ -n "$ext" ]; then
    name="${stem}-${stamp}.${ext}"
else
    name="${stem}-${stamp}"
fi

mkdir -p "$dir/snapshots"
cp -f "$f" "$dir/snapshots/$name"

# 同时记一行"这版是什么"，方便以后对照
{
    printf '%s  %s  md5=%s\n' \
        "$(date '+%Y-%m-%d %H:%M')" "$name" "$(md5 -q "$dir/snapshots/$name" 2>/dev/null || md5sum "$dir/snapshots/$name" | cut -d' ' -f1)"
} >>"$dir/snapshots/INDEX.txt"

echo "已留档: $dir/snapshots/$name"
ls -lh "$dir/snapshots/$name"
