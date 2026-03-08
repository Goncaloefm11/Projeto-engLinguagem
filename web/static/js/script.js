// Configuração do Mermaid (pode ficar fora)
mermaid.initialize({ 
    startOnLoad: false,
    theme: 'default',
    securityLevel: 'loose'
});

// Global variable to store the current analysis report
let currentAnalysisReport = null;

// Coloca as interações com elementos HTML aqui dentro:
document.addEventListener('DOMContentLoaded', () => {
    const exampleSelect = document.getElementById('exampleSelect');

    // Verifica se o elemento existe antes de adicionar o listener
    if (exampleSelect) {
        exampleSelect.addEventListener('change', function() {
            if (this.value && typeof examples !== 'undefined' && examples[this.value]) {
                document.getElementById('grammarInput').value = examples[this.value];
                setTimeout(autoResize, 0);
            }
        });
    }

    // Inicializa o tamanho das caixas ao carregar
    autoResize();

    // Redimensionar enquanto o utilizador digita
    ['grammarInput', 'inputPhrase'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', autoResize);
        }
    });

    // Ajustar tamanho quando se muda de separador (Pills do Bootstrap)
    document.querySelectorAll('button[data-bs-toggle="pill"]').forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', () => {
            autoResize();
        });
    });
});

// A função autoResize pode ficar fora, pois apenas é chamada após o DOM estar pronto
function autoResize() {
    const textareas = ['grammarInput', 'inputPhrase'];
    textareas.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.style.height = 'auto';
            el.style.height = el.scrollHeight + 'px';
        }
    });
}


// Chamar ao carregar a página
window.onload = autoResize;

async function analyzeGrammar() {
    const grammar = document.getElementById('grammarInput').value;
    const spinner = document.getElementById('analyzeSpinner');
    spinner.style.display = 'inline-block';
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({grammar: grammar})
        });
        
        const data = await response.json();
        displayAnalysisResult(data);
        
        // Mudar para a tab de resultados correta
        const analysisTab = document.querySelector('a[href="#analysisTab"]');
        new bootstrap.Tab(analysisTab).show();
        return data;
    } catch (error) {
        alert('Erro ao analisar: ' + error.message);
        return null;
    } finally {
        spinner.style.display = 'none';
    }
}

function displayAnalysisResult(data) {
    const container = document.getElementById('analysisResult');
    
    // Store report globally for suggestion application
    currentAnalysisReport = data.success ? data.report : null;
    
    if (!data.success) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <h5>Erro de Validação</h5>
                <p>${data.error}</p>
                ${data.details ? '<ul>' + data.details.map(d => `<li>${d}</li>`).join('') + '</ul>' : ''}
            </div>
        `;
        return;
    }
    
    const report = data.report;
    let html = '';
    
    if (report.is_ll1) {
        html += `<div class="alert alert-success"><i class="bi bi-check-circle-fill me-2"></i><strong>Gramática LL(1) válida! Não existem conflitos.</strong></div>`;
    } else {
        html += `<div class="alert alert-warning"><i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Atenção: A Gramática possui conflitos LL(1).</strong></div>`;
    }
    
    html += `
        <div class="row mb-3 mt-4">
            <div class="col-md-6">
                <h6>Símbolos Terminais:</h6>
                <div class="p-2 border rounded bg-light">${report.grammar.terminals.map(t => `<span class="terminal-badge">${t}</span>`).join(' ')}</div>
            </div>
            <div class="col-md-6 mt-3 mt-md-0">
                <h6>Símbolos Não-Terminais:</h6>
                <div class="p-2 border rounded bg-light">${report.grammar.non_terminals.map(nt => `<span class="nonterminal-badge">${nt}</span>`).join(' ')}</div>
            </div>
        </div>
    `;
    
    html += `
        <div class="mb-3 mt-4">
            <h6>Produções Lidas pelo Sistema:</h6>
            <div class="result-box">
                ${report.grammar.productions.map((p, i) => `<div><span class="text-muted">[${i}]</span> ${p}</div>`).join('')}
            </div>
        </div>
    `;
    
    if (report.nullable.length > 0) {
        html += `
            <div class="mb-3 mt-4">
                <h6>Símbolos Anuláveis (Derivam ε):</h6>
                <div class="p-2 border rounded bg-light">${report.nullable.map(n => `<span class="nonterminal-badge">${n}</span>`).join(' ')}</div>
            </div>
        `;
    }
    
    html += `
        <div class="row mt-4">
            <div class="col-md-6">
                <h6>Conjuntos FIRST:</h6>
                <div class="result-box">
                    ${Object.entries(report.first_sets).map(([nt, set]) => 
                        `<div class="mb-1"><strong>FIRST(${nt})</strong> = { ${set.join(', ')} }</div>`
                    ).join('')}
                </div>
            </div>
            <div class="col-md-6 mt-3 mt-md-0">
                <h6>Conjuntos FOLLOW:</h6>
                <div class="result-box">
                    ${Object.entries(report.follow_sets).map(([nt, set]) => 
                        `<div class="mb-1"><strong>FOLLOW(${nt})</strong> = { ${set.join(', ')} }</div>`
                    ).join('')}
                </div>
            </div>
        </div>
    `;
    
    if (report.conflicts && report.conflicts.length > 0) {
        html += `
            <div class="d-flex justify-content-between align-items-center mt-4 mb-3">
                <h6 class="text-danger mb-0"><i class="bi bi-shield-exclamation me-2"></i>Conflitos Detetados e Sugestões:</h6>
                <button class="btn btn-warning btn-sm" onclick="applyAllSuggestions(event)">
                    <i class="bi bi-check-all me-1"></i>Aplicar Todas as Sugestões
                </button>
            </div>
        `;
        
        report.conflicts.forEach((c, index) => {
            const hasCorrection = c.corrected_grammar && c.corrected_grammar.trim() !== '';
            html += `
                <div class="alert conflict-alert shadow-sm">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="text-danger fw-bold">${c.type}</h6>
                        </div>
                        ${hasCorrection ? `
                            <button class="btn btn-sm btn-success" onclick="applySuggestion(event, ${index})" title="Aplicar esta sugestão">
                                <i class="bi bi-check-circle me-1"></i>Aplicar
                            </button>
                        ` : ''}
                    </div>
                    <p class="mb-2">${c.description}</p>
                    <hr>
                    <p class="mb-1 fw-bold"><i class="bi bi-lightbulb-fill text-warning me-1"></i> Sugestão do Sistema:</p>
                    <pre class="mb-0 bg-white p-2 border rounded" style="font-size: 13px;">${c.suggestion}</pre>
                    ${hasCorrection ? `
                        <p class="mt-3 mb-1 fw-bold"><i class="bi bi-pencil-square me-1"></i> Gramática sugerida:</p>
                        <pre class="mb-0 bg-white p-2 border rounded" style="font-size: 13px;">${c.corrected_grammar}</pre>
                    ` : ''}
                </div>
            `;
        });
    }
    
    container.innerHTML = html;
    buildLL1Table(report);

    /*
    // If any conflict requires LL(K) (K>1), inform the user in the grammar textarea
    if (report.conflicts && report.conflicts.length > 0) {
        const requires = report.conflicts.filter(c => c.type && c.type.indexOf('REQUIRES_LL') !== -1);
        if (requires.length > 0) {
            // Determine the maximum K requested (if multiple conflicts)
            const ks = requires.map(c => {
                const m = c.type.match(/REQUIRES_LL\((\d+)\)/);
                return m ? parseInt(m[1], 10) : null;
            }).filter(x => x !== null);
            const maxK = ks.length ? Math.max(...ks) : null;
            const grammarInput = document.getElementById('grammarInput');
            const msg = maxK
                ? `Atenção: esta gramática exige LL(K) com K = ${maxK}. Por favor refaça a gramática para que seja compatível com LL(1).`
                : 'Atenção: esta gramática não é compatível com LL(1). Por favor refaça a gramática para que seja compatível com LL(1).';
            if (grammarInput) {
                grammarInput.value = msg;
                autoResize();
            }
        }
    }
    */
}

function buildLL1Table(report) {
    const container = document.getElementById('ll1TableResult');
    const table = report.ll1_table;
    
    if (!table || Object.keys(table).length === 0) {
        container.innerHTML = '<div class="text-muted text-center p-5">Tabela de parsing vazia.</div>';
        return;
    }
    
    const nonTerminals = Object.keys(table);
    const terminals = new Set();
    Object.values(table).forEach(row => {
        Object.keys(row).forEach(t => terminals.add(t));
    });
    const terminalList = Array.from(terminals).sort();
    
    let html = '<table class="table table-bordered table-sm ll1-table text-center">';
    html += '<thead><tr><th class="bg-secondary">M / T</th>';
    terminalList.forEach(t => { html += `<th>${t}</th>`; });
    html += '</tr></thead><tbody>';
    
    nonTerminals.forEach(nt => {
        html += `<tr><th class="bg-light text-dark align-middle">${nt}</th>`;
        terminalList.forEach(t => {
            const productions = table[nt] && table[nt][t];
            if (productions) {
                const hasConflict = productions.length > 1;
                const cellClass = hasConflict ? 'conflict fw-bold text-danger' : 'align-middle';
                html += `<td class="${cellClass}">${productions.join('<br>')}</td>`;
            } else {
                html += '<td></td>';
            }
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function parseInput() {
    const grammar = document.getElementById('grammarInput').value;
    const input = document.getElementById('inputPhrase').value;
    const spinner = document.getElementById('parseSpinner');
    spinner.style.display = 'inline-block';
    
    try {
        const response = await fetch('/parse', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({grammar: grammar, input: input})
        });
        
        const data = await response.json();
        displayParseResult(data);
    } catch (error) {
        alert('Erro ao analisar: ' + error.message);
    } finally {
        spinner.style.display = 'none';
    }
}

function displayParseResult(data) {
    const treeContainer = document.getElementById('treeResult');
    const stepsContainer = document.getElementById('stepsResult');
    
    if (!data.success) {
        treeContainer.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="bi bi-x-circle me-2"></i>Erro de Parsing</h5>
                ${data.errors ? data.errors.map(e => `<p class="mb-1">${e}</p>`).join('') : data.error}
            </div>
        `;
        // If backend provided a suggested example sentence for a corrected grammar, show it
        if (data.suggested_example && data.suggested_example.trim() !== '') {
            const exampleHtml = `
                <div class="mt-3 alert alert-secondary">
                    <h6 class="mb-1">Exemplo válido para a gramática:</h6>
                    <div class="d-flex align-items-start">
                        <pre id="suggestedExample" class="mb-0 bg-white p-2 border rounded flex-grow-1" style="font-size:13px;">${escapeHtml(data.suggested_example)}</pre>
                        <div class="ms-2">
                            <button class="btn btn-sm btn-outline-primary" onclick="useSuggestedExample()">Usar exemplo</button>
                        </div>
                    </div>
                </div>
            `;
            treeContainer.innerHTML += exampleHtml;
        }
        stepsContainer.innerHTML = `<div class="alert alert-danger">Derivação falhou.</div>`;
    } else {
        if (data.tree_text) {
            let treeHtml = `<h6>Representação Textual:</h6>
                <pre class="result-box shadow-sm">${data.tree_text}</pre>`;
            
            if (data.tree_mermaid) {
                treeHtml += `<h6 class="mt-4 border-top pt-3">Representação Gráfica (Mermaid):</h6>
                    <div id="mermaidTree" class="text-center overflow-auto mt-2 p-3 bg-light border rounded"></div>`;
            }
            treeContainer.innerHTML = treeHtml;
            
            if (data.tree_mermaid) {
                try {
                    const mermaidDiv = document.getElementById('mermaidTree');
                    mermaidDiv.innerHTML = data.tree_mermaid;
                    mermaid.init(undefined, mermaidDiv);
                } catch (e) {
                    console.error('Mermaid error:', e);
                }
            }
        }
        
        if (data.derivation_steps && data.derivation_steps.length > 0) {
            let stepsHtml = '<table class="table table-striped table-hover table-sm step-table">';
            stepsHtml += '<thead class="table-dark"><tr><th>#</th><th>Stack</th><th>Input Restante</th><th>Ação do Parser</th></tr></thead>';
            stepsHtml += '<tbody>';
            
            data.derivation_steps.forEach(step => {
                stepsHtml += `<tr>
                    <td class="fw-bold">${step.step}</td>
                    <td>${step.stack.join(' ')}</td>
                    <td>${step.input.join(' ')}</td>
                    <td><span class="badge bg-info text-dark">${step.action}</span></td>
                </tr>`;
            });
            
            stepsHtml += '</tbody></table>';
            stepsContainer.innerHTML = stepsHtml;
        } else {
            stepsContainer.innerHTML = `<div class="alert alert-info">Passos de derivação passo-a-passo não disponíveis (utilizado parser Lark em background).</div>`;
        }
    }
    
    const treeTab = document.querySelector('a[href="#treeTab"]');
    new bootstrap.Tab(treeTab).show();
}

async function generateParser() {
    const grammar = document.getElementById('grammarInput').value;
    const language = document.getElementById('parserLanguage').value;
    
    try {
        const response = await fetch('/generate-parser', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                grammar: grammar,
                type: 'recursive',
                language: language
            })
        });
        
        const data = await response.json();
        displayCodeResult(data);
    } catch (error) {
        alert('Erro ao gerar: ' + error.message);
    }
}

function displayCodeResult(data) {
    const container = document.getElementById('codeResult');
    
    if (!data.success) {
        container.innerHTML = `<div class="alert alert-danger shadow-sm">
            <h6><i class="bi bi-exclamation-octagon-fill me-2"></i>Erro na Geração</h6>
            <p>${data.error}</p>
        </div>`;
    } else {
        container.innerHTML = `
            <h6 class="text-white mb-3">
                <i class="bi bi-file-code me-2"></i>
                Código Fonte Gerado (Descendente Recursivo) - ${data.language}
            </h6>
            <pre><code class="language-${data.language}">${escapeHtml(data.code)}</code></pre>
        `;
    }
    
    const codeTab = document.querySelector('a[href="#codeTab"]');
    new bootstrap.Tab(codeTab).show();
}

function copyCode() {
    const codeBlock = document.querySelector('#codeResult pre');
    if(codeBlock) {
        navigator.clipboard.writeText(codeBlock.textContent).then(() => {
            const btn = document.querySelector('button[onclick="copyCode()"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check2"></i> Copiado!';
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-secondary');
            }, 2000);
        });
    }
}

function applySuggestion(ev, conflictIndex) {
    if (!currentAnalysisReport || !currentAnalysisReport.conflicts) {
        alert('Nenhum relatório de análise disponível.');
        return;
    }
    
    const conflict = currentAnalysisReport.conflicts[conflictIndex];
    if (!conflict || !conflict.corrected_grammar || conflict.corrected_grammar.trim() === '') {
        alert('Esta sugestão não possui correção automática disponível.');
        return;
    }
    
    // Apply the corrected grammar (do NOT auto-analyze)
    const grammarInput = document.getElementById('grammarInput');
    grammarInput.value = conflict.corrected_grammar;

    // Resize the textarea
    autoResize();

    // Visual feedback on the clicked button (if available)
    const btn = ev && ev.target ? ev.target.closest('button') : null;
    if (btn) {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Aplicado!';
        btn.disabled = true;
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }, 1500);
    }

    // IMPORTANT: do not call analyzeGrammar() here. Let the user click "Analisar" when ready.
}

async function applyAllSuggestions(ev) {
    if (!currentAnalysisReport || !currentAnalysisReport.conflicts || currentAnalysisReport.conflicts.length === 0) {
        alert('Nenhum conflito encontrado.');
        return;
    }

    const btn = ev && ev.target ? ev.target : null;
    const originalHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<i class="bi bi-check2-all me-1"></i>A aplicar...';
        btn.disabled = true;
    }

    const grammarInput = document.getElementById('grammarInput');

    // Collect all conflicts that provide an automatic corrected grammar
    const corrections = currentAnalysisReport.conflicts.filter(c => c.corrected_grammar && c.corrected_grammar.trim() !== '');
    if (corrections.length === 0) {
        alert('Nenhuma correção automática disponível para os conflitos encontrados.');
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
        return;
    }

    // Apply the last suggested corrected grammar (safe, non-destructive automatic step)
    // NOTE: We do NOT re-run analysis here. The user should click "Analisar" when ready.
    grammarInput.value = corrections[corrections.length - 1].corrected_grammar;
    autoResize();

    alert(`${corrections.length} correção(ões) aplicadas. Carregue em "Analisar" para recalcular quando desejar.`);

    if (btn) {
        btn.innerHTML = '<i class="bi bi-check2-all me-1"></i>Aplicadas!';
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }, 1500);
    }
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function useSuggestedExample() {
    const el = document.getElementById('suggestedExample');
    if (!el) return;
    const example = el.textContent || el.innerText || '';
    const input = document.getElementById('inputPhrase');
    if (input) {
        input.value = example;
        autoResize();
    }
}