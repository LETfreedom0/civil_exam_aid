我已经根据您提供的表头完成了数据库结构和导入脚本的更新。

### 1. 数据库变更 (`common/schema.sql`)

我添加了两个新字段，并更新了部分字段的注释以匹配新表头：

* 新增 `fresh_grad_year` (对应 '面向2026年应届毕业生招考')

* 新增 `inspection_ratio` (对应 '考察比例')

* 更新 `grassroots_exp` (对应 '2年及以上基层工作经历要求')

* 更新 `physical_test` (对应 '体能测评比例')

**重要提示**：
由于数据库 Schema 发生了变化（增加了列），您需要在 Supabase SQL Editor 中运行以下命令来更新现有的 `positions` 表：

```sql
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS fresh_grad_year text;
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS inspection_ratio text;
```

*(或者，如果您现在的表里没有重要数据，可以直接删除表重建，重新运行整个* *`schema.sql`)*

### 2. 脚本变更 (`scripts/import_positions.py`)

我已经完全重写了 `COLUMN_MAPPING` 配置，现在它与您的 Excel 表头一一对应：

* 精确匹配了所有 26 个字段（除了您输入中看起来像空列的那一项）。

* 现在脚本运行时将使用新的映射规则进行数据提取。

### 接下来

1. 请先在数据库执行上述 `ALTER TABLE` 语句。
2. 再次运行导入脚本：

   ```bash
   python scripts/import_positions.py
   ```

   观察日志中的表头映射检查部分，应该能看到所有字段都显示 `[√]`。

