import React,{useEffect,useMemo,useRef,useState}from"react";

const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const pct=n=>(n>0?"+":"")+Number(n||0).toFixed(2)+"%";
const fmt=n=>new Intl.NumberFormat("en-IN",{notation:"compact",maximumFractionDigits:1}).format(Number(n)||0);
const tone=s=>s?.side==="bullish"?"up":s?.side==="bearish"?"down":"flat";
const pathFor=points=>points.map((p,i)=>(i?"L":"M")+p[0].toFixed(1)+","+p[1].toFixed(1)).join(" ");
const curve=(x0,y0,x1,y1)=>{const dx=(x1-x0)*.52;return `M${x0},${y0} C${x0+dx},${y0} ${x1-dx},${y1} ${x1},${y1}`};
function useBoardSize(ref){
 const[size,setSize]=useState({width:0,height:0});
 useEffect(()=>{const node=ref.current;if(!node)return;const measure=()=>{const r=node.getBoundingClientRect();setSize({width:Math.round(r.width),height:Math.max(640,Math.round(r.height))})};measure();const observer=new ResizeObserver(measure);observer.observe(node);return()=>observer.disconnect()},[ref]);
 return size;
}
function MiniProfile({stock,x,y,w,h,selected,onSelect,onPin,selectedSector,kind="tile"}){
 const up=stock.side==="bullish";
 const values=(stock.candles||[]).map(c=>Number(c.change)||0);
 const max=Math.max(.5,...values.map(Math.abs));
 const points=values.map((v,i)=>[x+8+i/Math.max(1,values.length-1)*(w-16),y+h*.72-v/max*h*.25]);
 const spark=pathFor(points);
 const isCard=kind==="card",isTall=kind==="tall";
 return <g className={`mf-native-node ${kind} ${up?"is-up":"is-down"} ${selected===stock.symbol?"is-lit":""} ${selectedSector&&stock.sector!==selectedSector?"is-sector-dim":""}`}
   onMouseEnter={()=>onSelect(stock.symbol)} onFocus={()=>onSelect(stock.symbol)} onClick={()=>{onSelect(stock.symbol);onPin(stock.symbol)}} tabIndex="0" role="button" aria-label={`Select ${stock.symbol}, ${pct(stock.changePct)}`}>
  <rect x={x} y={y} width={w} height={h} rx={isCard?9:6}/>
  <text className="mf-node-symbol" x={x+9} y={y+17}>{stock.symbol}</text>
  <text className="mf-node-change" x={x+w-8} y={y+17} textAnchor="end">{pct(stock.changePct)}</text>
  <path className="mf-node-spark" d={spark}/>
  {isCard&&<><text className="mf-node-meta" x={x+9} y={y+h-34}>OI {fmt(stock.oi)} · {String(stock.buildup||"").replaceAll("_"," ")}</text><text className="mf-node-meta" x={x+9} y={y+h-19}>SUP {fmt(stock.support)} · RES {fmt(stock.resistance)}</text><text className="mf-node-meta" x={x+9} y={y+h-6}>PCR {Number(stock.pcr||0).toFixed(2)} · OI Δ {pct(stock.oiChangePct)}</text></>}
  {isTall&&<><text className="mf-node-meta" x={x+9} y={y+34}>OPTION OI BY STRIKE</text>{(stock.strikes||[]).slice(0,5).map((strike,i)=>{const yy=y+46+i*Math.max(9,(h-54)/5),maxOI=Math.max(1,...stock.strikes.map(v=>Math.max(v.put,v.call)));return <g key={strike.strike}><text className="mf-strike" x={x+8} y={yy+6}>{fmt(strike.strike)}</text><rect className="mf-oi-track" x={x+w*.38} y={yy} width={w*.25} height="4" rx="2"/><rect className="mf-oi-put" x={x+w*.38} y={yy} width={w*.25*strike.put/maxOI} height="4" rx="2"/><rect className="mf-oi-track" x={x+w*.68} y={yy} width={w*.25} height="4" rx="2"/><rect className="mf-oi-call" x={x+w*.68} y={yy} width={w*.25*strike.call/maxOI} height="4" rx="2"/></g>})}</>}
  {!isCard&&!isTall&&<text className="mf-node-meta" x={x+9} y={y+h-7}>OI {fmt(stock.oi)}</text>}
 </g>
}
export default function FlowDiagram({stocks=[],selected,onSelect=()=>{},onPin=()=>{},selectedSector}){
 const host=useRef(null),{width:W}=useBoardSize(host),[cross,setCross]=useState(null);
 const data=useMemo(()=>stocks.filter(s=>Number.isFinite(Number(s.changePct))).map(s=>({...s})),[stocks]);
 const bulls=useMemo(()=>data.filter(s=>s.side==="bullish").sort((a,b)=>b.changePct-a.changePct),[data]);
 const bears=useMemo(()=>data.filter(s=>s.side==="bearish").sort((a,b)=>a.changePct-b.changePct),[data]);
 const flats=useMemo(()=>data.filter(s=>s.side==="rangebound"),[data]);
 const width=Math.max(1200,W||1500),height=width<760?980:width<1120?820:760;
 const layout=useMemo(()=>{
  const pad=14,axis=42,cardW=width>=1500?300:width>=1120?260:210,tallW=width>=1500?126:108,smallW=width>=1500?104:width>=1120?88:72,gap=5;
  const cardX=width-pad-cardW,tallX=cardX-10-tallW,smallStart=tallX-8-smallW*3-gap*2,gateR=smallStart-78,gateL=gateR-66,x0=pad+axis,x1=gateL-52;
  const top=pad+78,bottom=height-pad-36,mid=height/2,zero=(top+bottom)/2;
  const halves={bullish:{top:pad+4,bottom:mid-10},bearish:{top:mid+10,bottom:height-pad-4}};
  return {pad,axis,cardW,tallW,smallW,gap,cardX,tallX,smallStart,gateR,gateL,x0,x1,top,bottom,mid,zero,halves};
 },[width,height]);
 const features={bullish:bulls.slice(0,2),bearish:bears.slice(0,2)};
 const featureSymbols=new Set([...features.bullish,...features.bearish].map(s=>s.symbol));
 const boxes={bullish:[],bearish:[]};
 for(const side of ["bullish","bearish"]){const area=layout.halves[side],rows=Math.max(1,Math.floor((area.bottom-area.top+5)/49)),list=(side==="bullish"?bulls:bears).filter(s=>!featureSymbols.has(s.symbol)).slice(0,rows*3);list.forEach((s,i)=>{const row=Math.floor(i/3),col=i%3,h=Math.min(44,(area.bottom-area.top-(rows-1)*5)/rows),y=side==="bullish"?area.top+row*(h+5):area.bottom-h-row*(h+5);boxes[side].push({stock:s,x:layout.smallStart+col*(layout.smallW+layout.gap),y,w:layout.smallW,h})})}
 const cardBoxes={bullish:[],bearish:[]};
 for(const side of ["bullish","bearish"]){const area=layout.halves[side],n=features[side].length,h=(area.bottom-area.top-(n-1)*8)/Math.max(1,n);features[side].forEach((stock,i)=>{const y=area.top+i*(h+8);cardBoxes[side].push({stock,y,h,tall:{x:layout.tallX,y,w:layout.tallW,h},card:{x:layout.cardX,y,w:layout.cardW,h}})})}
 const targets=new Map();
 [...boxes.bullish,...boxes.bearish].forEach(b=>targets.set(b.stock.symbol,{x:b.x,y:b.y+b.h/2}));
 Object.values(cardBoxes).flat().forEach(b=>targets.set(b.stock.symbol,{x:b.tall.x,y:b.y+Math.min(24,b.h/2)}));
 const gateRows=new Map(),flowNames=[...bulls.filter(s=>targets.has(s.symbol)),...flats,...bears.filter(s=>targets.has(s.symbol))];
 const gateTop=layout.top+5,gateBottom=layout.bottom-5;
 flowNames.forEach((s,i)=>gateRows.set(s.symbol,gateTop+(i+.5)/Math.max(1,flowNames.length)*(gateBottom-gateTop)));
 const maxMove=Math.max(1,...data.map(s=>Math.abs(s.changePct||0)));
 const yValue=v=>layout.zero-clamp(v/maxMove,-1,1)*(layout.zero-layout.top-8);
 const drawnPaths=data.map(s=>{const values=(s.candles||[]).map(c=>Number(c.change)||0);if(!values.length)values.push(0,Number(s.changePct)||0);const points=values.map((v,i)=>[layout.x0+i/Math.max(1,values.length-1)*(layout.x1-layout.x0),yValue(v)]);const row=gateRows.get(s.symbol);let d=pathFor(points);if(row!=null)d+=` C${layout.x1+28},${points.at(-1)[1]} ${layout.gateL-18},${row} ${layout.gateL},${row} L${layout.gateR},${row}`;return {stock:s,d,row}}).filter(p=>p.row!=null||p.stock.side==="rangebound");
 const paths={targets,gateRows,paths:drawnPaths,maxMove,yValue,flowNames};
 const sectors=useMemo(()=>{const map=new Map();data.forEach(s=>{const a=map.get(s.sector)||[];a.push(s.changePct);map.set(s.sector,a)});return [...map].map(([name,values])=>({name,median:[...values].sort((a,b)=>a-b)[Math.floor(values.length/2)]})).sort((a,b)=>b.median-a.median).slice(0,8)},[data]);
 const sectorPills=sectors.slice(0,Math.max(2,Math.min(5,Math.floor((layout.x1-layout.x0)/88))));\n const sectorX=layout.x0+12,sectorW=Math.max(64,Math.min(132,(layout.x1-layout.x0)/Math.max(1,sectorPills.length)-5));
 return <section ref={host} className="mf-flow-diagram mf-faithful-diagram" aria-label="Order Flow continuous market diagram">
  {W>0&&<svg className="mf-faithful-svg" viewBox={`0 0 ${width} ${height}`} onPointerMove={e=>{const r=e.currentTarget.getBoundingClientRect();setCross(clamp((e.clientX-r.left)/r.width*width,layout.x0,layout.x1))}} onPointerLeave={()=>setCross(null)} role="group" aria-label="Futures paths converge through the market flow gate and branch to stock tiles and featured option cards">
   <defs><linearGradient id="mf-gate-fill" x1="0" x2="1"><stop offset="0" stopColor="var(--mf-up)" stopOpacity=".13"/><stop offset=".5" stopColor="var(--th-muted)" stopOpacity=".08"/><stop offset="1" stopColor="var(--mf-down)" stopOpacity=".13"/></linearGradient></defs>
   <rect className="mf-diagram-half is-up" x={layout.pad} y={layout.halves.bullish.top} width={width-layout.pad*2} height={layout.halves.bullish.bottom-layout.halves.bullish.top} rx="10"/>
   <rect className="mf-diagram-half is-down" x={layout.pad} y={layout.halves.bearish.top} width={width-layout.pad*2} height={layout.halves.bearish.bottom-layout.halves.bearish.top} rx="10"/>
   <text className="mf-half-label is-up" x={layout.pad+10} y={layout.halves.bullish.top+17}>BULLISH FLOW · {bulls.length}</text>
   <text className="mf-half-label is-down" x={layout.pad+10} y={layout.halves.bearish.top+17}>BEARISH FLOW · {bears.length}</text>
   <text className="mf-diagram-caption" x={layout.x0} y="22">INTRADAY FUTURES FAN</text>
   <text className="mf-diagram-caption" x={layout.gateL+4} y="22">CONVERGENCE GATE</text>
   <text className="mf-diagram-caption" x={layout.smallStart} y="22">UNDERLYING MAP</text>
   {sectorPills.map((s,i)=>{const x=sectorX+i*(sectorW+5),y=36;return <g key={s.name}><rect className="mf-sector-pill" x={x} y={y} width={sectorW} height="27" rx="7"/><text className="mf-sector-name" x={x+7} y={y+11}>{s.name}</text><text className="mf-sector-median" x={x+7} y={y+22}>{pct(s.median)} median</text></g>})}
   {[-1,-.5,0,.5,1].map(v=><g key={v}><line className="mf-diagram-grid" x1={layout.x0} x2={layout.x1} y1={layout.zero-v*(layout.zero-layout.top-8)} y2={layout.zero-v*(layout.zero-layout.top-8)}/><text className="mf-diagram-axis" x={layout.x0-8} y={layout.zero-v*(layout.zero-layout.top-8)+3} textAnchor="end">{v>0?"+":""}{(v*paths.maxMove).toFixed(1)}%</text></g>)}
   <line className="mf-diagram-zero" x1={layout.x0} x2={layout.x1} y1={layout.zero} y2={layout.zero}/>
   {sectors.map(s=>{const yy=layout.zero-(s.median/paths.maxMove)*(layout.zero-layout.top-8);return <line key={s.name} className="mf-sector-median-line" x1={layout.x0} x2={layout.x1} y1={yy} y2={yy}/>})}
   <path className="mf-gate-shell" d={`M${layout.gateL},${layout.top+10} Q${layout.gateL-12},${layout.top+10} ${layout.gateL-12},${layout.top+24} L${layout.gateL-12},${layout.bottom-24} Q${layout.gateL-12},${layout.bottom-10} ${layout.gateL},${layout.bottom-10} L${layout.gateR},${layout.bottom-10} Q${layout.gateR+12},${layout.bottom-10} ${layout.gateR+12},${layout.bottom-24} L${layout.gateR+12},${layout.top+24} Q${layout.gateR+12},${layout.top+10} ${layout.gateR},${layout.top+10} Z`}/>
   <path className="mf-zero-spine" d={`M${layout.x0},${layout.zero} H${layout.gateR+10} C${layout.gateR+28},${layout.zero} ${layout.gateR+22},${layout.mid} ${layout.smallStart-12},${layout.mid} H${width-layout.pad}`}/>
   {paths.paths.map(({stock,d,row})=><path key={stock.symbol} d={d} className={`mf-fan-path ${tone(stock)} ${selected===stock.symbol?"is-active":""} ${selectedSector&&stock.sector!==selectedSector?"is-sector-dim":""}`} onMouseEnter={()=>onSelect(stock.symbol)} onClick={()=>{onSelect(stock.symbol);onPin(stock.symbol)}}/>)}
   {[...bulls.filter(s=>gateRows.has(s.symbol)),...bears.filter(s=>gateRows.has(s.symbol))].map(s=>{const row=gateRows.get(s.symbol),target=targets.get(s.symbol);return <path key={s.symbol+"-branch"} className={`mf-gate-branch ${tone(s)} ${selected===s.symbol?"is-active":""}`} d={target?curve(layout.gateR,row,target.x,target.y):""}/>})}
   {flowNames.map(s=>{const y=gateRows.get(s.symbol);return <line key={s.symbol+"-gate"} className={`mf-gate-row ${tone(s)}`} x1={layout.gateL} x2={layout.gateR} y1={y} y2={y}/>})}
   <text className="mf-gate-word" x={(layout.gateL+layout.gateR)/2} y={layout.mid-4} textAnchor="middle">FLOW</text><text className="mf-gate-count" x={(layout.gateL+layout.gateR)/2} y={layout.mid+10} textAnchor="middle">{flowNames.length} paths</text>
   {["bullish","bearish"].map(side=>boxes[side].map(b=><MiniProfile key={b.stock.symbol} {...b} selected={selected} onSelect={onSelect} onPin={onPin} selectedSector={selectedSector}/>))}
   {["bullish","bearish"].map(side=>cardBoxes[side].map(b=><g key={b.stock.symbol}><MiniProfile stock={b.stock} {...b.tall} selected={selected} onSelect={onSelect} onPin={onPin} selectedSector={selectedSector} kind="tall"/><path className={`mf-card-joint ${side}`} d={`M${b.tall.x+b.tall.w},${b.y+Math.min(24,b.h/2)} H${b.card.x}`}/><MiniProfile stock={b.stock} {...b.card} selected={selected} onSelect={onSelect} onPin={onPin} selectedSector={selectedSector} kind="card"/></g>))}
   {cross!==null&&<g className="mf-diagram-cross" pointerEvents="none"><line x1={cross} x2={cross} y1={layout.top} y2={layout.bottom}/><text x={clamp(cross,layout.x0+20,layout.x1-20)} y={layout.top-6} textAnchor="middle">T+{Math.round((cross-layout.x0)/(layout.x1-layout.x0)*75)}m</text></g>}
  </svg>}
  <div className="mf-diagram-foot"><span><i className="up"/> Futures path → gate → underlying</span><span><i className="down"/> Featured cards include option OI by strike</span><span>{data.length} underlyings · {flats.length} rangebound</span></div>
 </section>
}
