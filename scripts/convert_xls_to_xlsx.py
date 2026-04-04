import os
import win32com.client as win32
import sys

def convert_xls_to_xlsx(directory):
    """
    将指定目录下的所有 .xls 文件转换为 .xlsx 文件
    """
    if not os.path.exists(directory):
        print(f"错误: 目录不存在 - {directory}")
        return

    # 获取所有 xls 文件
    xls_files = [f for f in os.listdir(directory) if f.lower().endswith('.xls')]
    
    if not xls_files:
        print(f"在目录中未找到 .xls 文件: {directory}")
        return

    print(f"找到 {len(xls_files)} 个 .xls 文件，准备开始转换...")

    try:
        # 启动 Excel 应用程序
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
    except Exception as e:
        print(f"无法启动 Excel 应用程序: {e}")
        print("请确保已安装 Microsoft Excel。")
        return

    success_count = 0
    
    try:
        for filename in xls_files:
            file_path = os.path.join(directory, filename)
            new_file_path = os.path.join(directory, filename + 'x') # .xls -> .xlsx

            # 如果目标文件已存在，跳过或覆盖（这里选择跳过）
            if os.path.exists(new_file_path):
                print(f"[跳过] 文件已存在: {filename}x")
                continue

            try:
                print(f"正在转换: {filename} ...")
                wb = excel.Workbooks.Open(file_path)
                
                # FileFormat=51 corresponds to xlOpenXMLWorkbook (.xlsx)
                wb.SaveAs(new_file_path, FileFormat=51)
                wb.Close()
                success_count += 1
                print(f"[成功] -> {filename}x")
            except Exception as e:
                print(f"[失败] 转换 {filename} 时出错: {e}")
    finally:
        # 确保退出 Excel
        excel.Quit()
        print("-" * 30)
        print(f"处理完成。成功转换: {success_count}/{len(xls_files)}")

if __name__ == "__main__":
    # 默认路径
    target_dir = r"C:\Users\Administrator\Downloads\浙江2026省考\附件1：2026年浙江省各级机关单位公务员招考职位一览表（不含特警等）"
    
    # 如果提供了命令行参数，则使用参数
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]

    print(f"目标目录: {target_dir}")
    convert_xls_to_xlsx(target_dir)
