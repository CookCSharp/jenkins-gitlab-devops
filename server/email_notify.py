'''
该脚本实现以下功能：
1.获取合并请求与提交的相关信息
2.创建邮箱内容模板
3.邮箱通知结果需要处理合并请求的人
'''


#-*- coding:utf-8 -*-
import smtplib
import sys
import os
import json
import gitlab_hook_common as ghc
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime


merge_request_messages = ''


def get_mrs_info():
    global merge_request_messages
    assignees_emails = []
    mr_assignees = []
    users = ghc.read_json_file(ghc.get_file_path_relative_current_file('users.json'))
    if 'mrs_info' in commit_info:
        for mr in commit_info['mrs_info']:
            assignee_names = []
            for user in users:
                if user['id'] in mr['assignee_ids']:
                    assignee_name = user['username']
                    assignees_emails.append(user['email'])
                    assignee_names.append(assignee_name)
            mr_assignees.append({'id': mr['id'], 'web_url': mr['web_url'], 'assignee_names': assignee_names})
    # else:
    #     merge_request_messages = 'target repository has commited <br/>'

    merge_index = 0
    for mr_assignee in mr_assignees:
        merge_index += 1
        mr_id = mr_assignee['id']
        mr_assignee_names = ', '.join(mr_assignee['assignee_names'])
        merge_request_messages += f"{merge_index}. Merge <a href='{mr['web_url']}'>#{mr_id}</a> need {mr_assignee_names} resolve <br/>"
        latest_commit_url = mr['web_url']+f"/commits?commit_id={commit_info['commit_sha1']}"
        latest_commit_user = commit_info['committer_name']
        merge_request_messages += f"<div style='margin-left: 30px;'>最近一次提交<a href='{latest_commit_url}'>#{commit_info['commit_title']}</a>由{latest_commit_user}发起</div>"

    old_email_to_list = list(setting['EmailTo'])
    new_email_to_list = set(old_email_to_list+ assignees_emails)

    return {'merge_request_messages': merge_request_messages, 'new_email_to_list': list(new_email_to_list)}


def get_all_commits():
    commits_api = ghc.list_project_commits_api.replace('id', str(commit_info['target_project_id'])) 
    commits_dict = ghc.get(commits_api)

    return commits_dict


def init_email_content():
    commits_dict = get_all_commits()   
    commits_info = '' 
    for commit in commits_dict:
        authored_date = datetime.strptime(commit['authored_date'].split('.')[0].replace('T',' '), f'%Y-%m-%d %H:%M:%S')
        committed_date = datetime.strptime(commit['committed_date'].split('.')[0].replace('T',' '), f'%Y-%m-%d %H:%M:%S')
        commits_info += "<img src='http://192.168.41.140:1080/uploads/-/system/user/avatar/19/gitlab.png' width='50' height='50' style='float: left;margin-top: 15px;'/> <br/>"
        commits_info += f"<div style='margin-bottom: 5px;'><a href='{commit['web_url']}' style>{commit['title']}</a> </div>"
        commits_info += f"<font size='2'>由{commit['author_name']}创作于{authored_date}, {commit['committer_name']}提交于{committed_date}</font> <br/><hr/>"

    # http://192.168.41.140:1080/system-software-team/devopstest/-/commit/8e596e09a64e40f45cfe8ae6c9893a7391cad2e9
    # http://192.168.41.140:1080/system-software-team/devopstest/-/commits/master
    web_url = str(commit['web_url'])
    commit = web_url.split('-').pop(-1)
    more_commits=web_url.replace(commit,"/commits/master")

    content = f"""
                <tr>本邮件由系统自动发出，请勿回复！<tr>  <br />
                <br />
                <tr>{merge_request_messages}<tr>  <br />
                <tr><font color="#CC0000" weight='bold'>项目{project_name}编译结果: {build_result}</font><tr>  <br />  
                <br />             
                <tr>以下为目标仓库上master分支上的部分提交记录：<tr>  <br />
                <a href='{more_commits}'>更多提交记录...</a> <br />
                <br />
                {commits_info}                            
            """
    return content


def send_email():
    # 1.连接邮箱服务器
    con = smtplib.SMTP('192.168.28.22', 25)
    con.set_debuglevel(1)
    # 2.登录邮箱
    con.login('jenkins@rndncatest.com', 'jenkins')
    # 3.设置邮件主题
    merge_count = None
    if len(commit_info['mrs_info']) > 0:
        merge_count = len(commit_info['mrs_info'])
    else:
        merge_count = 'None'
    subject = Header(f'{project_name} - {merge_count} merge request need resolve and Build #{build_numer}','utf-8')
    # 4.创建邮箱内容
    msg = MIMEText(content_template, 'html', 'utf-8')
    # msg = MIMEMultipart() # 带附件实例的对象
    # msg = MIMEText('测试一下', 'plain', 'utf-8')
    # msg.attach(html)
    msg['Subject'] = subject
    msg['From'] = 'jenkins@rndncatest.com'
    msg['To'] = ','.join(email_to_list)
    msg['Cc'] = ','.join(email_cc_list)
    # 5.发送邮件
    con.sendmail('jenkins@rndncatest.com', email_to_list + email_cc_list, msg.as_string())
    con.quit()


if __name__ == '__main__':
    setting = ghc.read_devops_setting_file()
    commit_info = ghc.read_json_file(ghc.get_file_path_relative_current_file('commit_info.json'))

    project_name = setting['Project']['name']
    email_cc_list = setting['EmailCc']
    mrs_info = get_mrs_info()
    email_to_list = mrs_info['new_email_to_list']
    merge_request_messages = mrs_info['merge_request_messages']
    # os.chdir(f'../../{project_name}')

    build_result = sys.argv[1]
    print(f'{project_name} build result: {build_result}')
    build_numer = sys.argv[2]

    # 初始化gitlab api
    ghc.init_gitlab_api_info(commit_info['gitlab_server'])
    
    content_template = init_email_content()
    send_email()

