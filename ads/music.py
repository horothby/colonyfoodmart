import numpy as np, wave, sys
sr=44100; bpm=112; beat=60/bpm; total=32.0
N=int(sr*total); L=np.zeros(N); R=np.zeros(N)
def add(sig,t,pan=0.5,g=1.0):
    i=int(t*sr); j=min(N,i+len(sig)); 
    if i>=N: return
    L[i:j]+=sig[:j-i]*g*(1-pan)*2**.5*.7; R[i:j]+=sig[:j-i]*g*pan*2**.5*.7
def hz(n): return 440*2**((n-69)/12)
def pan_note(f,d=0.9):
    t=np.arange(int(sr*d))/sr
    env=np.exp(-t*4.5)*(1-np.exp(-t*400))
    s=np.sin(2*np.pi*f*t)+.5*np.sin(2*np.pi*2*f*t)*np.exp(-t*3)+.28*np.sin(2*np.pi*3.01*f*t)*np.exp(-t*7)+.12*np.sin(2*np.pi*4.2*f*t)*np.exp(-t*12)
    return s*env*.32
def bass(f,d):
    t=np.arange(int(sr*d))/sr; env=np.exp(-t*3)*(1-np.exp(-t*300))
    return (np.sin(2*np.pi*f*t)+.3*np.sin(2*np.pi*2*f*t))*env*.5
def kick():
    t=np.arange(int(sr*.3))/sr; f=50+90*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-t*9)*.8
rng=np.random.default_rng(3)
def shaker(d=.07):
    t=np.arange(int(sr*d))/sr; n=rng.standard_normal(len(t)); n=np.diff(n,prepend=0)
    return n*np.exp(-t*60)*.07
def snare():
    t=np.arange(int(sr*.18))/sr; n=rng.standard_normal(len(t))
    return (n*.5+np.sin(2*np.pi*190*t))*np.exp(-t*22)*.22
# chords: C  F  G  C  /  Am F G C  (I IV V I)
prog=[(48,[60,64,67]),(53,[60,65,69]),(55,[59,62,67]),(48,[60,64,67]),(57,[60,64,69]),(53,[60,65,69]),(55,[59,62,67]),(48,[60,64,67])]
mel=[[76,None,74,72,74,None,76,79],[77,None,76,74,72,None,69,72],[74,None,71,74,79,None,77,74],[72,None,76,None,79,None,84,None],
     [76,None,72,76,81,None,79,76],[77,None,81,79,77,None,74,72],[74,76,77,79,77,None,74,71],[72,None,None,None,67,72,76,None]]
bar=4*beat; nbars=int(np.ceil(total/bar))
for b in range(nbars):
    t0=b*bar; root,ch=prog[b%8]; m=mel[b%8]
    for k in range(4):
        add(kick(),t0+k*beat,.5,1)
    for k in (1,3): add(snare(),t0+k*beat,.45, .9 if b>0 else 0)
    for k in range(16): add(shaker(),t0+k*beat/4,.65, 1.3 if k%4==2 else .7)
    # soca bass: 1, and-of-2, 4-ish
    for (o,d) in ((0,.6),(1.5,.4),(2.5,.6),(3.5,.4)): add(bass(hz(root-12+ (7 if o==2.5 else 0)),d*beat*1.5),t0+o*beat,.5,1)
    # comping pan chords on offbeats
    for k in range(4):
        for n in ch: add(pan_note(hz(n),.35)*.45,t0+(k+.5)*beat,.3)
    if b>=1 or True:
        for k,n in enumerate(m):
            if n is not None: add(pan_note(hz(n)),t0+k*beat/2,.62, .9)
mix=np.stack([L,R],1)
# fade in/out
fi=int(sr*.3); fo=int(sr*2.5); mix[:fi]*=np.linspace(0,1,fi)[:,None]; mix[-fo:]*=np.linspace(1,0,fo)[:,None]
mix=np.tanh(mix/np.abs(mix).max()*1.6)/np.tanh(1.6)*.89
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix*32767).astype('<i2').tobytes())
