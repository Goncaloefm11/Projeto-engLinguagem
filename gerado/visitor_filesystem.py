"""
Visitor para a gramática Filesystem
Gera um shell script que cria a estrutura de diretórios e ficheiros
"""

class FilesystemVisitor:
    """Visitor que converte a árvore de Filesystem em shell script."""
    
    def __init__(self):
        self.script_lines = []
        self.indent_level = 0
    
    def _indent(self):
        return "    " * self.indent_level
    
    def _add_line(self, line):
        """Adiciona uma linha ao script com indentação."""
        if line.strip():
            self.script_lines.append(self._indent() + line)
        else:
            self.script_lines.append("")
    
    def _clean_string(self, s):
        """Remove aspas externas e limpa a string."""
        if isinstance(s, str):
            s = s.strip()
            if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
                return s[1:-1]
        return s
    
    def _extract_string_value(self, node):
        """Extrai o valor de string de um nó.
        
        Se o nó é um não-terminal 'string', extrai o valor do seu filho.
        Se é um terminal direto (com aspas), remove as aspas.
        """
        if not isinstance(node, dict):
            return self._clean_string(str(node))
        
        # Se é o não-terminal 'string', procura no primeiro filho
        if node.get('name') == 'string':
            children = node.get('children', [])
            if children and isinstance(children[0], dict):
                # O valor está no filho (terminal)
                return self._clean_string(children[0].get('name', ''))
            return ''
        
        # Se é um terminal direto com valor
        name = node.get('name', '')
        return self._clean_string(name)
    
    def visit(self, node):
        """Ponto de entrada: visita a árvore e gera o script."""
        self.script_lines = []
        self.indent_level = 0
        
        # Começar o script
        self._add_line("#!/bin/bash")
        self._add_line("# Shell script gerado automaticamente a partir da árvore Filesystem")
        self._add_line("set -e  # Exit on error")
        self._add_line("")
        self._add_line("# Criar estrutura de diretórios e ficheiros")
        self._add_line("")
        
        # Visitar a árvore
        self._visit_node(node)
        
        self._add_line("")
        self._add_line("echo 'Estrutura criada com sucesso!'")
        
        return "\n".join(self.script_lines)
    
    def _visit_node(self, node):
        """Visita recursivamente cada nó da árvore."""
        if node is None or not isinstance(node, dict):
            return
        
        name = node.get('name', '')
        children = node.get('children', [])
        
        # Se o nó for Z, Conteudo ou Conteudo_P, apenas exploramos os filhos
        if name in ('Z', 'Conteudo', 'Conteudo_P'):
            for child in children:
                self._visit_node(child)
                
        elif name == 'Dir':
            self._visit_dir(node)
            
        elif name == 'Ficheiro':
            self._visit_file(node)
            
        else:
            # Fallback para outros nós (como tokens terminais)
            for child in children:
                self._visit_node(child)
    
    def _visit_dir(self, node):
        """Processa um nó Dir: cria mkdir, cd, conteúdo, cd .."""
        children = node.get('children', [])
        
        # Um Dir tem: ( string Conteudo ) ou é um Ficheiro
        # Procurar a string (nome do diretório)
        dir_name = None
        conteudo_node = None
        
        for i, child in enumerate(children):
            if isinstance(child, dict):
                if child.get('name') not in ('(', ')', 'Conteudo', 'Ficheiro'):
                    # É a string do nome
                    dir_name = self._extract_string_value(child)
                elif child.get('name') == 'Conteudo':
                    conteudo_node = child
                elif child.get('name') == 'Ficheiro':
                    # Este Dir é na verdade um Ficheiro
                    self._visit_file(child)
                    return
            elif isinstance(child, str):
                if child not in ('(', ')', '[', ']'):
                    dir_name = self._clean_string(child)
        
        if not dir_name:
            # Se não encontrou nome, tenta processar como Ficheiro
            for child in children:
                if isinstance(child, dict) and child.get('name') == 'Ficheiro':
                    self._visit_file(child)
            return
        
        # Criar diretório
        self._add_line(f'mkdir -p "{dir_name}"')
        self._add_line(f'cd "{dir_name}"')
        self.indent_level += 1
        
        # Processar conteúdo
        if conteudo_node:
            self._visit_node(conteudo_node)
        
        # Voltar ao diretório anterior
        self.indent_level -= 1
        self._add_line('cd ..')
    
    def _visit_file(self, node):
        """Processa um nó Ficheiro: cria comando cp."""
        children = node.get('children', [])
        
        # Ficheiro: [ string string ]
        # Procurar as duas strings (origem e destino)
        strings = []
        for child in children:
            if isinstance(child, dict) and child.get('name') not in ('[', ']'):
                strings.append(self._extract_string_value(child))
            elif isinstance(child, str) and child not in ('[', ']'):
                strings.append(self._clean_string(child))
        
        if len(strings) >= 2:
            origem = strings[1]
            destino = strings[0]
            self._add_line(f'cp "{origem}" "{destino}"')

