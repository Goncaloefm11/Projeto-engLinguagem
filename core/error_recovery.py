# core/error_recovery.py

def analyze_error_context(stack_esperado, token_recebido, seguintes, gramatica):
    """
    Analisa o contexto do erro sintático.
    Para um parser LL(1), o contexto ideal envolve olhar para o que o parser
    esperava (stack) vs o que realmente chegou (lookahead/token_recebido).
    
    Args:
        stack_esperado (list): Lista de símbolos (terminais/não-terminais) esperados.
        token_recebido (str): O token que causou a falha.
        seguintes (list): Lista dos próximos tokens (lookahead extra).
        gramatica (dict): A definição da gramática.
        
    Returns:
        dict: Estrutura com o diagnóstico da falha.
    """
    # Extrair os tipos dos tokens seguintes para análise de contexto
    tipos_seguintes = [t.get('type') for t in seguintes if isinstance(t, dict)]
    
    diagnostico = {
        'token_falha': token_recebido,
        'esperados': stack_esperado,
        'contexto_seguinte': tipos_seguintes,
        'tipo_falha': 'DESCONHECIDO'
    }

    # Heurísticas de diagnóstico
    if token_recebido == '$':
        diagnostico['tipo_falha'] = 'FIM_PREMATURO'
    elif not stack_esperado:
        # Se a stack está vazia mas ainda há tokens, temos "lixo" no fim da frase
        diagnostico['tipo_falha'] = 'TOKENS_EXTRA'
    elif token_recebido not in gramatica.get('terminais', []):
        diagnostico['tipo_falha'] = 'TOKEN_INVALIDO_LEXICO'
    else:
        diagnostico['tipo_falha'] = 'CONFLITO_LOOKAHEAD'

    return diagnostico


def sugerir_recuperacao(stack_esperado, token_recebido, gramatica, tabela):
    """
    Com base no diagnóstico e na tabela LL(1), sugere ações de recuperação:
    Inserção, Remoção ou Substituição.
    """
    sugestoes = []
    
    # Filtrar o épsilon ('ε') ou elementos vazios para não sugerir "inserir nada"
    esperados_uteis = [s for s in stack_esperado if s and s.strip() != 'ε']
    
    if esperados_uteis:
        # Tentar usar um terminal conhecido; se não, usamos o primeiro disponível
        terminais_esperados = [s for s in esperados_uteis if s in gramatica.get('terminais', [])]
        alvo = terminais_esperados[0] if terminais_esperados else esperados_uteis[0]
        
        # 1. Substituir (Apenas se não for o fim da frase)
        if token_recebido != '$':
            sugestoes.append({
                'acao': 'SUBSTITUIR',
                'alvo': token_recebido,
                'por': alvo,
                'descricao': f"Substituir '{token_recebido}' por '{alvo}'."
            })
            
        # 2. Inserir (Se for $, esta fica no topo da lista)
        sugestoes.append({
            'acao': 'INSERIR',
            'token': alvo,
            'descricao': f"Inserir token '{alvo}' no final da frase." if token_recebido == '$' else f"Inserir token '{alvo}' antes de '{token_recebido}'."
        })

    # 3. Panic Mode Recovery: Remoção
    if token_recebido != '$':
        sugestoes.append({
            'acao': 'REMOVER',
            'token': token_recebido,
            'descricao': f"Ignorar (remover) o token '{token_recebido}' e continuar o parsing."
        })

    return {
        'estrategias': sugestoes,
        'recomendada': sugestoes[0] if sugestoes else None
    }
def format_error_message(diagnostico, recuperacao):
    """
    Transforma os dicionários de diagnóstico e recuperação numa mensagem
    amigável para o utilizador ler na interface gráfica.
    """
    token_falha = diagnostico.get('token_falha', '?')
    tipo_falha = diagnostico.get('tipo_falha', 'ERRO')
    
    msg = f"Erro Sintático detetado no token '{token_falha}'. "
    
    if tipo_falha == 'TOKENS_EXTRA':
        msg += "A frase fornecida tem tokens extra após a conclusão da análise. "
    elif tipo_falha == 'FIM_PREMATURO':
        msg += "A frase terminou prematuramente, a gramática esperava mais elementos. "
    elif tipo_falha == 'TOKEN_INVALIDO_LEXICO':
        msg += "O token inserido não faz parte do vocabulário da linguagem. "
    else:
        esperados = diagnostico.get('esperados', [])
        if esperados:
            msg += f"Neste contexto, esperava-se encontrar: {', '.join(esperados)}. "
            
    # Adicionar a sugestão principal
    recomendada = recuperacao.get('recomendada')
    if recomendada:
        msg += f" Sugestão de Recuperação Automática: {recomendada['descricao']}"
        
    return msg