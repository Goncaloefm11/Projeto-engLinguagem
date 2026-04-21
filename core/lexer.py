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
        self._preparar_literals()
    
    def _preparar_literals(self):
        """Extrai e ordena os literais por tamanho (maior primeiro)."""
        self.literais = []
        for t in self.terminais:
            if len(t) >= 2 and t[0] == "'" and t[-1] == "'":
                lit = t[1:-1]
                if lit and lit != 'ε':
                    self.literais.append(lit)
        
        # Ordena por tamanho descendente para evitar conflitos na separação
        self.literais.sort(key=len, reverse=True)
    
    def _separar_com_literals(self, frase):
        """
        Separa a frase em partes respeitando os literais definidos.
        
        Exemplo: '<nome>Joana</nome>' com literais ['<nome>', '</nome>']
        Resultado: ['<nome>', 'Joana', '</nome>']
        """
        if not self.literais:
            return frase.split()
        
        # Cria padrão regex para separar por literais
        pattern = "(" + "|".join(re.escape(l) for l in self.literais) + ")"
        partes = []
        
        for pedaco in re.split(pattern, frase):
            if not pedaco:
                continue
            if pedaco in self.literais:
                partes.append(pedaco)
            else:
                # Divide o pedaço não-literal por espaços
                partes.extend(pedaco.split())
        
        return partes
    
    def _encontrar_candidatos(self, token_str):
        """
        Encontra todos os tipos de terminais que podem corresponder a um token.
        
        Verifica em ordem:
        1. Correspondência exata com literais
        2. Correspondência com expressões regulares nas produções
        
        Returns:
            Lista de candidatos (tipos de terminais) ou None se nenhum match
        """
        candidatos = []
        
        # 1. Verifica correspondência exata com literais
        if token_str in self.terminais:
            candidatos.append(token_str)
        
        # Verifica com aspas (para literais)
        literal_com_aspas = f"'{token_str}'"
        if literal_com_aspas in self.terminais and literal_com_aspas not in candidatos:
            candidatos.append(literal_com_aspas)
        
        # 2. Procura por padrões regex nas regras lexicais
        for _, producoes_nt in self.producoes.items():
            for prod in producoes_nt:
                # Uma regra lexical tem exatamente uma produção com um token
                if len(prod) == 1:
                    padrao = prod[0].strip("'")
                    try:
                        # fullmatch garante que o padrão corresponde à string toda
                        if re.fullmatch(padrao, token_str) and prod[0] not in candidatos:
                            candidatos.append(prod[0])
                    except re.error:
                        # Padrão inválido, ignora
                        pass
        
        return candidatos if candidatos else None
    
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
            
            # Cria o token com o primeiro candidato como tipo principal
            token = {
                'type': candidatos[0],
                'value': parte,
                'candidates': candidatos
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
        
        # Adiciona EOF token
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
