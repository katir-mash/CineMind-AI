"""Прозрачный рекомендатель: TF-IDF + косинусная близость + рейтинг.
Не генеративная нейросеть; локальный алгоритм обработки текста."""
import math, re
from collections import Counter
from database import movies

def tokens(text):return re.findall(r'[\wа-яёәіңғүұқөһ]+',text.lower())
def vectors(documents):
    tokenized=[tokens(d) for d in documents]
    n=len(tokenized); df=Counter(t for doc in tokenized for t in set(doc))
    idf={t:math.log((n+1)/(count+1))+1 for t,count in df.items()}
    v=[]
    for doc in tokenized:
        count=Counter(doc)
        weights={t:(1+math.log(freq))*idf[t] for t,freq in count.items()}
        norm=math.sqrt(sum(x*x for x in weights.values())) or 1
        v.append({t:val/norm for t,val in weights.items()})
    return v

def cosine(a,b):return sum(v*b.get(t,0) for t,v in a.items())
def recommend(query='',favorites=None,limit=8):
    all_movies=list(movies(sort='Рейтинг ↓'))
    if not all_movies:return []
    favorites=set(favorites or [])
    texts=[f"{m['genre']} {m['genre']} {m['title']} {m['description']}" for m in all_movies]
    favorite_text=' '.join(texts[i] for i,m in enumerate(all_movies) if m['id'] in favorites)
    target=((query or '').strip()+' '+favorite_text).strip()
    if not target:target='лучшие фильмы интересный сюжет'
    matrix=vectors(texts+[target]);target_vec=matrix[-1]
    result=[]
    for movie,vec in zip(all_movies,matrix[:-1]):
        if movie['id'] in favorites:continue
        similarity=cosine(target_vec,vec)
        score=0.8*similarity+0.2*(movie['rating']/10)
        why=f"Сходство описания: {similarity:.0%}; рейтинг: {movie['rating']}/10."
        result.append((movie,score,why))
    return sorted(result,key=lambda row:row[1],reverse=True)[:limit]

def compare(films,weights=(0.5,0.3,0.2)):
    """Взвешенная сумма: рейтинг (50%), новизна (30%), компактность (20%)."""
    if not films:return []
    out=[]
    for m in films:
        rating=m['rating']/10
        freshness=max(0,min(1,(m['year']-1980)/50))
        duration=max(0,min(1,(240-m['duration'])/180))
        score=weights[0]*rating+weights[1]*freshness+weights[2]*duration
        out.append((m,round(score*100,2),f'Рейтинг {rating:.2f}×{weights[0]:.0%} + новизна {freshness:.2f}×{weights[1]:.0%} + длительность {duration:.2f}×{weights[2]:.0%}'))
    return sorted(out,key=lambda x:x[1],reverse=True)
