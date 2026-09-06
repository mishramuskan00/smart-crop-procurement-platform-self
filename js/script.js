
// Mobile navigation
const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");
if(menuToggle){
  menuToggle.addEventListener("click", () => navLinks.classList.toggle("open"));
}

// Homepage multimedia slider
const slides = [...document.querySelectorAll(".slide")];
const dots = [...document.querySelectorAll(".dot")];
let currentSlide = 0;
let sliderTimer;

function showSlide(index){
  if(!slides.length) return;
  currentSlide = (index + slides.length) % slides.length;
  slides.forEach((s,i)=>s.classList.toggle("active",i===currentSlide));
  dots.forEach((d,i)=>d.classList.toggle("active",i===currentSlide));
}

function startSlider(){
  if(slides.length > 1){
    clearInterval(sliderTimer);
    sliderTimer = setInterval(()=>showSlide(currentSlide+1),5000);
  }
}
document.querySelector(".prev")?.addEventListener("click",()=>{showSlide(currentSlide-1);startSlider();});
document.querySelector(".next")?.addEventListener("click",()=>{showSlide(currentSlide+1);startSlider();});
dots.forEach((dot,i)=>dot.addEventListener("click",()=>{showSlide(i);startSlider();}));
startSlider();

// Search: simple client-side highlight/message for the static demo
const searchForm = document.querySelector("#siteSearch");
if(searchForm){
  searchForm.addEventListener("submit",(e)=>{
    e.preventDefault();
    const q = searchForm.querySelector("input").value.trim();
    if(!q){ alert("कृपया खोज शब्द दर्ज करें।"); return; }
    alert("डेमो खोज: " + q + "\\nइस static prototype में आप अपने वास्तविक search backend/API को बाद में जोड़ सकते हैं।");
  });
}

// Current year
document.querySelectorAll("[data-year]").forEach(el=>el.textContent=new Date().getFullYear());

// Login demo
document.querySelector("#loginForm")?.addEventListener("submit",(e)=>{
  e.preventDefault();
  const user = document.querySelector("#username").value.trim();
  if(!user){ alert("कृपया मोबाइल/यूज़र आईडी दर्ज करें।"); return; }
  alert("डेमो लॉगिन सफल। वास्तविक authentication/API बाद में जोड़ा जा सकता है।");
});
