我已经修复了 CSS 语法错误。

### 错误原因
在之前的重构中，我可能不小心将 `margin-bottom: 20rpx;` 粘贴到了 `justify-content` 属性的同一行，导致 CSS 解析器报错。

### 修复内容
`pages/detail/detail.vue`:
```css
/* 修复前 */
justify-content: space-between; 20rpx;

/* 修复后 */
justify-content: space-between;
margin-bottom: 20rpx;
```

现在样式文件应该可以正常编译了，您可以查看优化后的 UI 效果。
