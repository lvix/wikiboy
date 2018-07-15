from datetime import datetime 
import hashlib 
import random 


class DecisionMaker:
    """
    自动决策者的类定义，包含两个简单函数
     """

    def decide(self, choices):
        
        if not choices:
            return '输入错误哟'

        question = ''
        qmark = ''

        # 如果问题和第一个选项没有被隔开，则尝试分离
        if choices[0][-1] in '?？吗':
            question = choices[0] 
            if question[-1] not in '?？':
                question += '?'
            choices.pop(0)
        elif '?' in choices[0]:
            qmark = '?'
        elif '？' in choices[0]:
            qmark = '？'

        if len(qmark) > 0:
            # 分离
            question = choices[0].split(qmark)[0] + '?'
            choices[0] = choices[0].split(qmark)[1] 
        
        if len(choices) < 2:
            return '请输入两个以上的选项'

        if len(question) > 0:
            question = '\n' + question  

        deci_str = '决策结果:' + question + '\n'
        sum_list = []
        for ch in choices:
            sum_list.append(self.gen_checksum(ch, question=question))
        for i in range(len(choices)):
            deci_str += '{} ： {:.2%}\n'.format(choices[i], sum_list[i]/sum(sum_list))

        return deci_str

    def gen_checksum(self, plaintext, question=''):
        """
        进行 checksum 的运算，用于决策
        :param plaintext(str): 用于计算的字符串
        :param question(str): 所需要决策的问题
        :return chksum: 计算后的结果 
         """
        dt = datetime.utcnow().strftime('%Y%m%d%H')
        h = hashlib.md5((plaintext + dt + question).encode('utf-8')).hexdigest()
        chksum = ord(h[0]) + ord(h[2]) + ord(h[-1]) + ord(h[-3]) + ord(random.choice(list(h)))
        return chksum
        