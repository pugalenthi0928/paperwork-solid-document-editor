'use strict';

const $ = (selector) => document.querySelector(selector);
let documentId = 'my-document';
let model = {
  title: 'My first SOLID document',
  elements: [
    { type: 'text', text: 'Hello world! This is a real document built with Python and SOLID design principles.' },
    { type: 'text', text: 'Try editing this text, adding an image, or rearranging the blocks on the left.' }
  ]
};
let renderSequence = 0;
let pendingPreview = null;
let toastTimeout = null;

$('#paperDate').textContent = new Date().toLocaleDateString('en-AU', {day: 'numeric', month: 'short', year: 'numeric'});

function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.classList.add('show');
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => node.classList.remove('show'), 3100);
}

async function api(path, data) {
  const response = await fetch(path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Server error ${response.status}`);
  return result;
}

function elementButton(symbol, title, handler, disabled = false) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'icon-btn';
  button.title = title;
  button.setAttribute('aria-label', title);
  button.textContent = symbol;
  button.disabled = disabled;
  button.addEventListener('click', handler);
  return button;
}

function renderBlocks() {
  const wrap = $('#blocks');
  wrap.replaceChildren();
  $('#blockCount').textContent = `${model.elements.length} BLOCK${model.elements.length === 1 ? '' : 'S'}`;
  model.elements.forEach((block, index) => {
    const card = document.createElement('section');
    card.className = 'block';
    const top = document.createElement('div');
    top.className = 'block-top';
    const title = document.createElement('div');
    title.className = 'block-type';
    const idx = document.createElement('span');
    idx.className = 'block-index';
    idx.textContent = String(index + 1).padStart(2, '0');
    const name = document.createElement('span');
    name.textContent = ({text:'Text block', image:'Image block', newline:'Line break', tab:'Indent'})[block.type] || block.type;
    title.append(idx, name);
    const controls = document.createElement('div');
    controls.className = 'block-controls';
    controls.append(
      elementButton('↑', 'Move up', () => act({kind: 'move', index, to: index - 1}), index === 0),
      elementButton('↓', 'Move down', () => act({kind: 'move', index, to: index + 1}), index === model.elements.length - 1),
      elementButton('×', 'Delete block', () => act({kind: 'remove', index}))
    );
    top.append(title, controls);
    const body = document.createElement('div');
    body.className = 'block-body';
    if (block.type === 'text') {
      const textarea = document.createElement('textarea');
      textarea.value = block.text;
      textarea.setAttribute('aria-label', 'Text for block ' + (index + 1));
      textarea.placeholder = 'Write something…';
      textarea.addEventListener('input', () => {
        model.elements[index].text = textarea.value;
        schedulePreview();
      });
      body.append(textarea);
    } else if (block.type === 'image') {
      const url = document.createElement('input');
      url.type = 'url';
      url.value = block.src;
      url.placeholder = 'https://example.com/photo.jpg';
      url.setAttribute('aria-label', 'Image URL');
      url.addEventListener('input', () => {
        model.elements[index].src = url.value;
        schedulePreview();
      });
      const caption = document.createElement('input');
      caption.className = 'minor-input';
      caption.value = block.alt || '';
      caption.placeholder = 'Image caption';
      caption.setAttribute('aria-label', 'Image caption');
      caption.addEventListener('input', () => {
        model.elements[index].alt = caption.value;
        schedulePreview();
      });
      body.append(url, caption);
    } else {
      const description = document.createElement('div');
      description.className = 'block-utility';
      description.textContent = block.type === 'newline' ? 'Inserts extra vertical space.' : 'Adds a small visual indentation.';
      body.append(description);
    }
    card.append(top, body);
    wrap.append(card);
  });
}

async function refreshPreview() {
  const sequence = ++renderSequence;
  $('#paperTitle').textContent = model.title || 'Untitled document';
  try {
    const result = await api('/api/preview', {document: model});
    if (sequence === renderSequence) $('#rendered').innerHTML = result.html;
  } catch (error) {
    if (sequence === renderSequence) $('#rendered').textContent = `Preview unavailable: ${error.message}`;
  }
}

function schedulePreview() {
  window.clearTimeout(pendingPreview);
  pendingPreview = window.setTimeout(refreshPreview, 200);
}

async function act(action) {
  try {
    const result = await api('/api/action', {document: model, action});
    model = result.document;
    renderBlocks();
    $('#rendered').innerHTML = result.html;
    $('#paperTitle').textContent = model.title;
  } catch (error) {
    toast(error.message);
  }
}

for (const button of document.querySelectorAll('[data-add]')) {
  button.addEventListener('click', () => {
    const type = button.dataset.add;
    const element = type === 'text' ? {type, text: ''}
      : type === 'image' ? {type, src: 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=900', alt: 'Workspace photograph'}
      : {type};
    act({kind: 'add', element});
  });
}

$('#titleInput').addEventListener('input', (event) => {
  model.title = event.target.value;
  $('#paperTitle').textContent = model.title || 'Untitled document';
  schedulePreview();
});

$('#saveBtn').addEventListener('click', async () => {
  try {
    await api('/api/save', {id: documentId, document: model});
    toast('Saved successfully as ' + documentId);
  } catch (error) { toast('Could not save: ' + error.message); }
});

$('#loadBtn').addEventListener('click', () => {
  $('#docId').value = documentId;
  $('#openDialog').showModal();
});

$('#openDialog').addEventListener('close', async () => {
  if ($('#openDialog').returnValue !== 'open') return;
  const id = $('#docId').value;
  if (!/^[A-Za-z0-9_-]{1,60}$/.test(id)) return toast('Use letters, numbers, underscores and hyphens only');
  try {
    const response = await fetch('/api/load?id=' + encodeURIComponent(id));
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Failed to load');
    model = result.document;
    documentId = id;
    $('#titleInput').value = model.title;
    $('#paperId').textContent = id;
    renderBlocks();
    await refreshPreview();
    toast('Opened ' + id);
  } catch (error) { toast(error.message); }
});

async function exportDocument(fmt) {
  try {
    // Save current edits first so download always matches the visible document.
    await api('/api/save', {id: documentId, document: model});
    const response = await fetch('/api/export?id=' + encodeURIComponent(documentId) + '&format=' + fmt);
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || 'Export failed');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = documentId + '.' + fmt;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('Exported ' + fmt.toUpperCase() + ' document');
  } catch (error) { toast(error.message); }
}

$('#exportHTML').addEventListener('click', () => exportDocument('html'));
$('#exportTXT').addEventListener('click', () => exportDocument('txt'));
renderBlocks();
refreshPreview();
