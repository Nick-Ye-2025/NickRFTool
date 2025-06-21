def ten2two(x):
    if x==0:
        return '0'
    binary=''
    while x>0:
        print('被除前的x:',x)
        binary=str(x%2)+binary
        x=x//2
        print('被除后的x:',x)
    return binary
print(ten2two(10))