# -*- coding:utf-8 -*-
"""
所有测试用例一次性回归测试
cd community_service
python3 unittest/run_all_cases.py

覆盖率测试
coverage3 run unittest/run_all_cases.py

生成覆盖率详情，存放于cov_html_run_all_cases文件加下，入口index.html
coverage3 html -d ../cov_html_run_all_cases --include="./*" --omit="./config/*,./lib/*,./test/*"

查看覆盖率总报告
coverage3 report --include="./*" --omit="./config/*,./lib/*,./test/*"
"""
import os
import unittest
from tests.base_service import TestCaseEnvUtil

# 不被测试的case。
# 如无必要，最好不要跳过case。因为...测测更健康。
EXCLUDE_FILES = [
    'base_service.py',
    'run_all_cases.py',
]

# 路径特征
test_path_marker = 'standard_community_server/tests'

if __name__ == '__main__':

    # 加载当前测试目录下所有cases
    suite = unittest.TestSuite()
    current_path = os.path.dirname(os.path.realpath(__file__))
    current_path = current_path.split(test_path_marker)[0] + test_path_marker
    for root, dirs, files in os.walk(current_path):
        for f in sorted(files):
            # 非测试文件
            if f in EXCLUDE_FILES or f.startswith('.') or not f.endswith('.py') or '__init__.' in f:
                continue

            # 加载测试类class
            mod_paths = root.split(current_path + '/')
            mod_path_head = ''
            if len(mod_paths) is 2:
                mod_path_head = mod_paths[-1].replace('/', '.') + '.'
            from importlib import import_module
            mod = import_module(mod_path_head + f.replace('.py', ''))
            for name in dir(mod):
                if not name.startswith('Test'):
                    continue
                # 加载测试类中的具体function
                test_class = getattr(mod, name)
                for test_class_fun_name in sorted(dir(test_class)):
                    if not test_class_fun_name.startswith('test_'):
                        continue
                    suite.addTest(test_class(test_class_fun_name))

    # 初始化单测环境
    result = TestCaseEnvUtil.prepare_server_for_test_cases()
    if not result:
        print('failed to test all cases')
        exit()

    # 串行运行所有用例
    runner = unittest.TextTestRunner(buffer=True, verbosity=2, failfast=True)
    result = runner.run(suite)

    # 关闭测试环境
    TestCaseEnvUtil.close_server_for_test_cases()
    exit(not result.wasSuccessful())
