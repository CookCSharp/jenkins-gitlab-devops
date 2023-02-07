'''
该脚本实现以下功能：
1.源代码编译(.Net/C++/Python)
'''

#-*- coding:utf-8 -*-
import os
import re
import gitlab_hook_common as ghc


languages = ['.net', 'c/c++', 'python']
exit_result = True
exit_message = ''


def get_errors(error_pattern:str|re.Pattern[str], buffer:bytes):
    try:
        text = buffer.decode(encoding='utf-8')
        decode_result = True
    except Exception:
        decode_result = False
    
    if decode_result == False:
        text = buffer.decode(encoding='gbk')
    
    errors = re.findall(error_pattern, text)
    return errors


def get_build_message(lang:str, full_path:str, build_cmd:str, error_pattern:str|re.Pattern[str]):
    command = build_cmd.replace('${file_path}', full_path)
    # print(command)
    res = os.popen(command)       
    buffers = res.buffer.read()
    errors = get_errors(error_pattern, buffers)
    
    global exit_result
    global exit_message
    if len(errors) <= 0:
        exit_message += f'{lang} build success;' 
    else:
        exit_result = False
        exit_message += f'{lang} build error;'  


def build_project():
    for lang in languages:
        match lang:
            case '.net':
                dotnet_solution_path = setting['Project']['dotnet_solution_path']
                full_path = ghc.get_absolute_src_path(dotnet_solution_path)
                build_cmd = setting['Project']['dotnet_build_cmd']
                error_pattern = r'[1-9]{1}[0-9]*\s个错误'             
            case 'c/c++':
                cpp_solution_path = setting['Project']['cpp_solution_path']
                full_path = ghc.get_absolute_src_path(cpp_solution_path)
                build_cmd = setting['Project']['cpp_build_cmd'] 
                error_pattern = 'error' 
            case 'python':
                python_solution_path = setting['Project']['python_solution_path']
                full_path = ghc.get_absolute_src_path(python_solution_path)
                build_cmd = setting['Project']['python_build_cmd']
                error_pattern = 'error'  

        if os.path.exists(full_path):
            get_build_message(lang, full_path, build_cmd, error_pattern)
        else:
            global exit_message
            exit_message += f'{lang} sourcecode is not exist;'

        
if __name__ == '__main__':
    # 获取远程仓库的项目信息
    project_info = ghc.get_project_info()
    if project_info == False:
        exit_result = False
        exit_message = 'the project has no remote repository on gitlab;'
    else:
        # 读取devops_setting.json配置文件
        setting = ghc.read_devops_setting_file()

        # build源代码
        build_project()

    print(f'project check {exit_result}: {exit_message}')
    # sys.exit(build_result)
