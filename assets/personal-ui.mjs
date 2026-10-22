const $=id=>document.getElementById(id);
export function renderList(state,show){
 const list=$("chapterList"),fragment=document.createDocumentFragment();
 for(let i=0;i<state.entries.length;i++){
  const entry=state.entries[i],li=document.createElement("li"),b=document.createElement("button");
  b.type="button";b.textContent=entry.chapter===null?entry.title:"Chương "+entry.chapter;
  b.title=entry.name;
  if(i===state.current)b.setAttribute("aria-current","page");
  b.addEventListener("click",()=>void show(i));li.append(b);fragment.append(li);
 }
 list.replaceChildren(fragment);
}
export function setupControls(state,show,clear){
 $("clearButton").addEventListener("click",clear);
 $("prevChapter").addEventListener("click",()=>void show(state.current-1));
 $("nextChapter").addEventListener("click",()=>void show(state.current+1));
 document.addEventListener("keydown",e=>{
  if($("reader").hidden||!e.altKey||e.ctrlKey||e.metaKey||e.shiftKey)return;
  if(["INPUT","TEXTAREA","SELECT"].includes(document.activeElement?.tagName))return;
  if(e.key==="ArrowLeft"&&state.current>0){e.preventDefault();void show(state.current-1);}
  if(e.key==="ArrowRight"&&state.current<state.entries.length-1){e.preventDefault();void show(state.current+1);}
 });
 let font=20;
 const update=()=>{
  document.documentElement.style.setProperty("--size",font+"px");
  $("fontLabel").textContent=font+" px";
  $("fontDown").disabled=font===16;$("fontUp").disabled=font===30;
 };
 $("fontDown").addEventListener("click",()=>{font=Math.max(16,font-1);update();});
 $("fontUp").addEventListener("click",()=>{font=Math.min(30,font+1);update();});
 update();
 $("themeToggle").addEventListener("click",()=>{
  const root=document.documentElement;
  const light=root.dataset.theme==="light"||(!root.dataset.theme&&matchMedia("(prefers-color-scheme:light)").matches);
  root.dataset.theme=light?"dark":"light";
  $("themeToggle").setAttribute("aria-label",light?"Chuyển sang sáng":"Chuyển sang tối");
 });
}
