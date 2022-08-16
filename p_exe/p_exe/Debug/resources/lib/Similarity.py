#20200314
#why
#相似度计算，分成三类：1.都不是专业领域内的词;2.两个词都是专业领域内的词;3.一个是专业领域，另一个是非专业领域
from lib.cilin import *
from pyhanlp import *


cs = CilinSimilarity()
#cs是cilin类的一个实例，目的为了调用它里面的函数
# sim1 = cs.similarity(w1, w2)
# sim2 = cs.sim2013(w1, w2)
# sim3 = cs.sim2016(w1, w2)


def isConsistent(s1,s2):#关系是否相同
    if s1==s2:
        return 1
    else:
        return 0

def similar(s1,s2):#相似度计算（分三类）
    if s1==s2:
        return 1
    elif isExist(s1) and isExist(s2):
        if s1==s2:
            return 1
        else:
            return 0
    elif isExist(s1) or isExist(s2):
        return 0
    else: #非领域的且不相等用“基于同义词词林的词语相似度计算方法”计算
        return cs.similarity(s1, s2)

def isExist(s):#判断是否属于领域类词
    if word_count3(s)>0: #如果是领域中的词
        return True
    else:
        return False

def word_count3(s):#语料库词频计算：对600个标准答案进行分词后词频的计算
    model_path = "data/dictionary/领域/领域.txt"
    with open(model_path, "r",encoding='UTF-8') as fr:
        while True:
            data = fr.readline()[:-1].split(' ')# 一行一行的读
            if len(data) >1: #若未读完
                if s == data[0]: #如果等于领域中的词
                    return (int)(data[2]) #返回领域中该词出现的次数
            else:
                break
    return 0



if __name__ == '__main__':
    s1 = "香蕉"
    s2 = "指"
    print(isExist(s1))
    print(isExist(s2))
    print(similar(s1,s2))
    print(cs.similarity(s1, s2))