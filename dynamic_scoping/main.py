# dynamic scoping symbol table generation
from dataclasses import dataclass
import random
import string
import re

TEST_FILE = "/home/onyr/Documents/5passau/programing_paradigm/src/clite_symbol_table/test_files/course_example.clite"

@dataclass(eq=True, frozen=True)
class ScopeId:
    id: str

@dataclass
class VariableDeclaration:
    name: str
    type: str
    line_index: int

    def __str__(self) -> str:
        return f"<{self.name}, {self.type}, {self.line_index}>"

@dataclass
class Scope:
    id: ScopeId
    parent: ScopeId | None
    variables: list[VariableDeclaration]

    def __str__(self) -> str:
        var_str = ", ".join([str(var) for var in self.variables])
        return "Scope ({}) variables: {}".format(self.id.id, var_str)

@dataclass
class SymbolTable:
    scopes: dict[ScopeId, Scope]

    def __str__(self) -> str:
        return "\n".join([str(scope) for scope in self.scopes])


# read the file line by line
# function declarations are scopes
# start adding function parameters to the scope
# if a variable is declared, add it to the current scope
# when a scope ends, make the parent scope the current scope
# blocks are scopes with random names

# all functions are also variables in the global scope
# the global scope is also the same as the main function scope


def generate_random_string(length: int = 5) -> str:
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for _ in range(length))


class Translator:
    symbol_table: SymbolTable

    global_scope_id: ScopeId
    current_scope: Scope

    def __init__(self) -> None:
        print("Static symbol table generation...")

        with open(TEST_FILE) as f:
            lines = f.readlines()

        self.global_scope_id = ScopeId("main")
        self.current_scope: Scope = Scope(self.global_scope_id, None, [])
        symbol_table = SymbolTable({
            self.global_scope_id: self.current_scope
        })

        for i in range(len(lines)):
            line = lines[i]
            
            # match main function declaration
            if self.main_function_declaration(line, i):
                continue
            
            self.variables_declaration(line, current_scope, i)
            potential_new_scope = self.new_scope(line, current_scope, symbol_table.scopes)
            potential_end_of_scope = self.end_of_scope(line, current_scope)
            
            if potential_new_scope is not None:
                # add new scope to the current scope
                current_scope = potential_new_scope
                symbol_table.scopes[current_scope.id] = current_scope
            elif potential_end_of_scope:
                if current_scope.parent is not None:
                    current_scope = symbol_table.scopes[current_scope.parent]

        # print the remaining outermost scope
        assert current_scope.id == self.global_scope_id
        print(current_scope)


    def main_function_declaration(self, line: str, line_index: int) -> bool:
        res = re.match(r"\s*void main\s*\(\s*\)\s*{", line)
        if res is not None:
            # current scope is the main function scope
            self.current_scope = self.symbol_table.scopes[self.global_scope_id]

            # add main function to the current scope
            self.current_scope.variables.append(VariableDeclaration("main", "void", line_index))
            return True
        
        return False
    
    
    def function_declaration(self, line: str, line_index: int) -> bool:
        res = re.match(r"\s*(int|float|char|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*{", line)
        if res is not None:
            # add function to the current scope
            self.current_scope.variables.append(VariableDeclaration(res.group(1), "void", line_index))
            return True
        
        return False






def main():
    Translator()


# run the main function
if __name__ == "__main__":
    main()