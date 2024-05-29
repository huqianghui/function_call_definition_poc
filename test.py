import subprocess

def delete_directories_with_pattern(pattern):
    try:
        # 执行 ls | grep 命令，获取匹配指定模式的目录列表
        result = subprocess.run(f"ls | grep {pattern}", shell=True, capture_output=True, text=True, check=True)
        matched_directories = result.stdout.split('\n')

        # 删除匹配到的目录
        for directory in matched_directories:
            if directory:
                subprocess.run(["rm", "-rf", directory], check=True)
        
        print(f"Deleted directories matching pattern '{pattern}' successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete directories with pattern '{pattern}': {e}")

# 调用函数，传入要匹配的模式
delete_directories_with_pattern("aigbb_functions_kernel")

