const $ = (id) => document.getElementById(id);
const text = $("text"), go = $("go"), errBox = $("error");

function words(t){ const m = t.trim().match(/\S+/g); return m ? m.length : 0; }
function showError(msg){ errBox.textContent = msg; errBox.hidden = !msg; }

async function api(url, options){
  let res;
  try { res = await fetch(url, options); }
  catch { throw new Error("Cannot reach the server. Make sure it is still running."); }
  let data = {};
  try { data = await res.json(); } catch {}
  if (!res.ok) throw new Error(data.error || "Something went wrong (" + res.status + ").");
  return data;
}

text.addEventListener("input", () => { $("count").textContent = words(text.value) + " words"; });
$("ratio").addEventListener("input", (e) => { $("ratioVal").textContent = e.target.value + "%"; });
$("clear").addEventListener("click", () => { text.value = ""; text.dispatchEvent(new Event("input")); $("result").hidden = true; showError(""); });

$("file").addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => { text.value = reader.result; text.dispatchEvent(new Event("input")); showError(""); };
  reader.onerror = () => showError("Could not read that file. Try a plain .txt file.");
  reader.readAsText(f);
  e.target.value = "";
});

function render(item){
  $("summary").textContent = item.summary;
  const pct = Math.round((1 - item.summary_words / item.original_words) * 100);
  $("stats").textContent = item.original_words + " words → " + item.summary_words + " words (" + pct + "% shorter)";
  const box = $("original");
  box.textContent = "";
  const keep = new Set(item.selected);
  item.sentences.forEach((s, i) => {
    const node = keep.has(i) ? document.createElement("mark") : document.createElement("span");
    node.textContent = s;
    box.appendChild(node);
    box.appendChild(document.createTextNode(" "));
  });
  $("result").hidden = false;
}

go.addEventListener("click", async () => {
  showError("");
  go.disabled = true; go.textContent = "Summarizing…";
  try {
    const item = await api("/api/summarize", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ text: text.value, ratio: $("ratio").value / 100 })
    });
    render(item);
    $("result").scrollIntoView({behavior: "smooth", block: "start"});
    loadHistory();
  } catch (e) { showError(e.message); }
  finally { go.disabled = false; go.textContent = "Summarize"; }
});

$("copy").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("summary").textContent); $("copy").textContent = "Copied"; }
  catch { $("copy").textContent = "Press Ctrl+C"; }
  setTimeout(() => { $("copy").textContent = "Copy"; }, 1500);
});

async function loadHistory(){
  try {
    const items = await api("/api/history");
    const list = $("list");
    list.textContent = "";
    $("empty").hidden = items.length > 0;
    items.forEach((it) => {
      const li = document.createElement("li");
      const open = document.createElement("button");
      open.className = "open"; open.type = "button";
      const pv = document.createElement("span"); pv.className = "pv"; pv.textContent = it.preview || "(empty)";
      const meta = document.createElement("span"); meta.className = "meta";
      meta.textContent = it.created_at + " · " + it.original_words + " → " + it.summary_words + " words";
      open.append(pv, meta);
      open.addEventListener("click", async () => {
        try {
          const full = await api("/api/history/" + it.id);
          text.value = full.original; text.dispatchEvent(new Event("input"));
          render(full); showError("");
        } catch (e) { showError(e.message); loadHistory(); }
      });
      const del = document.createElement("button");
      del.className = "del"; del.type = "button"; del.textContent = "×"; del.setAttribute("aria-label", "Delete this summary");
      del.addEventListener("click", async () => {
        try { await api("/api/history/" + it.id, {method: "DELETE"}); loadHistory(); }
        catch (e) { showError(e.message); }
      });
      li.append(open, del);
      list.appendChild(li);
    });
  } catch (e) { showError(e.message); }
}

$("clearAll").addEventListener("click", async () => {
  if (!confirm("Delete all saved summaries?")) return;
  try { await api("/api/history", {method: "DELETE"}); loadHistory(); }
  catch (e) { showError(e.message); }
});

loadHistory();
