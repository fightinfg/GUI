'''
生成语料库的配置文件
'''
from collections import Counter
f = open("语料库.txt",encoding='utf-8')

lines = f.read().splitlines()

f.close()

result = Counter(lines).items()

f = open('词库.txt','w',encoding='utf-8')
for k,v in result:
    f.write(""+(str)(k)+' n '+(str)(v)+'\n')
f.close()