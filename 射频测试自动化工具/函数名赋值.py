def dec(funa):
    def wrapper(*args,**kwargs):
        print('我要开始计算函数了~')
        #执行实际函数
        funa(*args,**kwargs)
        print('函数执行结束~')
    return wrapper

def cal(x,y):
    print(f'{x}+{y}={x+y}')

d=dec(cal)
d(200,50)