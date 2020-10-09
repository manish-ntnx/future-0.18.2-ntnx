from lib2to3.fixer_base import BaseFix
from lib2to3.refactor import RefactoringTool
from lib2to3.fixer_util import (Leaf, syms, token, Call,
    Name, is_probably_builtin, Node, find_indentation,
    find_root, is_import, touch_import, make_suite)
from lib2to3.patcomp import PatternCompiler
from libfuturize.fixer_util import touch_import_top

class FixCstringIo(BaseFix):
    PATTERN = """
        import_name< 'import' modulename='cStringIO' >
        |
        import_name< 'import' dotted_as_name< 'cStringIO' 'as' modulename=any > >
        |
        import_from< 'from' packagename='cStringIO' 'import' importname='StringIO' >
        |
        import_from< 'from' packagename='cStringIO' 'import' import_as_name<importname='StringIO' 'as' constantname=any > >
        |
        import_name< 'import' modulename='StringIO' >
        |
        import_name< 'import' dotted_as_name< 'StringIO' 'as' modulename=any > >
        |
        import_from< 'from' packagename='StringIO' 'import' importname='StringIO' >
        |
        import_from< 'from' packagename='StringIO' 'import' import_as_name<importname='StringIO' 'as' constantname=any > >
        |
        any
        """

    USAGE_PATTERN = """
        power< libname="cStringIO" trailer<'.' attribute=any > >
        |
        power< libname="cStringIO" trailer<'.' attribute=any > trailer<'(' arglist=any ')' > >
        |
        power< libname="cStringIO" trailer<'.' attribute=any > trailer<'(' ')' > >
        |
        power< libname="StringIO" trailer<'.' attribute=any > >
        |
        power< libname="StringIO" trailer<'.' attribute=any > trailer<'(' arglist=any ')' > >
        |
        power< libname="StringIO" trailer<'.' attribute=any > trailer<'(' ')' > >
        """

    stringio_tree = RefactoringTool(fixer_names=[]).refactor_string("""import sys
if sys.version_info[0] < 3:
  from cStringIO import StringIO as StringIO
else:
  from io import BytesIO as StringIO
  """, name="test")

    def start_tree(self, tree, filename):
        super(FixCstringIo, self).start_tree(tree, filename)
        self.usage_patterns = []
        self.usage_patterns.append(
              PatternCompiler().compile_pattern(self.USAGE_PATTERN))

    def match(self, node):
        results = {"node": node}
        match = self.pattern.match(node, results)
        if match and node.type in (syms.import_from, syms.import_name):
            if "modulename" in results:
                name = results.get("modulename")
            return results
        if node.type == token.STRING:
            if "\\x" in node.value:
                return results


    def transform(self, node, results):
        print ("node %s:results %s", results)
        match = False
        node = results.get("node")
        if node.type == syms.import_from:
            match = True
        if node.type == syms.import_name:
            match = True

        if node.type == syms.power:
            if "arglist" in results:
                childs = [Leaf(1, 'StringIO'),
                      Node(syms.trailer, [
                        Leaf(7, '('),
                        results.get("arglist").clone(),
                        Leaf(8, ')')
                      ])
                    ]
            else:
                childs = [Leaf(1, 'StringIO'),
                      Node(syms.trailer, [
                        Leaf(7, '('),
                        Leaf(8, ')')
                      ])
                    ]
            power_stmt= Node(syms.power, childs, prefix=node.prefix)
            node.replace(power_stmt)
        if not match:
            return
        packagename = ""
        if "importname" in results:
            packagename = results["importname"].value
        if "modulename" in results:
            packagename = results["modulename"].value
        if "constantname" in results:
            packagename = results["packagename"].value
        if not packagename:
            return
        tree = self.stringio_tree.clone()
        indentation = find_indentation(node)
        self.fix_indentation(tree, indentation)
        #touch_import_top(None, name_to_import="sys", node=node)
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
