n={}
total={}
with open('query_latency','r') as file:
    for f in file:
        str = f.split(' ')
        temp = str[1].split('\n')
        str[1] = temp[0]
        if str[0] not in n:
            n[str[0]] = 0
        n[str[0]] += float(str[1])

file = open("latency_data.txt",'a')
file.write(f'n     latency\n')
for l in n:
    print(l, ' ',n[l])
    file.write(f'{l}       {n[l]/10}\n')

file.close()