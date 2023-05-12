# static scoping symbol table generation
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
# for each line, check if it is a variable declaration or a new scope
# if it is a variable declaration, add it to the current scope
# if it is a new scope, add it to the current scope and make it the current scope
# if it is the end of a scope, make the parent scope the current scope

def generate_random_string(length: int = 5) -> str:
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for _ in range(length))


class Translator:
    symbol_table: SymbolTable

    def __init__(self) -> None:
        print("Static symbol table generation...")

        with open(TEST_FILE) as f:
            lines = f.readlines()

        global_scope_id = ScopeId("global")
        current_scope: Scope = Scope(global_scope_id, None, [])
        symbol_table = SymbolTable({
            global_scope_id: current_scope
        })

        for i in range(len(lines)):
            line = lines[i]
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
        assert current_scope.id == global_scope_id
        print(current_scope)

        
    def variables_declaration(self, line: str, current_scope: Scope, line_index: int):
        # using re, check if string is of the form "type variable_name(, variable_name)*;"
        # for every variable name, add it to the current scope
        potential_var_declaration = re.match(r"^\s*(int|float|char|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(,\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*)*;$", line)
        if potential_var_declaration is not None:
            variables_type = potential_var_declaration.group(1)
            variables = re.split(r"\s*,\s*", potential_var_declaration.group(2))
            if potential_var_declaration.group(3) is not None:
                potential_additional_variables = re.sub(r"^\s*,\s*", "", potential_var_declaration.group(3))
                variables.extend(re.split(r"\s*,\s*", potential_additional_variables))
            for variable in variables:
                current_scope.variables.append(VariableDeclaration(variable, variables_type, line_index + 1))


    def new_scope(self, line: str, current_scope: Scope, scopes: dict[ScopeId, Scope]) -> None | Scope:
        potential_new_scope = re.match(r"^\s*(.*?){\s*$", line)
        if potential_new_scope is not None:
            scope_name: str = potential_new_scope.group(1)
            # group 1 can be empty for unamed blocks, just add a random name to it
            if scope_name == "":
                scope_name = "unnamed_scope_" + generate_random_string()
            new_scope_id = ScopeId(scope_name)
            new_scope = Scope(new_scope_id, current_scope.id, [])
            return new_scope
        else:
            return None


    def end_of_scope(self, line: str, current_scope: Scope) -> bool:
        """
        If end of scope, return the parent scope
        Also print the scope and its variables before deleting it
        """
        potential_end_of_scope = re.match(r"^\s*}\s*$", line)
        if potential_end_of_scope is not None:
            print(current_scope)
            return True
        else:
            return False



def main():
    Translator()


# run the main function
if __name__ == "__main__":
    main()
