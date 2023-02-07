import os
import json
import requests


shanghai_gitlab_server = '192.168.9.90'
shanghai_gitlab_access_token = 'e__CrXfVXzgxYDyhQNBX'
wuhan_gitlab_server = '192.168.41.140'
wuhan_gitlab_access_token = '-5r8VDuHJnHhezJKjczf'
devops_setting_file_name = 'devops_setting.json'

forks_info = []
current_project_info = {}
target_project_info = {}


def get(api:str, params:object=None):
    reply = requests.get(api, headers=header, params=params)
    json_dict = json.loads(reply.text)

    return json_dict


def post(api:str, data:object):
    reply = requests.post(api, data=data, headers=header)
    status = json.loads(reply.text)


def init_gitlab_api_info(gitlab_server:int):
    global gitlabAccessToken
    global header
    global base_api
    if gitlab_server == 0: # 上海      
        header = {'PRIVATE-TOKEN' : shanghai_gitlab_access_token}
        base_api = 'http://192.168.9.90:9092/api/v4/'
    else: # 武汉
        header = {'PRIVATE-TOKEN' : wuhan_gitlab_access_token}
        base_api = 'http://192.168.41.140:1080/api/v4/'

    global target_project_infos_api
    global list_forks_api
    global list_all_users_api
    global get_single_commit_api
    global list_all_branches_api
    global create_branch_api
    global list_project_hooks_api
    global create_project_hook_api  
    global merge_request_api
    global list_project_mrs_api
    global list_mr_commits_api
    global list_project_commits_api

    # 查询指定项目
    target_project_infos_api = f'{base_api}projects'
    # 列出所有fork的信息
    list_forks_api = f'{base_api}projects/id/forks'
    # 获取所有用户
    list_all_users_api = f'{base_api}users'
    # 获取单次提交的信息
    get_single_commit_api = f'{base_api}projects/id/repository/commits/sha1'
    # 列出仓库下所有分支
    list_all_branches_api = f'{base_api}projects/id/repository/branches'
    # 创建新分支
    create_branch_api = f'{base_api}projects/id/repository/branches'
    # 列出项目钩子
    list_project_hooks_api = f'{base_api}projects/id/hooks'
    # 创建项目钩子
    create_project_hook_api = f'{base_api}projects/id/hooks'
    # 创建合并请求
    merge_request_api = f'{base_api}projects/id/merge_requests'
    # 获取项目的所有合并请求
    list_project_mrs_api = f'{base_api}projects/id/merge_requests'
    # 获取某个合并请求下的所有提交信息
    list_mr_commits_api = f'{base_api}projects/p_id/merge_requests/mr_id/commits'
    # 列出项目所有的提交
    list_project_commits_api = f'{base_api}projects/id/repository/commits'

    # print(f'测试：{target_project_infos_api}')
    # print(f"gitlabAccessToken:{gitlabAccessToken}")
    # print(f"header:{header}")
    # print(f"base_api:{base_api}")
    return 


def get_project_name_with_path():
    f = os.popen('git remote -v')
    cmd_output = f.read()
    if len(cmd_output) <= 0:
        return

    url = cmd_output.strip('\n').split('\n')[0].split('\t')[1].replace('(fetch)','').strip()
    # url = 'http://192.168.41.140:1080/sherry.zeng/test1.git'
    # url = 'git@192.168.9.90:systemsoftwareteam/documents.git'
    # url = 'http://192.168.9.90:9092/systemsoftwareteam/documents.git'

    # 上海ssh地址: git@192.168.9.90:systemsoftwareteam/documents.git
    if shanghai_gitlab_server in url and url.find('@') >= 0:
        gitlab_server = 0
        ssh_url = url
        web_url = url.replace(':',':9092/').replace('git@', 'http://')
        project_name = url.split('/')[-1].replace('.git','')
        path_with_namespace = url.split(':')[1].replace('.git','')
    # 上海http地址: http://192.168.9.90:9092/systemsoftwareteam/documents.git
    elif shanghai_gitlab_server in url and url.find('@') < 0:
        gitlab_server = 0
        ssh_url = url.replace('http://', 'git@').replace('9092/','')
        web_url = url
        project_name = url.split('/')[-1].replace('.git','')
        path_with_namespace = '/'.join(url.split('/')[-2:]).replace('.git','')
    # 武汉ssh地址: ssh://git@192.168.41.140:1022/sherry.zeng/test1.git
    elif wuhan_gitlab_server in url and url.find('@') >= 0:
        gitlab_server = 1
        ssh_url = url
        web_url = url.replace('ssh://git@', 'http://').replace('1022','1080')
        project_name = url.split('/')[-1].replace('.git','')
        path_with_namespace = '/'.join(url.split('/')[-2:]).replace('.git','')
    # 武汉http地址: http://192.168.41.140:1080/sherry.zeng/test1.git
    elif wuhan_gitlab_server in url and url.find('@') < 0:
        gitlab_server = 1
        ssh_url = url.replace('http://', 'ssh://git@').replace('1080','1022')
        web_url = url
        project_name = url.split('/')[-1].replace('.git','')
        path_with_namespace = '/'.join(url.split('/')[-2:]).replace('.git','')
    else:
        print("I don't know the server address")

    # print("ssh_url:"+ssh_url)
    # print("web_url:"+web_url)
    # print("project_name:"+project_name)  
    # print("path_with_namespace:"+path_with_namespace)
    init_gitlab_api_info(gitlab_server)  
    return {'gitlab_server':gitlab_server, 'ssh_url': ssh_url, 'web_url': web_url, 'project_name': project_name, 'path_with_namespace': path_with_namespace}


def get_project_info():
    has_project = True
    project_name_with_path = get_project_name_with_path()
    if project_name_with_path == None:
        has_project = False
    else:
        has_project = True

    param_pi = {
                'search': project_name_with_path['project_name'],
                'order_by': 'id',
                'sort': 'asc',
               }
    project_dicts = get(target_project_infos_api, param_pi)
    # project_dicts = get(target_project_infos_api+f"?search={project_name_with_path['project_name']}&order_by=id&sort=asc")
    
    for dict_temp in project_dicts:
        if dict_temp['path_with_namespace'] == project_name_with_path['path_with_namespace']:
            global current_project_info
            current_project_info = dict(dict_temp) 
            global target_project_info
            is_target_repo = 'forked_from_project' not in current_project_info
            if is_target_repo:       
                target_project_info = current_project_info       
            else:
                target_project_info = current_project_info['forked_from_project']

    return has_project                 
            

def get_all_projects_info(project_name:str):
    param_pi = {
                'search': project_name,
                'order_by': 'id',
                'sort': 'asc',
               }
    project_dicts = get(target_project_infos_api, param_pi)
    return project_dicts


def get_single_commit(project_id:int, sha1:str):
    single_commit_api = get_single_commit_api.replace('id', str(project_id)).replace('sha1', sha1)
    commit = get(single_commit_api)
    return commit


def get_opened_mrs(p_id:int):
    mrs = get_all_mrs(p_id, '?state=opened')
    return mrs


def get_all_mrs(p_id:int, api_params:str='?state=all'):
    project_mrs_api = list_project_mrs_api.replace('id', str(p_id)) + api_params
    mrs = get(project_mrs_api)
    return mrs


def get_all_commits_mr(p_id:int, mr_id:int):
    mr_commits_api = list_mr_commits_api.replace('p_id', str(p_id)).replace('mr_id', str(mr_id))
    commits = get(mr_commits_api)
    return commits


def get_all_forks(p_id:int):
    forks_api = list_forks_api.replace('id', str(p_id))
    json_dict = get(forks_api)
    for dict in json_dict:
        forks_info.append({'id': dict['id'], 'username': dict['owner']['username'], 'web_url': dict['web_url']})
    
    print(forks_info)


def get_absolute_src_path(relative_src_path:str):
    gitlab_parent_dir = os.path.abspath(f'{os.path.abspath(__file__)}/../..')
    absolute_src_path = os.path.join(gitlab_parent_dir, relative_src_path)
    return absolute_src_path


def get_file_path_relative_current_file(filename:str, current_file=__file__):
    prent_dir = os.path.abspath(f'{os.path.abspath(current_file)}/..')
    file_path = os.path.join(prent_dir, filename)
    return file_path


def copy_setting_files__to_remote_folder(file_path_lists:list):
    os.system('net use \\\\192.168.28.21\ipc$ Aa123456 /user:ncatest\chance.zheng')
    for file_path in file_path_lists:
        os.system(f'copy {file_path} \\\\192.168.28.21\\21_每日编译文件夹\\trunk\\08_DevOps /y')

    # os.system('copy gitlab\\dev_ops_setting.json \\\\192.168.28.21\\21_每日编译文件夹\\trunk\\08_DevOps /y')
    # os.system('copy gitlab\\commit_info.json \\\\192.168.28.21\\21_每日编译文件夹\\trunk\\08_DevOps /y')
    # os.system('del gitlab\\commit_info.json')
    # os.system('net use \\\\192.168.28.19\IPC$ /del /y')   


def read_json_file(file_path:str)->dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        json_str = f.read().replace('','')
        json_dict = json.loads(json_str)

    return json_dict


def read_devops_setting_file():
    file_path = get_file_path_relative_current_file(devops_setting_file_name)
    return read_json_file(file_path)


def save_json_file(json_content, file_path:str):
    # json_obj = object()
    # if type(json_content) == list:
    #     keys = [str(f'user{x+1}') for x in range(len(json_content))]
    #     json_obj = dict(zip(keys, json_content))
    # elif type(json_content) == dict:
    #     json_obj = json_content

    # with open('project_info.json', 'w', encoding='utf-8') as f:
    #     json.dump(project_info, f)

    # json转string
    str_json = json.dumps(json_content, indent=4, ensure_ascii=False)
    f = open(file_path, 'w', encoding='utf-8')
    f.write(str_json)
    f.close()