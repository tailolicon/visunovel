import {validateFiles,decodeUtf8,paragraphs,chapterLabel} from "./personal-core.mjs";
import {setupControls,renderList} from "./personal-ui.mjs";
const $=id=>document.getElementById(id);
const state={entries:[],current:-1,ticket:0};
const welcome=$("welcome"),reader=$("reader"),input=$("fileInput"),prose=$("chapterText");
function error(message){$("errorMessage").textContent=message;$("errorMessage").hidden=false;}
function resetError(){$("errorMessage").textContent="";$("errorMessage").hidden=true;}
async function show(index){
 if(index<0||index>=state.entries.length)return;
 const ticket=++state.ticket,entry=state.entries[index];
 try{
  const data=decodeUtf8(new Uint8Array(await entry.file.arrayBuffer()));
  if(ticket!==state.ticket)return;
  const fragment=document.createDocumentFragment();
  for(const line of paragraphs(data)){const p=document.createElement("p");p.textContent=line;fragment.append(p);}
  prose.replaceChildren(fragment);state.current=index;
  $("readerTitle").textContent=entry.title;
  $("chapterKicker").textContent=chapterLabel(entry);
  $("sourceFilename").textContent=entry.name+" · chỉ trong phiên hiện tại";
  $("prevChapter").disabled=index===0;$("nextChapter").disabled=index===state.entries.length-1;
  renderList(state,show);
  welcome.hidden=true;reader.hidden=false;scrollTo(0,0);$("readerTitle").focus({preventScroll:true});
 }catch(e){if(ticket===state.ticket)error("Không đọc được "+entry.name+": "+e.message);}
}
async function load(files){
 resetError();
 try{
  const entries=validateFiles(files);
  state.entries=entries;state.current=-1;
  $("collectionSummary").textContent=entries.length+" tệp · chỉ lưu trong tab này";
  $("chapterCount").textContent=String(entries.length);
  const preferred=entries.findIndex(item=>item.chapter!==null&&item.chapter>=137);
  await show(preferred<0?0:preferred);
 }catch(e){error(e.message);}
}
input.addEventListener("change",()=>{if(input.files.length)void load(input.files);input.value="";});
const drop=$("dropzone");
drop.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();input.click();}});
drop.addEventListener("dragover",e=>{e.preventDefault();drop.classList.add("dragging");});
drop.addEventListener("dragleave",()=>drop.classList.remove("dragging"));
drop.addEventListener("drop",e=>{e.preventDefault();drop.classList.remove("dragging");if(e.dataTransfer.files.length)void load(e.dataTransfer.files);});
setupControls(state,show,()=>{state.ticket++;state.entries=[];state.current=-1;prose.replaceChildren();$("chapterList").replaceChildren();reader.hidden=true;welcome.hidden=false;resetError();$("statusMessage").textContent="Đã xóa bộ tệp khỏi tab.";});
addEventListener("pagehide",()=>{state.ticket++;state.entries=[];prose.replaceChildren();});
