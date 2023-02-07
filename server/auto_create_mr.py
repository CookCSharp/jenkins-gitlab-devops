'''
该脚本实现以下功能：
1.拉取目标仓库的代码与触发jenkins的代码仓库合并，有错误就邮箱通知
2.更新commit_info.json文件信息
3.创建合并请求
'''


import json
import sys
import os
import smtplib
import gitlab_hook_common as ghc
from email.header import Header
from email.mime.text import MIMEText
from datetime import datetime


next_merge_request_id = 0


def send_email(source:str, target:str, merge_id:int):
    # 1.连接邮箱服务器
    con = smtplib.SMTP('192.168.28.22', 25)
    con.set_debuglevel(1)
    # 2.登录邮箱
    con.login('jenkins@rndncatest.com', 'jenkins')
    # 3.设置邮件主题
    subject = Header(f'{project_name} - Merge failure on jenkins #{build_numer}','utf-8')
    # 4.创建邮箱内容
    # msg = MIMEText(content_template, 'html', 'utf-8')
    # msg = MIMEMultipart() # 带附件实例的对象
    # Merge blocked: merge conflicts must be resolved.
    msg = MIMEText(f'本邮件由系统自动发出，请勿回复！\n\n Merge {source} into {target} will fail.', 'plain', 'utf-8')
    # msg.attach(html)
    msg['Subject'] = subject
    msg['From'] = 'jenkins@rndncatest.com'
    msg['To'] = ','.join(email_to_lists)
    # 5.发送邮件
    con.sendmail('jenkins@rndncatest.com', email_to_lists, msg.as_string())
    con.quit()


def merge_branch():
    os.chdir('../../')
    if os.path.exists(project_name) == True:
        os.system('{} {}'.format('rd /S/Q', project_name))

    os.system(f"git clone -b {commit_info['target_branch']} {target_repo}")
    os.chdir(f'{project_name}')

    # if os.path.exists(f'{project_name}') == False:
    #     os.system(f'git clone {target_repo}')
    #     os.chdir(f'{project_name}')
    # else:
    #     os.chdir(f'{project_name}')
    #     os.system('git pull origin master')

    source_branch = f"{commit_info['source_group']}: {commit_info['source_branch']}"
    target_branch = f"{commit_info['target_group']}: {commit_info['target_branch']}"
    
    pull_cmd = os.system(f"git pull {source_repo} {commit_info['source_branch']}")
    if pull_cmd > 0:
        send_email(source_branch, target_branch, next_merge_request_id)
        return False
    else:
        return True


def get_merge_request_info():
    opened_mrs = ghc.get_opened_mrs(commit_info['target_project_id'])
    mr_ids = []
    merge_requests_info = []
    current_merge_request_info = None
    for mr in opened_mrs:
        commits = ghc.get_all_commits_mr(mr['target_project_id'], mr['iid'])   
        merge_requests_info.append({'merge_request_id': mr['iid'], 'title': mr['title'], 'commits': commits, 'web_url': mr['web_url']})
        for commit in commits:
            if commit['id'] == commit_info['commit_sha1']:
                merge_request_id = mr['iid']
                current_merge_request_info = {'merge_request_id': merge_request_id, 'title': mr['title'], 'commits': commits, 'web_url': mr['web_url']}

    global next_merge_request_id
    all_mrs = ghc.get_all_mrs(commit_info['target_project_id'])
    [mr_ids.append(mr['iid']) for mr in all_mrs]
    mr_ids.sort(reverse=True)
    if len(all_mrs) <= 0:
        next_merge_request_id = 1
    elif len(opened_mrs) <= 0:
        next_merge_request_id = int(mr_ids[0]) + 1
    else:
        next_merge_request_id = mr_ids[0]
 
    return {'current_merge_request': current_merge_request_info, 'merge_requests': merge_requests_info}


def update_mr_info(merge_request:dict):
    merge_request_id = merge_request['merge_request_id']
    merge_request_title = merge_request['title']
    
    commits = merge_request['commits']
    description = ''
    for commit in commits:
        description += str(commit['message'])

    new_merge_request = {}
    new_merge_request.update(id = merge_request_id)
    new_merge_request.update(title = merge_request_title)
    new_merge_request.update(description = description) 
    new_merge_request.update(assignee_ids = setting['MR']['assignee_ids'])
    new_merge_request.update(web_url = merge_request['web_url']) 
    
    return new_merge_request  


def update_commit_info():
    commit_sha1_value = commit_info['commit_sha1']
    commit = ghc.get_single_commit(commit_info['source_project_id'], commit_sha1_value)

    commit_info.update(author_name = commit['author_name'])
    commit_info.update(author_email = commit['author_email'])
    authored_date = datetime.strptime(commit['authored_date'].split('.')[0].replace('T',' '), f'%Y-%m-%d %H:%M:%S')  
    commit_info.update(authored_date = str(authored_date))
    commit_info.update(committer_name = commit['committer_name'])
    commit_info.update(committer_email = commit['committer_email'])
    committed_date = datetime.strptime(commit['committed_date'].split('.')[0].replace('T',' '), f'%Y-%m-%d %H:%M:%S')
    commit_info.update(committed_date = str(committed_date))
    commit_info.update(commit_title = commit['title'])
    commit_info.update(commit_message = commit['message'])
    commit_info.update(commit_detail = commit['web_url'])

    merge_request_info = get_merge_request_info() 
    current_merge_request = merge_request_info['current_merge_request']
    merge_requests = merge_request_info['merge_requests']
    mrs_info = []
    if current_merge_request == None:
        current_merge_request = {}
        current_merge_request.update(id = next_merge_request_id)
        title = f"{commit_info['source_group']}:{commit_info['source_branch']}合并到{commit_info['target_group']}:{commit_info['target_branch']}"
        current_merge_request.update(title = title)
        current_merge_request.update(description = commit_info['commit_message']) 
        current_merge_request.update(assignee_ids = setting['MR']['assignee_ids'])
        base_url = commit_info['commit_detail'].replace(commit_info['source_group'],commit_info['target_group'])
        web_url = base_url.replace(base_url.split('-').pop(-1),f'/merge_requests/{next_merge_request_id}')
        current_merge_request.update(web_url = web_url) 
        commit_info.update(current_mr_info = current_merge_request)
        mrs_info.append(current_merge_request)
    else:
        commit_info.update(current_mr_info = update_mr_info(current_merge_request))    
 
    for merge_request in merge_requests:
        mrs_info.append(update_mr_info(merge_request))
 
    commit_info.update(mrs_info = mrs_info)   
    # ghc.save_json_file(commit_info, '../BuildCheck_Deployment/run/commit_info.json')    
    ghc.save_json_file(commit_info, ghc.get_file_path_relative_current_file('commit_info.json')) 


def create_mr():   
    # 'assignee_id' : setting_mr['assignee_id'],
    param_mr = {
                'id' : commit_info['source_project_id'],
                'target_project_id' : commit_info['target_project_id'],
                'title' : commit_info['current_mr_info']['title'],
                'description' : commit_info['current_mr_info']['description'],
                'assignee_ids' : setting_mr['assignee_ids'],
                'reviewer_id' : setting_mr['reviewer_id'],
                'source_branch' : commit_info['source_branch'],
                'target_branch' : commit_info['target_branch'],
                'remove_source_branch' : False,
                'allow_collaboration' : True,
                'squash' : False  
               }
    merge_api = ghc.merge_request_api.replace('id', str(commit_info['source_project_id']))
    ghc.post(merge_api, param_mr)


if __name__ == '__main__':
    # 获取配置信息
    setting = ghc.read_devops_setting_file()
    setting_mr = setting['MR']
    project_name = setting['Project']['name']
    email_to_lists = setting['EmailTo']

    source_repo = sys.argv[1]  # 触发Jenkins的Gitlab仓库地址
    build_numer = sys.argv[2]  # Jenkins的Build Number

    if source_repo == setting['Project']['target_repo']:
        print('target repository has commited')
    else:
        # 读取commit_info.json文件
        commit_info = ghc.read_json_file(ghc.get_file_path_relative_current_file('commit_info.json'))
        target_repo = commit_info['target_repository']

        # 初始化gitlab api
        ghc.init_gitlab_api_info(commit_info['gitlab_server'])

        # 拉取source_repository与target_repository合并
        merge_res = merge_branch()       
        if merge_res == True:
            # 更新commit_info.json文件
            update_commit_info()

            # 创建合并请求
            create_mr()

        print(merge_res)