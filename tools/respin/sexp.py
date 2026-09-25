import sys
def parse(s):
    toks=[];i=0;n=len(s)
    while i<n:
        c=s[i]
        if c in '()': toks.append(c);i+=1
        elif c.isspace(): i+=1
        elif c=='"':
            j=i+1
            while s[j]!='"':
                j+= 2 if s[j]=='\\' else 1
            toks.append(s[i:j+1]);i=j+1
        else:
            j=i
            while j<n and not s[j].isspace() and s[j] not in '()': j+=1
            toks.append(s[i:j]);i=j
    st=[[]]
    for t in toks:
        if t=='(': st.append([])
        elif t==')': x=st.pop(); st[-1].append(x)
        else: st[-1].append(t)
    return st[0][0]
def find(node,name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]
def walk(node):
    yield node
    for c in node:
        if isinstance(c,list): yield from walk(c)
