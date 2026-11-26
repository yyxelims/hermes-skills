# CSS 选择器提取指南

## 从浏览器获取选择器

1. F12 打开开发者工具
2. 点击左上角「选择元素」按钮（或 Ctrl+Shift+C）
3. 鼠标移到目标元素上，点击
4. 在 Elements 面板中右键高亮的 HTML 行 → Copy → Copy selector

## 手写选择器（比自动生成的更可靠）

| 写法 | 含义 | 例子 |
|------|------|------|
| `标签.class名` | 按 class 匹配 | `img.acti` |
| `标签#id名` | 按 id 匹配 | `div#send-btn` |
| `标签[属性="值"]` | 按属性匹配 | `img[src="icon.png"]` |
| `标签[属性*="部分值"]` | 属性值包含某字符串 | `img[src*="training"]` |
| `选择器1, 选择器2` | 逗号=或，任一命中即可 | `img.acti, img.new-one` |

## class 名里有空格

HTML `class="acti ng-star-inserted"` 是两个 class。选择器写法：`img.acti.ng-star-inserted`（空格换成点）。

## 控制台验证

```javascript
document.querySelector('img.acti.ng-star-inserted')
// 返回元素 → 正确
// 返回 null → 选择器不对

document.querySelectorAll('img.acti').length
// 检查是否唯一匹配
```
