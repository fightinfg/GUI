#20200331
#why
#关系词对预处理

from pyhanlp import *
import numpy as np

def classification(s):#文本分类
    with open('data/dictionary/用于分类的词库/分类.txt','r',encoding="utf-8") as fr:
        words = fr.read().splitlines()
        fr.close()
    for word in words:
        if word in s:
            return "A"     #A类
    return "B"            #B类



def predone1(s):  # 标准答案的处理（破折号，分号）、以及标记
    flag = False  # 是否有缩短原句
    flag1 = False  # 是否有破折号step4：将标准答案缩短成破折号之后的句子
    index1 = s.find("：")  # 检测句子中是否有冒号
    # 如果检索的字符串不存在，则返回-1，否则返回首次出现该子字符串时的索引。
    if index1 != -1:  # 若有，再检测冒号前是否有逗号或者句号
        if s[0:index1].find("，")!=-1 or s[0:index1].find("。")!=-1:#有
            if FirstIsDash(s,"——"):
                flag1 = True
        else:#无
            flag = True
            s = s[index1+1::] # 用分号之后的句子
    else:#无冒号
        if FirstIsDash(s,"——"):
            flag1 = True
    if flag1:
         flag = True
         s = s[s.find("——")+2::] # 用破折号之后的句子

    if "分为" in s:
        index = s.find("分为")
        if '。' not in s[:index] and '；' not in s[index]: # 句号，分号未出现在”分为“之前
            if s[:index].count('，')<2: # 若前面语句很少，只保留“分为”后面的成分
                s = s[index+2:]

    return s,flag

def FirstIsDash(s,ps):#检测句子第一个标点符号是否为ps
    #常用标点符号
    Punc = ["。","？","！","，","、","；","：","“","”","‘","’","—","（","）"]
    index = s.find(ps)
    if index ==-1:
        return False
    else:
        for i in range(0,index):
            if s[i] in Punc:
                return False
    return True

def DFS(word_array,index,weight,level):#赋初始层级 参数word集，开始的位置，权重集，层级
    for idx in range(0,len(word_array)):
        if word_array[idx].HEAD.ID == index: #若index=0,先找到句子的head，将head.id为0的作为第一层，之后将这个词的id作为要寻找的下一层head.id,若找不到返回一层作为节点再找。
            weight[0][idx] = level
            '''
            print("word_array[idx].HEAD.ID",word_array[idx].HEAD.ID)
            print("idx", idx)
            print("level",level)
            '''

            DFS(word_array,word_array[idx].ID,weight,level+1)
    return weight

def predone(s):#个别词汇的替换
    '''
    (1)个别词替换
    (2)删除末尾句号
    (3)去掉句中所有空格
    :param s:
    :return:
    '''
    a = ["或非","合理所","对逾期","按合同","将顾客","或以","中所","中的","部分为"]
    b = ["或者非","合理而","对于逾期","按照合同","把顾客","或者以","中而","当中的","部分是"]
    for i in range(0,len(a)):
        if a[i] in s:
            s = s.replace(a[i],b[i])

    punc = "。"
    if s[-1] in punc:
        s = s.rstrip(s[-1])
        # s[-1]指最后一个
        # rstrip() 删除 string 字符串末尾的指定字符（默认为空格）.

    s = s.replace(" ", "")#去掉空格

    T = []#去掉注释
    tmp = ""
    flag = False
    for i in range(0,len(s)):
        # 当遇到）则显示（）内注释完成，把字符串放数组T中
        if s[i]=="）" or s[i]==")":
            tmp += s[i]
            # print("1tmp:"+tmp+"\n")
            flag = False
            T.append(tmp)
            # print(T)
            tmp = ""
        if s[i]=="（"or s[i]=="(":
            # if (s[i+1]>"a" and s[i+1]<"z") or (s[i+1]>"A" and s[i+1]<"Z"):
            flag = True
        if flag:
            tmp += s[i]
            # print(i)
            #  print("2tmp:" +tmp + "\n")
    #print(T)

    for item in T:
        #print(item)
        s = s.replace(item,"")

    # 去掉在……中,就什么言,一般来说
    if FirstIsDash(s,"，"): # 检测句子第一个标点符号是否为逗号
        index = s.find("，")
        if len(s[0:index])<8:
            if s[0] == "在" and s[index-1]=="中":
                s = s[index+1:]
            elif s[index-2:index]=="而言":
                s = s[index+1:]
    
    if s.find("一般来说")!=-1: 
        s = s.replace("一般来说，","")

    return s

def Preprocessing2(s):#只将标点符号去掉
    sentence = HanLP.parseDependency(s)
    #print(sentence)
    word_array = sentence.getWordArray()
    #print(word_array)
    # ID序号,LEMMA依存词, DEPREL关系, HEAD.LEMMA核心词,CPOSTAG 当前词语的词（粗粒度）,POSTAG 当前词语的词性（细粒度）

    weight = np.zeros((1, len(word_array)))  # 层级创建
    weight = DFS(word_array, 0, weight, 1)  # 层级初始化

    Negative_words = open_dict("data/dictionary/否定词/Negative_Words.txt")#否定词词典的读取
    count = 0# 否定词个数提取
    words=[]
    for word in word_array:
        # print(word)
        if word.LEMMA in Negative_words:
            count = count + 1
        # print("%s --(%s)--> %s" % (word.LEMMA, word.DEPREL, word.HEAD.LEMMA))
        words.append({'LEMMA': word.LEMMA,'CPOSTAG':word.CPOSTAG, 'DEPREL': word.DEPREL, 'HEAD.LEMMA': word.HEAD.LEMMA,'HEAD.CPOSTAG': word.HEAD.CPOSTAG,'ID':word.ID,'ID2':word.HEAD.ID})
    
    TYPE_DEPREL = ["标点符号"]
    DEL_i =[]
    for i in range(0,len(words))[::-1]:  
        # print(words[i])
        if words[i]["DEPREL"] in TYPE_DEPREL:
            DEL_i.append(i)


    #print("weight0", weight)
    #print(DEL_i)
    for idx in DEL_i:
        words.pop(idx)
        weight = DFS(word_array,idx+1,weight,weight[0][idx-1]) #更新words后，word_array也更新，对此时的权重更新

    #print(word_array)
    '''
    print("words",words)
    print("count",count)
    print("weight",weight)
    '''



    return words,count,weight

def open_dict(path):#dict格式文件读取
    dictionary = open(path, 'r', encoding='utf-8-sig')
    dict = []
    for word in dictionary:
        word = word.strip('\n')
        dict.append(word)
    return dict

def Preprocessing3(s):#关系词对预处理
    #s="固定货架和移动货架"
    sentence = HanLP.parseDependency(s) # 使用HanLP时,句法分析
    #print("sentence",sentence)
    word_array = sentence.getWordArray() # 直接拿到数组，任意顺序或逆序遍历
    #print("word_array",word_array)
    # ID序号,LEMMA依存词, DEPREL关系, HEAD.LEMMA核心词,CPOSTAG 当前词语的词（粗粒度）,POSTAG 当前词语的词性（细粒度）
    IDs = []# 介宾词典
    words=[] # 词的相关字典

    Negative_words = open_dict("data/dictionary/否定词/Negative_Words.txt")#否定词词典的读取
    count = 0# 否定词个数提取

    # 介宾关系ID提取
    for word in word_array:
        # print(word)
        if word.LEMMA in Negative_words: # 统计否定词
            count = count + 1
        # print("%s --(%s)--> %s" % (word.LEMMA, word.DEPREL, word.HEAD.LEMMA))
        words.append({'LEMMA': word.LEMMA,'CPOSTAG':word.CPOSTAG, 'DEPREL': word.DEPREL, 'HEAD.LEMMA': word.HEAD.LEMMA,'HEAD.CPOSTAG': word.HEAD.CPOSTAG,'ID':word.ID,'ID2':word.HEAD.ID})
        if word.DEPREL == "介宾关系":
            IDs.append(word.ID)  # 将介宾关系词的id加入ids数组内

    #print("words1",words)
    #print("IDs1",IDs)

    
    # 介宾关系处理:该介宾关系的核心词被当作某个关系的依存词时，将该某个关系的依存词改为该介宾关系的依存词！注意：应该按照ID进行查找，否则无法避免由于同一个词语带来的漏洞
    for id in IDs:
        for word in words:
            if word['ID'] == word_array[id-1].HEAD.ID:
                word['LEMMA'] = word_array[id-1].LEMMA
                word['CPOSTAG'] = word_array[id-1].CPOSTAG
                word['ID'] = word_array[id-1].ID

    #print("IDs2", IDs)

    # 关系词对中多余成分的删除
    # 1.删除关系类型：左附加关系、右附加关系、标点、介宾
    # 2.删除不包含词性：['n','d','r','q','a','v','m','t','x']
    Part_of_speech = ['n','d','r','q','a','v','m','t','x']
    TYPE_DEPREL = ["右附加关系","左附加关系","标点符号","介宾关系"]
    DEL_i =[] # 需要删除的词的编号
    for i in range(0,len(words))[::-1]:  
        if words[i]["DEPREL"] in TYPE_DEPREL or words[i]["CPOSTAG"] not in Part_of_speech:
            DEL_i.append(i)
    for idx in DEL_i:
        words.pop(idx)  # words执行删除

    #print("words2", words)


    # 并列关系处理
    # ID序号,LEMMA依存词, DEPREL关系, HEAD.LEMMA核心词,CPOSTAG 当前词语的词（粗粒度）,POSTAG 当前词语的词性（细粒度）
    tmp = []
    for word in words:
        # print(word)
        if word["DEPREL"] == "并列关系" and word['CPOSTAG'] == 'n' and word['HEAD.CPOSTAG'] == 'n':
            bl = word_array[word['ID']-1].HEAD #提取核心词
            if bl.DEPREL!="定中关系":
                tmp.append({'LEMMA':word['LEMMA'],'CPOSTAG':word['CPOSTAG'],'DEPREL':bl.DEPREL,'HEAD.LEMMA':bl.HEAD.LEMMA,'HEAD.CPOSTAG':bl.HEAD.CPOSTAG,'ID':word['ID'],'ID2':bl.HEAD.ID})
            elif bl.HEAD.CPOSTAG =='n':
                tmp.append({'LEMMA':word['LEMMA'],'CPOSTAG':word['CPOSTAG'],'DEPREL':bl.DEPREL,'HEAD.LEMMA':bl.HEAD.LEMMA,'HEAD.CPOSTAG':bl.HEAD.CPOSTAG,'ID':word['ID'],'ID2':bl.HEAD.ID})
    words.extend(tmp)

    #print("words3", words)
    
    #已经将核心词的关系与词放到并列关系内了，就删掉核心词？
    for i in range(0,len(words))[::-1]:  
        if words[i]["HEAD.LEMMA"]=="##核心##":
            #print("核心:",words[i])
            words.pop(i)

    #print("words4", words)
    
    # DEL_i =[]
    # for i in range(0,len(words))[::-1]:  
    #     if words[i]["DEPREL"] == "并列关系":
    #         DEL_i.append(i)
    # for idx in DEL_i:
    #     words.pop(idx)

    

    return words,count

def onlyAorB(s):#对标准答案的分词进行标点检测，若只有“、”或者只有“；”，重置之前的题目分类，将该类定义为A类题目；
    Punc = ["。","？","！","，","、","；","：","“","”","‘","’","—","（","）"]
    index1 = s.find("；")
    index2 = s.find("、")
    if index1 ==-1 and index2!=-1:
        aim = "、"
    elif index1 !=-1 and index2==-1:
        aim = "；"
    else:
        return False

    for subs in s:
        if subs in Punc and subs !=aim:
            return False
    return True


if __name__ == '__main__':

    # S = [
    #     "在仓储企业中，一般包括保管员、理货员、商品养护员等岗位。",
    #     "在仓库中，质量验收主要指物品外观检验，由仓库保管职能机构组织进行。",
    #     "在实践中，很多物流货运企业既不使用自己的汽车，也不租用别人的汽车，而是把货物运输交给专业的汽车承运人来完成，与其签订汽车货物运输合同，即运输外包。",
    #     "就功能而言，世界自由贸易区可分为以下类型：转口集散型；贸工结合、以贸为主型；出口加工型；保税仓储型。",
    #     "一般来说，保险人或其代理人现场查看的内容主要包括以下几点：对受损货物拍照，做好取证工作；了解被保险货物的基本情况，询问知情人，详细了解出险地点、时间、经过及原因，核查损失是否属于保险责任范围；对受损货物进行清点，确定损失范围、数量及损失程度，做好记录，编写检验报告，必要时可聘用专业技术人员鉴定。"
    # ]
    # for s in S:
    #     print("源：",s)
    #     print("改：",predone(s))
    #     print()
    # print(onlyAorB("就垛苫盖法；鱼鳞式苫盖法；固定棚架苫盖法；活动棚架苫盖法；隔离苫盖法"))
    '''
    "装卸搬运方式——按照装卸搬运作业对象，分为单件作业、集装作业、散装作业。",
        "ABC分析法，就是以某类库存物资品种数占物资品种数的百分数和该类物资金额占库存物资总金额的百分数大小为标准，将库存物资分为A、B、C三类，进行分级管理。"

    s="盘点方法可分为(sjjh快捷键就是)两类，一类(sj键就是)是人机盘点，一类是人工盘点。"
    print(predone(s))
    
    S = [
        "货架可以分为固定货架和移动货架。"
        #"盘点方法可分为两类，一类是人机盘点，一类是人工盘点。",
    ]
    for s in S:
        print("源：",s)
        print("改：",predone1(predone(s))[0])
        [s, flag1] = predone1(predone(s))
        print("改2：",Preprocessing2(s))
        #print()
    #print()
    '''

    s="固定货架和移动货架"
    Preprocessing3(s)