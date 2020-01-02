from typing import Dict, List, Callable, Union, Set

class Connection:
    def __init__(self, node_name_from, node_name_to):
        self.node_name_from = node_name_from
        self.node_path_from = [node_name_from]

        self.node_name_to = node_name_to
        self.node_path_to = [node_name_to]
        self.properties_map={}
        self.properties_list=[]
        self.graph = None
    def set_property(self, id, value):
        if id in self.properties_map:
            self.properties_map[id] = value
        else:
            self.add_property(id, value)

    def add_property(self, property, value):
        self.properties_map[property] = value
        self.properties_list.append(property)

    def __repr__(self):
        return f"({self.node_name_from}->{self.node_name_to})"

    def get_input_node(self):
        return self.graph.nodes[self.node_name_from]

    def get_output_node(self):        
        return self.graph.nodes[self.node_name_to]
    

class Node:
    def __init__(self, id):
        self.id = id
        self.inputs : Dict[str, Connection] = {}
        self.outputs : Dict[str, Connection] = {}
        self.properties_map={}
        self.properties_list=[]

    def add_property(self, property, value):
        self.properties_map[property] = value
        self.properties_list.append(property)

    def __repr__(self):
        res = f"(node {self.id}"
        if "label" in self.properties_map:
            res += f" label={self.properties_map['label']}"
        res += ")"
        return res

    def set_property(self, id, value):
        if id in self.properties_map:
            self.properties_map[id] = value
        else:
            self.add_property(id, value)
    def get_property(self, id, default=""):
        return self.properties_map.get(id,default)

    def set_label(self, value):
        self.set_property("label", value)
    def label(self):
        return self.get_property("label")


class DotParser:
    def __init__(self, lines, graph):
        self.lines = lines
        self.line_num = 0
        self.col = 0
        self.graph =  graph

    def read_prologue(self):
        token = self.read_next_token()
        assert token in ["digraph"], f"Can't read graph type: got {token}"
        self.graph.make_directional_graph()

        token = self.read_next_token()
        if token != "{":
            self.graph.name = token
            token = self.read_next_token()
        assert token == "{", f"expect {'{'} to begin the graph, got {token}"

        while True:
            pos = self.remember_pos()
            prop = self.read_next_token()
            assignment = self.read_next_token()
            if assignment != '=':
                self.restore_pos(pos)
                break
            value = self.read_next_token()
            semicolon = self.read_next_token()
            assert semicolon == ';', f"semicolon expected around {self.location()}"
            assert prop not in self.graph.properties_map, f"property `{prop}` already exists"
            self.graph.add_property(prop, value)

    def read_body(self):
        while True:
            pos = self.remember_pos()            
            id = self.read_next_token()
            if not id or id == '}':
                return
            if id == 'c63':
                id=id


            op = self.read_next_token()

            if op == '[':
                self.create_node(id)
                op = self.read_next_token()
                assert op == ';'
                continue

            from_path = [id]
            from_node = id
            to_path = []
            to_node = ""

            # connection from the point
            if op == ':':
                self.restore_pos(pos)
                path = self.read_node_path()
                op = self.read_next_token()
                assert op == "->", f"got {op}, expect connection around {self.location()}"
                from_path = path
                from_node = path[0]

            if op == "->":
                dst_path = self.read_node_path()
                to_node = dst_path[0]
                to_path = dst_path
                connection = Connection(from_node, to_node)
                connection.node_path_from = from_path
                connection.node_path_to = to_path
                pos = self.remember_pos()
                if self.read_next_token() == '[':
                    self.read_properties(connection)
                else:
                    self.restore_pos(pos)
                self.graph.defer_connection(connection)
                op = self.read_next_token()
                assert op == ';'
                continue



            assert False, f"unexpected node-token {op} around {self.location()}"

    def read_node_path(self):
        node_path = []
        while True:
            sub_node = self.read_next_token()
            assert sub_node.isalnum(), f"got {sub_node}, but expected path around {self.location()}"
            node_path.append(sub_node)
            pos = self.remember_pos()
            if self.read_next_token() == ':':
                continue
            self.restore_pos(pos)
            break
        return node_path


    def read_properties(self, obj):        
        while True:
            prop = self.read_next_token()
            assert prop, f"properties not terminated around {self.location()}"
            
            if prop == ']':
                break
            assert prop.isalnum(), f"invalid prop id {prop} around {self.location()}"
            assignment = self.read_next_token()
            assert assignment=='=', f"expected {prop}=<value> around {self.location()}"
            value = self.read_next_token()
            obj.add_property(prop, value)

            next = self.read_next_token()
            if next == ']':
                break
            if next == ',':
                continue
            assert False, f"unexpected token {next} around {self.location()}, expect COMMA(next prop) or RCURLY(end of list)"

    def create_node(self, id):        
        assert id not in self.graph.nodes
        node = Node(id)
        self.graph.add_node(node)
        self.read_properties(node)

            
    def location(self)->str:
        return f"{self.line_num+1}:{1+self.col}"


    def remember_pos(self):
        return (self.line_num, self.col)
    def restore_pos(self, remembered_pos):
        self.line_num = remembered_pos[0]
        self.col = remembered_pos[1]



    def read_next_token(self) -> str:
        if not self.find_next_token():
            return None

        doubles = ["->"]

        for candidate in doubles:
            if self.current_char() == candidate[0] and self.next_char_in_line() == candidate[1]:
                self.go_to_next_char()
                self.go_to_next_char()
                return candidate

        if self.current_char() in "{}[]()<>;,:=":
            token = self.current_char()
            self.go_to_next_char()
            return token
        


        if self.current_char() == '"':
            return self.read_string_token()
        if self.current_char().isalnum():
            return self.read_id_token()
        raise Exception(f"Unknown token start `{self.current_char()}`")

    def read_string_token(self) -> str:
        start = self.col 
        start_line = self.line_num
        end = start
        self.go_to_next_char()
        while True:
            assert self.line_num == start_line, f"unterminated string at {start_line}"
            end+=1
            if self.current_char() == '\\':
                self.go_to_next_char()
                self.go_to_next_char()
                end += 1
                continue

                
            assert self.current_char() != '\\', "escaping nyi"
            if self.current_char() == '"':
                self.go_to_next_char()
                end+=1                
                break
            self.go_to_next_char()
        token = self.lines[start_line][start:end]
        return token
        
    def read_id_token(self) -> str:
        start = self.col
        start_line = self.line_num
        end = start
        while self.current_char().isalnum() and self.line_num == start_line:
            end+=1
            self.go_to_next_char()
        token = self.lines[start_line][start:end]
        return token
        
    def find_next_token(self) -> bool:
        if self.eof():
            return False
        while self.current_char().isspace():
            self.go_to_next_char()
            if self.eof():
                return False
        return True

    def eof(self) -> bool:
        if self.line_num >= len(self.lines):
            return True
        if self.col >= len(self.lines[self.line_num]):
            return True
        return False

    def next_char_in_line(self) -> str:
        if self.eof() or self.col + 1 >= len(self.current_line()):
            return ""
        return self.current_line()[self.col+1]

    def current_char(self) -> str:
        if self.eof():
            return ""
        return self.current_line()[self.col]

    def go_to_next_char(self):
        if self.col + 1 < len(self.current_line()):
            self.col += 1
        else:
            self.line_num += 1
            self.col = 0
    
    def current_line(self):
        if self.eof():
            return ""
        return self.lines[self.line_num]

    def assert_in_bounds(self):
        assert self.line_num >= 0, f"Line num {self.line_num} is negative" 
        assert self.line_num < len(self.lines), f"Line num {self.line_num} is out of bounds" 
         



class Graph:
    def __init__(self):
        self.nodes : Dict[str, Node] = {}
        self.node_list = []
        self.name = ""
        self.is_directional = False
        self.properties_map={}
        self.properties_list=[]
        self.connect_later : List[Connection] = []
        self.connections : List[Connection] = []
        self.pinned_nodes : Set[str] = set()

    def make_directional_graph(self):
        self.is_directional = True

    def defer_connection(self, con : Connection):
        con.graph = self
        self.connect_later.append(con)

    def add_property(self, property, value):
        self.properties_map[property] = value
        self.properties_list.append(property)

    def add_node(self, node : Node):
        assert node.id
        self.nodes[node.id] = node
        self.node_list.append(node.id)

    def propogate_connections(self):
        for c in self.connect_later:
            assert c.node_name_from in self.nodes
            assert c.node_name_to in self.nodes

            src = self.nodes[c.node_name_from]
            dst = self.nodes[c.node_name_to]
            src.outputs[dst.id] = c
            dst.inputs[src.id] = c

            self.connections.append(c)

        self.connect_later = []
        

    def read_dot(self, fname):
        dp = DotParser(open(fname).readlines(), self)
        dp.read_prologue()
        dp.read_body()
        self.propogate_connections()

    def write_dot(self, fname):
        
        with open(fname, "w") as f:
            dw = DotWriter(self, f)
            dw.print()
        
    def select_nodes(self, accept: Callable[[Node], bool]) -> List[Node]:
        res = [self.nodes[node_id] for  node_id in self.node_list if accept(self.nodes[node_id])]
        return res


    def disconnect_node_inputs(self, n:Union[Node, str]):
        if type(n) == str:
            n = self.nodes[n]
        for id in n.inputs:
            c = n.inputs[id]
            other_node = self.nodes[c.node_name_from]
            del other_node.outputs[n.id]
            self.connections.remove(c)
        n.inputs=[]

    def disconnect_node_outputs(self, n:Union[Node, str]):
        for id in n.outputs:
            c = n.outputs[id]
            other_node = self.nodes[c.node_name_to]
            del other_node.inputs[n.id]
            self.connections.remove(c)
        n.outputs=[]

    def disconnect_node(self, n:Union[Node, str]):
        self.disconnect_node_inputs(n)
        self.disconnect_node_outputs(n)


    def pin_node(self, n : Union[Node, str]):
        if type(n) == str:
            n = self.nodes[n]
        self.pinned_nodes.add(n.id)    

    def delete_node(self, n : Union[Node, str]):
        """Delete node, unless it was pinned"""
        if type(n) == str:
            n = self.nodes[n]
        if n.id in self.pinned_nodes:
            print(f"Trying to delete pinned node {n.id}")
            return 
        self.disconnect_node(n)        
        del self.nodes[n.id]
        self.node_list.remove(n.id)


        


class DotWriter:
    def __init__(self, graph : Graph, file):
        self.graph = graph
        self.file = file

    def print(self):
        self.write_prologue()
        self.write_nodes()
        self.write_connections()
        print("}", file=self.file)
        

    def write_prologue(self):
        graph_type = ""
        if self.graph.is_directional:
            graph_type = "digraph"
        else:
            assert False, "unknown graph type"

        print(f"{graph_type} {self.graph.name} {'{'}", file=self.file)
        for prop in self.graph.properties_list:
            print(f"{prop}={self.graph.properties_map[prop]};", file=self.file)
    
    def write_nodes(self):
        for id in self.graph.node_list:
            node = self.graph.nodes[id]
            print(f"{id}",end="", file=self.file)
            self.write_properties(node)
            print(";", file=self.file)
    def write_properties(self, obj):
        if obj.properties_list:
            print(" [",end="", file=self.file)
            is_first = True 
            for prop_id in obj.properties_list:
                prop = obj.properties_map[prop_id]
                if not is_first:
                    print(", ", end="", file=self.file)
                print(f"{prop_id}={prop}",end="", file=self.file)
                is_first = False
            print("]",end="", file=self.file)

    def write_connections(self):
        for c in self.graph.connections:
            lhs = ":".join(c.node_path_from)
            rhs = ":".join(c.node_path_to)
            print(f"{lhs} -> {rhs}", file=self.file, end="")
            self.write_properties(c)
            print(";",file=self.file)

            

def remove_unused_produced_wires(g : Graph):
    while True:
        nodes = g.select_nodes(lambda n:not n.outputs and (n.label().startswith('"$') or n.label().startswith('"BUF')))
        if not nodes:
            break
        for node in nodes:
            g.delete_node(node)

def resolve_buffers(g):
    nodes = g.select_nodes(lambda n : n.label().startswith('"BUF'))
    for buf_node in nodes:
        if len(buf_node.outputs) != 1:
            print(f"BUF has too many outputs: {buf_node.outputs}")
            continue
        output_connection = list(buf_node.outputs.values())[0]
        named_node = g.nodes[output_connection.node_name_to]
        buf_node.set_label(named_node.label())
        if not named_node.outputs:
            g.delete_node(named_node)

        if len(buf_node.inputs) == 1:
            input_connection = list(buf_node.inputs.values())[0]
            input_node = g.nodes[input_connection.node_name_from]
            if input_node.label().startswith('"$'):
                input_node.set_label(buf_node.label())
                g.delete_node(buf_node)



def assign_names_to_gates(g, gates=["$xor|","$and|","$or|"]):
    nodes = g.select_nodes(lambda n:any(gate in n.label() for gate in gates))
    for node in nodes:
        if len(node.outputs) != 1:
            continue

        output_connection = list(node.outputs.values())[0]
        named_node = g.nodes[output_connection.node_name_to]
        node.set_property("color", named_node.get_property("color"))
        node.set_property("fontcolor", named_node.get_property("fontcolor"))
        if "{{" in named_node.label():
            continue
        if named_node.label()[0] != '"':
            continue
        if named_node.label()[-1] != '"':
            continue

        our_label = node.label()
        linked_label = named_node.label()[1:-1]
        our_label = our_label.replace("Y", f"Y\\n{linked_label}")
        node.set_label(our_label)

        if len(named_node.outputs) in [1]:
            for connection_id in named_node.outputs:
                output_connection = named_node.outputs[connection_id]
                new_connection = Connection(node.id, output_connection.node_name_to)                
                g.defer_connection(new_connection)
            g.delete_node(named_node)
            

    g.propogate_connections()



def color_path(g : Graph, path:List[str], new_color:str):
    """ Example of select """
    nodes = g.select_nodes(lambda n : n.label() in path)
    for node in nodes:
        node.set_property("color", new_color)

def color_connections(g : Graph):
    for c in g.connections:
        input_color = c.get_input_node().get_property("color")
        output_color = c.get_output_node().get_property("color")
        if input_color and input_color == output_color:
            c.set_property("color", input_color)


def clean_nmigen_graph(g):
    remove_unused_produced_wires(g)
    resolve_buffers(g)
    assign_names_to_gates(g)

if __name__ == "__main__":
    g = Graph()
    g.read_dot("ltp.dot")
    #color_connections(g)
    #remove_unused_produced_wires(g)
    #resolve_buffers(g)
    #assign_names_to_gates(g)

    g.write_dot("ltp2.dot")
