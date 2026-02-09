class AnalisadorGramatica:
    def __init__(self, producoes):
        self.producoes = producoes
        self.nao_terminais = list(producoes.keys())
        self.first = {nt: set() for nt in self.nao_terminais}
        self.follow = {nt: set() for nt in self.nao_terminais}

    def calcular_first(self, simbolo):
        if simbolo not in self.nao_terminais:
            return {simbolo}
        
        res = set()
        for derivacao in self.producoes[simbolo]:
            if derivacao[0] == 'e':
                res.add('e')
            else:
                for s in derivacao:
                    f = self.calcular_first(s)
                    res.update(f - {'e'})
                    if 'e' not in f: break
                else:
                    res.add('e')
        return res

    def calcular_follow(self, simbolo_alvo):
        # A primeira regra: Símbolo inicial recebe $ (fim de frase)
        if simbolo_alvo == self.nao_terminais[0]:
            self.follow[simbolo_alvo].add('$')

        for nt, derivacoes in self.producoes.items():
            for derivacao in derivacoes:
                if simbolo_alvo in derivacao:
                    idx = derivacao.index(simbolo_alvo)
                    proximo = derivacao[idx + 1:]
                    
                    if proximo:
                        # Se houver algo depois, adiciona o FIRST do que vem a seguir
                        f_proximo = self.get_first_de_sequencia(proximo)
                        self.follow[simbolo_alvo].update(f_proximo - {'e'})
                        if 'e' in f_proximo:
                            self.follow[simbolo_alvo].update(self.follow[nt])
                    else:
                        # Se for o último, recebe o FOLLOW da cabeça da produção
                        if nt != simbolo_alvo:
                            self.follow[simbolo_alvo].update(self.follow[nt])

    def get_first_de_sequencia(self, sequencia):
        res = set()
        for s in sequencia:
            f = self.calcular_first(s)
            res.update(f - {'e'})
            if 'e' not in f: return res
        res.add('e')
        return res

    def executar(self):
        # Calcula todos os FIRST
        for nt in self.nao_terminais:
            self.first[nt] = self.calcular_first(nt)
        
        # Calcula FOLLOW (precisa de várias passagens para propagar símbolos)
        for _ in range(3): # Loop simples para garantir propagação
            for nt in self.nao_terminais:
                self.calcular_follow(nt)
        
        return self.first, self.follow
