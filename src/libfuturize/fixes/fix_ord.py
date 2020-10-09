#
# Author: samir.das@nutanix.com, vaibhav.gupta@nutanix.com
#         manish.singh@nutanix.com
#

from lib2to3.fixer_base import BaseFix
from lib2to3.refactor import RefactoringTool
from lib2to3.fixer_util import (Leaf, syms, token, Call,
    Name, is_probably_builtin, Node, find_indentation,
    find_root, is_import, touch_import, make_suite)
from lib2to3.patcomp import PatternCompiler
from libfuturize.fixer_util import touch_import_top

class FixOrd(BaseFix):
    PATTERN = """
        any
        """

    USAGE_PATTERN = """
        power< ord_func='ord' trailer<'(' arglist=any ')' > >
        """

    ord_tree = RefactoringTool(fixer_names=[]).refactor_string("""
# Override ord for py3 to return arg
# as we have fixed byte-strings with prefix 'b"
# which make str[0] as int
_ord = lambda arg: ord(arg) if not isinstance(arg, int) else arg
""", name="test")

    def start_tree(self, tree, filename):
        super(FixOrd, self).start_tree(tree, filename)
        self.usage_patterns = []
        self.process_ord_func = False
        self.process_ord_func_done = False
        self.usage_patterns.append(
              PatternCompiler().compile_pattern(self.USAGE_PATTERN))

    def match(self, node):
        results = {"node": node}
        for pattern in self.usage_patterns:
            if pattern.match(node, results):
                if "ord_func" in results:
                    self.process_ord_func = True
                return results

    def find_insert_pos(self, node):
        def is_import_stmt(node):
            return (node.type == syms.simple_stmt and node.children and
                    is_import(node.children[0]))
        root = find_root(node)
        insert_pos = offset = 0
        for idx, node in enumerate(root.children):
            if not is_import_stmt(node):
                continue
            for offset, node2 in enumerate(root.children[idx:]):
                if not is_import_stmt(node2):
                    break
            insert_pos = idx + offset
            break
        return root, insert_pos

    def process_ord(self, node):
        root, insert_pos = self.find_insert_pos(node)
        if self.process_ord_func and not self.process_ord_func_done:
            root.insert_child(insert_pos, self.ord_tree.clone())
            self.process_ord_func_done = True

    def transform(self, node, results):
        match = False
        node = results.get("node")
        if node.type == syms.power:
            if "ord_func" in results:
                node = results.get("ord_func")
                node.value = "_ord"
                node.changed()
                self.process_ord(node)
                return
            power_stmt= Node(syms.power, childs, prefix=node.prefix)
            node.replace(power_stmt)
        if not match:
            return
        tree = self.stringio_tree.clone()
        indentation = find_indentation(node)
        self.fix_indentation(tree, indentation)
        node.replace(tree)

    def fix_indentation(self, tree, indentation):
        for ch in tree.children:
            if ch.type == token.INDENT:
                ch.value += indentation
            if ch.type == 1:
                if ch.value == "else":
                    ch.prefix = indentation
            if isinstance(ch, Node):
                # fix except clause as it does not indentation leaf.
                self.fix_indentation(ch, indentation)
