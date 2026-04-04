import os
import sys
import subprocess
import glob

def batch_import(directory):
    """
    遍历指定目录下的所有 Excel 文件，并调用 import_positions.py 进行导入
    """
    # 获取当前脚本所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    import_script = os.path.join(current_dir, "import_positions.py")
    
    if not os.path.exists(import_script):
        print(f"错误: 找不到导入脚本 {import_script}")
        return

    # 确保目录存在
    if not os.path.exists(directory):
        print(f"错误: 目录不存在 {directory}")
        return

    print(f"开始扫描目录: {directory}")
    
    # 查找所有 xlsx 和 xls 文件
    excel_files = []
    # 递归查找
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.xlsx', '.xls')) and not file.startswith('~$'):
                excel_files.append(os.path.join(root, file))
    
    if not excel_files:
        print("未找到 Excel 文件")
        return

    print(f"共找到 {len(excel_files)} 个 Excel 文件，准备开始导入...")
    
    success_count = 0
    fail_count = 0

    for i, file_path in enumerate(excel_files):
        print(f"\n[{i+1}/{len(excel_files)}] 正在处理: {file_path}")
        try:
            # 调用 import_positions.py
            result = subprocess.run(
                [sys.executable, import_script, file_path],
                capture_output=False, # 让输出直接显示在控制台
                text=True
            )
            
            if result.returncode == 0:
                print(f"文件 {os.path.basename(file_path)} 处理完成")
                success_count += 1
            else:
                print(f"文件 {os.path.basename(file_path)} 处理失败 (Exit Code: {result.returncode})")
                fail_count += 1
                
        except Exception as e:
            print(f"执行出错: {e}")
            fail_count += 1

    print("\n" + "="*30)
    print(f"批量导入完成！")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print("="*30)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        # 默认扫描 data 目录，如果没有则扫描当前目录的上级目录下的 data 文件夹
        # 假设脚本在 scripts/ 目录下，我们想扫描项目根目录下的 data/ 目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(project_root, "data")
        
        # 如果 data 目录不存在，则询问用户输入
        if not os.path.exists(target_dir):
            print(f"默认数据目录 {target_dir} 不存在。")
            target_dir = input("请输入包含 Excel 文件的文件夹路径: ").strip()
            # 去除引号（如果用户是拖入文件夹的）
            target_dir = target_dir.strip('"').strip("'")

    batch_import(target_dir)
