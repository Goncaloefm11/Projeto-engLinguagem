import networkx as nx
import matplotlib.pyplot as plt
from lark import Visitor, Token

class CFGBuilder(Visitor):
    def __init__(self):
        self.graph = nx.DiGraph()
        self.counter = 0
        self.last_node_id = "START"
        self.graph.add_node("START", label="Start", shape="oval")
        
        # Pilha para lidar com IFs e Loops (branches)
        self.split_stack = [] 

    def _add_node(self, label, shape="box"):
        node_id = f"node_{self.counter}"
        self.counter += 1
        self.graph.add_node(node_id, label=label, shape=shape)
        
        # Ligar o nó anterior a este
        if self.last_node_id:
            self.graph.add_edge(self.last_node_id, node_id)
        
        self.last_node_id = node_id
        return node_id

    def assign_expr(self, tree):
        # Ex: x = 10
        var = tree.children[0].value
        self._add_node(f"{var} = ...")

    def print_stmt(self, tree):
        self._add_node("print(...)")

    def exec_stmt(self, tree):
        self._add_node("exec(...)", shape="octagon") # Forma diferente para perigo

    def conditional(self, tree):
        # IFstmt
        cond_node = self._add_node("IF ?", shape="diamond")
        
        # Guardamos o nó do IF para ligar ao ELSE depois
        # Nota: Fazer um CFG perfeito com Visitor é complexo.
        # Vamos fazer uma aproximação visual sequencial.
        pass

    def while_loop(self, tree):
        self._add_node("WHILE ?", shape="diamond")

    def do_while_loop(self, tree):
        self._add_node("DO ... WHILE", shape="diamond")
        
    def flow_control(self, tree):
        # break / continue
        cmd = tree.children[0].data # break_stmt
        self._add_node(str(cmd).upper().replace("_STMT", ""))

    def draw(self, filename="cfg.png"):
        plt.figure(figsize=(10, 12))
        
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Desenhar nós
        labels = nx.get_node_attributes(self.graph, 'label')
        nx.draw(self.graph, pos, with_labels=True, labels=labels, 
                node_size=2000, node_color="lightblue", font_size=8, 
                font_weight="bold", arrows=True, edge_color="gray")
        
        plt.title("Control Flow Graph (Visualização TP2)")
        plt.savefig(filename)
        print(f"📸 CFG guardado como '{filename}'")
        plt.close()