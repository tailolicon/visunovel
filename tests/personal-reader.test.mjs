import test from "node:test";
import assert from "node:assert/strict";
import {chapterNumber,sortChapterFiles,validateFiles,decodeUtf8,paragraphs,MAX_FILE_BYTES} from "../assets/personal-core.mjs";
const f=(name,size=100)=>({name,size});
test("Chapter number and private draft filename",()=>{
 assert.equal(chapterNumber("chapter-137.vi.txt"),137);
 assert.equal(chapterNumber("Chương 142.md"),142);
 assert.equal(chapterNumber("the-demon-king-overrun-chapter-150.vi.txt"),150);
 assert.equal(chapterNumber("137.txt"),137);
 assert.equal(chapterNumber("notes.md"),null);
});
test("Numerical ordering with unknown files last",()=>{
 assert.deepEqual(sortChapterFiles([f("notes.md"),f("chapter-150.txt"),f("chapter-137.md")]).map(x=>x.chapter),[137,150,null]);
});
test("Duplicates are not silently overwritten",()=>{
 assert.equal(sortChapterFiles([f("chapter-137.txt"),f("chapter-137.md")]).length,2);
});
test("Input validation and size limits",()=>{
 assert.throws(()=>validateFiles([]));
 assert.throws(()=>validateFiles([f("index.html")]));
 assert.throws(()=>validateFiles([f("chapter-137.txt",MAX_FILE_BYTES+1)]));
 assert.throws(()=>validateFiles(Array.from({length:201},(_,i)=>f("chapter-"+i+".txt"))));
 assert.throws(()=>validateFiles(Array.from({length:7},(_,i)=>f("chapter-"+i+".txt",MAX_FILE_BYTES))));
});
test("UTF-8 and paragraph boundaries",()=>{
 const text=decodeUtf8(new TextEncoder().encode("Xin chào\r\n\r\nĐoạn sau"));
 assert.deepEqual(paragraphs(text),["Xin chào","Đoạn sau"]);
 assert.throws(()=>decodeUtf8(new Uint8Array([255,254])));
 assert.throws(()=>decodeUtf8(new TextEncoder().encode("   ")));
});
