pwd=int(input("请输入密码："))
if pwd<0:
    raise Exception('密码不能为负数')
if len(str(pwd))>=6:
    print('密码长度正确')
else:
    ex=Exception('密码长度不足6位')
    raise ex
print('您输入的密码为:',pwd)
print(type(pwd))
