let selectedSymptoms = new Set();
let allSymptoms = [];

document.addEventListener('DOMContentLoaded', () => {
    // Initial data fetch from Python when ready
    if (window.pywebview) {
        initApp();
    } else {
        window.addEventListener('pywebviewready', initApp);
    }
});

async function initApp() {
    try {
        // Fetch symptoms
        allSymptoms = await pywebview.api.get_symptoms();
        
        renderSymptoms(allSymptoms);
        
        // Fetch conclusions for backward chaining
        const conclusions = await pywebview.api.get_conclusions();
        console.log(conclusions)
        renderConclusions(conclusions);
        
    } catch (error) {
        console.error('Initialization error:', error);
        showNotification('Failed to connect to backend.');
    }
}

function renderSymptoms(symptoms) {
    const list = document.getElementById('symptoms-list');
    list.innerHTML = '';
    
    symptoms.forEach(sym => {
        const item = document.createElement('div');
        item.className = 'symptom-item';
        item.dataset.id = sym;
        item.onclick = () => toggleSymptom(sym, item);
        
        const name = sym.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        item.innerHTML = `
            <div class="checkbox-custom">
                <i class="fas fa-check"></i>
            </div>
            <span class="symptom-name">${name}</span>
        `;
        
        list.appendChild(item);
    });
}

function renderConclusions(conclusions) {
    const select = document.getElementById('disease-select');
    conclusions.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        select.appendChild(opt);
    });
}

function toggleSymptom(sym, element) {
    if (selectedSymptoms.has(sym)) {
        selectedSymptoms.delete(sym);
        element.classList.remove('selected');
    } else {
        selectedSymptoms.add(sym);
        element.classList.add('selected');
    }
    
    document.getElementById('symptom-count').textContent = `${selectedSymptoms.size} selected`;
}

function filterSymptoms() {
    const query = document.getElementById('symptom-search').value.toLowerCase();
    const items = document.querySelectorAll('.symptom-item');
    
    items.forEach(item => {
        const name = item.querySelector('.symptom-name').textContent.toLowerCase();
        if (name.includes(query)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

function switchTab(tab) {
    // Nav items
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`nav-${tab}`).classList.add('active');
    
    // Content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');

    // Reset Results :
    clearResults()
}

async function runDiagnosis() {
    if (selectedSymptoms.size === 0) {
        showNotification('Please select at least one symptom.');
        return;
    }
    
    const display = document.getElementById('results-display');
    display.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Running Expert System...</p></div>';
    
    try {
        const result = await pywebview.api.run_diagnosis(Array.from(selectedSymptoms));
        renderDiagnosisResults(result);
    
    } catch (error) {
        console.error('Diagnosis error:', error);

    }
}

function renderDiagnosisResults(data) {
    const display = document.getElementById('results-display');
    display.innerHTML = '';
    
    if (data.fired_rules.length === 0) {
        display.innerHTML = `
            <div class="discovery-badge" style="background: #fee2e2; color: #991b1b; border-color: #fecaca;">
                <i class="fas fa-exclamation-triangle"></i> No specific diagnosis found for these symptoms.
            </div>
        `;
        return;
    }
    
    // Trace Section
    const traceHeader = document.createElement('h3');
    traceHeader.textContent = 'Diagnostic Trace';
    traceHeader.style.fontSize = '14px';
    traceHeader.style.color = 'var(--text-muted)';
    display.appendChild(traceHeader);
    
    data.fired_rules.forEach(rule => {
        const trace = document.createElement('div');
        trace.className = 'trace-item';
        trace.innerHTML = `
            <b>Rule ${rule.rule_id} fired:</b> 
            Matched ${rule.conditions.join(', ')} <br>
            <span style="color: var(--primary)">&rarr; Discovered: ${rule.conclusion}</span>
        `;
        display.appendChild(trace);
    });
    
    // Results Section
    data.fired_rules.forEach(rule => {
        if (rule.precautions) {
            const card = document.createElement('div');
            card.className = 'diagnosis-card';
            card.innerHTML = `
                <div class="diagnosis-header">
                    <h4><i class="fas fa-file-medical"></i> Report: ${rule.conclusion}</h4>
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="diagnosis-body">
                    <div class="treatment-box">
                        <h5><i class="fas fa-hand-holding-medical"></i> Treatment & Advice:</h5>
                        <p>${rule.precautions}</p>
                    </div>
                </div>
            `;
            display.appendChild(card);
        }
    });
}

async function runVerification() {
    const disease = document.getElementById('disease-select').value;
    if (!disease) {
        showNotification('Please select a disease to verify.');
        return;
    }
    
    if (selectedSymptoms.size === 0) {
        showNotification('Select symptoms to check against.');
        return;
    }
    
    const display = document.getElementById('results-display');
    display.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Checking logic path...</p></div>';
    
    try {
        const result = await pywebview.api.run_verification(disease, Array.from(selectedSymptoms));
        renderVerificationResults(result, disease);
    } catch (error) {
        console.error('Verification error:', error);

    }
}

function renderVerificationResults(data, disease) {
    const display = document.getElementById('results-display');
    display.innerHTML = '';
    
    const statusColor = data.success ? 'var(--success)' : 'var(--danger)';
    const statusIcon = data.success ? 'fa-check-double' : 'fa-times-circle';
    
    display.innerHTML = `
        <div class="discovery-badge" style="background: ${data.success ? '#f0fdf4' : '#fef2f2'}; border-color: ${data.success ? '#bbf7d0' : '#fecaca'}; color: ${statusColor}">
            <i class="fas ${statusIcon}"></i> 
            Hypothesis for <b>${disease}</b>: <b>${data.success ? 'CONFIRMED' : 'NOT SUPPORTED'}</b>
        </div>
        <h3 style="font-size: 14px; color: var(--text-muted); margin-top: 10px;">Verification Logic Trace:</h3>
        <div class="bwd-log">
            ${data.trace.join('<br>')}
        </div>
    `;
}

function resetApp() {
    selectedSymptoms.clear();
    document.querySelectorAll('.symptom-item').forEach(item => item.classList.remove('selected'));
    document.getElementById('symptom-count').textContent = '0 selected';
    document.getElementById('symptom-search').value = '';
    filterSymptoms();
    clearResults();
    showNotification('Session reset successfully.');
}

function clearResults() {
    const display = document.getElementById('results-display');
    display.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-clipboard-check"></i>
            <p>Select symptoms and run analysis to see results here.</p>
        </div>
    `;
}


function showNotification(msg) {
    const note = document.getElementById('notification');
    note.textContent = msg;
    note.classList.add('show');
    setTimeout(() => note.classList.remove('show'), 3000);
}
