#20200322
#why
#关键词提取及权重的赋值
from lib.cilin import *
from lib.preprocess import *
from pyhanlp import *
import numpy as np

def KEYWORD2(s1,flag):#flag表示是否进行破折号删除等
    [set1,count1,level1] = Preprocessing2(s1)#答案，set1是关系词集，count1是否定词数，level1是词权重
    '''
    print("set1",set1)
    print("level1", level1)
    print("flag", flag)
    '''

    key_words = keyword4(set1, level1, flag)#flag表示是否进行破折号删除等
    #print("inKEYWORD2",key_words)
    # 出现次数大于3的关键词去掉
    for i in range(0,len(key_words))[::-1]:
        '''
        print(key_words[i],subcount(key_words[i], s1))
        货架 2
        货架 2
        ##核心## 0
        固定 1
        '''
        if(subcount(key_words[i], s1)) >= 3:
            key_words.pop(i)

    #print("key_word6",key_words)

    # 若标准答案提取不出关键词，且存在并列关系，并列关系的核心词和依存词均作为关键词。
    if len(key_words)==0:
        for item in set1:
            if item['DEPREL']=="并列关系":
                if item['LEMMA'] not in key_words:
                    key_words.append(item['LEMMA'])
                if item['HEAD.LEMMA'] not in key_words:
                    key_words.append(item['HEAD.LEMMA'])
    
    for i in range(0,len(key_words))[::-1]:
        if key_words[i]=="##核心##":
            key_words.pop(i)
    return key_words

def keyword4(SET,level,flag):
    #参数：SET是关系词集，level是词权重，flag表示是否进行破折号删除等
    #超男3：根据TF_IDF阈值设定进行筛选，并将同级同词性的进行挑选并加入关键词集合内，+并列关系的做处理+主谓关系处理
    stopWord1 = stopWord()
    level_list = {}
    key = []
    key_word = []
    for item in SET:
        '''
        print(item)
        print(item['LEMMA'],level[0][item['ID']-1])
        print(item['HEAD.LEMMA'],level[0][item['ID2']-1])
        '''
        # level是二维数组，只有第0行的，id从1开始所有要-1

        if (item['DEPREL'] == "主谓关系" and level[0][item['ID']-1]<=4 and level[0][item['ID2']-1]<=4 and flag==False):
            continue
        else:
            # ID序号,LEMMA依存词, DEPREL关系, HEAD.LEMMA核心词,CPOSTAG 当前词语的词（粗粒度）,POSTAG 当前词语的词性（细粒度）
            #print(item,level[0][item['ID']-1],level[0][item['ID2']-1])

            '''限定词包括
            冠词（article） 定冠词（DEFINITE ARTICLE），不定冠词（INDEFINITE ARTICLE），零冠词（ZERO ARTICLE)
            形容词性的物主代词限定词（POSSESSIVE PRONOUN DETERMINATOR），my，your，his，her，our，their，its.名词属格（POSSESSIVE NOUN），John's，my friend's.指示限定词（DEMONSTRATIVE DETERMINATOR），this，that，these，those，such.关系限定词（RELATIVE DETERMINATOR)，whose，which.疑问限定词（INTERROGATIVE DETERMINATOR），what，which，whose.不定限定词（INDEFINITE DETERMINATOR），no，some，any，each，every，enough，either，neither，all，both，half，several，many，much，(a) few，(a) little，other，another.
            数词（numeral） 基数词（CARDINAL NUMBER) 和序数词（ORDINAL NUMBER)倍数词（MULTIPLICATIVE NUMBER) 和分数词（FRACTIONAL NUMBER)
            量词（QUANTIFIER) a lot of，lots of，plenty of，a great deal of，a good deal of，a large amountof，a small amount of，a quantity of，a great number of，a good number of 等。
            '''

            if item['LEMMA'] not in stopWord1 and item['CPOSTAG'] != "d": # 依存词不在停用词里，且当前词的词性不是限定词
                if item['ID'] not in key:
                    if TF_IDF(item['LEMMA']):
                        tmp = level[0][item['ID']-1]
                        if level_list.__contains__(tmp):# 判断是否包含子串
                            level_list[tmp].append(item['CPOSTAG'])#某一词作为关键词的时候，记录它的层级以及词性
                        else: #否则令他的层级=当前词性
                            level_list[tmp] = [item['CPOSTAG']]
                        key.append(item['ID']) #记录关键词Id
                        key_word.append(item['LEMMA']) #记录关键词依存词
            # if item['ID2'] not in key and level[0][item['ID2']-1] !=2:
            if item['HEAD.LEMMA'] not in stopWord1 and item['HEAD.CPOSTAG'] != "d":# 核心词不在停用词里，且当前词的词性不是限定词
                if item['ID2'] not in key:
                    if TF_IDF(item['HEAD.LEMMA']):
                        tmp = level[0][item['ID2']-1]
                        if level_list.__contains__(tmp):
                            level_list[tmp].append(item['HEAD.CPOSTAG'])
                        else:
                            level_list[tmp] = [item['HEAD.CPOSTAG']]
                        key.append(item['ID2'])#记录核心词Id
                        key_word.append(item['HEAD.LEMMA'])#记录核心词依存词

    #print("level_list",level_list)
    #print("key_word1",key_word)

        for item in SET:
            if (item['DEPREL'] == "主谓关系" and level[0][item['ID']-1]<=4 and level[0][item['ID2']-1]<=4 and flag==False):
                continue
            else:
                if item['LEMMA'] not in stopWord1 and item['CPOSTAG'] != "d":
                    if item['ID'] not in key:
                        tmp = level[0][item['ID']-1]
                        if level_list.__contains__(tmp):
                            if item['CPOSTAG'] in level_list[tmp]:
                                key.append(item['ID'])
                                key_word.append(item['LEMMA'])
                if item['HEAD.LEMMA'] not in stopWord1 and item['HEAD.CPOSTAG'] != "d":
                    if item['ID2'] not in key:
                        tmp = level[0][item['ID2']-1]
                        if level_list.__contains__(tmp):
                            if item['HEAD.CPOSTAG'] in level_list[tmp]:
                                key.append(item['ID2'])
                                key_word.append(item['HEAD.LEMMA'])

    # ID序号,LEMMA依存词, DEPREL关系, HEAD.LEMMA核心词,CPOSTAG 当前词语的词（粗粒度）,POSTAG 当前词语的词性（细粒度）
    un_words1 = un_words()#非关键词读取
    andWords = []#并列词汇     
    del_words = []#并列词汇中需要剔除的词(剔除非关键词，)
    for item in SET:###并列处理
        # print(item)
        if item['DEPREL'] == "并列关系":
            andWords.append(item['HEAD.LEMMA'])
            andWords.append(item['LEMMA'])
            if item['LEMMA']  in un_words1 and item['HEAD.LEMMA']  in un_words1: # 若当前词（依存词）和核心词是非关键词汇
                del_words.append(item['LEMMA'])
                del_words.append(item['HEAD.LEMMA'])
            if item['ID'] in key and item['ID2'] not in key:# 若当前词（依存词）的id和核心词id不在关键词id里面
                if item['HEAD.LEMMA'] not in stopWord1:# 若核心词不是停用词
                    key.append(item['ID2'])
                    key_word.append(item['HEAD.LEMMA'])
            if item['ID2'] in key and item['ID'] not in key:# 若核心词id在关键词id里面，当前词（依存词）的id不在关键词id里面
                if item['LEMMA'] not in stopWord1:# 若当前词不是停用词
                    key.append(item['ID'])
                    key_word.append(item['LEMMA'])

    
    #并列词汇中需要剔除的词：
    for word in del_words:
        while word in andWords:
            andWords.remove(word)
    #print("key_word2", key_word)

    # 核心词是”分为“处理
    for item in SET:
        if item["HEAD.LEMMA"]=="分为":
            if item["CPOSTAG"]=="p":
                for item2 in SET:
                    if item2["ID2"] == item["ID"] and item2["LEMMA"] in key_word:
                        while item2["LEMMA"] in key_word:
                            key_word.pop(key_word.index(item2["LEMMA"]))
            else:
                if item["LEMMA"] in key_word and level[0][item['ID']-1] < level[0][item['ID2']-1]+2:
                    while item["LEMMA"] in key_word:
                        key_word.pop(key_word.index(item["LEMMA"]))

    #print("key_word3", key_word)

    # 单个字处理:若单个词的词性不是名词，剔除改关键词
    for item in SET:
        if len(item["LEMMA"])==1 and item['CPOSTAG']!="n" and key_word.__contains__(item["LEMMA"]):
            key_word.pop(key_word.index(item["LEMMA"]))
        if len(item["HEAD.LEMMA"])==1 and item['HEAD.CPOSTAG']!="n" and key_word.__contains__(item["HEAD.LEMMA"]):
            key_word.pop(key_word.index(item["HEAD.LEMMA"]))

    #print("key_word4", key_word)

    # 非关键词处理
    for idx in range(0,len(key_word))[::-1]:
        if key_word[idx] in un_words1 and (key_word[idx] not in andWords):
            key_word.pop(idx)

    #print("key_word5", key_word)

    return key_word

def stopWord():#停用词
    with open('data/dictionary/停用词/stopwords.txt','r',encoding="utf-8") as fr:
        stopWord = fr.read().splitlines()
        fr.close()
    return stopWord

def max_count():
    MAX = 0
    model_path = "data/dictionary/语料库/my_cws_model.txt"
    with open(model_path, "r",encoding='UTF-8') as fr:
        while True:
            data = fr.readline()[:-1].split(' ')
            if len(data) >1:
                if int(data[2])>MAX:
                    MAX = int(data[2])
            else:
                break
    return MAX

def TF_IDF(word):#TF_IDF的计算
    max1 = max_count()
    max2 = 818357166
    tf = float(word_count2(word))/float(max1)
    if tf==0:
        tf = 1.0/float(max1)
    idf = float(max2)/(word_count1(word)+1)
    tf_idf = tf*idf
    # return tf_idf
    if tf_idf < 0.084:
        return False
    else:
        return True

'''
语料库词频计算是什么 
'''
def word_count2(s):#语料库词频计算：对600个标准答案进行分词后词频的计算
    model_path = "data/dictionary/语料库/my_cws_model.txt"
    with open(model_path, "r", encoding='UTF-8') as fr:
        while True:
            data = fr.readline()[:-1].split(' ')
            if len(data) >1:
                if s == data[0]:
                    return data[2]
            else:
                break
    return "0"

def word_count1(s):#全网语料库词频计算
    # model_path = "data/dictionary/my_cws_model"
    model_path = "data/dictionary/全网语料库/全网语料库"
    HanLP.Config.CoreDictionaryPath = model_path + ".txt"  # unigram
    CoreDictionary = LazyLoadingJClass('com.hankcs.hanlp.dictionary.CoreDictionary')
    return CoreDictionary.getTermFrequency(s)

def un_words():#非关键词汇
    with open('data/dictionary/非关键词汇/非关键词汇.txt','r',encoding="utf-8") as fr:
        un_words = fr.read().splitlines()
        fr.close()
    return un_words

def subcount(sub,s):#查找字串数量
    return s.count(sub,0,len(s)+1)

def Participle(SET):#单纯分词（将句法分析分词的容器进行转变）
    words = []
    for item in SET:
        if words.__contains__(item['LEMMA'])==False:
            words.append(item['LEMMA'])
        # if words.__contains__(item['HEAD.LEMMA'])==False:
        #     if item['HEAD.LEMMA'] !="##核心##":
        #         words.append(item['HEAD.LEMMA'])
    return words

if __name__ == '__main__':
    '''
    s=[{'LEMMA': '货架', 'CPOSTAG': 'n', 'DEPREL': '主谓关系', 'HEAD.LEMMA': '分为', 'HEAD.CPOSTAG': 'v', 'ID': 1, 'ID2': 3},
       {'LEMMA': '可以', 'CPOSTAG': 'v', 'DEPREL': '状中结构', 'HEAD.LEMMA': '分为', 'HEAD.CPOSTAG': 'v', 'ID': 2, 'ID2': 3},
       {'LEMMA': '分为', 'CPOSTAG': 'v', 'DEPREL': '核心关系', 'HEAD.LEMMA': '##核心##', 'HEAD.CPOSTAG': 'ROOT', 'ID': 3, 'ID2': 0},
       {'LEMMA': '固定', 'CPOSTAG': 'v', 'DEPREL': '动宾关系', 'HEAD.LEMMA': '分为', 'HEAD.CPOSTAG': 'v', 'ID': 4, 'ID2': 3},
       {'LEMMA': '货架', 'CPOSTAG': 'n', 'DEPREL': '动宾关系', 'HEAD.LEMMA': '固定', 'HEAD.CPOSTAG': 'v', 'ID': 5, 'ID2': 4},
       {'LEMMA': '和', 'CPOSTAG': 'c', 'DEPREL': '左附加关系', 'HEAD.LEMMA': '货架', 'HEAD.CPOSTAG': 'n', 'ID': 6, 'ID2': 8},
       {'LEMMA': '移动', 'CPOSTAG': 'v', 'DEPREL': '定中关系', 'HEAD.LEMMA': '货架', 'HEAD.CPOSTAG': 'n', 'ID': 7, 'ID2': 8},
       {'LEMMA': '货架', 'CPOSTAG': 'n', 'DEPREL': '并列关系', 'HEAD.LEMMA': '货架', 'HEAD.CPOSTAG': 'n', 'ID': 8, 'ID2': 5}]
    level=[[2,2,1,2,3,5,5,4,2]]

    k = keyword4(s, level, False)#flag表示是否进行破折号删除等    
    '''
    s=[{'LEMMA': '固定', 'CPOSTAG': 'v', 'DEPREL': '核心关系', 'HEAD.LEMMA': '##核心##', 'HEAD.CPOSTAG': 'ROOT', 'ID': 1, 'ID2': 0},
       {'LEMMA': '货架', 'CPOSTAG': 'n', 'DEPREL': '动宾关系', 'HEAD.LEMMA': '固定', 'HEAD.CPOSTAG': 'v', 'ID': 2, 'ID2': 1},
       {'LEMMA': '和', 'CPOSTAG': 'c', 'DEPREL': '左附加关系', 'HEAD.LEMMA': '货架', 'HEAD.CPOSTAG': 'n', 'ID': 3, 'ID2': 5},
       {'LEMMA': '移动', 'CPOSTAG': 'v', 'DEPREL': '定中关系', 'HEAD.LEMMA': '货架', 'HEAD.CPOSTAG': 'n', 'ID': 4, 'ID2': 5},
       {'LEMMA': '货架', 'CPOSTAG': 'n', 'DEPREL': '并列关系', 'HEAD.LEMMA': '货架', 'HEAD.CPOSTAG': 'n', 'ID': 5, 'ID2': 2}]
    level=[[1.,2.,4.,4.,3.]]
    k = keyword4(s, level, False)




    print(TF_IDF(""))