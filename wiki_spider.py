import requests
from bs4 import BeautifulSoup

class WikiSpider:
    """
    基于 requests 的简单维基百科爬虫
    """
    def __init__(self, is_proxy=False):
        """
        初始化 requests 的各种设置
        :param is_proxy: 是否使用代理
        """
        
        # 歧义页面
        self.ambi_board = {}
        # requests session
        self.session = requests.Session()
        # requests proxy
        self.proxies = None
        self.request_kwargs = None
        if is_proxy:
            self.proxies = {
                "http": "http://127.0.0.1:1080",
                "https": "http://127.0.0.1:1080",
            }

            self.request_kwargs = {
                "proxy_url": "http://127.0.0.1:1080"
            }
        # requests header
        self.wiki_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,de;q=0.6',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def tg_wiki(self, chat_id, kw):
        """
        用于 telegram 的查询入口
        """
        try:
            # 尝试把 kw 当数字处理
            item_num = int(kw)
            # 如果确定是数字，则前往歧义页面进行处理
            brief = self.wiki_by_ambi_num(chat_id, item_num)
            print(brief[:120] + '...\n')
            # bot.send_message(chat_id=chat_id, text=brief)
            return brief 
            
        except ValueError:
            pass

        try:
            brief = self.wiki(chat_id, kw)
            if not brief:
                brief = '什么也没找到'
            print(brief[:120] + '...\n')
            # bot.send_message(chat_id=chat_id, text=brief)
            return brief
        except IndexError:
            # bot.send_message(chat_id=chat_id, text='请输入文字')
            return '请输入文字'
        except Exception as e:
            print(e)

    def wiki(self, chat_id, kw):
        """
        依靠关键字查询主入口
        :param chat_id(int): Telegram 的对话id
        :param kw(str): 关键字 
         """
        print('正在查询: ', kw)

        # 如果输入为空
        if not kw or not kw.strip():
            return '什么都没有找到'

        # url 前缀
        prefix = 'https://zh.wikipedia.org/wiki/'
        url = prefix + kw

        # 清空当前 chat 在 ambi_board 上的数据
        if chat_id in self.ambi_board:
            self.ambi_board.pop(chat_id)
        # 返回以网址查询的结果
        return self.wiki_by_url(chat_id, url)

    def wiki_by_ambi_num(self, chat_id, num):
        """
        从歧义页面中选择
        :param chat_id(int): Telegram 的对话 id
        :param num(int): 选择的序号
        """
        url = None
        try:
            # 尝试从 ambi_board 中选取目标项目的 url
            url = self.ambi_board[chat_id][num]['url']
        except (KeyError, IndexError):
            return '输入错误，重新选择'
        if url:
            return self.wiki_by_url(chat_id, url)
        else:
            return '输入错误，重新选择'


    def wiki_by_url(self, chat_id, url):
        """
        对 url 发起请求，并进行内容分析处理
        :param chat_id(int): Telegram 的对话 id
        :param url(str): 所要请求的 url
        """
        # get 请求
        r = self.session.get(url, headers=self.wiki_headers, proxies=self.proxies)
        url = r.url  
        # 用 BeautifulSoup 进行处理
        soup = BeautifulSoup(r.text, 'lxml')

        # 歧义页面
        try:
            # 如果页面中存在歧义页面的 disambigbox 元素
            disambigbox = soup.select('#disambigbox')
            if disambigbox:
                # 提取选项列表，保存到 self.ambi_board 
                ambi_list = soup.select('.mw-parser-output > ul > li')
                self.ambi_board[chat_id] = {}

                i = 0
                # print(ambi_list)
                for item in ambi_list:
                    # item = ambi_list[i]
                    # item_title = item.find_all('a')[0]['title']
                    tag_a = item.find('a')
                    if 'class' in tag_a.attrs and 'new' in tag_a['class']:
                        continue
                    item_url = 'https://zh.wikipedia.org' + tag_a['href']
                    item_description = item.get_text()
                    # 提取
                    self.ambi_board[chat_id][i] = {
                                            'url': item_url,
                                            'description': item_description,
                                            }
                    i += 1
                
                # 生成 ambi_str  
                ambi_str = disambigbox[0].parent.find('p').get_text() + '\n'
                for k, v in self.ambi_board[chat_id].items():
                    ambi_str += '[{}] {}\n'.format(k, v['description'])
                ambi_str += '输入 /wiki@wikiboy_bot+数字 选择所要查看的条目'
                return ambi_str
        except IndexError:
            return '处理内容发生错误'
        except Exception as e:
            print(e)
            return '什么都没有找到'


        # 正常页面
        brief = '' # 内容简要
        title = '' # 标题
        target_p = None # 目标的 p 元素
        try:
            title = soup.h1.get_text() + '\n' 
            main_content = soup.select('.mw-parser-output > p')
            if main_content:
                target_p = main_content[0]
                if target_p.select('span[class="latitude"]') or len(target_p.get_text().strip()) < 5:
                    target_p = target_p.find_next_sibling('p')
                brief = target_p.get_text()
        except Exception as e:
            print(e)

        # 如果没有找到 main_content 进入搜索页面
        if len(soup.select('.noarticletext')) > 0:
            try:
                search_url_prefix = 'https://zh.wikipedia.org/wiki/Special:%E6%90%9C%E7%B4%A2/'
                search_resp = requests.get(search_url_prefix + title[:-1], headers=self.wiki_headers, proxies=self.proxies)
                search_soup = BeautifulSoup(search_resp.text, 'lxml')
                search_results = search_soup.select('.mw-search-results > li > div > a')

                # 处理搜索结果
                # 清空歧义页面的数据
                self.ambi_board[chat_id] = {}
                ambi_str = '没有直接相关的结果，但我尝试做了搜索：'
                if len(search_results) == 0:
                    return '什么都没有找到'
                for i in range(len(search_results)):
                    res = search_results[i]
                    item_url = 'https://zh.wikipedia.org' + res['href']
                    item_description = res.get_text()
                    self.ambi_board[chat_id][i] = {
                            'url': item_url,
                            'description': item_description,
                            }
                    ambi_str += '\n[{}] {}'.format(i, item_description)
                ambi_str += '\n输入 /wiki@wikiboy_bot+数字 选择所要查看的条目'
                return ambi_str
            except Exception as e:
                print(e)
                return '什么都没有找到'

        if not brief:
            return '什么都没有找到'

        # 移除所有的方括号
        brief = self.remove_brackets(brief, '[]')
        return title + brief + '\n' + url


    def remove_brackets(self, text, bracket_pair):
        """
        移除字符串 text 当中的某类括号，以及括号内的内容
        （没用正则写挺蠢的）
        """
        left = bracket_pair[0]
        right = bracket_pair[1]
        depth = 0
        left_marks = []
        right_marks = []
        for i in range(len(text)):
            if text[i] == left:
                if depth == 0:
                    left_marks.append(i)
                depth += 1
            if text[i] == right:
                depth -= 1
                if depth == 0:
                    right_marks.append(i)
        if depth != 0 or len(left_marks) != len(right_marks):
            return text
        left_marks.append(len(text))
        right_marks.insert(0, -1)
        new_text = ''
        for i in range(len(left_marks)):
            new_text += text[right_marks[i] + 1: left_marks[i]]
        return new_text