'''
生成器与内存管理
用生成器实现斐波那契数列，支持无限生成或指定长度
'''
data=[]
#1,1,2,3,5,8,13
def funa(n):
    if n<=1:
        return n
    else:
        return funa(n-1)+funa(n-2) #n为2的时候，funa(1)+funa(0)
for i in range(1,11):
    data.append(funa(i))
print(data)