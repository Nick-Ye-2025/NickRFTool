import itertools
def is_leap_year(year):
    if year%3200==0:
        return False
    elif year%400==0:
        return True
    elif year%100==0:
        return False
    elif year%4==0:
        return True
    return False
# print(is_leap_year(2100))

#判断实参是否真实数据
def is_valid_data(year,month,day):
    print('Month的判断结果是:',month<1 or month>12)
    if month<1 or month>12:
        return False
    month_days={
        1:31,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31,
        
    }
    if is_leap_year(year):
        month_days[2]=29
    else:
        month_days[2]=28
    print('Day的判断结果是:',1<=day<=month_days[month])
    print('*'*10)
    return 1<=day<=month_days[month]

def get_valid_data(num1,num2,num3):
    data=[]
    #peimutations返回元组数据
    for i in itertools.permutations((num1,num2,num3)): 
        #可迭代对象拆包，当右侧可迭代对象的元素数量与左侧变量数量匹配时，自动按顺序赋值。
        year,month,day=i
        print(i)
        if is_valid_data(year,month,day):
            data.append(i)
    # print(data)
    return data

if __name__ == '__main__':
    print('测试:',get_valid_data(2,7,29))