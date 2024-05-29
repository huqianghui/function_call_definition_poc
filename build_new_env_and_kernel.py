import subprocess
import json
from typing import List, Dict
import fcntl,time
import os
import logging


# 从环境变量中读取日志级别，默认为 INFO
log_level = os.getenv('LOG_LEVEL', 'DEBUG')

# 将日志级别字符串转换为对应的日志级别常量
numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

# 配置日志记录器
logging.basicConfig(level=numeric_level)


kernel_prefix="aigbb_functions_kernel"

current_kernel_name = "aigbb_functions_kernel_1"

def get_current_kernel_name():
    global current_kernel_name
    return current_kernel_name

# get the list of jupyter kernels
def find_kernel(kernel_name) -> List[Dict[str, str]]:
    logging.debug("find_kernel...")
    logging.debug("kernel_name: %s", kernel_name)

    # 使用 subprocess.Popen 执行 `jupyter kernelspec list` 并将输出传递给 grep
    process_jupyter = subprocess.Popen(
        ["jupyter", "kernelspec", "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    process_grep = subprocess.Popen(
        ["grep", kernel_name],
        stdin=process_jupyter.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 关闭第一个进程的 stdout，以便它可以接收 SIGPIPE 信号
    process_jupyter.stdout.close()
    
    # 捕获 grep 的输出和错误
    output, error = process_grep.communicate()
    
    # 将每行转换为 JSON 对象，并放入数组中
    json_objects = []
    
    if process_grep.returncode == 0:
        # 将输出按行分割并去掉空行
        matched_lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        
        for line in matched_lines:
            parts = line.split()  # 假设每行格式为 "kernel_name path"
            if len(parts) >= 2:
                json_objects.append({
                    "kernel_name": parts[0],
                    "path": " ".join(parts[1:])  # 处理路径中可能包含空格的情况
                })
        logging.debug("find_kernel list: %s", json_objects)
        return json_objects
    else:
        logging.debug("Does not find any kernel by kernel name: %s.",kernel_name)
        return json_objects

# build the kernel name and create the kernel
def build_kernel(lock_timeout :int=15) -> bool:

    logging.debug("build_kernel...")
    logging.debug("lock_timeout: %s", lock_timeout)

    global current_kernel_name

    lock_filename = "lock_file"
    try:
        # 尝试获取文件锁
        with open(lock_filename, "w") as lock_file:
            # 尝试获取排他锁，超时时间为 15 秒
            logging.debug("Try to get the lock...")

            start_time = time.time()
            while True:
                try:
                    # 尝试获取文件锁，
                    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    logging.info("Get the lock successfully...")
                    break  # 获取锁成功，退出循环
                except BlockingIOError:
                    # 如果超过超时时间，则抛出异常
                    if time.time() - start_time >= lock_timeout:
                        logging.error("Get the lock failed...")
                        raise
                    # 等待一段时间后再次尝试获取锁
                    time.sleep(1)
                    
            kernelList = find_kernel(kernel_prefix)
            next_kernel_name = kernel_prefix + "_" + str(len(kernelList) + 1)
            
            createKernelFlg=create_kernel(next_kernel_name)
            modifyKernelJsonfileTo(next_kernel_name)
            
            # update the current_kernel_name if the latest kernel is created successfully
            if createKernelFlg :
                logging.info("Update current_kernel_name to %s .",next_kernel_name)

                current_kernel_name = next_kernel_name
    
    except IOError:
        logging.error("Another process is already running. Please try again later.")
        return False
    
    finally:
        # 释放文件锁
        try:
            fcntl.lockf(lock_file, fcntl.LOCK_UN)
        except:
            pass

    return True 
    
def create_kernel(kernel_name:str)->bool:

    logging.debug("create_kernel...")
    logging.debug("kernel_name: %s", kernel_name)
    currentPath=  os.getcwd()

    # 定义要执行的五个步骤，将 kernel_name 作为参数传入
    commands = [
        f"python -m venv {currentPath}/{kernel_name}",
        f"source {currentPath}/{kernel_name}/bin/activate",
        f"{currentPath}/{kernel_name}/bin/pip install -r requirements.txt",
        f"{currentPath}/{kernel_name}/bin/pip install ./aigbb_functions",
        f"{currentPath}/{kernel_name}/bin/python -m ipykernel install --name={kernel_name}  --user --display-name 'Python ({kernel_name})'"
    ]

    for command in commands:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logging.error(f"Error executing command: {command}")
            logging.error(f"Error message: {stderr}")
            return False
    return True

def modifyKernelJsonfileTo(kernel_name:str) -> bool:
    
    logging.debug("modifyKernelJsonfileTo...")
    logging.debug("kernel_name: %s", kernel_name)

    kernelList = find_kernel(kernel_name)
    logging.debug("kernelList: %s", kernelList)
    if len(kernelList) == 0:
        return True
    
    pythonEnvPath = os.path.join(os.getcwd(), kernel_name, 'bin', 'python')

    kernelJsonfilePath = kernelList[0]['path'] + "/kernel.json"

    # 打开并读取文件内容
    with open(kernelJsonfilePath, 'r') as f:
        kernel_data = json.load(f)

    # 更新 Python 路径
    kernel_data["argv"][0] = pythonEnvPath

    # 写回文件
    with open(kernelJsonfilePath, 'w') as f:
        json.dump(kernel_data, f, indent=4)    
    
    return True

# remove the remaining python env & kernel by kernel name
def remove_kernel_by_name(kernel_name:str):

    logging.debug("remove_kernel_by_name...")
    logging.debug("kernel_name: %s", kernel_name)


    # 定义要执行的两个步骤，将 kernel_name 作为参数传入
    commands = [
        f"jupyter kernelspec remove -f {kernel_name} -y",
        f"rm -rf {kernel_name}"
    ]

    for command in commands:
        logging.debug("process command: %s",command)
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logging.error(f"Error executing command: {command}")
            logging.error(f"Error message: {stderr}")
            return False
    return True

# clean the remaining env
def delete_directories_with_pattern(pattern):
    try:
        # 执行 ls | grep 命令，获取匹配指定模式的目录列表
        result = subprocess.run(f"ls | grep {pattern}", shell=True, capture_output=True, text=True, check=False)
        matched_directories = result.stdout.split('\n')

        # 删除匹配到的目录
        for directory in matched_directories:
            if directory:
                subprocess.run(["rm", "-rf", directory], check=True)
        
        print(f"Deleted directories matching pattern '{pattern}' successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete directories with pattern '{pattern}': {e}")


# remove the remaining python env & kernel
def remove_all_gbb_env_kernel():
    logging.debug("remove_all_gbb_env_kernel...")

    kernelList = find_kernel(kernel_prefix)
    logging.debug("kernelList: %s", kernelList)

    for kernel in kernelList:
        remove_kernel_by_name(kernel["kernel_name"])
    
    # clean the remaining env
    delete_directories_with_pattern(kernel_prefix)

# remove the remaining kernel
remove_all_gbb_env_kernel()
# build the default kernel
build_kernel()