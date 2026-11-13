import universe from "./marketFlowUniverse.json";
const NIFTY_50 = ["ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL","CIPLA","COALINDIA","DRREDDY","EICHERMOT","ETERNAL","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HINDALCO","HINDUNILVR","ICICIBANK","INDIGO","INFY","ITC","JIOFIN","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","MAXHEALTH","NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE","SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM","TMPV","TATASTEEL","TCS","TECHM","TITAN","TRENT","ULTRACEMCO","WIPRO"];
const FNO_SYMBOLS = universe.underlyings.map(item=>item.symbol);
const SECTOR_LABELS = universe.sectors;
const hash = (s) => [...s].reduce((h,c)=>Math.imul(h^c.charCodeAt(0),16777619)>>>0,2166136261);
const round = (n,d=2)=>Number(n.toFixed(d));
function makeStock(symbol,index) {
  const h=hash(symbol), sign=((h%7)<3?-1:1), drift=sign*(0.28+(h%210)/100);
  const spot=800+(h%45000), prevClose=spot/(1+drift/100);
  const oi=180000+(h%2400000), oiPct=((h>>>5)%1900)/100-5;
  const buildup=drift>=0?(oiPct>=0?"LONG_BUILD":"SHORT_COVER"):(oiPct>=0?"SHORT_BUILD":"LONG_UNWIND");
  const candles=Array.from({length:76},(_,i)=>{const t=i/75;const wobble=Math.sin((i+h%11)*.33)*.16+Math.sin((i+h%7)*.11)*.11;return {at:i,change:round(drift*t+wobble*t,3)}});
  const strikes=Array.from({length:9},(_,i)=>{const strike=round(spot*(.92+i*.02),0),call= Math.round(oi*(.08+((h+i*17)%24)/100)),put=Math.round(oi*(.08+((h+i*29)%24)/100));return {strike,call,put}});
  const byPut=[...strikes].sort((a,b)=>b.put-a.put),byCall=[...strikes].sort((a,b)=>b.call-a.call);
  return {symbol,sector:SECTOR_LABELS[universe.underlyings.find(item=>item.symbol===symbol)?.sector]?.label||(["Financials","Technology","Industrials","Consumer"][index%4]),spot:round(spot,2),prevClose:round(prevClose,2),changePct:round(drift,2),future:round(spot*(1.001+(h%35)/10000),2),oi,oiChangePct:round(oiPct,2),buildup,side:drift>.5?"bullish":drift<-.5?"bearish":"rangebound",candles,strikes,support:byPut[0].strike,resistance:byCall[0].strike,zone:{low:strikes[3].strike,high:strikes[5].strike},pcr:round(strikes.reduce((s,x)=>s+x.put,0)/strikes.reduce((s,x)=>s+x.call,0),2),strength:Math.min(99,Math.round(38+Math.abs(drift)*12+Math.abs(oiPct)*3))};
}
export function buildDemoFlow(scope="fno") {
 const symbols=scope==="nifty50"?["NIFTY",...NIFTY_50]:FNO_SYMBOLS;
 const stocks=symbols.map(makeStock).sort((a,b)=>Math.abs(b.changePct)-Math.abs(a.changePct));
 const bullish=stocks.filter(x=>x.side==="bullish").sort((a,b)=>b.changePct-a.changePct);
 const bearish=stocks.filter(x=>x.side==="bearish").sort((a,b)=>a.changePct-b.changePct);
 const sectorMap=new Map();
 for(const s of stocks){const row=sectorMap.get(s.sector)||{id:s.sector,label:s.sector,count:0,bullish:0,bearish:0,rangebound:0,changes:[]};row.count++;row[s.side]++;row.changes.push(s.changePct);sectorMap.set(s.sector,row)}
 const sectors=[...sectorMap.values()].map(s=>({...s,changePct:round([...s.changes].sort((a,b)=>a-b)[Math.floor(s.changes.length/2)],2)})).sort((a,b)=>b.changePct-a.changePct);
 return {stocks,bullish,bearish,sectors,featured:{bullish:bullish.slice(0,3),bearish:bearish.slice(0,3)},asOf:Date.now()};
}
