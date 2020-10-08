from lib2to3.fixer_base import BaseFix
from lib2to3.refactor import RefactoringTool
from lib2to3.fixer_util import (Leaf, syms, token, Call,
    Name, is_probably_builtin, Node, find_indentation,
    find_root, is_import, touch_import, make_suite)
from lib2to3.patcomp import PatternCompiler
from libfuturize.fixer_util import touch_import_top

class FixChr(BaseFix):
    PATTERN = """
        any
        """

    USAGE_PATTERN = """
        power< chr_func='chr' trailer<'(' arglist=any ')' > >
        """

    chr_tree = RefactoringTool(fixer_names=[]).refactor_string("""
# Override chr for py3 to return byte-str (same as py2)
_chr = lambda arg: chr(arg) if sys.version_info[0] < 3 else bytes([arg])
""", name="test")

    def start_tree(self, tree, filename):
        super(FixChr, self).start_tree(tree, filename)
        self.usage_patterns = []
        self.process_chr_func = False
        self.process_chr_func_done = False
        self.usage_patterns.append(
              PatternCompiler().compile_pattern(self.USAGE_PATTERN))

    def match(self, node):
        results = {"node": node}
        for pattern in self.usage_patterns:
            if pattern.match(node, results):
                if "chr_func" in results:
                    self.process_chr_func = True
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

    def process_chr(self, node):
        root, insert_pos = self.find_insert_pos(node)
        if self.process_chr_func and not self.process_chr_func_done:
            root.insert_child(insert_pos, self.chr_tree.clone())
            self.process_chr_func_done = True

    def transform(self, node, results):
        match = False
        node = results.get("node")
        if node.type == syms.power:
            if "chr_func" in results:
                node = results.get("chr_func")
                node.value = "_chr"
                node.changed()
                self.process_chr(node)
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
