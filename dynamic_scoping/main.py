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
        self.symbol_table = SymbolTable({
            self.global_scope_id: self.current_scope
        })

        for i in range(len(lines)):
            line = lines[i]
            
            # match main function declaration
            if self.main_function_declaration(line, i):
                continue

            if self.function_declaration(line, i):
                continue
            
            if self.variables_declaration(line, i):
                continue

            if self.new_scope(line):
                continue

            if self.end_of_scope(line):
                continue
            
        # print the remaining outermost scope
        assert self.current_scope.id == self.global_scope_id
        print(self.current_scope)


    def main_function_declaration(self, line: str, line_index: int) -> bool:
        res = re.match(r"\s*void\s*main\s*\(\s*\)\s*{", line)
        if res is not None:
            # current scope is the main function scope
            self.current_scope = self.symbol_table.scopes[self.global_scope_id]

            # add main function to the current scope
            self.current_scope.variables.append(VariableDeclaration("main", "void", line_index))
            return True
        
        return False
    
    
    def function_declaration(self, line: str, line_index: int) -> bool:
        res = re.match(r"^\s*(int|float|char|bool|void)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*{\s*$", line)
        
        if res is not None:
            # add function to the current scope
            function_name = res.group(2)
            function_type = res.group(1)
            self.current_scope.variables.append(
                VariableDeclaration(function_name, function_type, line_index)
            )
            
            # create new scope for the function
            self.new_scope(line)
            
            # add function parameters to the current scope
            potential_function_parameters = res.group(3)
            if potential_function_parameters is not None:
                self.variables_declaration(potential_function_parameters, line_index)

            return True
    
        return False
    

    def variables_declaration(self, line: str, line_index: int) -> bool:
        # using re, check if string is of the form "type variable_name(, variable_name)*;"
        # for every variable name, add it to the current scope
        potential_var_declaration = re.match(r"^\s*(int|float|char|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*((,\s*(int|float|char|bool)?\s*[a-zA-Z_][a-zA-Z0-9_]*\s*)*)?;?\s*$", line)
        if potential_var_declaration is not None:

            # first variable (mandatory)
            first_variable_type = potential_var_declaration.group(1)
            variable_name = potential_var_declaration.group(2)
            self.current_scope.variables.append(VariableDeclaration(variable_name, first_variable_type, line_index + 1))

            # additional variables (optional)
            remaining_line = potential_var_declaration.group(3)
            while remaining_line is not None:
                potential_var_declaration = re.match(r"^\s*,?\s*(int|float|char|bool)?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*((,\s*(int|float|char|bool)?\s*[a-zA-Z_][a-zA-Z0-9_]*\s*)*)?;?\s*$", remaining_line)
                
                if potential_var_declaration is None:
                    break
                
                variable_name = potential_var_declaration.group(2)
                variables_type = first_variable_type
                if potential_var_declaration.group(1) is not None: # type is specified
                    variables_type = potential_var_declaration.group(1)
                self.current_scope.variables.append(VariableDeclaration(variable_name, variables_type, line_index + 1))
                
                # update remainings
                remaining_line = potential_var_declaration.group(3)

            return True
        
        return False
    

    def new_scope(self, line: str) -> None | Scope:
        potential_new_scope = re.match(r"^\s*(.*?){\s*$", line)
        if potential_new_scope is not None:
            scope_name: str = potential_new_scope.group(1)
            # group 1 can be empty for unamed blocks, just add a random name to it
            if scope_name == "":
                scope_name = "unnamed_scope_" + generate_random_string()
            new_scope_id = ScopeId(scope_name)
            new_scope = Scope(new_scope_id, self.current_scope.id, [])

            # add new scope to the symbol table
            self.symbol_table.scopes[new_scope_id] = new_scope

            # add new scope to the current scope
            self.current_scope = new_scope

            return True
        
        return False
    

    def end_of_scope(self, line: str) -> bool:
        """
        If end of scope, change self.current_scope to the parent scope
        NOTE: Except for the global scope!
        Also print the scope and its variables before deleting it
        """
        potential_end_of_scope = re.match(r"^\s*}\s*$", line)
        if potential_end_of_scope is not None and self.current_scope.id != self.global_scope_id:
            print(self.current_scope)
            self.current_scope = self.symbol_table.scopes[self.current_scope.parent]

            return True
        else:
            return False






def main():
    Translator()


# run the main function
if __name__ == "__main__":
    main()