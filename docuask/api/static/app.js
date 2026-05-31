const sampleDocument = `Production readiness means designing for failure before users find it.

A timeout is a reliability boundary. It tells the application how long it is willing to wait for another service before giving up and returning control.

Retries can help with short failures, but retries without exponential backoff and jitter multiply traffic and can make a struggling dependency worse.

Health checks should distinguish whether a process is alive, whether an instance is ready for traffic, whether dependencies are available, and whether users can complete the critical workflow.`;

let selectedDocumentId = null;
let selectedDocumentTitle = "";

const elements = {
  answerMeta: document.querySelector("#answer-meta"),
  answerText: document.querySelector("#answer-text"),
  content: document.querySelector("#document-content"),
  documentFile: document.querySelector("#document-file"),
  documentForm: document.querySelector("#document-form"),
  documentList: document.querySelector("#document-list"),
  healthDetails: document.querySelector("#health-details"),
  healthDot: document.querySelector("#overall-dot"),
  healthStatus: document.querySelector("#overall-status"),
  loadSample: document.querySelector("#load-sample"),
  questionForm: document.querySelector("#question-form"),
  questionInput: document.querySelector("#question-input"),
  refreshHealth: document.querySelector("#refresh-health"),
  selectedDocument: document.querySelector("#selected-document"),
  sources: document.querySelector("#sources"),
  title: document.querySelector("#document-title"),
};

function setBusy(form, busy) {
  const button = form.querySelector("button[type='submit']");
  if (button) {
    button.disabled = busy;
    button.textContent = busy ? "Working..." : button.dataset.label;
  }
}

function setMessage(message, detail = "") {
  elements.answerMeta.textContent = message;
  if (detail) {
    elements.answerText.textContent = detail;
  }
}

function renderSources(sources) {
  elements.sources.innerHTML = "";
  for (const source of sources) {
    const node = document.createElement("div");
    node.className = "source";
    node.textContent = source.slice(0, 360);
    elements.sources.append(node);
  }
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const detail = body && body.detail ? body.detail : `Request failed with ${response.status}`;
    throw new Error(detail);
  }
  return body;
}

async function refreshHealth() {
  elements.refreshHealth.disabled = true;
  try {
    const health = await requestJson("/api/health");
    elements.healthDot.className = `health-dot ${health.status}`;
    elements.healthStatus.textContent = `Service ${health.status}`;
    elements.healthDetails.textContent = `database=${health.database} redis=${health.redis} llm=${health.llm}`;
  } catch (error) {
    elements.healthDot.className = "health-dot unhealthy";
    elements.healthStatus.textContent = "Health check failed";
    elements.healthDetails.textContent = error.message;
  } finally {
    elements.refreshHealth.disabled = false;
  }
}

function renderDocuments(documents) {
  elements.documentList.innerHTML = "";
  if (!documents.length) {
    const empty = document.createElement("p");
    empty.className = "selected-doc";
    empty.textContent = "No documents yet. Upload the sample to start the demo.";
    elements.documentList.append(empty);
    return;
  }

  for (const doc of documents) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "document-row";
    row.innerHTML = `
      <span>
        <strong>${doc.title}</strong>
        <span>${doc.chunk_count} chunks · id ${doc.id}</span>
      </span>
      <span class="status-pill ${doc.status}">${doc.status}</span>
    `;
    row.addEventListener("click", () => selectDocument(doc));
    elements.documentList.append(row);

    if (!selectedDocumentId && doc.status === "completed") {
      selectDocument(doc);
    }
  }
}

function selectDocument(doc) {
  selectedDocumentId = doc.id;
  selectedDocumentTitle = doc.title;
  elements.selectedDocument.textContent = `${doc.title} · ${doc.status}`;
}

async function loadDocuments() {
  const documents = await requestJson("/api/documents");
  renderDocuments(documents);
}

async function pollDocument(documentId) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const doc = await requestJson(`/api/documents/${documentId}`);
    selectDocument(doc);
    if (doc.status === "completed" || doc.status === "failed") {
      await loadDocuments();
      return doc;
    }
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
  await loadDocuments();
  return null;
}

async function handleDocumentSubmit(event) {
  event.preventDefault();
  elements.documentForm.querySelector("button[type='submit']").dataset.label = "Upload Document";
  setBusy(elements.documentForm, true);
  setMessage("Uploading document...", "The worker will chunk and embed the content.");
  try {
    const title = elements.title.value.trim();
    const content = elements.content.value.trim();
    if (!title || !content) {
      throw new Error("Title and content are required.");
    }
    const doc = await requestJson("/api/documents", {
      method: "POST",
      body: JSON.stringify({ title, content }),
    });
    selectDocument(doc);
    setMessage("Document queued.", "Waiting for background processing to finish.");
    const processed = await pollDocument(doc.id);
    if (processed && processed.status === "failed") {
      setMessage("Document processing failed.", processed.error_message || "Check worker logs.");
    } else {
      setMessage("Document ready.", "Ask a question to run retrieval and the LLM call.");
    }
  } catch (error) {
    setMessage("Document upload failed.", error.message);
  } finally {
    setBusy(elements.documentForm, false);
  }
}

async function handleQuestionSubmit(event) {
  event.preventDefault();
  elements.questionForm.querySelector("button[type='submit']").dataset.label = "Ask Question";
  setBusy(elements.questionForm, true);
  renderSources([]);
  setMessage("Asking DocuAsk...", "This is the path that slows down when Lab 2 injects latency.");
  try {
    const question = elements.questionInput.value.trim();
    if (!question) {
      throw new Error("Question is required.");
    }
    const payload = { question };
    if (selectedDocumentId) {
      payload.document_id = selectedDocumentId;
    }
    const answer = await requestJson("/api/questions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const latency = Math.round(answer.latency_ms);
    elements.answerMeta.textContent = `${selectedDocumentTitle || "All documents"} · ${latency} ms`;
    elements.answerText.textContent = answer.answer || "No answer returned.";
    renderSources(answer.sources || []);
  } catch (error) {
    setMessage("Question failed.", error.message);
  } finally {
    setBusy(elements.questionForm, false);
    refreshHealth();
  }
}

function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.addEventListener("load", () => {
    elements.title.value = file.name.replace(/\.[^.]+$/, "");
    elements.content.value = String(reader.result || "");
  });
  reader.readAsText(file);
}

function loadSampleDocument() {
  elements.title.value = "Production Readiness Notes";
  elements.content.value = sampleDocument;
}

function init() {
  elements.documentForm.querySelector("button[type='submit']").dataset.label = "Upload Document";
  elements.questionForm.querySelector("button[type='submit']").dataset.label = "Ask Question";
  loadSampleDocument();
  elements.loadSample.addEventListener("click", loadSampleDocument);
  elements.refreshHealth.addEventListener("click", refreshHealth);
  elements.documentForm.addEventListener("submit", handleDocumentSubmit);
  elements.questionForm.addEventListener("submit", handleQuestionSubmit);
  elements.documentFile.addEventListener("change", handleFileChange);
  refreshHealth();
  loadDocuments().catch((error) => setMessage("Could not load documents.", error.message));
}

init();
