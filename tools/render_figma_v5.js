// Figma Plugin API body. The caller supplies bookPages and pageIds from layout-v5.json.
// Uses native text, vectors and photo fills. No page-sized raster exports.
const createdNodeIds = [], mutatedNodeIds = [], records = [], warnings = [];
const px = 72 / 25.4 * 2;
const fonts = {
  serif: {family:'PT Serif',style:'Regular'},
  italic: {family:'PT Serif',style:'Italic'},
  sans: {family:'IBM Plex Sans',style:'Regular'},
  bold: {family:'IBM Plex Sans',style:'Bold'}
};
await Promise.all(Object.values(fonts).map(f=>figma.loadFontAsync(f)));
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('17:60'));
const hashes = {
  'v4_door.png':'ebfcc5f3cfa08fc4a8f3714b8cce3ff1647b470c',
  'v4_chocolate.png':'8ad8b1048e6c2e91a37561808583cf872a506b29',
  'v4_chair.png':'f8f899627a34e5cc8072c59262d82547c3b21566',
  'v4_menu_photo.png':'bdc30611182fafc5b0e589b9c4bec0b3de967ea1'
};
function color(h){return {r:parseInt(h.slice(1,3),16)/255,g:parseInt(h.slice(3,5),16)/255,b:parseInt(h.slice(5,7),16)/255};}
function solid(h){return [{type:'SOLID',color:color(h)}];}
function track(n){createdNodeIds.push(n.id);return n;}
for (const p of bookPages) {
  const frame = await figma.getNodeByIdAsync(pageIds[p.number]);
  if(frame.children.length) throw new Error('Page already populated: '+p.number);
  frame.name=String(p.number).padStart(2,'0')+' / '+p.name;
  frame.fills=solid(p.background); mutatedNodeIds.push(frame.id);
  for(const l of p.layers){
    let n;
    if(l.type==='text'){
      // The wrapper keeps editable text in an auto-layout context with a fixed width.
      const wrap=track(figma.createAutoLayout());frame.appendChild(wrap);
      wrap.name=l.id+' / '+l.role;wrap.layoutMode='VERTICAL';wrap.fills=[];
      wrap.paddingTop=wrap.paddingRight=wrap.paddingBottom=wrap.paddingLeft=0;
      wrap.itemSpacing=0;wrap.clipsContent=false;
      wrap.resize((l.w+1.5)*px,l.h*px);wrap.x=l.x*px;wrap.y=l.y*px;
      wrap.primaryAxisSizingMode='AUTO';wrap.counterAxisSizingMode='FIXED';
      n=track(figma.createText());n.fontName=fonts[l.font];wrap.appendChild(n);
      n.name=l.id+' / '+(l.source_id!==undefined?'source '+l.source_id:l.figure_source_id!==undefined?'figure '+l.figure_source_id:l.role);
      n.characters=l.text;n.fontSize=l.size*2;n.lineHeight={unit:'PIXELS',value:l.leading*2};
      n.fills=solid(l.color);n.textAlignHorizontal=l.align==='right'?'RIGHT':'LEFT';
      n.resize((l.w+1.5)*px,l.h*px);n.textAutoResize='HEIGHT';n.layoutSizingVertical='HUG';
      if(n.height > l.h*px+2) warnings.push({page:p.number,layer:l.id,expected:l.h*px,actual:n.height});
      if(l.y*px+n.height>250*px)warnings.push({page:p.number,layer:l.id,bottom:l.y*px+n.height});
    } else if(l.type==='svg'){
      n=track(figma.createNodeFromSvg(l.svg));frame.appendChild(n);
      for(const child of n.findAll())createdNodeIds.push(child.id);
      n.resize(l.w*px,l.h*px);n.x=l.x*px;n.y=l.y*px;n.name=l.id+' / вектор';
    } else if(l.type==='photo' && l.crop){
      n=track(figma.createFrame());frame.appendChild(n);n.fills=[];n.clipsContent=true;
      n.resize(l.w*px,l.h*px);n.x=l.x*px;n.y=l.y*px;n.name=l.id+' / фрагмент';
      const im=track(figma.createRectangle());n.appendChild(im);
      const [x0,y0,x1,y1]=l.crop;im.resize(l.w*px/(x1-x0),l.h*px/(y1-y0));
      im.x=-x0*im.width;im.y=-y0*im.height;im.name='Исходное изображение';
      im.fills=[{type:'IMAGE',imageHash:hashes[l.file],scaleMode:'FILL'}];
    } else {
      n=track(figma.createRectangle());frame.appendChild(n);
      n.resize(l.w*px,l.h*px);n.x=l.x*px;n.y=l.y*px;n.name=l.id+' / '+l.type;
      n.fills=l.type==='photo'?[{type:'IMAGE',imageHash:hashes[l.file],scaleMode:'FILL'}]:solid(l.color);
    }
    records.push({page:p.number,layer:l.id,nodeId:n.id,type:l.type,source_id:l.source_id,figure_source_id:l.figure_source_id});
  }
  frame.placeholder=false;
  if(frame.parent && 'placeholder' in frame.parent){frame.parent.placeholder=false;mutatedNodeIds.push(frame.parent.id);}
}
return {createdNodeIds,mutatedNodeIds,records,warnings};
