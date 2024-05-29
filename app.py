from flask import Flask, request, jsonify
import asyncio
from jupyter_client import KernelManager
import threading,os
from build_new_env_and_kernel import get_current_kernel_name,build_kernel
import logging
from function_export import update_init_py

# 从环境变量中读取日志级别，默认为 INFO
log_level = os.getenv('LOG_LEVEL', 'DEBUG')

# 将日志级别字符串转换为对应的日志级别常量
numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

# 配置日志记录器
logging.basicConfig(level=numeric_level)


# app1 for function call
app1 = Flask(__name__)

async def execute_code_in_kernel(code):
    
    # 使用预配置的内核（选择最新的内核）
    km = KernelManager(kernel_name=get_current_kernel_name())
    km.start_kernel()

    try:
        kc = km.client()
        kc.start_channels()
        kc.wait_for_ready()
        kc.execute("from aigbb_functions import * \n")
        # 发送代码执行请求
        
        msg_id = kc.execute(code)

        # 收集结果
        result = ""
        while True:
            msg = kc.get_iopub_msg()
            if msg['parent_header'].get('msg_id') == msg_id:
                if msg['msg_type'] == 'execute_result':
                    result = msg['content']['data']['text/plain']
                    break
                elif msg['msg_type'] == 'error':
                    result = '\n'.join(msg['content']['traceback'])
                    break
        return result
    finally:
        kc.stop_channels()
        km.shutdown_kernel()


@app1.route('/', methods=['GET'])
def helloApp1():
    return 'Hello from app1!'
    
@app1.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    code = data.get('code', '')

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    try:
        result =asyncio.run(execute_code_in_kernel(code)) 
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# app2 for function definition
app2 = Flask(__name__)

@app2.route('/', methods=['GET'])
def helloApp2():
    return 'Hello from app2!'

@app2.route('/register', methods=['POST'])
def index2():
    data = request.get_json()
    functionName = data.get('functionName', '')
    assert len(functionName) > 0, 'Function name is required!'

    functionScript = data.get('functionScript', '')
    assert len(functionScript) > 0, 'Function name is required!'

    packagesRequired = data.get('packages', '')

    # Create a directory to store the function
    directory = './aigbb_functions'
    # Create target Directory if don't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, f'{functionName}.py'), 'w') as file:
        file.write(functionScript)

    # Add the required packages to the extra-requirements.txt file
    if len(packagesRequired) >0 :
        with open('extra-requirements.txt', 'a') as file:
            file.write('\n' + packagesRequired)

    # Compile the function to validate the syntax
    try:
        compile(functionScript, functionName, "exec")
    except Exception as e:
        return jsonify({'error': f'Function syntax error: {str(e)}'}), 400

    # Update the __init__.py file
    update_init_py(functionName, functionName)
    
    buildKernelFld = build_kernel()
    if buildKernelFld:
        return jsonify({'result': 'Function registered successfully!'})
    else:
        return jsonify({'error': 'Function registration failed! Maybe someone is regetering at the same time.Please try later.'}), 500

# start the two apps
# 定义函数来运行第一个 Flask 应用
def run_app1():
    app1.run(host='0.0.0.0',port=8000)

# 定义函数来运行第二个 Flask 应用
def run_app2():
    app2.run(host='0.0.0.0',port=8001)

if __name__ == '__main__':
    # 创建线程来运行两个应用
    t1 = threading.Thread(target=run_app1)

    t2 = threading.Thread(target=run_app2)
    
    # 启动线程
    t1.start()
    t2.start()
    
    # 等待线程完成
    t1.join()
    t2.join()
