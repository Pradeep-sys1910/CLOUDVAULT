const API = "http://127.0.0.1:5000";

/* ================= SIGNUP ================= */
async function signup() {
    const btn = event.target;
    btn.innerText = "Creating...";

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if(!name || !email || !password){
        alert("Please fill all fields");
        btn.innerText = "Signup";
        return;
    }

    const res = await fetch(API+"/signup",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name,email,password})
    });

    const data = await res.json();
    alert(data.message || data.error);

    if(res.status === 201){
        window.location="login.html";
    }

    btn.innerText = "Signup";
}

/* ================= LOGIN ================= */
async function login(){
    const btn = event.target;
    btn.innerText = "Logging in...";

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    const res = await fetch(API+"/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email,password})
    });

    const data = await res.json();

    if(data.token){
        localStorage.setItem("token", data.token);
        window.location="dashboard.html";
    }else{
        alert(data.error);
    }

    btn.innerText = "Login";
}

/* ================= LOGOUT ================= */
function logout(){
    localStorage.removeItem("token");
    window.location="login.html";
}

/* ================= UPLOAD FILE ================= */
async function uploadFile(){
    const file = document.getElementById("fileInput").files[0];
    if(!file) return alert("Choose a file first");

    const formData = new FormData();
    formData.append("file", file);

    await fetch(API+"/upload",{
        method:"POST",
        headers:{
            "Authorization":"Bearer " + localStorage.getItem("token")
        },
        body:formData
    });

    alert("Uploaded successfully ☁️");
    loadFiles();
    
}

/* ================= FILE ICON ================= */
function getFileIcon(name){
    const ext = name.split('.').pop().toLowerCase();

    if(["png","jpg","jpeg","gif"].includes(ext)) return "🖼️";
    if(["pdf"].includes(ext)) return "📄";
    if(["mp4","mov"].includes(ext)) return "🎬";
    if(["zip","rar"].includes(ext)) return "🗜️";
    return "📁";
}

/* ================= LOAD FILES ================= */
async function loadFiles(){
    const res = await fetch(API+"/files",{
        headers:{
            "Authorization":"Bearer " + localStorage.getItem("token")
        }
    });

    const files = await res.json();
    const list = document.getElementById("fileList");
    if(!list) return;

    list.innerHTML = "";

    if(files.length === 0){
        list.innerHTML = "No files uploaded yet";
        return;
    }

    files.forEach(file => {
        const url = `https://cloudvault-files-001.s3.ap-south-1.amazonaws.com/${file.name}`;

        list.innerHTML += `
        <div class="file-item">
            <div class="file-left">
                <span class="file-icon">${getFileIcon(file.name)}</span>
                <div>
                    <div>${file.name}</div>
                    <small>${file.size} KB</small>
                </div>
            </div>

            <div class="file-actions">
                <button onclick="downloadFile('${file.name}')">Download</button>

                <button onclick="deleteFile('${file.name}')">Delete</button>
            </div>
        </div>`;
    });
}

/* ================= DELETE FILE ================= */
async function deleteFile(filename){
    if(!confirm("Delete this file?")) return;

    await fetch(`${API}/delete/${filename}`,{
        method:"DELETE",
        headers:{
            "Authorization":"Bearer " + localStorage.getItem("token")
        }
    });

    loadFiles();
}
async function downloadFile(filename){
    const res = await fetch(`${API}/download/${filename}`,{
        headers:{
            "Authorization":"Bearer " + localStorage.getItem("token")
        }
    });

    const data = await res.json();
    window.open(data.url, "_blank");
}


/* ================= AUTO LOAD FILES ================= */
if(window.location.pathname.includes("dashboard.html")){
    loadFiles();
}
