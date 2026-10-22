const $ = (selector) => document.querySelector(selector);
const state = { books: [], filter: "all", query: "", currentBook: null, chapterIndex: -1, font: Number(localStorage.getItem("visu-font") || 20) };
const favorites = new Set(JSON.parse(localStorage.getItem("visu-favorites") || "[]"));
const escapeHTML = (s) => String(s ?? "").replace(/[&<>"']/g, (ch) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" })[ch]);
const strip = (s) => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const byId = (id) => state.books.find((book) => book.id === id);
const isAvailable = (book) => book.status === "available" && Array.isArray(book.chapters) && book.chapters.length > 0;
let toastTimer;
function toast(message) { const el = $("#toast"); el.textContent = message; el.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 2800); }
function persist() { try { localStorage.setItem("visu-favorites", JSON.stringify([...favorites])); } catch {} }
function applyTheme() { document.documentElement.classList.toggle("light", localStorage.getItem("visu-theme") === "light"); $("#themeIcon").textContent = document.documentElement.classList.contains("light") ? "☀" : "☾"; }
function toggleTheme() { const next = document.documentElement.classList.contains("light") ? "dark" : "light"; localStorage.setItem("visu-theme",next); applyTheme(); }
function renderCover(book) {
 const a = /^#[0-9a-fA-F]{6}$/.test(book.coverA) ? book.coverA : "#352d41";
 const b = /^#[0-9a-fA-F]{6}$/.test(book.coverB) ? book.coverB : "#171823";
 return '<div class="book-cover" style="--cover-a:'+a+';--cover-b:'+b+'"><span class="cover-label">visuNovel / LIBRARY</span><span class="cover-symbol">'+escapeHTML(book.symbol || "V")+'</span><span class="book-status '+(isAvailable(book) ? "available":"")+'">'+(isAvailable(book)?"CÓ THỂ ĐỌC":"CHỜ PHÁT HÀNH")+'</span></div>';
}
function renderLibrary() {
 const books = state.books.filter((b) => (state.filter === "all" || (state.filter === "available" && isAvailable(b)) || (state.filter === "pending" && !isAvailable(b)) || (state.filter === "saved" && favorites.has(b.id))) && strip(b.title+" "+b.author+" "+b.genres.join(" ")).includes(strip(state.query)));
 $("#bookCount").textContent = state.books.length + " tác phẩm";
 $("#bookGrid").innerHTML = books.length ? books.map((b) => '<article class="book-card">'+renderCover(b)+'<div class="book-info"><div class="book-category">'+escapeHTML(b.genres.join(" • "))+'</div><h3 class="book-title">'+escapeHTML(b.title)+'</h3><p class="book-summary">'+escapeHTML(b.summary)+'</p><div class="book-meta"><span>'+ (isAvailable(b) ? b.chapters.length+" chương" : "Đang chuẩn bị")+'</span><div class="card-actions"><button class="save-button '+(favorites.has(b.id)?"saved":"")+'" data-fav="'+escapeHTML(b.id)+'" aria-label="Lưu truyện" aria-pressed="'+favorites.has(b.id)+'">'+(favorites.has(b.id)?"♥":"♡")+'</button><button class="card-link" data-book="'+escapeHTML(b.id)+'">Chi tiết →</button></div></div></div></article>').join("") : '<div class="empty-state">Không có tác phẩm phù hợp. Hãy thử từ khóa khác.</div>';
}
function showSection(which) {
 $("#homeView").classList.toggle("hidden",which!=="home");
 $("#bookView").classList.toggle("hidden",which!=="book");
 $("#readerView").classList.toggle("hidden",which!=="reader");
 $(".footer").classList.toggle("hidden",which==="reader");
 window.scrollTo({top:0,behavior:"instant"});
}
function openBook(id, updateHash = true) {
 const book = byId(id);
 if(!book) { goHome(); return; }
 state.currentBook = book; state.chapterIndex = -1;
 const safeUrl = /^https:\/\/(m\.munpia\.com|series\.naver\.com)\//.test(book.sourceUrl || "") ? book.sourceUrl : "";
 const detail = '<div class="book-detail">'+renderCover(book)+'<div><p class="section-kicker">THE VISUNOVEL COLLECTION</p><h1 class="detail-title">'+escapeHTML(book.title)+'</h1><div class="detail-info">Tác giả: '+escapeHTML(book.author)+'<br>'+escapeHTML(book.originalTitle||"")+'</div><div class="detail-tags">'+book.genres.map((g)=>'<span>'+escapeHTML(g)+'</span>').join("")+'</div><p class="detail-info">'+escapeHTML(book.description)+'</p>'+(book.status!=="available"?'<div class="notice">Tác phẩm này chưa được phát hành trên visuNovel. Nội dung chỉ được đăng khi có quyền dịch, phân phối và đã hoàn tất kiểm duyệt.</div>':'')+'<div class="detail-actions">'+(isAvailable(book)?'<button class="primary-button" data-read="0">Bắt đầu đọc ↗</button>':'')+(safeUrl?'<a class="secondary-button" href="'+safeUrl+'" target="_blank" rel="noopener noreferrer">Xem bản gốc ↗</a>':'')+'</div></div></div>';
 $("#bookContent").innerHTML = detail+(isAvailable(book)?'<div class="chapter-list"><h2 class="chapter-heading">Mục lục</h2>'+book.chapters.map((c,i)=>'<div class="chapter-row"><button data-read="'+i+'">'+escapeHTML(c.title)+'</button><span>CHƯƠNG '+String(i+1).padStart(2,"0")+'</span></div>').join("")+'</div>':'');
 showSection("book");
 if(updateHash) location.hash = "book/"+encodeURIComponent(book.id);
 document.title = book.title+" — visuNovel";
}
async function openChapter(index, updateHash=true) {
 const book=state.currentBook;
 if(!book || !isAvailable(book) || !book.chapters[index]) return;
 const chapter=book.chapters[index];
 try {
  const res=await fetch("./"+chapter.path,{cache:"no-store"});
  if(!res.ok) throw Error("HTTP "+res.status);
  const data=await res.json();
  if(data.bookId!==book.id || !Array.isArray(data.paragraphs)) throw Error("Sai cấu trúc chương");
  state.chapterIndex=index;
  $("#readerMeta").textContent=book.title+" / CHƯƠNG "+String(index+1).padStart(2,"0");
  $("#readerTitle").textContent=data.title;
  $("#chapterBody").replaceChildren(...data.paragraphs.map((value)=>{
   const p=document.createElement("p");p.textContent=value;
   if(/^[“"—–-]/.test(value)) p.className="dialogue";
   return p;
  }));
  $("#prevChapter").disabled=index===0;$("#nextChapter").disabled=index===book.chapters.length-1;
  $("#chapterBody").style.setProperty("--reader-size",state.font+"px");
  showSection("reader");
  updateProgress();
  if(updateHash) location.hash = "read/"+encodeURIComponent(book.id)+"/"+index;
  document.title=data.title+" — visuNovel";
  try {localStorage.setItem("visu-last-read",JSON.stringify({bookId:book.id,index}));} catch {}
 } catch(e){ console.error(e);toast("Không tải được chương. Hãy thử lại."); }
}
function updateProgress(){
 if(!$("#readerView") || $("#readerView").classList.contains("hidden")) return;
 const root=document.documentElement;
 const max=root.scrollHeight-root.clientHeight;
 $("#readerProgress").style.width=(max>0?Math.min(100,Math.round(root.scrollTop/max*100)):100)+"%";
}
function goHome() {showSection("home");state.currentBook=null;state.chapterIndex=-1;document.title="visuNovel — Đọc một thế giới khác";location.hash="home";}
function route() {
 const hash=decodeURIComponent(location.hash.slice(1)); const [kind,id,index]=hash.split("/");
 if(kind==="book"&&byId(id)) return openBook(id,false);
 if(kind==="read"&&byId(id)) {state.currentBook=byId(id);return openChapter(Number(index),false);}
 showSection("home");
 if(kind==="library") setTimeout(()=>$("#library").scrollIntoView(),30);
 if(kind==="about") setTimeout(()=>$("#about").scrollIntoView(),30);
}
document.addEventListener("click",(e)=>{
 const fav=e.target.closest("[data-fav]"); if(fav){const id=fav.dataset.fav;favorites.has(id)?favorites.delete(id):favorites.add(id);persist();renderLibrary();toast(favorites.has(id)?"Đã lưu vào thư viện của bạn":"Đã bỏ lưu");return;}
 const book=e.target.closest("[data-book]");if(book){openBook(book.dataset.book);return;}
 const read=e.target.closest("[data-read]");if(read){openChapter(Number(read.dataset.read));return;}
 const filter=e.target.closest("[data-filter]");if(filter){state.filter=filter.dataset.filter;document.querySelectorAll("[data-filter]").forEach(el=>{el.classList.toggle("active",el===filter);el.setAttribute("aria-pressed",String(el===filter));});renderLibrary();}
});
$("#themeButton").addEventListener("click",toggleTheme);
$("#readerTheme").addEventListener("click",toggleTheme);
$("#searchInput").addEventListener("input",e=>{state.query=e.target.value;renderLibrary();});
$("#bookBack").addEventListener("click",goHome);
$("#readerBack").addEventListener("click",()=>openBook(state.currentBook.id));
$("#fontDown").addEventListener("click",()=>{state.font=Math.max(16,state.font-1);$("#chapterBody").style.setProperty("--reader-size",state.font+"px");localStorage.setItem("visu-font",String(state.font));});
$("#fontUp").addEventListener("click",()=>{state.font=Math.min(28,state.font+1);$("#chapterBody").style.setProperty("--reader-size",state.font+"px");localStorage.setItem("visu-font",String(state.font));});
$("#prevChapter").addEventListener("click",()=>openChapter(state.chapterIndex-1));
$("#nextChapter").addEventListener("click",()=>openChapter(state.chapterIndex+1));
window.addEventListener("hashchange",route);
window.addEventListener("scroll",updateProgress,{passive:true});
applyTheme();
(async()=>{try{const res=await fetch("./data/library.json");if(!res.ok)throw Error("HTTP "+res.status);const data=await res.json();state.books=data.books;renderLibrary();route();}catch(e){console.error(e);$("#bookGrid").innerHTML='<div class="empty-state">Không tải được thư viện. Hãy thử tải lại trang.</div>';}})();