def is_leap_year(year):
    if year%3200==0:
        return False
    if year%400==0:
        return True
    if year%100==0:
        return False
    if year%4==0:
        return True
    return False

def is_valid_data(year,month,day):
    if month<1 or month>12:
        print('Month-False:',month)
        return False
    month_days={
        1:31,3:31,5:31,7:31,8:31,10:31,12:31,
        4:30,6:30,9:30,11:30,
        2:29 if is_leap_year(year) else 28
    }
    if day<1 or day>month_days[month]:
        print('Day-False')
        return False
    return True
 
def get_valid_data(num_1,num_2,num_3):
    data=[]
    permutations=[
        (num_1,num_2,num_3),
        (num_1,num_3,num_2),
        (num_2,num_1,num_3),
        (num_2,num_3,num_1),
        (num_3,num_2,num_1),
        (num_3,num_1,num_2),
    ]
    for i in permutations:
        num_1,num_2,num_3=i
        if is_valid_data(num_1,num_2,num_3):
            data.append(i)
    return data

if __name__=='__main__':
    print(get_valid_data(2,7,29))