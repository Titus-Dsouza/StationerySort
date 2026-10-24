/**
 * StationerySort — AI Stationery Organizer
 * Frontend Application Logic (Vanilla JavaScript)
 * Hacktoberfest Open-Source AI Challenge Week 3: “Slow and Steady”
 */

// Global Application State
const state = {
  items: [],
  categories: [],
  stats: {},
  activeCategory: 'all',
  activeStatus: 'all',
  searchQuery: '',
  activeProposal: null,
  ollamaInfo: { available: false, active_model: 'gemma4:12b' },
  editingItemId: null
};

// DOM Element References
const dom = {
  // Status & Header
  ollamaStatusPill: document.getElementById('ollamaStatusPill'),
  ollamaStatusText: document.getElementById('ollamaStatusText'),
  aiEngineLabel: document.getElementById('aiEngineLabel'),
  aboutAiBtn: document.getElementById('aboutAiBtn'),
  resetSampleBtn: document.getElementById('resetSampleBtn'),

  // AI Assistant
  aiPromptForm: document.getElementById('aiPromptForm'),
  aiPromptInput: document.getElementById('aiPromptInput'),
  aiSubmitBtn: document.getElementById('aiSubmitBtn'),
  proposalCard: document.getElementById('proposalCard'),
  proposalSourceBadge: document.getElementById('proposalSourceBadge'),
  proposalActionBadge: document.getElementById('proposalActionBadge'),
  proposalItemName: document.getElementById('proposalItemName'),
  proposalCategory: document.getElementById('proposalCategory'),
  proposalCurrentQty: document.getElementById('proposalCurrentQty'),
  proposalNewQty: document.getElementById('proposalNewQty'),
  proposalDelta: document.getElementById('proposalDelta'),
  proposalLowStockWarning: document.getElementById('proposalLowStockWarning'),
  proposalExplanationText: document.getElementById('proposalExplanationText'),
  proposalConfirmBtn: document.getElementById('proposalConfirmBtn'),
  proposalDeclineBtn: document.getElementById('proposalDeclineBtn'),
  chipButtons: document.querySelectorAll('.chip-btn'),

  // Stats
  statTotalItems: document.getElementById('statTotalItems'),
  statTotalUnits: document.getElementById('statTotalUnits'),
  statLowStock: document.getElementById('statLowStock'),
  statCategories: document.getElementById('statCategories'),
  lowStockStatCard: document.getElementById('lowStockStatCard'),

  // Controls & Filters
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  statusFilter: document.getElementById('statusFilter'),
  categoryPillsContainer: document.getElementById('categoryPillsContainer'),
  openAddItemModalBtn: document.getElementById('openAddItemModalBtn'),

  // Inventory Grid
  itemsGrid: document.getElementById('itemsGrid'),
  itemsLoading: document.getElementById('itemsLoading'),
  emptyState: document.getElementById('emptyState'),
  emptyResetBtn: document.getElementById('emptyResetBtn'),
  resultsCountBadge: document.getElementById('resultsCountBadge'),

  // Item Modal
  itemModal: document.getElementById('itemModal'),
  itemForm: document.getElementById('itemForm'),
  modalTitle: document.getElementById('modalTitle'),
  closeItemModalBtn: document.getElementById('closeItemModalBtn'),
  cancelModalBtn: document.getElementById('cancelModalBtn'),
  formItemId: document.getElementById('formItemId'),
  formItemName: document.getElementById('formItemName'),
  formItemCategory: document.getElementById('formItemCategory'),
  formItemUnit: document.getElementById('formItemUnit'),
  formItemQuantity: document.getElementById('formItemQuantity'),
  formItemMinStock: document.getElementById('formItemMinStock'),
  formItemLocation: document.getElementById('formItemLocation'),
  formItemNotes: document.getElementById('formItemNotes'),

  // About Modal
  aboutModal: document.getElementById('aboutModal'),
  closeAboutModalBtn: document.getElementById('closeAboutModalBtn'),
  aboutGotItBtn: document.getElementById('aboutGotItBtn'),

  // Toast Container
  toastContainer: document.getElementById('toastContainer')
};

// ==========================================================================
// Initialization & Data Loading
// ==========================================================================

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await checkSystemStatus();
  await refreshCategories();
  await loadItems();
});

async function checkSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.ollama) {
      state.ollamaInfo = data.ollama;
      updateOllamaStatusUi(data.ollama);
    }
    if (data.stats) {
      updateStatsUi(data.stats);
    }
  } catch (err) {
    console.warn('Status check failed:', err);
    updateOllamaStatusUi({ available: false, message: 'Server unreachable' });
  }
}

function updateOllamaStatusUi(ollama) {
  dom.ollamaStatusPill.className = 'status-pill';
  if (ollama.available) {
    dom.ollamaStatusPill.classList.add('status-online');
    dom.ollamaStatusText.textContent = `Gemma (${ollama.active_model}) Online`;
    dom.aiEngineLabel.textContent = `Gemma (${ollama.active_model})`;
    dom.ollamaStatusPill.title = `Connected to Ollama at ${ollama.host}. Local inference ready.`;
  } else {
    dom.ollamaStatusPill.classList.add('status-fallback');
    dom.ollamaStatusText.textContent = 'Offline Fallback Engine';
    dom.aiEngineLabel.textContent = 'Smart Fallback Engine (Offline)';
    dom.ollamaStatusPill.title = `Ollama not detected. Using built-in rule parser fallback.`;
  }
}

function updateStatsUi(stats) {
  state.stats = stats;
  dom.statTotalItems.textContent = stats.total_items ?? 0;
  dom.statTotalUnits.textContent = stats.total_units ?? 0;
  dom.statLowStock.textContent = stats.low_stock_count ?? 0;
  dom.statCategories.textContent = stats.total_categories ?? 0;
}

// ==========================================================================
// Items & Categories Fetching
// ==========================================================================

async function loadItems() {
  dom.itemsLoading.style.display = 'flex';
  dom.itemsGrid.style.display = 'none';
  dom.emptyState.style.display = 'none';

  try {
    const params = new URLSearchParams();
    if (state.searchQuery.trim()) params.append('search', state.searchQuery.trim());
    if (state.activeCategory && state.activeCategory !== 'all') params.append('category', state.activeCategory);
    if (state.activeStatus && state.activeStatus !== 'all') params.append('status', state.activeStatus);

    const res = await fetch(`/api/items?${params.toString()}`);
    const data = await res.json();
    state.items = data.items || [];
    renderItems(state.items);
  } catch (err) {
    showToast('Failed to load stationery items.', 'error');
  } finally {
    dom.itemsLoading.style.display = 'none';
  }
}

async function refreshCategories() {
  try {
    const res = await fetch('/api/categories');
    const data = await res.json();
    state.categories = data.categories || [];
    renderCategoryPills(state.categories);
  } catch (err) {
    console.error('Failed to load categories:', err);
  }
}

function renderCategoryPills(categories) {
  dom.categoryPillsContainer.innerHTML = '';

  // All Items pill
  const allBtn = document.createElement('button');
  allBtn.className = `cat-chip ${state.activeCategory === 'all' ? 'active' : ''}`;
  allBtn.dataset.category = 'all';
  allBtn.textContent = 'All Items';
  allBtn.addEventListener('click', () => setCategoryFilter('all'));
  dom.categoryPillsContainer.appendChild(allBtn);

  // Distinct category pills with badge counts
  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = `cat-chip ${state.activeCategory === cat.category ? 'active' : ''}`;
    btn.dataset.category = cat.category;
    btn.innerHTML = `${escapeHtml(cat.category)} <span style="opacity:0.75; font-size:0.75rem;">(${cat.count})</span>`;
    btn.addEventListener('click', () => setCategoryFilter(cat.category));
    dom.categoryPillsContainer.appendChild(btn);
  });
}

function setCategoryFilter(category) {
  state.activeCategory = category;
  document.querySelectorAll('.cat-chip').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.category === category);
  });
  loadItems();
}

// ==========================================================================
// Inventory Rendering
// ==========================================================================

function renderItems(items) {
  dom.resultsCountBadge.textContent = `${items.length} ${items.length === 1 ? 'item' : 'items'}`;

  if (items.length === 0) {
    dom.itemsGrid.style.display = 'none';
    dom.emptyState.style.display = 'flex';
    return;
  }

  dom.emptyState.style.display = 'none';
  dom.itemsGrid.style.display = 'grid';
  dom.itemsGrid.innerHTML = '';

  items.forEach(item => {
    const card = createItemCard(item);
    dom.itemsGrid.appendChild(card);
  });
}

function getCategoryColorClass(cat) {
  const c = (cat || '').toLowerCase();
  if (c.includes('writing')) return 'cat-writing';
  if (c.includes('paper') || c.includes('note')) return 'cat-paper';
  if (c.includes('correct') || c.includes('tool')) return 'cat-tools';
  if (c.includes('fasten') || c.includes('clip')) return 'cat-clips';
  if (c.includes('adhes')) return 'cat-adhesives';
  return 'cat-desk';
}

function createItemCard(item) {
  const card = document.createElement('article');
  card.className = `item-card ${item.is_low_stock ? 'is-low-stock' : ''}`;
  card.id = `item-card-${item.id}`;

  const isLow = item.is_low_stock;
  const progressRatio = item.min_stock_level > 0 ? Math.min(100, Math.round((item.quantity / (item.min_stock_level * 2)) * 100)) : 100;
  const catClass = getCategoryColorClass(item.category);

  card.innerHTML = `
    <div class="item-top">
      <div class="item-tags">
        <span class="cat-pill ${catClass}">${escapeHtml(item.category)}</span>
        ${item.location ? `<span class="location-tag">📍 ${escapeHtml(item.location)}</span>` : ''}
      </div>
      ${isLow ? `
        <span class="low-stock-alert-badge" title="Quantity is at or below minimum threshold (${item.min_stock_level})">
          ⚠️ Low Stock
        </span>
      ` : ''}
    </div>

    <div>
      <h4 class="item-name">${escapeHtml(item.name)}</h4>
      ${item.notes ? `<p class="item-notes">${escapeHtml(item.notes)}</p>` : ''}
    </div>

    <div class="stock-info">
      <div class="stock-headline">
        <div class="stock-digits">
          <span class="qty-val">${item.quantity}</span>
          <span class="qty-unit">${escapeHtml(item.unit || 'pcs')}</span>
        </div>
        <span class="min-threshold">Min: ${item.min_stock_level} ${escapeHtml(item.unit || 'pcs')}</span>
      </div>

      <div class="progress-track" title="Stock vs safety threshold">
        <div class="progress-fill ${isLow ? 'fill-alert' : ''}" style="width: ${progressRatio}%;"></div>
      </div>
    </div>

    <div class="card-actions">
      <!-- Quantity Adjustment Stepper -->
      <div class="quantity-stepper">
        <button type="button" class="step-btn btn-minus" data-id="${item.id}" title="Decrease quantity by 1" ${item.quantity <= 0 ? 'disabled' : ''}>-</button>
        <span class="step-label">Adjust</span>
        <button type="button" class="step-btn btn-plus" data-id="${item.id}" title="Increase quantity by 1">+</button>
      </div>

      <!-- Edit / Delete Buttons -->
      <div class="card-icon-btns">
        <button type="button" class="icon-action-btn btn-edit" data-id="${item.id}" title="Edit Item">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button type="button" class="icon-action-btn icon-delete btn-delete" data-id="${item.id}" data-name="${escapeHtml(item.name)}" title="Delete Item">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>
  `;

  // Attach card event listeners
  const btnMinus = card.querySelector('.btn-minus');
  const btnPlus = card.querySelector('.btn-plus');
  const btnEdit = card.querySelector('.btn-edit');
  const btnDelete = card.querySelector('.btn-delete');

  btnMinus.addEventListener('click', () => adjustItemQuantity(item.id, -1));
  btnPlus.addEventListener('click', () => adjustItemQuantity(item.id, +1));
  btnEdit.addEventListener('click', () => openEditModal(item));
  btnDelete.addEventListener('click', () => deleteStationeryItem(item.id, item.name));

  return card;
}

// Quick Quantity Adjustment (+ / -)
async function adjustItemQuantity(itemId, delta) {
  try {
    const res = await fetch(`/api/items/${itemId}/adjust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      await checkSystemStatus();
      await refreshCategories();
      await loadItems();
    } else {
      showToast(data.error || 'Failed to adjust quantity.', 'error');
    }
  } catch (err) {
    showToast('Network error updating quantity.', 'error');
  }
}

// ==========================================================================
// Natural Language AI Assistant (Gemma via Ollama + Fallback)
// ==========================================================================

async function handleAiPromptSubmit() {
  const prompt = dom.aiPromptInput.value.trim();
  if (!prompt) {
    showToast('Please type a stationery update request.', 'info');
    dom.aiPromptInput.focus();
    return;
  }

  // Set loading state
  dom.aiSubmitBtn.disabled = true;
  dom.aiSubmitBtn.querySelector('.btn-text').textContent = 'Interpreting...';
  dom.aiSubmitBtn.querySelector('.btn-icon').style.display = 'none';
  dom.aiSubmitBtn.querySelector('.spinner').style.display = 'inline-block';
  dom.proposalCard.style.display = 'none';

  try {
    const res = await fetch('/api/ai/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });

    const data = await res.json();

    if (res.ok && data.success && data.proposal) {
      state.activeProposal = data.proposal;
      displayProposalCard(data.proposal, data.ai_source);
    } else {
      showToast(data.error || 'Could not interpret request.', 'error');
    }
  } catch (err) {
    showToast('Failed to connect to AI service.', 'error');
  } finally {
    dom.aiSubmitBtn.disabled = false;
    dom.aiSubmitBtn.querySelector('.btn-text').textContent = 'Interpret';
    dom.aiSubmitBtn.querySelector('.btn-icon').style.display = 'inline-block';
    dom.aiSubmitBtn.querySelector('.spinner').style.display = 'none';
  }
}

function displayProposalCard(proposal, aiSource) {
  // Update Source Badge
  if (aiSource && aiSource.startsWith('ollama')) {
    dom.proposalSourceBadge.textContent = `Local Gemma (${aiSource.replace('ollama:', '')})`;
    dom.proposalSourceBadge.style.background = 'rgba(255, 255, 255, 0.25)';
  } else {
    dom.proposalSourceBadge.textContent = 'Smart Fallback Engine';
    dom.proposalSourceBadge.style.background = '#F59E0B';
  }

  // Action Badge
  const actionMap = {
    add_stock: { text: 'ADD STOCK', class: 'action-add' },
    use_stock: { text: 'USE STOCK', class: 'action-use' },
    set_stock: { text: 'SET STOCK', class: 'action-set' },
    create_item: { text: 'CREATE NEW ITEM', class: 'action-create' },
    delete_item: { text: 'DELETE ITEM', class: 'action-delete' }
  };
  const actInfo = actionMap[proposal.action] || { text: proposal.action.toUpperCase(), class: 'action-add' };
  dom.proposalActionBadge.textContent = actInfo.text;
  dom.proposalActionBadge.className = `action-pill ${actInfo.class}`;

  // Item & Category
  dom.proposalItemName.textContent = proposal.item_name;
  dom.proposalCategory.textContent = proposal.category;
  dom.proposalCategory.className = `cat-pill ${getCategoryColorClass(proposal.category)}`;

  // Stock Transition
  const unit = proposal.unit || 'pcs';
  dom.proposalCurrentQty.textContent = `${proposal.current_quantity} ${unit}`;
  dom.proposalNewQty.textContent = `${proposal.proposed_quantity} ${unit}`;

  const delta = proposal.quantity_delta;
  if (proposal.action === 'use_stock') {
    dom.proposalDelta.textContent = `(-${delta})`;
    dom.proposalDelta.style.color = 'var(--color-alert)';
  } else if (proposal.action === 'add_stock') {
    dom.proposalDelta.textContent = `(+${delta})`;
    dom.proposalDelta.style.color = 'var(--color-forest)';
  } else {
    dom.proposalDelta.textContent = `(${proposal.proposed_quantity} total)`;
    dom.proposalDelta.style.color = 'var(--color-primary)';
  }

  // Low Stock Warning
  if (proposal.is_low_stock_warning || proposal.proposed_quantity <= proposal.min_stock_level) {
    dom.proposalLowStockWarning.style.display = 'flex';
  } else {
    dom.proposalLowStockWarning.style.display = 'none';
  }

  // Explanation
  dom.proposalExplanationText.textContent = proposal.explanation || 'Gemma parsed this proposed stock adjustment.';

  // Show card and scroll into view smoothly
  dom.proposalCard.style.display = 'block';
  dom.proposalCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// User Confirms AI Proposal -> Apply Changes to SQLite
async function handleProposalConfirm() {
  if (!state.activeProposal) return;

  dom.proposalConfirmBtn.disabled = true;
  dom.proposalConfirmBtn.textContent = 'Applying...';

  try {
    const res = await fetch('/api/ai/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposal: state.activeProposal })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast(data.message, 'success');
      state.activeProposal = null;
      dom.proposalCard.style.display = 'none';
      dom.aiPromptInput.value = '';

      // Update state and UI
      if (data.stats) updateStatsUi(data.stats);
      if (data.items) {
        state.items = data.items;
        renderItems(state.items);
      } else {
        await loadItems();
      }
      await refreshCategories();
    } else {
      showToast(data.error || 'Failed to apply proposal.', 'error');
    }
  } catch (err) {
    showToast('Network error applying proposal.', 'error');
  } finally {
    dom.proposalConfirmBtn.disabled = false;
    dom.proposalConfirmBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      Confirm & Apply Update
    `;
  }
}

function handleProposalDecline() {
  state.activeProposal = null;
  dom.proposalCard.style.display = 'none';
  showToast('Proposed update discarded. No changes were made.', 'info');
}

// ==========================================================================
// Add / Edit Item Modal Operations
// ==========================================================================

function openAddItemModal() {
  state.editingItemId = null;
  dom.modalTitle.textContent = 'Add Stationery Item';
  dom.formItemId.value = '';
  dom.itemForm.reset();
  dom.formItemQuantity.value = '1';
  dom.formItemMinStock.value = '2';
  dom.formItemUnit.value = 'pcs';
  dom.formItemLocation.value = 'Desk Drawer';
  dom.itemModal.style.display = 'flex';
  dom.formItemName.focus();
}

function openEditModal(item) {
  state.editingItemId = item.id;
  dom.modalTitle.textContent = `Edit '${item.name}'`;
  dom.formItemId.value = item.id;
  dom.formItemName.value = item.name;
  dom.formItemCategory.value = item.category || 'Writing';
  dom.formItemUnit.value = item.unit || 'pcs';
  dom.formItemQuantity.value = item.quantity;
  dom.formItemMinStock.value = item.min_stock_level;
  dom.formItemLocation.value = item.location || '';
  dom.formItemNotes.value = item.notes || '';
  dom.itemModal.style.display = 'flex';
  dom.formItemName.focus();
}

function closeItemModal() {
  dom.itemModal.style.display = 'none';
  state.editingItemId = null;
}

async function handleItemFormSubmit() {
  const name = dom.formItemName.value.trim();
  if (!name) {
    showToast('Item name is required.', 'error');
    dom.formItemName.focus();
    return;
  }

  const payload = {
    name,
    category: dom.formItemCategory.value,
    unit: dom.formItemUnit.value.trim() || 'pcs',
    quantity: Math.max(0, parseInt(dom.formItemQuantity.value, 10) || 0),
    min_stock_level: Math.max(0, parseInt(dom.formItemMinStock.value, 10) || 1),
    location: dom.formItemLocation.value.trim() || 'Desk',
    notes: dom.formItemNotes.value.trim()
  };

  const isEdit = Boolean(state.editingItemId);
  const url = isEdit ? `/api/items/${state.editingItemId}` : '/api/items';
  const method = isEdit ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message, 'success');
      closeItemModal();
      await checkSystemStatus();
      await refreshCategories();
      await loadItems();
    } else {
      showToast(data.error || 'Failed to save item.', 'error');
    }
  } catch (err) {
    showToast('Error saving item.', 'error');
  }
}

async function deleteStationeryItem(itemId, itemName) {
  if (!confirm(`Are you sure you want to remove '${itemName}' from your inventory?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/items/${itemId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      await checkSystemStatus();
      await refreshCategories();
      await loadItems();
    } else {
      showToast(data.error || 'Failed to delete item.', 'error');
    }
  } catch (err) {
    showToast('Error deleting item.', 'error');
  }
}

async function handleResetSampleData() {
  if (!confirm('Reset inventory back to sample student stationery items? Current custom edits will be replaced with standard sample data.')) {
    return;
  }

  try {
    const res = await fetch('/api/items/reset-sample', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      if (data.stats) updateStatsUi(data.stats);
      if (data.items) renderItems(data.items);
      await refreshCategories();
    } else {
      showToast('Failed to reset sample data.', 'error');
    }
  } catch (err) {
    showToast('Network error resetting sample data.', 'error');
  }
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================

function setupEventListeners() {
  // AI Assistant Form & Buttons
  dom.aiPromptForm.addEventListener('submit', handleAiPromptSubmit);
  dom.aiSubmitBtn.addEventListener('click', handleAiPromptSubmit);

  // Quick Chips
  dom.chipButtons.forEach(chip => {
    chip.addEventListener('click', () => {
      dom.aiPromptInput.value = chip.dataset.prompt;
      dom.aiPromptInput.focus();
    });
  });

  // Proposal Confirmation
  dom.proposalConfirmBtn.addEventListener('click', handleProposalConfirm);
  dom.proposalDeclineBtn.addEventListener('click', handleProposalDecline);

  // Search Input with Debounce
  let searchTimeout;
  dom.searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value;
    dom.clearSearchBtn.style.display = state.searchQuery ? 'block' : 'none';
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadItems, 250);
  });

  dom.clearSearchBtn.addEventListener('click', () => {
    dom.searchInput.value = '';
    state.searchQuery = '';
    dom.clearSearchBtn.style.display = 'none';
    loadItems();
  });

  // Status Filter
  dom.statusFilter.addEventListener('change', (e) => {
    state.activeStatus = e.target.value;
    loadItems();
  });

  // Low Stock Stat Card Click -> Instant Filter
  dom.lowStockStatCard.addEventListener('click', () => {
    dom.statusFilter.value = 'low_stock';
    state.activeStatus = 'low_stock';
    loadItems();
    dom.itemsGrid.scrollIntoView({ behavior: 'smooth' });
  });

  // Modals
  dom.openAddItemModalBtn.addEventListener('click', openAddItemModal);
  dom.closeItemModalBtn.addEventListener('click', closeItemModal);
  dom.cancelModalBtn.addEventListener('click', closeItemModal);
  dom.itemForm.addEventListener('submit', handleItemFormSubmit);

  dom.aboutAiBtn.addEventListener('click', () => {
    dom.aboutModal.style.display = 'flex';
  });
  dom.closeAboutModalBtn.addEventListener('click', () => {
    dom.aboutModal.style.display = 'none';
  });
  dom.aboutGotItBtn.addEventListener('click', () => {
    dom.aboutModal.style.display = 'none';
  });

  // Empty state reset
  dom.emptyResetBtn.addEventListener('click', () => {
    dom.searchInput.value = '';
    state.searchQuery = '';
    dom.clearSearchBtn.style.display = 'none';
    dom.statusFilter.value = 'all';
    state.activeStatus = 'all';
    setCategoryFilter('all');
  });

  // Reset Sample Data
  dom.resetSampleBtn.addEventListener('click', handleResetSampleData);

  // Close modals on backdrop click
  window.addEventListener('click', (e) => {
    if (e.target === dom.itemModal) closeItemModal();
    if (e.target === dom.aboutModal) dom.aboutModal.style.display = 'none';
  });
}

// ==========================================================================
// Toast Notification Utility
// ==========================================================================

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${escapeHtml(message)}</span>
    <button style="background:none;border:none;cursor:pointer;color:#8E9990;font-size:1.1rem;line-height:1;">&times;</button>
  `;

  const closeBtn = toast.querySelector('button');
  closeBtn.addEventListener('click', () => toast.remove());

  dom.toastContainer.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
