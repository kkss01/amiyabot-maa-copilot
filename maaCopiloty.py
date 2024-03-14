import os
import json
import time

from typing import Dict, List, Tuple
from core import Message, Chain, log, bot as main_bot
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
    version='1.0',
    plugin_id='kkss-maa-copilot',
    plugin_type='',
    description='让兔兔可以查询maa作业',
    document=f'{curr_dir}/README.md',
    #global_config_default=f'{curr_dir}/default.json',
    #global_config_schema=f'{curr_dir}/schema.json',
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
    md += '\n ### ' + content['doc']['details']
    md += '\n ## 干员 & 干员组: \n <font size="5">'
    md += ''.join([f"{o['name']}({o['skill']})  "
        for o in content['opers']
    ]) + '</font> '
    if 'groups' in content:
        md += '<br>' 
        for g in content['groups']:
            md += '<font size="5">'
            md += f"**[{g['name']}]**: "
            md += " or ".join([f"{o['name']}({o['skill']}) " for o in g['opers']]) + '<br>'
        md += '</font> ' 
    
    

    code =  '神秘代码:  maa://' + str(cop['id'])

    return [md, code]


async def query_verify(data:Message):
    text = remove_prefix(data.text).lower()
    
    if not text.startswith('maa'):
        return False
    
    return True, 6
    

@bot.on_message(verify=query_verify)
async def _(data: Message):
    search = data.text.split('maa', 1)[1].strip()
    if search.__len__() < 2:
        return Chain(data).text('关键词过短, 请重新搜索')
    search = search.split(' ', 1)
    keyword = search[0]
    desc = search[1] if len(search) > 1 else ''
    print(f'\n >>>var>>> { keyword = }')
    print(f'\n >>>var>>> { desc = }')

    response = await fetch_copilot(
        {'levelKeyword':keyword, 'document':desc, 'orderBy':'views'})
    if not response:
        return Chain(data).text('网络错误, 请稍候重试')
    
    res = await build_result(response)

    if res: 
        return Chain(data).markdown(res[0]).text(res[1])
    
    return Chain(data).text('没有搜索到相关结果, 请搜索关卡名或代号')



