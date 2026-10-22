export const MAX_FILE_BYTES = 5 * 1024 * 1024;
export const MAX_TOTAL_BYTES = 30 * 1024 * 1024;
export const MAX_FILES = 200;
export function chapterNumber(name) {
  const base=String(name||"").replace(/\.(txt|md)$/i,"").replace(/\.vi$/i,"");
  const m=base.match(/(?:chapter|chap|chuong|chương|ch)[ ._-]*([0-9]{1,5})/i);
  if(m)return Number(m[1]);
  const last=base.match(/(?:^|[ ._-])([0-9]{1,5})$/);
  return last?Number(last[1]):null;
}
export function readableTitle(name) {
 return String(name||"").replace(/\.(txt|md)$/i,"").replace(/\.vi$/i,"").replace(/[_-]+/g," ").trim()||"Chương không tên";
}
export function sortChapterFiles(files) {
 return Array.from(files,(file,originalIndex)=>({file,originalIndex,name:file.name,chapter:chapterNumber(file.name),title:readableTitle(file.name)})).sort((a,b)=>{
   if(a.chapter!==null&&b.chapter===null)return -1;
   if(a.chapter===null&&b.chapter!==null)return 1;
   if(a.chapter!==null&&b.chapter!==null&&a.chapter!==b.chapter)return a.chapter-b.chapter;
   return a.name.localeCompare(b.name,"vi",{numeric:true})||a.originalIndex-b.originalIndex;
 });
}
export function validateFiles(files) {
 const list=Array.from(files);
 if(!list.length)throw Error("Chưa chọn tệp.");
 if(list.length>MAX_FILES)throw Error("Tối đa 200 tệp.");
 let total=0;
 for(const f of list){
  if(!/\.(txt|md)$/i.test(f.name))throw Error("Chỉ hỗ trợ TXT và MD.");
  if(!Number.isSafeInteger(f.size)||f.size<0||f.size>MAX_FILE_BYTES)throw Error("Tệp vượt 5 MB: "+f.name);
  total+=f.size;
 }
 if(total>MAX_TOTAL_BYTES)throw Error("Tổng dung lượng vượt 30 MB.");
 return sortChapterFiles(list);
}
export function decodeUtf8(bytes) {
 const text=new TextDecoder("utf-8",{fatal:true}).decode(bytes).replace(/\r\n?/g,"\n");
 if(!text.trim())throw Error("Tệp rỗng.");
 return text;
}
export function paragraphs(text){return text.split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean);}
export function chapterLabel(x){return x.chapter===null?x.title:"Chương "+x.chapter;}
