// Inputs: SETUP, PAGES, DIAGRAMS. Use empty page frames from figma-v4.json.\n
const page=await figma.getNodeByIdAsync("0:1");await figma.setCurrentPageAsync(page);
await Promise.all([{family:"IBM Plex Sans",style:"Regular"},{family:"IBM Plex Sans",style:"Bold"},{family:"IBM Plex Sans",style:"Italic"},{family:"PT Serif",style:"Regular"},{family:"PT Serif",style:"Italic"}].map(f=>figma.loadFontAsync(f)));
const created=[],mutated=[],photos=[],checks=[],textNodes=[];const track=n=>{created.push(n.id);return n};
const paint=hex=>[{type:"SOLID",color:{r:parseInt(hex.slice(1,3),16)/255,g:parseInt(hex.slice(3,5),16)/255,b:parseInt(hex.slice(5,7),16)/255}}];
const header=await figma.getNodeByIdAsync(SETUP.components[0].id),folio=await figma.getNodeByIdAsync(SETUP.components[1].id);
for(const data of PAGES){
 const target=SETUP.pages.find(p=>p.number===data.number);const frame=await figma.getNodeByIdAsync(target.id);if(frame.children.length>0)throw new Error("Page already contains content: "+data.number);
 mutated.push(frame.id);frame.resize(data.w,data.h);
 for(const block of data.texts){
  if(block.role==="header"||block.role==="footer"){
   const c=block.role==="header"?header:folio;const t=track(c.createInstance());frame.appendChild(t);t.setProperties({[SETUP.components[block.role==="header"?0:1].property]:block.text});t.x=block.x;t.y=block.y;
   for(const ch of t.findAllWithCriteria({types:["TEXT"]}))created.push(ch.id);
   continue;
  }
  const wrap=track(figma.createAutoLayout("VERTICAL"));frame.appendChild(wrap);wrap.name="Абзац";wrap.fills=[];wrap.x=block.x;wrap.y=block.y;
  const t=track(figma.createText());wrap.appendChild(t);const first=block.spans[0];t.fontName={family:first.family,style:first.style};t.fontSize=first.size;t.characters=block.text;t.lineHeight={unit:"PIXELS",value:block.lineHeight};t.textAutoResize="HEIGHT";t.resize(block.w,Math.max(1,block.lineHeight));t.textAutoResize="HEIGHT";t.layoutSizingVertical="HUG";wrap.clipsContent=false;t.fills=paint("#000000");
  for(const span of block.spans){if(span.end>span.start){t.setRangeFontName(span.start,span.end,{family:span.family,style:span.style});t.setRangeFontSize(span.start,span.end,span.size);}}
  t.name=block.text.slice(0,54).replace(/\n/g," ");textNodes.push({page:data.number,id:t.id,characters:t.characters.length});
  if(t.height>block.lineHeight*block.lines+2)checks.push({page:data.number,id:t.id,height:t.height,expected:block.lineHeight*block.lines});
 }
 for(const item of data.images){
  const spec=DIAGRAMS[item.file];
  if(!spec){const r=track(figma.createRectangle());frame.appendChild(r);r.name="Фото / "+item.file;r.x=item.x;r.y=item.y;r.resize(item.w,item.h);r.fills=paint("#E8E4DC");photos.push({id:r.id,file:item.file});continue;}
  const f=track(figma.createFrame());frame.appendChild(f);f.name="Разбор / "+item.file;f.resize(spec.width,spec.height);f.fills=paint(spec.background);f.clipsContent=false;
  for(const layer of spec.layers){
   if(layer.type==="rect"){const r=track(figma.createRectangle());f.appendChild(r);r.x=layer.x;r.y=layer.y;r.resize(layer.w,layer.h);r.fills=paint(layer.fill);}
   else {const t=track(figma.createText());f.appendChild(t);const family=layer.font==="serif"||layer.font==="italic"?"PT Serif":"IBM Plex Sans";const style=layer.font==="bold"?"Bold":layer.font==="italic"?"Italic":"Regular";t.fontName={family,style};t.fontSize=layer.size;t.characters=layer.text;t.textAutoResize="HEIGHT";t.resize(Math.min(layer.w||spec.width-layer.x,spec.width-layer.x),layer.size*1.3);t.textAutoResize="HEIGHT";t.lineHeight={unit:"PIXELS",value:layer.size*1.23};t.x=layer.x;t.y=layer.y;t.fills=paint(layer.color);t.name=layer.text;}
  }
  f.rescale(item.w/spec.width);f.x=item.x;f.y=item.y;
 }
 const spread=await figma.getNodeByIdAsync(target.spread);spread.placeholder=false;mutated.push(spread.id);
 checks.push({page:data.number,children:frame.children.length,bounds:[frame.width,frame.height]});
}
return {createdNodeIds:created,mutatedNodeIds:[...new Set(mutated)],photos,textNodes,checks};
