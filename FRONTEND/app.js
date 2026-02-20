const API = "http://127.0.0.1:5000";

let allFiles = [];   // 🔥 store files globally for search + sort
/* ===== PAGE LOADER ON FIRST LOAD ===== */
window.addEventListener("load", () => {
    setTimeout(() => hideLoader(), 600);
});

/* ================= SIGNUP ================= */
async function signup() {
    const btn = document.getElementById("signupBtn");
    const msg = document.getElementById("signupMsg");

    btn.innerText = "Creating...";
    btn.disabled = true;

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    const res = await fetch(API + "/signup", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name,email,password})
    });

    const data = await res.json();

    if(res.status === 201){
        msg.innerHTML = "📧 Verification email sent! Please check your inbox.";
        btn.innerText = "Account Created";
    } else {
        msg.innerHTML = "❌ " + data.error;
        btn.innerText = "Create Account";
        btn.disabled = false;
    }
}


/* ================= LOGIN ================= */
async function login(){
    const btn = event.target;
    btn.innerText="Logging in...";

    const email=document.getElementById("email").value;
    const password=document.getElementById("password").value;

    const res=await fetch(API+"/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email,password})
    });

    const data=await res.json();

    if(data.token){
        localStorage.setItem("token",data.token);
        window.location="dashboard.html";
    }else alert(data.error);

    btn.innerText="Login";
}

/* ================= LOGOUT ================= */
function logout(){
    localStorage.removeItem("token");
    window.location="login.html";
}

/* ================= SHOW SELECTED FILE NAME ================= */
document.addEventListener("DOMContentLoaded",()=>{
    const input=document.getElementById("fileInput");
    if(input){
        input.addEventListener("change",()=>{
            if(input.files.length>0){
                input.title=input.files[0].name;
            }
        });
    }
});

/* ================= UPLOAD FILE ================= */
function uploadFile(){
    const file = document.getElementById("fileInput").files[0];
    if(!file) return alert("Choose a file");

    showLoader();

    const progressBox = document.getElementById("uploadProgressBox");
    const bar = document.getElementById("uploadProgress");
    const percentText = document.getElementById("uploadPercent");

    progressBox.classList.remove("progress-hidden");

    const xhr = new XMLHttpRequest();
    xhr.open("POST", API + "/upload");

    xhr.setRequestHeader(
        "Authorization",
        "Bearer " + localStorage.getItem("token")
    );

    xhr.upload.onprogress = (e) => {
        if(e.lengthComputable){
            let percent = Math.round((e.loaded/e.total)*100);
            bar.style.width = percent + "%";
            percentText.innerText = percent + "% uploading...";
        }
    };

    xhr.onload = () => {
        hideLoader();
        percentText.innerText = "Upload complete 🎉";
        setTimeout(()=>{
            progressBox.classList.add("progress-hidden");
            bar.style.width = "0%";
            loadFiles();
        },1200);
    };

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
}


/* ================= LOAD FILES ================= */
async function loadFiles(){

    // 🔥 SHOW SKELETON LOADING FIRST
    const list = document.getElementById("fileList");
    list.innerHTML = `
        <div class="skeleton"></div>
        <div class="skeleton"></div>
        <div class="skeleton"></div>
    `;

    const res = await fetch(API+"/files",{
        headers:{ "Authorization":"Bearer "+localStorage.getItem("token")}
    });

    const files = await res.json();
    allFiles = files;

    renderFiles(files);
    updateStorageStats(files);
}

/* ================= RENDER FILES ================= */
function renderFiles(files){
    const list=document.getElementById("fileList");
    list.innerHTML="";
    
    if(files.length===0){
        list.innerHTML="<p>No files uploaded</p>";
        return;
    }
    /* ================= STORAGE STATS ================= */
function updateStorageStats(files){
    let totalKB = 0;
    files.forEach(f => totalKB += f.size);

    let totalMB = (totalKB / 1024).toFixed(2);
    let count = files.length;

    const storageText = document.getElementById("storageText");
    if(storageText){
        storageText.innerText = `${totalMB} MB • ${count} files`;
    }
}


    files.forEach(file=>{
        // remove UUID prefix
        let clean=file.name;
        if(clean.includes("_")) clean=clean.substring(clean.indexOf("_")+1);

        list.innerHTML+=`
        <div class="file-card fade-in">
            <div class="file-name">📄 ${clean}</div>
            <div class="file-size">${file.size} KB</div>
            <button onclick="downloadFile('${file.name}')">Download</button>
            <button onclick="deleteFile('${file.name}')">Delete</button>
        </div>`;
    });
}

/* ================= SEARCH ================= */
function searchFiles(){
    const term=document.getElementById("searchInput").value.toLowerCase();

    const filtered=allFiles.filter(file=>{
        let name=file.name.toLowerCase();
        return name.includes(term);
    });

    renderFiles(filtered);
}

/* ================= SORT ================= */
function sortFiles(){
    const type=document.getElementById("sortSelect").value;
    let sorted=[...allFiles];

    if(type==="name"){
        sorted.sort((a,b)=>a.name.localeCompare(b.name));
    }
    if(type==="size"){
        sorted.sort((a,b)=>a.size-b.size);
    }

    renderFiles(sorted);
}

/* ================= DELETE ================= */
async function deleteFile(filename){
    if(!confirm("Delete this file?")) return;

    await fetch(API+"/delete/"+filename,{
        method:"DELETE",
        headers:{ "Authorization":"Bearer "+localStorage.getItem("token")}
    });

    loadFiles();
}

/* ================= DOWNLOAD ================= */
async function downloadFile(filename){
    const res=await fetch(API+"/download/"+filename,{
        headers:{ "Authorization":"Bearer "+localStorage.getItem("token")}
    });

    const data=await res.json();
    window.open(data.url,"_blank");
}

/* ================= SHOW SELECTED FILE NAME ================= */
function showFileName(){
    const file = document.getElementById("fileInput").files[0];
    const label = document.getElementById("selectedFileName");

    if(file){
        label.innerText = "Selected: " + file.name;
    }else{
        label.innerText = "";
    }
}
/* ================= FORGOT PASSWORD ================= */
async function forgotPassword(){
    const email = document.getElementById("resetEmail").value;
    const msg = document.getElementById("forgotMsg");

    const res = await fetch(API+"/forgot-password",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email})
    });

    const data = await res.json();
    msg.innerText = data.message || data.error;
}

/* ================= RESET PASSWORD ================= */
async function resetPassword(){
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    const password = document.getElementById("newPassword").value;
    const msg = document.getElementById("resetMsg");

    const res = await fetch(API+"/reset-password",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({token,password})
    });

    const data = await res.json();

    if(res.status===200){
        msg.innerHTML = "✅ Password updated! <br><a href='login.html'>Login</a>";
    } else {
        msg.innerText = data.error;
    }
}



/* ================= AUTO LOAD ================= */
if(window.location.pathname.includes("dashboard.html")){
    window.onload=loadFiles;
}
