def render_conflicts_html(conflicts):
    """Emulate the subset of the JS rendering logic for conflicts relevant to REQUIRES_LL.
    Returns the generated HTML as string."""
    html_parts = []
    # header area
    # Only consider corrections for actionable conflicts (exclude REQUIRES_LL)
    anyHasCorrections = any((c.get('corrected_grammar') and c.get('corrected_grammar').strip() != '') and not (c.get('type') and 'REQUIRES_LL' in c.get('type')) for c in conflicts)
    if anyHasCorrections:
        html_parts.append('<button class="btn-warning">Aplicar Todas as Sugestões</button>')
    else:
        html_parts.append('<button class="btn-secondary" disabled>Aplicar Todas as Sugestões</button>')
    for c in conflicts:
        hasCorrection = bool(c.get('corrected_grammar') and c.get('corrected_grammar').strip() != '') and not (c.get('type') and 'REQUIRES_LL' in c.get('type'))
        isRequiresLL = (c.get('type') and 'REQUIRES_LL' in c.get('type'))
        if isRequiresLL:
            # render only short message
            html_parts.append(f"<div class='requires-ll'>{c.get('description')}</div>")
            continue
        # otherwise render suggestion and optional apply
        if hasCorrection:
            html_parts.append("<button>Aplicar</button>")
        if c.get('suggestion'):
            html_parts.append(f"<pre>{c.get('suggestion')}</pre>")
    return '\n'.join(html_parts)


def test_requires_ll_hides_apply_button():
    # Simulate a conflict marked as REQUIRES_LL with a corrected_grammar present
    conflicts = [
        {
            'type': 'REQUIRES_LL(2)',
            'description': 'Gramática impossível de resolver com LL(1). Experimente LL(K) onde K = 2.',
            'suggestion': 'Alguma sugestão que não deve ser mostrada como ação',
            'corrected_grammar': 'S -> ...'  # even if present, should be ignored for REQUIRES_LL
        }
    ]

    html = render_conflicts_html(conflicts)

    # The rendered HTML should include the description
    assert 'Gramática impossível de resolver com LL(1)' in html
    # The global apply-all button is shown, but disabled/grey
    assert 'Aplicar Todas as Sugestões' in html
    assert 'btn-secondary' in html
    assert 'disabled' in html
    # Per-conflict apply action must not be rendered
    assert '<button>Aplicar</button>' not in html


def test_regular_conflict_shows_apply_when_correction_present():
    conflicts = [
        {
            'type': 'FIRST/FIRST',
            'description': 'Conflito FIRST/FIRST para S',
            'suggestion': 'Fatoração à esquerda...',
            'corrected_grammar': 'S -> a S\nS -> b'
        }
    ]
    html = render_conflicts_html(conflicts)
    assert 'Aplicar' in html
    assert 'Fatoração' in html
    assert 'btn-warning' in html


def test_first_follow_conflict_has_no_apply_button():
    # FIRST/FOLLOW conflicts without corrected_grammar should NOT show apply button
    conflicts = [
        {
            'type': 'FIRST/FOLLOW',
            'description': 'Conflito FIRST/FOLLOW para A',
            'suggestion': 'Reformulação da Produção Anulável...',
            'corrected_grammar': ''  # No automatic correction for generic FIRST/FOLLOW
        }
    ]
    html = render_conflicts_html(conflicts)
    
    # Apply-all button should be disabled (no corrections available)
    assert 'btn-secondary' in html
    assert 'disabled' in html
    
    # No per-conflict apply button
    assert '<button>Aplicar</button>' not in html
    
    # Suggestion must be visible
    assert 'Reformulação' in html


def test_list_pattern_first_follow_shows_apply_button():
    # List pattern FIRST/FOLLOW with corrected_grammar SHOULD show apply button
    conflicts = [
        {
            'type': 'FIRST/FOLLOW',
            'description': 'Conflito FIRST/FOLLOW para Lista',
            'suggestion': 'Substituição de Forma Plural...',
            'corrected_grammar': 'Lista → Elem | Elem , Elem\nElem → id'  # Auto-correction for list pattern
        }
    ]
    html = render_conflicts_html(conflicts)
    
    # Apply-all button should be active (corrections available)
    assert 'btn-warning' in html
    assert 'disabled' not in html
    
    # Per-conflict apply button SHOULD be present
    assert '<button>Aplicar</button>' in html
