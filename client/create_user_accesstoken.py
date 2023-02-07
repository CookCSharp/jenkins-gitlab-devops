'''
该脚本实现以下功能：
1.在gitlab上创建项目的webhook
2.初始化devops_setting.json文件配置
3.将devops_setting.json、commit_info.json、users.json拷贝到\\192.168.28.21\21_每日编译文件夹\trunk\08_DevOps
'''

import gitlab_hook_common as ghc


shanghai_target_hook_url = 'http://192.168.41.99:8000/project/DevOps_SH'
shanghai_target_token = 'fe4772dc797a5c11293c3017e1bfa344'
wuhan_target_hook_url = 'http://192.168.41.99:8000/project/DevOps_WH'
wuhan_target_token = '26bb8e6efa3a5783f193c4ae862147e2'

exit_result = True
exit_message = ''


def get_hook_info():
    project_name_with_path = ghc.get_project_name_with_path()
    gitlab_server = project_name_with_path['gitlab_server']
    if gitlab_server == 0:
        target_hook_url = shanghai_target_hook_url
        target_token = shanghai_target_token
    else:
        target_hook_url = wuhan_target_hook_url
        target_token = wuhan_target_token

    return {'url': target_hook_url, 'token': target_token}


def create_project_hook():
    hook_info = get_hook_info()
    target_hook_url = hook_info['url']
    target_token = hook_info['token']
    
    get_hooks_api = ghc.list_project_hooks_api.replace('id', str(ghc.current_project_info['id']))
    project_hooks = ghc.get(get_hooks_api)
    urls = []
    for project_hook in project_hooks:
        urls.append(project_hook['url'])

    if target_hook_url in urls:
        print(f"the {ghc.current_project_info['path_with_namespace']}'s webhook '{target_hook_url}' is already existed")
    else:
        param_ph = {
                    'id' : ghc.current_project_info['id'],
                    'url' : target_hook_url,
                    'token' : target_token,
                    'push_events' : True,
                    'merge_requests_events' : False
                   }
        create_hook_api = ghc.create_project_hook_api.replace('id', str(ghc.current_project_info['id']))
        ghc.post(create_hook_api, data=param_ph)
        print(f"create {ghc.current_project_info['path_with_namespace']}'s webhook '{target_hook_url}' success")


def init_devops_setting(project_name:str, ssh_url:str):
    file_path = ghc.get_file_path_relative_current_file(ghc.devops_setting_file_name)
    json_dict = ghc.read_json_file(file_path)
    project = dict(json_dict['Project'])
    project.update(name = project_name)
    project.update(target_repo = ssh_url)
    json_dict.update(Project = project)
    ghc.save_json_file(json_dict, file_path)


def copy_files():
    # 将devops_setting.json、commit_info.json、users.json拷贝到远程供读取
    file_path_lists = [ghc.get_file_path_relative_current_file(ghc.devops_setting_file_name), ghc.get_file_path_relative_current_file('commit_info.json'), ghc.get_file_path_relative_current_file('users.json')]
    ghc.copy_setting_files__to_remote_folder(file_path_lists)


if __name__ == '__main__': 
    # 获取远程仓库的项目信息
    project_info = ghc.get_project_info()
    if project_info == False:
        exit_result = False
        exit_message = 'the project has no remote repository on gitlab;'
    else:
        # 创建webhook
        create_project_hook()

        # 初始化配置信息
        init_devops_setting(ghc.target_project_info['name'], ghc.target_project_info['ssh_url_to_repo'])

        # 拷贝json文件至远程
        copy_files()

        exit_result = True
        exit_message = 'Success!'      

    print(f'project check {exit_result}: {exit_message}')