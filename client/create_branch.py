'''
该脚本实现以下功能：
1.获取gitlab上所有用户信息
2.获取本次提交信息并保存至commit_info.json
3.提交代码前拉取目标仓库的代码并与本地代码合并
4.以默认分支为基础创建以gitlab用户名为名的本地/远程分支
'''

import os
import gitlab_hook_common as ghc
# import numpy as np


users_info = []
commit_info = {}


def get_all_users(): 
    users = ghc.get(ghc.list_all_users_api)
    for user in users:
        users_info.append({'id': user['id'],'username': user['username'], 'email': user['email']})

    get_id = lambda user: user['id']
    users_info.sort(key=get_id, reverse=False)
    ghc.save_json_file(users_info, ghc.get_file_path_relative_current_file('users.json'))


def get_current_commit():
    # git rev-parse --short HEAD'
    f1 = os.popen('git rev-parse HEAD')
    commit_sha1_value = f1.read().strip()

    # # %H 完整hash字符串  %h简短hash字符串 %cd提交时间
    # f2 = os.popen('git log --pretty="%s" -p -1')
    # commit_message = f2.read().strip()

    source_project_id = ghc.current_project_info['id']
    target_project_id = ghc.target_project_info['id']
    source_repository = ghc.current_project_info['ssh_url_to_repo']
    target_repository = ghc.target_project_info['ssh_url_to_repo']
    path_with_namespace = ghc.get_project_name_with_path()
    source_group_name = path_with_namespace['path_with_namespace']
    source_branch_name = source_group_name.split('/')[0]   
    target_branch_name = ghc.read_devops_setting_file()['Project']['default_branch']

    if ghc.shanghai_gitlab_server in source_repository:
        target_group_name = str(target_repository.split(':')[1]).replace('.git','')
        commit_info.update(gitlab_server = 0)
    else:
        target_group_name = '/'.join(target_repository.split('/')[-2:]).replace('.git','')
        commit_info.update(gitlab_server = 1)
    commit_info.update(commit_sha1 = commit_sha1_value)
    commit_info.update(source_project_id = source_project_id)
    commit_info.update(source_project_id = source_project_id)
    commit_info.update(target_project_id = target_project_id)
    commit_info.update(source_repository = source_repository)
    commit_info.update(target_repository = target_repository)
    commit_info.update(source_group = source_group_name)
    commit_info.update(target_group = target_group_name)
    commit_info.update(source_branch = source_branch_name)
    commit_info.update(target_branch = target_branch_name) 
    # current_mr_info = {}
    # current_mr_info.update(title = f'{source_group_name}:{source_branch_name}合并到{target_group_name}:{target_branch_name}')
    # commit_info.update(current_mr_info = current_mr_info)

    ghc.save_json_file(commit_info, ghc.get_file_path_relative_current_file('commit_info.json'))


def pull_sourcecode():
    setting = ghc.read_devops_setting_file()
    global target_repo
    target_repo = ghc.target_project_info['ssh_url_to_repo']
    global default_branch
    default_branch = setting['Project']['default_branch']

    os.system('git stash')

    # # 该命令可保证自己项目下的master分支与目标仓库一致
    # my_branch = ghc.current_project_info['owner']['username']
    # os.system(f'git checkout {default_branch}')
    # os.system(f'git pull {target_repo} {default_branch}')
    # os.system(f'git checkout {my_branch}')
    # os.system(f'git rebase {default_branch}')

    os.system(f'git fetch {target_repo} {default_branch}')
    os.system('git rebase FETCH_HEAD')
    # os.system(f'git merge --no-ff FETCH_HEAD') # 禁止快进式合并

    os.system('git stash pop')


def create_branch_base_remote():
    param_cb = {
                'id': ghc.current_project_info['id'], 
                'branch': ghc.current_project_info['owner']['username'], 
                'ref': 'master'
               }
    branch_api = ghc.create_branch_api.replace('id', str(ghc.current_project_info['id']))
    ghc.post(branch_api, param_cb)

def create_branch_base_local():
    local_branch_name = ghc.current_project_info['owner']['username']

    with os.popen('git branch -a') as f:
        branches = f.read().strip().split('\n')
        for branch in branches:
            is_existed = branch.replace('*','').strip() == str(local_branch_name)                  
            if(is_existed == True):
                existed = True             
                break
            else:
                existed = False  

    # if(existed == True):
    #     print(f"the branch '{local_branch_name}' is already existed")
    #     os.system(f'git branch -D {local_branch_name}')
    #     os.system(f'git push origin --delete {local_branch_name} --no-verify')
    #   # os.system(f'git checkout {local_branch_name}')
    #   # os.system('git merge --no-ff tmp')
    #     os.system(f'git rebase master {local_branch_name}')
    #     os.system(f'git push --set-upstream origin {local_branch_name} --no-verify')
    #     os.system(f'git checkout master')
    # else:  
    #     print(f'the {local_branch_name} is not existed')
    #     os.system(f'git branch --track {local_branch_name} master')
    #     # os.system(f'git checkout {local_branch_name}')
    #     # os.system(f'git checkout -b {local_branch_name} --track master')
    #     os.system(f'git push --set-upstream origin {local_branch_name} --no-verify')

    if existed == False:
        os.system(f'git checkout -b {local_branch_name} master')
        os.system(f'git push --set-upstream origin {local_branch_name} --force')
        default_branch = ghc.read_devops_setting_file()['Project']['default_branch']
        os.system(f'git push origin {default_branch}')


if __name__ == '__main__': 
    # 获取远程仓库的项目信息
    has_project_info = ghc.get_project_info()

    # 获取所有用户信息
    get_all_users()

    # 获取本次提交信息并保存
    get_current_commit()
   
    # 拉取目标仓库的代码与本地合并
    pull_sourcecode()

    if has_project_info == True:
        # 创建远程新分支
        # create_branch_base_remote()

        # 创建本地新分支
        create_branch_base_local()