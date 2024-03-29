import os
import json
import time

from typing import Dict, List, Tuple
from core import Message, Chain, log
from core.util import any_match, remove_xml_tag
from core import AmiyaBotPluginInstance

from amiyabot import Message
from amiyabot.network.download import download_async
from amiyabot.network.httpRequests import http_requests


curr_dir = os.path.dirname(__file__)


class MaaCopilotPluginInstance(AmiyaBotPluginInstance):
    def install(self):
        ...


bot = MaaCopilotPluginInstance(
    name='maa作业查询',
    version='1.1.3',
    plugin_id='kkss-maa-copilot',
    plugin_type='',
    description='让兔兔可以查询maa作业',
    document=f'{curr_dir}/README.md',
    global_config_default=f'{curr_dir}/default.json',
    global_config_schema=f'{curr_dir}/schema.json',
)

def remove_prefix(text: str) -> str:
    for item in bot.get_container('prefix_keywords'):
        if item in text:
            text = text.replace(item, '')
            return text
    return text


async def fetch_copilot(params: dict=None) -> List[Dict]:
    url = 'https://prts.maa.plus/copilot/query'
    response = await http_requests.get(url, params=params)
    response = json.loads(response)
    
    if response['status_code'] != 200:
        log.error('maa查询: 网络错误')
        return None
       
    # if not data['data'] or not data['data']['total'] or not data['data']['data']:
    #     ...

    #print(f"\n {response['data']['total']  = }")
    return response


async def build_result(response:dict):

    if not response['data']['data']:
        return None
    
    cop = response['data']['data'][0]
    content = json.loads(cop['content'])

    md = '# ' + content['doc']['title']
    md += '\n ### ' + content['doc']['details'] + '<br><br>'
    md += '\n ## 干员 & 干员组:'
    md += '\n <font size="5">'
    md += ''.join([f"{o['name']}({o['skill']})  "
        for o in content['opers']
    ])
    if 'groups' in content:
        md += '<br>' 
        for g in content['groups']:
            md += f"**[{g['name']}]**: "
            md += " or ".join([f"{o['name']}({o['skill']}) " for o in g['opers']]) + '<br>'
    
    md += '\n ## <font color="#666">\n'

    md += f"评分: {cop['rating_level']/2 if cop['rating_level'] else '评分不足'} &emsp;"
    md += f"访问量: {cop['views']} &emsp;"
    md += f"作者: {cop['uploader']} &emsp;"
    md += f"{cop['upload_time'].split('T')[0]} &emsp;"
    md += '</font></font>' 
    code = '\n神秘代码:  maa://' + str(cop['id'])

    return [md, code]


async def query_verify(data:Message):
    text = remove_prefix(data.text).lower()
    
    if text.startswith('抄作业'):
        return True, 6, '抄作业'
    
    if text.startswith('maa') and bot.get_config('simpleKeyword'):
        print('maa!!ture')
        return True, 6, 'maa'
    
    return False
    

@bot.on_message(verify=query_verify)
async def _(data: Message):
    search = data.text.lower().split(data.verify.keypoint, 1)[1].strip()
    if search.__len__() < 2:
        return Chain(data).text('关键词过短, 请重新搜索')
    search = search.split(' ', 1)
    keyword = search[0]
    desc = search[1] if len(search) > 1 else ''

    response = await fetch_copilot(
        {'levelKeyword':keyword, 'document':desc, 'orderBy':'views'})
    if not response:
        return Chain(data).text('网络错误, 请稍候重试')
    
    res = await build_result(response)

    if res: 
        return Chain(data).markdown(res[0]).text(res[1])
    
    return Chain(data).text('没有搜索到相关结果. 请检查关卡名/代号, 或修改描述词')



