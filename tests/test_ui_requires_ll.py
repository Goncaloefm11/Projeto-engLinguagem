def render_conflicts_html(conflicts):
    """Emulate the subset of the JS rendering logic for conflicts relevant to REQUIRES_LL.
    Returns the generated HTML as string."""
    html_parts = []
    # header area
    # Only consider corrections for actionable conflicts (exclude REQUIRES_LL)
    anyHasCorrections = any((c.get('corrected_grammar') and c.get('corrected_grammar').strip() != '') and not (c.get('type') and 'REQUIRES_LL' in c.get('type')) for c in conflicts)
    if anyHasCorrections:
        html_parts.append('<button>Aplicar Todas as Sugestões</button>')
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
    # But should NOT include the 'Aplicar' button
    assert 'Aplicar' not in html


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
