                                                                                                                                                                                                                       # coding: utf-8
import sys
import codecs
import math
import copy
import re
import nltk
from log import *
from product import Product
from parameters import *
from nltk.corpus import wordnet as wn
from nltk.stem.lancaster import LancasterStemmer
from nltk.stem import WordNetLemmatizer
import xlrd

reload(sys)
sys.setdefaultencoding('utf8')




##################################################################################
#去停用词
##################################################################################
def deleteStopWords(stopwords,words_list):
    result = []
    for word in words_list:
        word = word.strip()
        word = word.lower()
        if word not in stopwords:
            result.append(word)
    return result


##################################################################################
#英文词词形还原
##################################################################################
def wordLemmatizer(wordnet_lemmatizer,words_list):
    result = []
    for word in words_list:
        word = word.strip()
        word = word.lower()
        word=wordnet_lemmatizer.lemmatize(word)
        result.append(word)
    return result

##################################################################################
#英文词词干化
##################################################################################
def stemWord(words_list):
    result = []
    for word in words_list:
        word = word.strip()
        word = word.lower()
        aa = wn.morphy(word)
        if aa==None:#我发现词干化会出现返回为空的情况
            result.append(word)
        else:
            result.append(aa)
    return result

##################################################################################
#分句
##################################################################################
# 设置分句的标志符号；可以根据实际需要进行修改
#cutlist = ".!！？;]()".decode('utf-8')
cutlist = ".!！？".decode('utf-8')

# 检查某字符是否分句标志符号的函数；如果是，返回True，否则返回False
def FindToken(cutlist, char):
    if char in cutlist:
        return True
    else:
        return False
    
# 进行分句的核心函数
def Cut(cutlist, lines):  #参数1：引用分句标志符；参数2：被分句的文本，为一行中文字符
    l = []  # 句子列表，用于存储单个分句成功后的整句内容，为函数的返回值
    line = []  # 临时列表，用于存储捕获到分句标志符之前的每个字符，一旦发现分句符号后，就会将其内容全部赋给l，然后就会被清空
    p = 0;
    start = 0;
    for i in lines:  #对函数参数2中的每一字符逐个进行检查 （本函数中，如果将if和else对换一下位置，会更好懂）
        if FindToken(cutlist, i):  # 如果当前字符是分句符号
            if start == p:
                p += 1
                start = p
                continue
            # line.append(i)          #将此字符放入临时列表中
            l.append(''.join(line))  # 并把当前临时列表的内容加入到句子列表中
            start = p + 1
            line = []  # 将符号列表清空，以便下次分句使用
        else:  # 如果当前字符不是分句符号，则将该字符直接放入临时列表中
            line.append(i)
        p += 1;
    if start < len(lines):
        l.append(''.join(line))
    return l



def sentenceSplite(product_summary):
    #返回的句子列表
    sentences_list=[]
     
    # 如果是空行,则去掉空行
    if product_summary.count('\n')==len(product_summary):
        return
        
    sentences_from_summary=product_summary.split("\n")
    for sentence in sentences_from_summary:
        if sentence!="":
            #分句，因为summary里边有可能一段是多句话
            lines = Cut(list(cutlist), list(sentence.decode('utf-8', 'ignore')))
            for line in lines:
                line=line.strip()# 去掉首尾的空白
                if line=="" or line==None:
                    continue
                line = re.sub('[^A-Za-z]', ' ', line)
                line = line.strip()
                line = re.sub(r"\s{2,}", " ", line)
                sentences_list.append(line)
                    
    return sentences_list




##################################################################################
#对产品描述进行预处理
##################################################################################
def summaryPreprocess(textPath):
    product_dic = {}

     #从 excel表里边读取数据
    workbook = xlrd.open_workbook(textPath)
    sheet = workbook.sheet_by_index(0) # sheet索引从0开始
    n_row=sheet.nrows
    
    #为了调试程序使用
    #n_row=1

    # 获取nltk的停用词表
    from nltk.corpus import stopwords
    stoplist = stopwords.words('english')


    #词性还原对象,这里发现词性还原的效果可能还没有词干化的效果好
    wordnet_lemmatizer = WordNetLemmatizer()

    for i in range(0, n_row):
        product_name=sheet.cell(i,0).value.encode('utf-8')
        product_summary=sheet.cell(i,1).value.encode('utf-8')

        #先分句试试----刘春改进的地方
        new_sentences_list=[]
        sentences_list=sentenceSplite(product_summary)
        
        for sentence in sentences_list:
            #分词
            words_list = nltk.word_tokenize(sentence)
            #writelog(words_list)
        
            #词性判断，保留动词，名词，形容词
            words_list_tag = nltk.pos_tag(words_list)
            num_word=len(words_list_tag)
            keeped_words_list=[]
            for j in range(0,num_word):
                if words_list_tag[j][1] in ("NN","NNS","NNP","NNPS","VB","VBD","VBP","VBZ","VBG","VBN","JJ"):
                    keeped_words_list.append(words_list_tag[j][0])
            #writelog(keeped_words_list)
        
            #去停用词
            words_list_delstopword = deleteStopWords(stoplist, keeped_words_list)
            #writelog(words_list_delstopword)
        
            #词干化
            new_words_list=stemWord(words_list_delstopword)
            #new_words_list = wordLemmatizer(wordnet_lemmatizer,words_list_delstopword)
            #writelog(new_words_list)
            
            #进一步过滤只有一个字母的单词
            newer_words_list=[]
            for word in new_words_list:
                if len(word)>1:
                    newer_words_list.append(word)
                    
            #过滤去停用词之后，只有一个词或者为空的句子
            if len(newer_words_list)<=1:
                continue
            
            #去掉同一个产品内相同的句子,也即过滤无用词之后，剩下的词相同
            if isExist(newer_words_list,new_sentences_list)==True:
                continue
            
            new_sentences_list.append(newer_words_list)

        product = Product(i, product_name, "",new_sentences_list)
        product_dic[i] = product
        
        
    return product_dic 


def isExist(sentence_words_list,setences_list):
    for sentence in setences_list:
        str_sentence_a=" ".join(sentence)
        str_sentence_b=" ".join(sentence_words_list)
        if str_sentence_a==str_sentence_b:
            return True
    return False

##################################################################################
#提取特征
##################################################################################
def featureExtractionByCollocations(product_dic):
    import nltk
    from nltk.collocations import *
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    features_supp_dic={}
    for (product_id, product) in product_dic.items():
        product_sentences_list=product.getWordsList()
        #一个产品的bigram列表
        #product_bigram_list=[]
        for sentence in product_sentences_list:
            finder = BigramCollocationFinder.from_words(sentence,window_size = 5)
            bigram_dic=finder.ngram_fd
            #bigram_list = finder.score_ngrams(bigram_measures.raw_freq)
            for (bigram,freq) in bigram_dic.items():
                #print bigram,freq
                #if bigram[0] not in product_bigram_list:
                #    product_bigram_list.append(bigram[0])
                if bigram in features_supp_dic.keys():
                    features_supp_dic[bigram]+=freq
                else:
                    features_supp_dic[bigram]=freq
            
        #统计各个bigram在各个产品中出现的频率
##        for bigram in product_bigram_list:
##            if bigram in features_supp_dic.keys():
##                features_supp_dic[bigram]+=1
##            else:
##                features_supp_dic[bigram]=1
    return features_supp_dic



##################################################################################
#合并使用相同单词，但是词序不同的特征
##################################################################################    
def mergeSamePhraseWithDiffOrder(features_supp_dic):
    num_featres=len(features_supp_dic)
    features_supp_list=[[] for i in range(0, num_featres)]
    i=0
    for (feature, supp) in features_supp_dic.items():
        features_supp_list[i].append(feature)
        features_supp_list[i].append(supp)
        i+=1
        
    #print   len(features_supp_dic)  
    i=num_featres-1
    while i>0:
        for j in range(0, i):
            set_a=set(features_supp_list[i][0])
            set_b=set(features_supp_list[j][0])
            inter_set=set_a-set_b
            if len(inter_set)==0:
                features_supp_list[j][1]+=features_supp_list[i][1]
                features_supp_list.pop(i)
                break
               
        i=i-1
    #print len(features_supp_list)  
    return features_supp_list

            
        
##################################################################################
#过滤低频的特征
##################################################################################    
def filterLowFrequency(features_supp_list):
    print "old features list length is:", len(features_supp_list)
    new_features_supp_list=[]
    for item in features_supp_list:
        if item[1]>3:
            new_features_supp_list.append(item)
    print "new features list length is:", len(new_features_supp_list)
    return new_features_supp_list
             


##################################################################################
#根据同义词合并特征
##################################################################################     
def getSynset(word):
    from nltk.corpus import wordnet as wn
    result=[]
    for synset in wn.synsets(word):
        synset_words=synset.lemma_names()
        for word in synset_words:
            if word not in result:
                result.append(word)
    return result

def isSynset(feature_a, feature_b):
    synset_a_0=getSynset(feature_a[0])
    synset_a_1=getSynset(feature_a[1])
    if (feature_b[0] in synset_a_0 and feature_b[1] in synset_a_1) or (feature_b[0] in synset_a_1 and feature_b[1] in synset_a_0):
        return True
    else:
        return False
     
     
def groupBySynset(features_supp_list):
    print "len of feature list:",len(features_supp_list)
    group_list=[]
    num_features=len(features_supp_list)
    for i in range(0,num_features):
        #print "current i:",i
        find=False
        for group in group_list:
            for menmber_id in group:
                if isSynset(features_supp_list[i][0], features_supp_list[menmber_id][0]):
                    group.append(i)
                    find=True
                    break
            if find==True:
                break
        if find==False:
            new_group=[]
            new_group.append(i)
            group_list.append(new_group)
            
    print "len of group list:",len(group_list)
    writelog("len of group list:{}".format(len(group_list)))
    #对group按照支持度进行排序
    new_group_list=[]
    for group in group_list:
        new_group_count_pair=[]
        new_group_count_pair.append(group)
        total_count=0
        for menmber_id in group:
            total_count+=features_supp_list[menmber_id][1]
        new_group_count_pair.append(total_count)
        new_group_list.append(new_group_count_pair)
    sorted_group_list=sorted(new_group_list,key=lambda p:p[1],reverse=True)
        
    for item in sorted_group_list:
        print "*********************"
        writelog("*********************")
        for menmber_id in item[0]:
            print features_supp_list[menmber_id][0]
            str_words=" ".join(features_supp_list[menmber_id][0])
            str_words+=":  "
            str_words+=str(features_supp_list[menmber_id][1])
            writelog(str_words)
    return group_list



#########################################################################################
# main
#########################################################################################
if __name__=="__main__":
    product_dic=summaryPreprocess(path+"data\\antivus\\Antivirus_new_new_selected_100.xls")
    features_supp_dic=featureExtractionByCollocations(product_dic)
    features_supp_list=mergeSamePhraseWithDiffOrder(features_supp_dic)
    new_features_supp_list=filterLowFrequency(features_supp_list)
    group_list=groupBySynset(new_features_supp_list)
    #print group_list
    


