class AnalisadorGramatica:
    def __init__(self, producoes):
        self.producoes = producoes
        self.nao_terminais = list(producoes.keys())
        self.terminais = self._extrair_terminais()
        self.first = {nt: set() for nt in self.nao_terminais}
        self.follow = {nt: set() for nt in self.nao_terminais}
        self.tabela = {} # Estrutura: {(Não-Terminal, Terminal): [Produção]}
        self.conflitos = []

    def _extrair_terminais(self):
        term = set()
        for corpos in self.producoes.values():
            for derivacao in corpos:
                for s in derivacao:
                    if s not in self.nao_terminais and s != 'e':
                        term.add(s)
        term.add('$') # Fim de frase
        return term

    # ... (Manter as funções calcular_first e calcular_follow que já tínhamos) ...

    def construir_tabela(self):
        for nt, derivacoes in self.producoes.items():
            for derivacao in derivacoes:
                # 1. Para cada terminal 't' no FIRST da derivação
                primeiros = self.get_first_de_sequencia(derivacao)
                for t in primeiros:
                    if t != 'e':
                        self._adicionar_na_tabela(nt, t, derivacao)
                
                # 2. Se a derivação pode ser vazia (e), olha para o FOLLOW do NT
                if 'e' in primeiros:
                    for t in self.follow[nt]:
                        self._adicionar_na_tabela(nt, t, derivacao)

    def _adicionar_na_tabela(self, nt, t, derivacao):
        chave = (nt, t)
        if chave not in self.tabela:
            self.tabela[chave] = []
        
        # Deteção de Conflitos LL(1) 
        if derivacao not in self.tabela[chave]:
            self.tabela[chave].append(derivacao)
            if len(self.tabela[chave]) > 1:
                self.conflitos.append(f"Conflito em ({nt}, {t}): {self.tabela[chave]}")

    def executar_completo(self):
        # 1. Conjuntos base 
        for nt in self.nao_terminais: self.first[nt] = self.calcular_first(nt)
        for _ in range(3): 
            for nt in self.nao_terminais: self.calcular_follow(nt)
        
        # 2. Tabela e Conflitos [cite: 17, 24]
        self.construir_tabela()
        return self.first, self.follow, self.tabela, self.conflitos