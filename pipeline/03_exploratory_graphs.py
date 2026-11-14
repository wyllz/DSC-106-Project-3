"""The six exploratory graphs for the checkpoint. Matplotlib is used here for analysis only;
the final interactive graphic is D3. Every number in a title is computed from the data."""
import json, pathlib, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT/'exploration'; OUT.mkdir(exist_ok=True)
SITE = ROOT/'docs' if (ROOT/'docs').is_dir() else ROOT
d = np.load(ROOT/'data_cache/anomalies.npz'); Y = d['years']; L = d['ssp126']; H = d['ssp585']; lat = d['lat']; lon = d['lon']
n_models = L.shape[0]
wl = np.cos(np.deg2rad(lat)); WS = wl.sum()*lon.size; W = wl[None,None,:,None]
gm = lambda a: (a*W).sum((2,3))/WS
GL, GH = gm(L), gm(H); G = GH-GL
win = lambda a,F: a[:,(Y>=F-19)&(Y<=F)].mean(1)
land = np.load(ROOT/'data_cache/landfrac.npy')/100

LOW, HIGH, INK, INK2, INK3, GRID = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#6f6d68', '#e1e0d9'
BINS = [-0.5,0.5,1.5,2.5,4,6,9]; COLORS = ['#2a78d6','#f0efec','#fde3c8','#fdbb84','#f58a54','#d7422c','#a30f12','#5c0a0f']
LABELS = ['below −0.5','±0.5','0.5–1.5','1.5–2.5','2.5–4','4–6','6–9','over 9']
plt.rcParams.update({'font.family':['Helvetica Neue','Arial','sans-serif'],'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':'#c3c2b7','axes.labelcolor':INK2,'xtick.color':INK3,'ytick.color':INK3,'font.size':14,'axes.grid':True,
    'grid.color':GRID,'grid.linewidth':.8,'axes.axisbelow':True,'figure.facecolor':'#fcfcfb','axes.facecolor':'#fcfcfb'})

def slide(n, title, sub=None):
    fig = plt.figure(figsize=(12,6.75), dpi=160)
    fig.text(.045,.945,f'Exploratory graph {n} of 6',fontsize=13,color=INK3,weight='medium')
    fig.text(.045,.885,title,fontsize=24,color=INK,weight='bold')
    if sub: fig.text(.045,.835,sub,fontsize=15,color=INK2)
    fig.text(.045,.025,f'CMIP6, {n_models} models, one per institution. Warming compared with each model\'s own 1995–2014 average.',fontsize=11,color=INK3)
    return fig
def save(fig,name): fig.savefig(OUT/name,dpi=160); plt.close(fig); print('wrote',name)

# ---------- Equal Earth, drawn by hand so these maps match the D3 map ----------
A1,A2,A3,A4 = 1.340264,-0.081106,0.000893,0.003796; MM = np.sqrt(3)/2
def ee(lo,la):
    l,p = np.deg2rad(lo),np.deg2rad(la); th = np.arcsin(MM*np.sin(p)); t2=th**2; t6=t2**3
    return l*np.cos(th)/(MM*(A1+3*A2*t2+t6*(7*A3+9*A4*t2))), th*(A1+A2*t2+t6*(A3+A4*t2))
topo = json.load(open(SITE/'data/land-110m.json')); sc,tr = topo['transform']['scale'],topo['transform']['translate']
ARCS=[]
for a in topo['arcs']:
    q=np.cumsum(np.array(a,float),axis=0); ARCS.append(np.c_[q[:,0]*sc[0]+tr[0],q[:,1]*sc[1]+tr[1]])
def draw_coast(ax):
    for arc in ARCS:
        br=np.where(abs(np.diff(arc[:,0]))>180)[0]+1
        for s in np.split(arc,br):
            x,y=ee(s[:,0],s[:,1]); ax.plot(x,y,color=INK,lw=.5,alpha=.6,solid_capstyle='round')
LATE=np.r_[-90,(lat[:-1]+lat[1:])/2,90]; LONE=np.r_[lon-1.25,180]
LO2,LA2=np.meshgrid(np.linspace(-180,180,LONE.size),LATE); MX,MY=ee(LO2,LA2)
def map_panel(ax,field,bins=BINS,colors=COLORS):
    ax.pcolormesh(MX,MY,field,cmap=ListedColormap(colors),norm=BoundaryNorm([-99]+list(bins)+[99],len(colors)),shading='flat',rasterized=True)
    draw_coast(ax)
    a=np.linspace(-90,90,200); x1,y1=ee(np.full(200,-180.),a); x2,y2=ee(np.full(200,180.),a)
    ax.plot(x1,y1,color='#c3c2b7',lw=.8); ax.plot(x2,y2,color='#c3c2b7',lw=.8)
    ax.set_aspect('equal'); ax.axis('off')
def swatches(fig,labels,colors,x=.045,y=.075,title='°C',w=.075):
    fig.text(x,y+.005,title,fontsize=13,color=INK,weight='medium')
    x0=x+.165
    for i,(lb,c) in enumerate(zip(labels,colors)):
        fig.patches.append(plt.Rectangle((x0+i*w,y+.012),w-.004,.018,transform=fig.transFigure,color=c,figure=fig))
        fig.text(x0+i*w,y-.018,lb,fontsize=12,color=INK2)

# ---------- 1: the two futures, global mean ----------
g21 = win(G,2040).mean(); g81 = win(G,2100).mean()
fig=slide(1,'Globally, the two futures look alike until about 2040',
          f'Annual global temperature. Then they split: +{win(GL,2100).mean():.1f}°C or +{win(GH,2100).mean():.1f}°C by 2081–2100.')
ax=fig.add_axes([.07,.12,.86,.68])
for k in range(n_models):
    ax.plot(Y[Y>=2014],GL[k][Y>=2014],color=LOW,lw=.6,alpha=.3); ax.plot(Y[Y>=2014],GH[k][Y>=2014],color=HIGH,lw=.6,alpha=.3)
    ax.plot(Y[Y<=2014],GL[k][Y<=2014],color='#898781',lw=.6,alpha=.3)
ax.plot(Y[Y<=2014],GL.mean(0)[Y<=2014],color=INK2,lw=2.4)
ax.plot(Y[Y>=2014],GL.mean(0)[Y>=2014],color=LOW,lw=2.6); ax.plot(Y[Y>=2014],GH.mean(0)[Y>=2014],color=HIGH,lw=2.6)
ax.axhline(0,color='#c3c2b7',lw=1)
ax.set_xlim(1950,2112); ax.set_ylabel('Warming (°C)'); ax.set_ylim(-1.6,7)
ax.annotate('High emissions\n(SSP5-8.5)',(2100,GH.mean(0)[-1]),(2101.5,GH.mean(0)[-1]),color=INK,fontsize=13,weight='bold',va='center')
ax.annotate('Low emissions\n(SSP1-2.6)',(2100,GL.mean(0)[-1]),(2101.5,GL.mean(0)[-1]),color=INK,fontsize=13,weight='bold',va='center')
ax.text(1982,.62,'Historical runs',color=INK2,fontsize=13,ha='center')
ax.text(1952,6.3,'Thin lines: individual models.  Thick lines: average of all models.',color=INK3,fontsize=12.5)
save(fig,'graph1_global_two_futures.png')

# ---------- 2: the gap through time ----------
F=np.arange(2015,2101); series=np.stack([win(G,f) for f in F],1); mean=series.mean(0); p10,p90=np.percentile(series,[10,90],axis=0)
fig=slide(2,f'The global gap is {g21:.2f}°C by 2021–2040, then {g81:.1f}°C by 2081–2100',
          'High minus low emissions. Each point is a 20-year average ending that year, calculated within each model first.')
ax=fig.add_axes([.07,.12,.86,.68])
for k in range(n_models): ax.plot(F,series[k],color='#898781',lw=.7,alpha=.45)
ax.fill_between(F,p10,p90,color=INK,alpha=.12,lw=0); ax.plot(F,mean,color=INK,lw=2.8)
ax.axhline(0,color='#c3c2b7',lw=1); ax.set_xlim(2015,2100); ax.set_ylabel('Gap (°C)')
first=F[np.where(series.min(0)<=0)[0].max()+1]
for f,dy,ha,tx in [(2040,.55,'center',f'2021–2040\n+{g21:.2f}°C'),(2060,.65,'center',f'2041–2060\n+{win(G,2060).mean():.2f}°C'),(2100,.05,'right',f'2081–2100\n+{g81:.2f}°C')]:
    v=mean[f-2015]; ax.plot([f],[v],'o',color=INK,ms=8,mec='#fcfcfb',mew=2,zorder=5,clip_on=False)
    ax.text(f-(8.5 if ha=='right' else 0),v+dy+(.25 if ha=='right' else 0),tx,ha=ha,color=INK,fontsize=14,weight='bold',va='bottom')
ax.text(2017,3.45,f'All {n_models} models show a positive gap from the window ending in {first} onward.',color=INK2,fontsize=14)
save(fig,'graph2_gap_through_time.png')

# ---------- 3: where it warms, high emissions ----------
hi=win(H,2100).mean(0); lo=win(L,2100).mean(0); gap=hi-lo
gh=(hi*wl[:,None]).sum()/WS
fig=slide(3,f'Warming is not even: +{gh:.1f}°C globally, up to +{hi.max():.0f}°C in the Arctic','High emissions, 2081–2100. Land warms faster than ocean, and the far north warms fastest.')
ax=fig.add_axes([.04,.115,.92,.70]); map_panel(ax,hi); swatches(fig,LABELS,COLORS,title='°C of warming'); save(fig,'graph3_warming_map_high.png')

# ---------- 4: where the choice matters ----------
gg=(gap*wl[:,None]).sum()/WS
fig=slide(4,f'The gap is uneven too: +{gap.min():.1f}°C to +{gap.max():.1f}°C, depending on the place','Extra warming from taking the high path instead of the low path, 2081–2100. Same colour scale as graph 3.')
ax=fig.add_axes([.04,.115,.92,.70]); map_panel(ax,gap); swatches(fig,LABELS,COLORS,title='°C of extra warming')
j,i=np.unravel_index(gap.argmax(),gap.shape); j2,i2=np.unravel_index(gap.argmin(),gap.shape)
for (jj,ii,txt,dx,dy) in [(j,i,f'Largest: +{gap[j,i]:.1f}°C\nCanadian Arctic',.42,-.15),(j2,i2,f'Smallest: +{gap[j2,i2]:.1f}°C\nSouthern Ocean',-.15,.38)]:
    x,y=ee(lon[ii],lat[jj]); ax.annotate(txt,(x,y),(x+dx,y+dy),fontsize=13,weight='bold',color=INK,arrowprops=dict(arrowstyle='-',color=INK,lw=1),va='center',
        bbox=dict(boxstyle='round,pad=.3',fc='#fcfcfb',ec='none',alpha=.9))
save(fig,'graph4_gap_map.png')

# ---------- 5: gap by latitude ----------
lm=land; landgap=(gap*wl[:,None]*lm).sum()/(wl[:,None]*lm).sum(); oceangap=(gap*wl[:,None]*(1-lm)).sum()/(wl[:,None]*(1-lm)).sum()
k=lat>=66.5; arc=(gap[k]*wl[k,None]).sum()/(wl[k].sum()*lon.size)
fig=slide(5,f'The Arctic\'s gap is {arc/gg:.1f}× the global gap, and land\'s is {landgap/oceangap:.1f}× the ocean\'s','Gap averaged around each latitude, for three 20-year periods. The gap grows everywhere, and fastest in the far north.')
ax=fig.add_axes([.07,.13,.86,.67]); shades={2040:'#b9b8b1',2060:'#6f6d68',2100:INK}
for f,tx in [(2040,'2021–2040'),(2060,'2041–2060'),(2100,'2081–2100')]:
    z=win(H-L,f).mean(0).mean(1); ax.plot(lat,z,color=shades[f],lw=2.6 if f==2100 else 2.2); 
    ax.text(lat[-1]+1.5,z[-1],tx,color=INK,fontsize=13,va='center',weight='bold' if f==2100 else 'normal')
ax.axhline(gg,color='#898781',lw=1.2); ax.text(-46,gg+.14,f'Global gap in 2081–2100: +{gg:.1f}°C',color=INK2,fontsize=13)
ax.axhline(0,color='#c3c2b7',lw=1)
ax.set_xlim(-90,113); ax.set_xticks([-90,-60,-30,0,30,60,90]); ax.set_xticklabels(['90°S','60°S','30°S','Equator','30°N','60°N','90°N']); ax.set_ylabel('Gap (°C)')
ax.spines['bottom'].set_bounds(-90,90)
save(fig,'graph5_gap_by_latitude.png')

# ---------- 6: where models disagree ----------
gf=win(H-L,2100); spread=np.percentile(gf,90,axis=0)-np.percentile(gf,10,axis=0); p10g=np.percentile(gf,10,axis=0)
share=100*((p10g<=0)*wl[:,None]).sum()/WS
SB=[1,1.5,2,3,4,6]; SC=['#e7eefb','#cde2fb','#9ec5f4','#6da7ec','#3987e5','#1c5cab','#0d366b']; SL=['under 1','1–1.5','1.5–2','2–3','3–4','4–6','over 6']
fig=slide(6,'Models disagree most near the poles and south of Greenland','How far apart the middle 80% of models are on the 2081–2100 gap. So the final graphic needs an uncertainty band.')
ax=fig.add_axes([.04,.115,.92,.70]); map_panel(ax,spread,SB,SC); swatches(fig,SL,SC,title='°C between models')
# Same bilinear sampling the D3 page uses, so this annotation matches the page's tooltip for this spot.
def bil(a,la,lo):
    fj=(la-lat[0])/2.5; fi=((lo-lon[0])/2.5)%lon.size; j0,i0=int(fj),int(fi); yy,xx=fj-j0,fi-i0; i1=(i0+1)%lon.size
    return (1-yy)*((1-xx)*a[j0,i0]+xx*a[j0,i1])+yy*((1-xx)*a[j0+1,i0]+xx*a[j0+1,i1])
lat0,lon0=52.5,-37.5; x,y=ee(lon0,lat0)
ax.annotate(f'South of Greenland, the middle 80%\nruns from {bil(np.percentile(gf,10,axis=0),lat0,lon0):+.1f}°C to {bil(np.percentile(gf,90,axis=0),lat0,lon0):+.1f}°C.\nEven the sign is disputed.'.replace('-','−'),(x,y),(x-.05,y-.62),fontsize=13,weight='bold',color=INK,va='center',
    arrowprops=dict(arrowstyle='-',color=INK,lw=1),bbox=dict(boxstyle='round,pad=.3',fc='#fcfcfb',ec='none',alpha=.92))
save(fig,'graph6_model_disagreement.png')

print('\nFacts for the script'); print(' first window with all models positive ends', first)
print(f' gap at 2040 {g21:.3f}, 2060 {win(G,2060).mean():.3f}, 2100 {g81:.3f}; low 2100 {win(GL,2100).mean():.2f}; high 2100 {win(GH,2100).mean():.2f}')
print(f' arctic {arc:.2f} ({arc/gg:.2f}x); land {landgap:.2f}, ocean {oceangap:.2f}, ratio {landgap/oceangap:.2f}; share of globe with p10 gap <=0: {share:.2f}%')
print(f' high map max {hi.max():.1f} at', np.unravel_index(hi.argmax(),hi.shape), f'lat {lat[np.unravel_index(hi.argmax(),hi.shape)[0]]}, lon {lon[np.unravel_index(hi.argmax(),hi.shape)[1]]}')
print(f' spread max {spread.max():.1f}; cells with p10<=0 at', sorted({(float(lat[a]),float(lon[b])) for a,b in zip(*np.where(p10g<=0))})[:10])
