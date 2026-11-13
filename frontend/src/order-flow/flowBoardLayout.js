export function getFlowBoardLayout(width,height){
 const w=Math.max(0,Number(width)||0),h=Math.max(0,Number(height)||0);
 const mode=w>=1500&&h>=620?"diagram":w>=1100?"split":w>=720?"stacked":"mobile";
 const columns=mode==="diagram"?{chart:Math.max(280,Math.round(w*.34)),gate:56,tiles:Math.max(230,Math.round(w*.27)),cards:Math.max(250,Math.round(w*.25))}:mode==="split"?{chart:Math.round(w*.48),gate:0,tiles:Math.round(w*.26),cards:Math.round(w*.26)}:mode==="stacked"?{chart:w,gate:0,tiles:w,cards:w}:{chart:w,gate:0,tiles:w,cards:w};
 return {mode,width:w,height:h,columns};
}

// Mirror the bullish fan around the chart's horizontal midpoint. All points
// stay inside the SVG viewBox, and bearish curves descend across the lower fan.
export function getFlowFanCoordinates(side,index){
 const i=Math.max(0,Math.min(7,Number(index)||0));
 const offset=i*4.5;
 const endOffset=i*4.8;
 return side==="bearish"
  ? {y0:50-offset,y1:92-endOffset}
  : {y0:50+offset,y1:8+endOffset};
}
