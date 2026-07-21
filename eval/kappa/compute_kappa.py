#!/usr/bin/env python3
"""Regenerate the RQ3 inter-rater agreement study: Cohen's kappa per axis and rater-pair,
raw agreement, confusion matrices, asymptotic + bootstrap 95% CIs, and the per-find CSV.
Three coders: rater1 = author labels (findings_full.author_class/instrument/commonmode);
rater2 = blind LLM (coding_rater2); adjudicator = blind LLM under the sharpened rule (coding_adjudicator)."""
import json, csv, math, random, os
D = os.path.dirname(os.path.abspath(__file__)) + "/"  # self-contained: read the data shipped beside this script
random.seed(20260721)  # fixed seed -> reproducible bootstrap

full = {f["id"]: f for f in json.load(open(D+"findings_full.json"))}
r2   = {c["id"]: c for c in json.load(open(D+"coding_rater2.json"))}
adj  = {c["id"]: c for c in json.load(open(D+"coding_adjudicator.json"))}
ids  = [i for i in full if i in r2 and i in adj]
N = len(ids)
print(f"N (finds coded by all three) = {N}  (full={len(full)} r2={len(r2)} adj={len(adj)})")

def lab(src, i, axis):
    if src is full: return full[i]["author_"+("class" if axis=="class" else ("instrument" if axis=="instrument" else "commonmode"))]
    key = {"class":"class","instrument":"instrument","common":"common_mode"}[axis]
    return src[i].get(key)

def binfac(v): return "FAC" if v in ("silent","fabrication") else "notFAC"

def cohen_kappa(a, b):
    cats = sorted(set(a)|set(b)); n=len(a)
    idx={c:k for k,c in enumerate(cats)}
    po = sum(1 for x,y in zip(a,b) if x==y)/n
    ma=[a.count(c)/n for c in cats]; mb=[b.count(c)/n for c in cats]
    pe = sum(ma[k]*mb[k] for k in range(len(cats)))
    k = (po-pe)/(1-pe) if pe!=1 else float('nan')
    # asymptotic SE (Cohen 1960 / Fleiss et al. simplified)
    se = math.sqrt(po*(1-po)/(n*(1-pe)**2)) if pe!=1 else float('nan')
    return k, po, pe, se, cats

def bootstrap_ci(a, b, reps=5000):
    ks=[]; n=len(a); pairs=list(zip(a,b))
    for _ in range(reps):
        s=[pairs[random.randrange(n)] for _ in range(n)]
        aa=[x for x,_ in s]; bb=[y for _,y in s]
        try:
            k,_,_,_,_=cohen_kappa(aa,bb)
            if not math.isnan(k): ks.append(k)
        except Exception: pass
    ks.sort()
    return ks[int(.025*len(ks))], ks[int(.975*len(ks))]

def bootstrap_ci_clustered(a, b, cluster, reps=5000):
    """Cluster (block) bootstrap: findings within one engine register are not independent
    (same author probing the same engine), so resample whole engine-clusters with replacement
    rather than individual findings. Widens the CI to the effective (cluster-count) sample size.
    `cluster[i]` is the register key (engine) of finding i, aligned with a/b."""
    pairs=list(zip(a,b,cluster))
    groups={}
    for x,y,c in pairs: groups.setdefault(c,[]).append((x,y))
    keys=list(groups); G=len(keys)
    ks=[]
    for _ in range(reps):
        chosen=[keys[random.randrange(G)] for _ in range(G)]  # resample clusters, not rows
        aa=[]; bb=[]
        for c in chosen:
            for x,y in groups[c]: aa.append(x); bb.append(y)
        try:
            k,_,_,_,_=cohen_kappa(aa,bb)
            if not math.isnan(k): ks.append(k)
        except Exception: pass
    ks.sort()
    if not ks: return float('nan'), float('nan')
    return ks[int(.025*len(ks))], ks[int(.975*len(ks))]

def confusion(a,b):
    cats=sorted(set(a)|set(b)); m={(x,y):0 for x in cats for y in cats}
    for x,y in zip(a,b): m[(x,y)]+=1
    return cats,m

pairs = [("rater1","rater2",full,r2), ("rater1","adjud",full,adj), ("rater2","adjud",r2,adj)]
axes  = ["class","binary","instrument","common"]

for axis in axes:
    print(f"\n{'='*70}\nAXIS: {axis}\n{'='*70}")
    for na,nb,sa,sb in pairs:
        if axis=="binary":
            a=[binfac(lab(sa,i,'class')) for i in ids]; b=[binfac(lab(sb,i,'class')) for i in ids]
        else:
            a=[lab(sa,i,axis) for i in ids]; b=[lab(sb,i,axis) for i in ids]
        k,po,pe,se,cats=cohen_kappa(a,b)
        lo95,hi95 = k-1.96*se, k+1.96*se
        blo,bhi = bootstrap_ci(a,b)
        clu=[full[i]["engine"] for i in ids]
        cblo,cbhi = bootstrap_ci_clustered(a,b,clu)
        pabak = 2*po - 1  # prevalence-and-bias-adjusted kappa (Byrt et al. 1993) = 2*p_observed - 1
        print(f"  {na} vs {nb}:  kappa={k:.3f}  raw-agreement={po:.3f}  PABAK={pabak:.3f}  "
              f"asymp95%[{lo95:.2f},{hi95:.2f}]  iid-boot95%[{blo:.2f},{bhi:.2f}]  "
              f"cluster-boot95%[{cblo:.2f},{cbhi:.2f}]")

# class-distribution per coder + FAC totals
print(f"\n{'='*70}\nCLASS DISTRIBUTION + FALSE-ALL-CLEAR TOTALS\n{'='*70}")
for name,src in (("rater1(author)",full),("rater2",r2),("adjud",adj)):
    cl=[lab(src,i,'class') for i in ids]
    fac=sum(1 for i in ids if binfac(lab(src,i,'class'))=="FAC")
    from collections import Counter
    print(f"  {name}: {dict(Counter(cl))}  | false-all-clear(FAC)={fac} "
          f"(silent={cl.count('silent')} fabrication={cl.count('fabrication')})")

# confusion matrix rater1 vs rater2 on class (the load-bearing one)
print(f"\n{'='*70}\nCONFUSION rater1 x rater2 (class)\n{'='*70}")
a=[lab(full,i,'class') for i in ids]; b=[lab(r2,i,'class') for i in ids]
cats,m=confusion(a,b)
print("rows=rater1, cols=rater2:", cats)
for x in cats: print(f"  {x:12s}", [m[(x,y)] for y in cats])

# min FAC across coders (the "invariant" claim)
facs=[sum(1 for i in ids if binfac(lab(s,i,'class'))=="FAC") for s in (full,r2,adj)]
print(f"\nFAC per coder: {facs}  -> min={min(facs)}, max={max(facs)}")

# write per-find CSV
with open(D+"kappa_perfind.csv","w",newline="") as fh:
    w=csv.writer(fh)
    w.writerow(["id","date","engine","rater1_class","rater2_class","adjud_class",
                "rater1_instrument","rater2_instrument","adjud_instrument",
                "rater1_commonmode","rater2_commonmode","adjud_commonmode","mechanism"])
    for i in ids:
        f=full[i]
        w.writerow([i,f["date"],f["engine"],f["author_class"],r2[i]["class"],adj[i]["class"],
                    f["author_instrument"],r2[i]["instrument"],adj[i]["instrument"],
                    f["author_commonmode"],r2[i]["common_mode"],adj[i]["common_mode"],
                    f["mechanism"][:200]])
print(f"\nWrote kappa_perfind.csv ({N} rows).")
