#多重嵌套的调用
def dec(funa):
    def outer():
        print('我是外层函数~')
        def inner(*args,**kwargs):
            print('我是内层函数，我要开始计算函数了~')
            #执行实际函数
            funa(*args,**kwargs)
            print('内层函数执行结束~')
        return inner
    return outer

def cal(x,y):
    print(f'{x}+{y}={x+y}')

d=dec(cal)
d()(200,50)

# def dec(funa):
#     def outer():
#         print('外层')
#         def inner():
#             print('内层')
#             funa()
#             print('内层结束')
#         return inner
#     return outer

# def aa():
#     print('我是funa')

# d=dec(aa)
# d()()