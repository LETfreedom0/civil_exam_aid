我已经更新了 `scripts/import_positions.py` 脚本，将新的 Excel 表头列名添加到了映射配置 `COLUMN_MAPPING` 中。

### 更新内容

根据您提供的 Terminal 输出，我添加了以下映射关系：

*   **`region_dept`** (地区部门) <- `用人部门`
*   **`rank_level`** (职级层次) <- `职位层级`
*   **`description`** (职位描述) <- `职位简介`
*   **`quota`** (招录人数) <- `招考人数`
*   **`education`** (学历) <- `学历要求`
*   **`grassroots_exp`** (基层工作经历) <- `基层工作经历最低年限`
*   **`other_requirements`** (其他要求) <- `其它条件`
*   **`is_set`** (是否组织专业能力测试) <- `是否组织专业能力测试`
*   **`interview_ratio`** (面试比例) <- `面试人数与计划录用人数的比 例` (已处理空格)
*   **`phone1`** (咨询电话) <- `考生咨询电话`

现在，当脚本检测到包含这些新列名的 Excel 文件时，它应该能够正确地提取数据并映射到相应的数据库字段。

### 接下来
您可以直接运行导入脚本来处理包含新表头的 Excel 文件：
```bash
python scripts/import_positions.py
```
*(注意：请确保 `LOCAL_FILE_PATH` 指向正确的文件路径，或者在脚本中正确配置了它)*
