import json
import collections
from pathlib import Path
import shutil
k={}
n={}
total={}

def keys_exists(element, *keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

with open('size.txt','r') as file:
    print("parsing file ....")
    for f in file:
        str = f.split(',')
        temp = str[len(str)-1].split('\n')
        str[len(str)-1] = temp[0]

        if str[0] not in k:
            k[str[0]] = {}

        if str[1] not in k[str[0]]:
            first_dict = k[str[0]]
            first_dict[str[1]] ={}
        
        if keys_exists(k, str[0], str[1], str[3]) == False:
            second_dict = k[str[0]][str[1]]
            second_dict[str[3]] = {}
            second_dict[str[3]] = int(str[7])
        else:
            k[str[0]][str[1]][str[3]] += int(str[7])

print('file parsing finished....')

result = 'mn'
for i in range(1,10):
    result = result+'{:6}'.format(float(i))

result+='\n'

dirpath = Path("data")
if dirpath.exists() and dirpath.is_dir():
    shutil.rmtree(dirpath)
Path("./data/").mkdir(parents=True, exist_ok=True)

print("generating result...")
for x in k:
    first_dict = k[x]
    for m in first_dict:
        result += m
        second_dict = first_dict[m]
        max_total = second_dict[max(second_dict.keys())]
        
        for n in sorted(second_dict.keys()):
           # print(f"{m} {n} {second_dict[n]} {max_total}")
            eta = float(max_total)/second_dict[n]
            result = result + '{:6}'.format(round(eta,2))
        result+='\n'
    with open('data/size_'+x,'w') as f:
        f.write(result)
    result = ""
    result = 'mn'
    for i in range(1,10):
        result = result+'{:6}'.format(float(i))
    result+='\n'

print('finished!')