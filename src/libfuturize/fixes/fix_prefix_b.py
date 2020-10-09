#
# Author: samir.das@nutanix.com, vaibhav.gupta@nutanix.com
#         manish.singh@nutanix.com
#
# Add a prefix 'b' to the strings starting with `\x`.

from lib2to3.fixer_base import BaseFix
from lib2to3.refactor import RefactoringTool
from lib2to3.fixer_util import (Leaf, syms, token, Call,
    Name, is_probably_builtin, Node, find_indentation,
    find_root, is_import, touch_import, make_suite)
from lib2to3.patcomp import PatternCompiler
from libfuturize.fixer_util import touch_import_top

class FixPrefixB(BaseFix):
    PATTERN = """
        any
        """

    USAGE_PATTERN = """
        """
    def start_tree(self, tree, filename):
        super(FixPrefixB, self).start_tree(tree, filename)
        #self.usage_patterns = []
        #self.usage_patterns.append(
         #     PatternCompiler().compile_pattern(self.USAGE_PATTERN))

    def match(self, node):
        results = {"node": node}
        #match = self.pattern.match(node, results)
        if node.type == token.STRING:
            if "\\x" in node.value:
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

    def transform(self, node, results):
        match = False
        node = results.get("node")
        # Fix byte string with "b" prefix
        if node.type == token.STRING:
            node.prefix = " b"
            node.changed()

        #tree = self.fix_prefix_b_tree.clone()
        #indentation = find_indentation(node)
        #self.fix_indentation(tree, indentation)
        #node.replace(tree)

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
