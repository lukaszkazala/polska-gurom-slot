using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;

public sealed class CascadeNumericConfig {
 public int[][] strips {get;set;}
 public int[][] refill {get;set;}
 public int[][] lines {get;set;}
 public int[][] pay {get;set;}
 public int[] scatter {get;set;}
 public int[] free {get;set;}
 public int scale {get;set;}
 public int cap {get;set;}
 public int fsMultiplier {get;set;}
 public int expansionNumerator {get;set;}
 public int expansionDenominator {get;set;}
 public int maxCascades {get;set;}
}

public static class CascadeFast {
 sealed class Rng {
  ulong state;
  public Rng(ulong seed) {state=seed;}
  public ulong Next() {
   unchecked {
    ulong z=(state+=0x9E3779B97F4A7C15UL);
    z=(z^(z>>30))*0xBF58476D1CE4E5B9UL;
    z=(z^(z>>27))*0x94D049BB133111EBUL;
    return z^(z>>31);
   }
  }
  public int Below(int n) {
   ulong nn=(ulong)n, threshold=unchecked(0UL-nn)%nn, r;
   do {r=Next();} while(r<threshold);
   return (int)(r%nn);
  }
 }
 sealed class Model {
  public CascadeNumericConfig c;
  public int[] awards=new int[100000];
  public byte[] counts=new byte[100000];
  public int[,] masks;
  public Model(CascadeNumericConfig config) {
   c=config; masks=new int[c.lines.Length,6];
   for(int i=0;i<100000;i++) {
    int[] s=new int[5];int t=i;
    for(int j=0;j<5;j++) {s[j]=t%10;t/=10;}
    for(int target=0;target<8;target++) {
     int n=0;while(n<5 && (s[n]==target || s[n]==8))n++;
     if(n>=3 && c.pay[target][n]>awards[i]) {awards[i]=c.pay[target][n];counts[i]=(byte)n;}
    }
   }
   for(int l=0;l<c.lines.Length;l++)
    for(int n=1;n<=5;n++)masks[l,n]=masks[l,n-1]|(1<<(3*(n-1)+c.lines[l][n-1]));
  }
 }
 static ulong Hash(ulong h,int v) {unchecked{return (h^(ulong)(v+1))*1099511628211UL;}}
 static ulong HashGrid(ulong h,int[] grid) {for(int i=0;i<15;i++)h=Hash(h,grid[i]);return h;}
 sealed class Spin {
  public int payout,scatter,fs,expansion,stages;
  public bool guard;
  public ulong hash;
 }
 static Spin PlaySpin(Model m,Rng rng,int budget,bool fs,bool trace) {
  var c=m.c;int[] g=new int[15];int scat=0;
  for(int reel=0;reel<5;reel++) {
   int stop=rng.Below(c.strips[reel].Length);
   for(int row=0;row<3;row++) {int sym=c.strips[reel][(stop+row)%c.strips[reel].Length];g[reel*3+row]=sym;scat+=sym==9?1:0;}
  }
  ulong hash=14695981039346656037UL;
  if(trace)hash=HashGrid(hash,g);
  int expansion=-1;
  if(fs && rng.Below(c.expansionDenominator)<c.expansionNumerator) {
   expansion=1+rng.Below(3);
   for(int row=0;row<3;row++)g[expansion*3+row]=8;
  }
  if(trace){hash=Hash(hash,scat);hash=Hash(hash,expansion);}
  int total=Math.Min(c.scatter[Math.Min(scat,5)],budget),stage=0;
  bool guard=false;
  for(;stage<c.maxCascades;stage++) {
   int raw=0,mask=0;
   for(int l=0;l<c.lines.Length;l++) {
    int[] line=c.lines[l];
    int code=g[line[0]]+10*g[3+line[1]]+100*g[6+line[2]]+1000*g[9+line[3]]+10000*g[12+line[4]];
    raw+=m.awards[code];mask|=m.masks[l,m.counts[code]];
   }
   raw*=fs?c.fsMultiplier:1;
   int credit=Math.Min(raw,budget-total);total+=credit;
   if(raw==0 || total>=budget)mask=0;
   if(mask!=0 && stage+1==c.maxCascades){mask=0;guard=true;}
   if(trace){hash=HashGrid(hash,g);hash=Hash(hash,raw);hash=Hash(hash,credit);hash=Hash(hash,mask);}
   if(mask==0)break;
   for(int reel=0;reel<5;reel++) {
    int offset=reel*3,nSurvive=0,s0=0,s1=0,s2=0;
    for(int row=0;row<3;row++)if((mask&(1<<(offset+row)))==0) {
     if(nSurvive==0)s0=g[offset+row];else if(nSurvive==1)s1=g[offset+row];else s2=g[offset+row];nSurvive++;
    }
    int holes=3-nSurvive;
    for(int row=0;row<holes;row++)g[offset+row]=c.refill[reel][rng.Below(c.refill[reel].Length)];
    if(nSurvive>0)g[offset+holes]=s0;
    if(nSurvive>1)g[offset+holes+1]=s1;
    if(nSurvive>2)g[offset+holes+2]=s2;
   }
  }
  return new Spin{payout=total,scatter=scat,fs=fs?0:c.free[Math.Min(scat,5)],expansion=expansion,stages=stage+1,guard=guard,hash=hash};
 }
 public static string Run(string configJson,long rounds,ulong seed,int traceRounds) {
  var c=JsonSerializer.Deserialize<CascadeNumericConfig>(configJson);var m=new Model(c);var rng=new Rng(seed);
  var watch=Stopwatch.StartNew();
  long total=0,baseTotal=0,bonusTotal=0,hits=0,profit=0,bonus=0,fsCount=0,expansions=0,capHits=0,guards=0,cascadeRounds=0,cascadeStages=0;
  double squares=0;int maximum=0;
  long[] scatter=new long[6],buckets=new long[9];var traces=new List<object>();
  for(long round=0;round<rounds;round++) {
   bool trace=round<traceRounds;Spin b=PlaySpin(m,rng,c.cap,false,trace);
   int paid=b.payout,remaining=c.cap-paid,freeTotal=0,played=0,expanded=0,stages=b.stages;
   bool guard=b.guard;ulong hash=b.hash;
   for(int i=0;i<b.fs && remaining>0;i++) {
    Spin f=PlaySpin(m,rng,remaining,true,trace);freeTotal+=f.payout;remaining-=f.payout;played++;expanded+=f.expansion>=0?1:0;stages+=f.stages;guard|=f.guard;
    if(trace){hash=Hash(hash,(int)(f.hash&0xffffffffUL));hash=Hash(hash,unchecked((int)(f.hash>>32)));hash=Hash(hash,f.payout);}
   }
   int win=paid+freeTotal;
   total+=win;baseTotal+=paid;bonusTotal+=freeTotal;squares+=(double)win*win;hits+=win>0?1:0;profit+=win>c.scale?1:0;
   bonus+=b.fs>0?1:0;fsCount+=played;expansions+=expanded;capHits+=win==c.cap?1:0;guards+=guard?1:0;
   scatter[b.scatter]++;maximum=Math.Max(maximum,win);cascadeRounds+=b.stages>1?1:0;cascadeStages+=stages;
   int bucket=win==0?0:win<c.scale?1:win<5*c.scale?2:win<20*c.scale?3:win<100*c.scale?4:win<500*c.scale?5:win<1000*c.scale?6:win<c.cap?7:8;buckets[bucket]++;
   if(trace)traces.Add(new{round,payout=win,basePayout=paid,bonusPayout=freeTotal,scatter=b.scatter,freeSpins=played,expansions=expanded,stages,hash=hash.ToString("x16")});
  }
  watch.Stop();double mean=(double)total/rounds/c.scale,variance=squares/rounds/c.scale/c.scale-mean*mean;
  return JsonSerializer.Serialize(new{method="Actual natural full-grid 20-line cascade model; compiled independent C# implementation; SplitMix64 with unbiased rejection sampling",seed,rounds,totalUnits=total,rtp=mean,baseRtp=(double)baseTotal/rounds/c.scale,bonusRtp=(double)bonusTotal/rounds/c.scale,variance,standardDeviation=Math.Sqrt(variance),normal95Interval=new[]{mean-1.96*Math.Sqrt(variance/rounds),mean+1.96*Math.Sqrt(variance/rounds)},hitFrequency=(double)hits/rounds,netProfitFrequency=(double)profit/rounds,bonusFrequency=(double)bonus/rounds,freeSpins=fsCount,expansions,maximumUnits=maximum,capHits,guardHits=guards,baseCascadeFrequency=(double)cascadeRounds/rounds,totalStages=cascadeStages,scatter,buckets,elapsedSeconds=watch.Elapsed.TotalSeconds,traces},new JsonSerializerOptions{WriteIndented=true});
 }
}
