from bs4 import BeautifulSoup
import requests
import json
import pprint


class YDict:
    url_prefix = 'http://m.youdao.com/dict?le=eng&q={}'

    def __init__(self, local_db=None):
        self.result = None
        self.session = None
        self.local_db = None

    def query_basic(self, keyword):
        url = self.url_prefix.format(keyword)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')

        try:
            empty_content_list = soup.select('p[class="empty-content"]')
            if len(empty_content_list) > 0:
                failing_result = {
                    'error': 404,
                    'message': 'no definition',
                }
                return failing_result

            result = {}

            cel = soup.select('div#ce')
            ce = cel[0] if len(cel) > 0 else None
            if ce:
                result['ce_text'] = self.neet_text(ce)
                return result 

            ecl = soup.select('div#ec')
            ec = ecl[0] if len(ecl) > 0 else None
            if ec:
                # 基本信息
                # 单词
                result['word'] = ec.select('h2 > span')[0].get_text().strip()
                # 音标
                phonetic_list = ec.select('span[class="phonetic"]')

                if len(phonetic_list) == 0:
                    result['phonetic'] = None
                elif len(phonetic_list) == 1:
                    result['phonetic'] = phonetic_list[0].get_text().strip()
                elif len(phonetic_list) == 2:
                    phonetic_dict = {}
                    for p in phonetic_list:
                        parent_str = p.parent.get_text().strip()
                        if '英' in parent_str:
                            phonetic_dict['british'] = p.get_text().strip()
                        elif '美' in parent_str:
                            phonetic_dict['american'] = p.get_text().strip()
                    if len(phonetic_dict) == 0:
                        result['phonetic'] = self.neet_text(phonetic_list[0].parent.parent)
                    else:
                        result['phonetic'] = phonetic_dict
                # 中文解释
                cndefl = ec.select('ul > li')

                result['definitions'] = {}
                for i in range(len(cndefl)):
                    result['definitions'][i] = self.neet_text(cndefl[i])
            return result
        except Exception as e:
            failing_result = {
                'error': 500,
                'message': e,
            }
            return failing_result

    def query_colllins(self, keyword):
        url_prefix = 'http://dict.youdao.com/w/eng/{}'
        url = url_prefix.format(keyword)
        result = {}
        try:
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'lxml')

            collinsl = soup.select('div#collinsResult')
            if len(collinsl) < 1:
                result = {
                    'error': 404,
                    'message': 'no definition'
                }
                return result
            collins = collinsl[0]
            # 单词
            result['word'] = self.neet_text(
                collins.select('span[class="title"]')[0])

            # 发音
            phonel = collins.find_all('em', class_="phonetic")
            phonetic = self.neet_text(phonel[0]) if len(phonel) > 0 else None
            if phonetic is None:
                phonel = collins.select('p', class_="collins-intro")
                phonetic = self.neet_text(
                    phonel[0]) if len(phonel) > 0 else None
            result['phonetic'] = phonetic

            # 变形
            formsl = collins.select('span[class="additional pattern"]')
            forms = self.neet_text(formsl[0]) if len(formsl) > 0 else None
            result['forms'] = forms

            # 主要解释
            definitions = {}
            wtcon = collins.find('div', class_="wt-container")
            def_ul = wtcon.select('ul')[0]

            def_list = def_ul.select('li')
            for i in range(len(def_list)):
                def_item = {}
                li = def_list[i]

                # 英英释义
                defini = self.neet_text(
                    li.select('div[class="collinsMajorTrans"] > p')[0])
                defini.replace('\'\'', '')
                def_item['definition'] = defini

                # 例句
                examples = li.select('div[class="examples"] > p')
                if len(examples) == 2:
                    example_sentence = self.neet_text(examples[0])
                    example_trans = self.neet_text(examples[1])
                    def_item['example'] = {
                        'sentence': example_sentence,
                        'trans': example_trans,
                    }
                definitions[i] = def_item
            result['definitions'] = definitions
            return result
        except Exception as e:
            failing_result = {
                'error': 500,
                'message': e,
            }
            return failing_result

    @staticmethod
    def neet_text(soup):
        return ' '.join(soup.get_text().strip().split())

    def query(self, keyword):
        self.result = self.query_colllins(keyword)
        if 'error' in self.result:
            self.result = self.query_basic(keyword)
            return self.parse_basic()
        return self.parse()

    def parse(self):
        parse_str = ''
        if self.result is not None:
            res = self.result
            if 'error' in res:
                parse_str += 'error: {}\nmessage: {}\n'.format(res.get('error', None), res.get('message', None))
                return parse_str
            else:
                word = res.get('word')
                phonetic = res.get('phonetic', None)
                forms = res.get('forms', None)
                parse_str += word + ' '
                if phonetic :
                    parse_str += phonetic + ' '
                if forms:
                    parse_str += forms + ' '
                parse_str += '\n'
                defs = res.get('definitions', None)
                for i, d in defs.items():
                    defi = d['definition']
                    example_str = ''
                    if 'example' in d:
                        sentence = d['example'].get('sentence', None)
                        trans = d['example'].get('trans', None)
                        if sentence:
                            example_str = '\n例: {}\n    {}'.format(
                                sentence, trans)

                    parse_str += '\n{}. {}{}\n'.format(i+1, defi, example_str)
                return parse_str
        return '还没有查询结果'

    def parse_basic(self):
        parse_str = ''
        if self.result is not None:
            res =self.result 
            if 'error' in res:
                parse_str += 'error: {}\nmessage: {}\n'.format(res.get('error', None), res.get('message', None))
            elif 'ce_text' in res:
                return res['ce_text']
            else:
                word = res.get('word')
                if word:
                    parse_str += word + ' '
                else:
                    return 'error: {}\nmessage: {}\n'.format(404, 'no definition')
                phonetic = res.get('phonetic', None)
                if phonetic is not None:
                    if isinstance(phonetic, dict) and 'phonetic_dict' in phonetic:
                        if 'britsh' in phonetic['phonetic_dict']:
                            parse_str += '英 '+ phonetic['phonetic_dict'].get('british') + ' '
                        if 'american' in phonetic['phonetic_dict']:
                            parse_str += '美 '+ phonetic['phonetic_dict'].get('american') + ' '
                    else:
                        parse_str += phonetic + ' '

                definitions = res.get('definitions')
                if definitions is not None:
                    for k, v in definitions.items():
                        parse_str += v + '\n'
            return parse_str
        return '还没有查询结果'

def main():
    yd = YDict()
    print(yd.query('slander'))
    print(yd.query('t-rex'))
    print(yd.query('xenophobic'))
    print(yd.query('adfbbkabiug'))
if __name__ == '__main__':
    main()
