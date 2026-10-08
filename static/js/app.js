let state={tasks:[],expenses:[],habits:[],notes:[],events:[],stats:{}};

const $=s=>document.querySelector(s);
const $$=s=>document.querySelectorAll(s);
function money(v){return "₹"+Number(v||0).toLocaleString("en-IN",{maximumFractionDigits:0})}
function toast(msg){const el=$("#toast");el.textContent=msg;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2200)}
async function api(url,opts={}){const r=await fetch(url,{headers:{"Content-Type":"application/json"},...opts});if(r.status===401){location.href="/login";return}const data=await r.json();if(!r.ok)throw new Error(data.error||"Something went wrong");return data}
async function load(){
 const d=await api("/api/dashboard");state=d;
 $("#pendingCount").textContent=d.stats.pending;$("#completedCount").textContent=d.stats.completed;$("#spentTotal").textContent=money(d.stats.spent);
 $("#avatar").textContent=(d.user.name||"D")[0].toUpperCase(); $("#sideDate").textContent=new Date().toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"});
 renderTasks();renderEvents();renderHabits();renderNotes();
}
function renderTasks(){
 $("#taskList").innerHTML=state.tasks.slice(0,6).map(t=>`
 <div class="task-row"><button class="check ${t.completed?'done':''}" onclick="toggleTask(${t.id},${!t.completed})">${t.completed?'✓':''}</button>
 <span class="task-title ${t.completed?'done':''}">${esc(t.title)}</span><span class="priority ${t.priority}">${t.priority}</span></div>`).join("")||'<div class="empty">No tasks yet.</div>';
}
function renderEvents(){
 $("#eventList").innerHTML=state.events.map(e=>`<div class="event"><div><strong>${esc(e.title)}</strong><br><small>${esc(e.kind)}</small></div><small>${fmtDate(e.event_date)} ${e.event_time||""}</small></div>`).join("")||'<div class="empty">Nothing scheduled.</div>';
}
function renderHabits(){
 $("#habitList").innerHTML=state.habits.map(h=>`<div class="habit-row"><div><strong>${esc(h.name)}</strong><br><span class="streak">🔥 ${h.streak} day streak</span></div><button class="habit-btn" onclick="habitDone(${h.id})">Done</button></div>`).join("");
}
function renderNotes(){
 $("#noteList").innerHTML=state.notes.map(n=>`<div class="note"><strong>${esc(n.title)}</strong><p>${esc(n.content).slice(0,130)}</p></div>`).join("");
}
function fmtDate(s){if(!s)return"";return new Date(s+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short"})}
function esc(s){return String(s||"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
async function toggleTask(id,completed){await api(`/api/tasks/${id}`,{method:"PATCH",body:JSON.stringify({completed})});await load();toast(completed?"Task completed":"Task reopened")}
async function habitDone(id){await api(`/api/habits/${id}/done`,{method:"POST"});await load();toast("Habit checked off")}
function openModal(id){$("#"+id).classList.add("open")}function closeModals(){$$(".modal").forEach(m=>m.classList.remove("open"))}
function form(type){
 const configs={
 task:{title:"Add a task",html:`<form class="form-grid" id="dynamicForm"><label>Task title<input name="title" placeholder="What needs to happen?" required></label><label>Priority<select name="priority"><option>high</option><option selected>medium</option><option>low</option></select></label><label>Due date<input type="date" name="due_date"></label><button class="primary" type="submit">Add task ↗</button></form>`},
 expense:{title:"Log an expense",html:`<form class="form-grid" id="dynamicForm"><label>What was it?<input name="title" placeholder="Lunch, travel, shopping..." required></label><label>Amount<input name="amount" type="number" step=".01" placeholder="0" required></label><label>Category<select name="category"><option>Food</option><option>Travel</option><option>Bills</option><option>Shopping</option><option>Health</option><option>Other</option></select></label><button class="primary" type="submit">Save expense ↗</button></form>`},
 note:{title:"Capture a note",html:`<form class="form-grid" id="dynamicForm"><label>Title<input name="title" placeholder="Idea, reminder, plan..." required></label><label>Note<textarea name="content" placeholder="Write it down."></textarea></label><button class="primary" type="submit">Save note ↗</button></form>`}
 };
 $("#formContent").innerHTML=`<span class="eyebrow">LIFE OS / ${type.toUpperCase()}</span><h2>${configs[type].title}</h2>${configs[type].html}`;
 openModal("formModal");
 $("#dynamicForm").onsubmit=async e=>{e.preventDefault();const d=Object.fromEntries(new FormData(e.target).entries());
 try{if(type==="task")await api("/api/tasks",{method:"POST",body:JSON.stringify(d)});if(type==="expense")await api("/api/expenses",{method:"POST",body:JSON.stringify(d)});if(type==="note")await api("/api/notes",{method:"POST",body:JSON.stringify(d)});closeModals();await load();toast("Saved");}catch(err){toast(err.message)}};
}
$$("[data-view]").forEach(btn=>btn.onclick=()=>activate(btn.dataset.view));
$$("[data-view-jump]").forEach(el=>el.onclick=()=>activate(el.dataset.viewJump));
function activate(view){
 $$(".nav-item").forEach(n=>n.classList.toggle("active",n.dataset.view===view));
 $("#currentViewLabel").textContent=view.toUpperCase();
 if(view==="overview")window.scrollTo({top:0,behavior:"smooth"});
 else if(view==="tasks")document.querySelector(".tasks-panel").scrollIntoView({behavior:"smooth",block:"center"});
 else if(view==="money")document.querySelector(".feature-card.black").scrollIntoView({behavior:"smooth",block:"center"});
 else if(view==="habits")document.querySelector(".lower-grid").scrollIntoView({behavior:"smooth",block:"center"});
 else if(view==="notes")document.querySelector(".note-list").scrollIntoView({behavior:"smooth",block:"center"});
 else if(view==="calendar")document.querySelector(".agenda-panel").scrollIntoView({behavior:"smooth",block:"center"});
 else if(view==="assistant")openAssistant();
 if(innerWidth<701)$("#sidebar").classList.remove("open");
}
function openAssistant() {
    $("#formContent").innerHTML = `
        <span class="eyebrow">LIFE OS / AI ASSISTANT</span>

        <h2>Ask your day a better question.</h2>

        <form class="form-grid" id="aiForm">

            <label>
                Question
                <textarea
                    id="aiPrompt"
                    name="prompt"
                    placeholder="What should I focus on today?"
                    required
                ></textarea>
            </label>

            <button
                class="primary"
                id="askAiBtn"
                type="submit">
                Ask Life OS ↗
            </button>

        </form>

        <div id="aiAnswer" class="ai-answer"></div>
    `;

    openModal("formModal");

    const form = $("#aiForm");
    const answerBox = $("#aiAnswer");
    const button = $("#askAiBtn");

    form.addEventListener("submit", async function(e) {

        e.preventDefault();

        const prompt = $("#aiPrompt").value.trim();

        if (!prompt) {
            answerBox.textContent = "Please enter a question.";
            return;
        }

        // Show loading
        button.disabled = true;
        button.textContent = "Thinking...";
        answerBox.textContent = "Life OS is thinking...";

        try {

            console.log("Sending AI request:", prompt);

            const response = await fetch("/api/ai", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    prompt: prompt
                })
            });

            console.log("AI response status:", response.status);

            const data = await response.json();

            console.log("AI response:", data);

            if (!response.ok) {
                throw new Error(
                    data.error || "AI request failed"
                );
            }

            answerBox.textContent =
                data.answer || "Life OS could not generate a response.";

        } catch (error) {

            console.error("AI ERROR:", error);

            answerBox.textContent =
                "AI Assistant error: " + error.message;

        } finally {

            button.disabled = false;
            button.textContent = "Ask Life OS ↗";

        }
    });
}
 $("#formContent").innerHTML=`<span class="eyebrow">LIFE OS / AI ASSISTANT</span><h2>Ask your day a better question.</h2><form class="form-grid" id="aiForm"><label>Question<textarea name="prompt" placeholder="What should I focus on today?"></textarea></label><button class="primary">Ask Life OS ↗</button></form><div id="aiAnswer" class="ai-answer"></div>`;
 openModal("formModal");
 $("#aiForm").onsubmit=async e=>{e.preventDefault();const prompt=new FormData(e.target).get("prompt");$("#aiAnswer").textContent="Thinking…";const r=await api("/api/ai",{method:"POST",body:JSON.stringify({prompt})});$("#aiAnswer").textContent=r.answer};

$("#quickAddBtn").onclick=()=>openModal("quickModal");
$$("[data-close]").forEach(b=>b.onclick=closeModals);
$$("[data-quick]").forEach(b=>b.onclick=()=>{closeModals();form(b.dataset.quick)});
$("#mobileMenu").onclick=()=>$("#sidebar").classList.toggle("open");
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModals()});
load().catch(()=>{});
/* =========================================
   DAY COUNTDOWN TIMER
   ========================================= */

function updateDayCountdown() {

    const now = new Date();

    // Midnight of tomorrow
    const tomorrow = new Date(now);

    tomorrow.setDate(now.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);

    // Remaining milliseconds
    const remaining = tomorrow - now;

    // Convert milliseconds
    const totalSeconds = Math.max(
        0,
        Math.floor(remaining / 1000)
    );

    const hours = Math.floor(totalSeconds / 3600);

    const minutes = Math.floor(
        (totalSeconds % 3600) / 60
    );

    const seconds = totalSeconds % 60;

    // Update timer
    const hoursElement = document.getElementById("countHours");
    const minutesElement = document.getElementById("countMinutes");
    const secondsElement = document.getElementById("countSeconds");

    if (hoursElement) {
        hoursElement.textContent =
            String(hours).padStart(2, "0");
    }

    if (minutesElement) {
        minutesElement.textContent =
            String(minutes).padStart(2, "0");
    }

    if (secondsElement) {
        secondsElement.textContent =
            String(seconds).padStart(2, "0");
    }

    // Calculate whole hours remaining
    const roundedHours = Math.ceil(
        remaining / (1000 * 60 * 60)
    );

    const hoursText =
        document.getElementById("hoursLeftText");
    if (hoursText) {

    if (hours === 1) {
        hoursText.textContent =
            "1 hour left in the day";
    } else {
        hoursText.textContent =
            `${hours} hours left in the day`;
    }
}

    // Current date
    const dateText =
        document.getElementById("currentDateText");

    if (dateText) {

        dateText.textContent =
            now.toLocaleDateString("en-IN", {
                weekday: "long",
                day: "2-digit",
                month: "long",
                year: "numeric"
            });
    }
}


// Run immediately
updateDayCountdown();


// Update every second
setInterval(updateDayCountdown, 1000);
