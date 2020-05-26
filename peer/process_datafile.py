n={}
total={}
with open('size.txt','r') as file:
    for f in file:
        str = f.split(',')
        temp = str[5].split('\n')
        str[5] = temp[0]
        if str[1] not in n:
            n[str[1]] =[]
            n[str[1]].append(str[5])
            total[str[1]] = int(str[5])
        else:
            n[str[1]].append(str[5])
            total[str[1]] += int(str[5])

m = len(n)
Tb = m*int(n[1])
data = open('data.txt','w')
data.write(f'n      eta     s%\n')
with open('output.csv','w') as file:
    for l in n:
        temp = f"{l}"
        for x in n[l]:
            temp = temp + ',' + x
        var = (1- (int(l)*1.0/m))*100
        temp=temp + f',{total[l]},{var}\n'
        file.write(temp)
        eta = m*1.0/int(l)
        data.write(f'{l}    {eta}     {var}\n')
