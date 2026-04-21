"""
Lexer para análise léxica.
Produz uma lista de tokens compatível com o parser recursivo descendente LL(1).
"""

import re


class Token:
    """Representa um token com tipo, valor e candidatos possíveis."""
    
    def __init__(self, type_: str, value: str, candidates: list = None):
        self.type = type_
        self.value = value
        self.candidates = candidates or [type_]
    
    def to_dict(self):
        """Converte para dicionário compatível com o parser."""
        return {
            'type': self.type,
            'value': self.value,
            'candidates': self.candidates
        }
    
    def __repr__(self):
        return f"Token(type='{self.type}', value='{self.value}')"


class Lexer:
    """Analisador léxico que tokeniza uma frase de acordo com a gramática."""
    
    def __init__(self, gramatica):
        """
        Inicializa o lexer com uma gramática.
        
        Args:
            gramatica: Dicionário com 'terminais' e 'producoes'
        """
        self.gramatica = gramatica
        self.terminais = gramatica.get('terminais', [])
        self.producoes = gramatica.get('producoes', {})
        self.literais = gramatica.get('literais', [])
    
    def _separar_com_literals(self, frase):
        """
        Separa a frase em partes respeitando os literais definidos.
        
        Exemplo: '<nome>Joana</nome>' com literais ['<nome>', '</nome>']
        Resultado: ['<nome>', 'Joana', '</nome>']
        """
        if not self.literais:
            return frase.split()
        
        # Cria padrão regex para separar por literais (ordem por tamanho decrescente)
        literais_ordenados = sorted(set(self.literais), key=len, reverse=True)
        pattern = "(" + "|".join(re.escape(l) for l in literais_ordenados) + ")"
        partes = []
        
        for pedaco in re.split(pattern, frase):
            if not pedaco:
                continue
            if pedaco in self.literais:
                partes.append(pedaco)
            else:
                partes.extend(pedaco.split())
        
        return partes
    
    def _encontrar_candidatos(self, token_str):
        """
        Encontra todos os tipos de terminais que podem corresponder a um token.
        
        Verifica em ordem:
        1. Correspondência exata com terminais
        2. Correspondência com expressões regulares nas produções
        
        Returns:
            Lista de candidatos (tipos de terminais) ou None se nenhum match
        """
        candidatos = []
        
        # 1. Verifica correspondência exata com terminais
        if token_str in self.terminais:
            candidatos.append(token_str)
        
        # 2. Procura por padrões regex nas regras lexicais
        for _, producoes_nt in self.producoes.items():
            for prod in producoes_nt:
                # Uma regra lexical tem exatamente uma produção com um padrão
                if len(prod) == 1:
                    padrao = prod[0]
                    try:
                        # fullmatch garante que o padrão corresponde à string toda
                        if re.fullmatch(padrao, token_str) and prod[0] not in candidatos:
                            candidatos.append(prod[0])
                    except re.error:
                        # Padrão inválido, ignora
                        pass
        
        return candidatos if candidatos else None
    
    def _normalizar_candidatos(self, candidatos):
        """Remove aspas externas dos candidatos (ex: "']'" -> "]")."""
        def _clean(sym):
            if isinstance(sym, str) and len(sym) >= 2 and sym[0] == "'" and sym[-1] == "'":
                return sym[1:-1]
            return sym
        
        return [_clean(c) for c in candidatos]
    
    def tokenizar(self, frase):
        """
        Tokeniza uma frase de acordo com a gramática.
        
        Args:
            frase: String a tokenizar
        
        Returns:
            Tupla (lista_tokens, erro)
            - lista_tokens: Lista de dicionários {'type': ..., 'value': ..., 'candidates': ...}
            - erro: Mensagem de erro (None se sucesso)
        """
        tokens = []
        partes = self._separar_com_literals(frase)
        
        for parte in partes:
            candidatos = self._encontrar_candidatos(parte)
            
            # Se nenhum candidato foi encontrado, erro
            if not candidatos:
                erro_msg = f"Token '{parte}' não reconhecido: não é um literal e não dá match nenhum padrão lexical."
                return None, erro_msg
            
            # Normaliza candidatos (remove aspas externas)
            candidatos_normalizados = self._normalizar_candidatos(candidatos)
            
            # Cria o token com o primeiro candidato normalizado como tipo
            token = {
                'type': candidatos_normalizados[0],
                'value': parte,
                'candidates': candidatos_normalizados
            }
            tokens.append(token)
        
        return tokens, None
    
    def tokenizar_com_eof(self, frase):
        """
        Tokeniza uma frase e adiciona o token EOF ($) no final.
        
        Args:
            frase: String a tokenizar
        
        Returns:
            Tupla (lista_tokens, erro)
        """
        tokens, erro = self.tokenizar(frase)
        if erro:
            return None, erro
        
        # Adiciona EOF token normalizado
        tokens.append({
            'type': '$',
            'value': '$',
            'candidates': ['$']
        })
        
        return tokens, None


def tokenizar_frase(frase, gramatica):
    """
    Função de compatibilidade para código existente.
    Tokeniza uma frase usando a gramática fornecida.
    
    Args:
        frase: String a tokenizar
        gramatica: Dicionário com 'terminais' e 'producoes'
    
    Returns:
        Tupla (lista_tokens, erro)
    """
    lexer = Lexer(gramatica)
    return lexer.tokenizar(frase)


def tokenizar_frase_com_eof(frase, gramatica):
    """
    Tokeniza uma frase e adiciona o token EOF.
    
    Args:
        frase: String a tokenizar
        gramatica: Dicionário com 'terminais' e 'producoes'
    
    Returns:
        Tupla (lista_tokens, erro)
    """
    lexer = Lexer(gramatica)
    return lexer.tokenizar_com_eof(frase)
