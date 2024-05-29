1. 分成两个requirements.txt文件。第一个来管理本身的依赖和一些默认的依赖。第二个管理通过function call新引入的依赖

   pip install ipykernel jupyter
   pip install -r requirements.txt ( including extra-requirements.txt)
2. 构建一个aigbb_functions模块

   所有的functions 都放到 aigbb_functions 模块下

   通过import * 的方式，每个方法都默认变成引入。
3. 构建新的kernel ，安装上面两步的依赖和模块

   1. 构建一个新的环境，避免干扰：
      1. python -m venv aigbb_functions_kernel_1
      2. source  aigbb_functions_kernel_1/bin/activate
      3. pip install -r requirements.txt ( including extra-requirements.txt)
      4. pip install  ./aigbb_functions
4. 注册内核(kernel位置：/Users/huqianghui/Library/Jupyter/kernels/aigbb_functions_kernel_1)

   python -m ipykernel install --user --name=aigbb_functions_kernel_1 --display-name "Python (aigbb_functions_kernel_1)"
5. 通过命令行 jupyter kernelspec list 查看所有内核情况
6. 启动服务，对外restful API 提供function call的能力 python 脚本执行能力

   1. 在启动服务的过程中，选择对应的最新的内核
