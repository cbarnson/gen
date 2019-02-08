# The MIT License (MIT)

# Copyright (c) 2019 Cody Barnson

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import re
import os
import textwrap
import sys
import string

def ng_component_spec_template(base_kebab, classname):
    return textwrap.dedent("""\
        import { %s } from "./%s.component";

        describe("%s", () => {
          let component: %s;
          beforeEach(() => {
            component = new %s();
          });

          describe("foo", () => {
            it("foo is foo", () => {
              expect(component).toBeDefined();
            });
          });
        });
        """ % (classname, base_kebab, classname, classname, classname))

def ng_component_html_template():
    return textwrap.dedent("""\
        <p>
          Hello world!
        </p>""")


def ng_component_index_template(base_kebab):
    # E.g. Input: my-draft-view
    return textwrap.dedent("""\
        export * from "./%s.component";
        """ % (base_kebab))


def ng_component_ts_template(selector, template_url, classname):
    # E.g. Input: app-my-draft-view, my-draft-view.component.html, MyDraftViewComponent
    return textwrap.dedent("""\
        import { Component, OnInit } from "@angular/core";

        @Component({
          selector: "%s",
          templateUrl: "./%s"
        })
        export class %s implements OnInit {

          constructor() {}

          ngOnInit(): void {}
        }
    """ % (selector, template_url, classname))


class KebabCaseConverter:
    _precompile = False
    _is_compiled = False
    _first_cap_re = None
    _all_cap_re = None

    def __init__(self, precompile):
        self._precompile = precompile

    def convert_to_kebab(self, input_string):
        if (self._precompile and not self._is_compiled):
            self.compile()
        if (self._precompile):
            s1 = self._first_cap_re.sub(r"\1-\2", input_string)
            return self._all_cap_re.sub(r"\1-\2", s1).lower()
        else:
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", input_string)
            return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()

    def compile(self):
        self._first_cap_re = re.compile('(.)([A-Z][a-z]+)')
        self._all_cap_re = re.compile('([a-z0-9])([A-Z])')
        self._is_compiled = True


class NgKebabConverter(KebabCaseConverter):
    def __init__(self):
        super().__init__(False)

    # E.g. DocViewer --> doc-viewer
    def convert_to_kebab(self, input_string):
        return super().convert_to_kebab(input_string)

    # E.g. DocViewer --> app-doc-viewer
    def selector(self, input_string):
        return "app-" + self.convert_to_kebab(input_string) + "-component"

    # E.g. DocViewer --> doc-viewer.component.html
    def template_file_name(self, input_string):
        result = self.convert_to_kebab(input_string)
        return result + ".component.html"

    # E.g. DocViewer --> doc-viewer.component.ts
    def component_file_name(self, input_string):
        result = self.convert_to_kebab(input_string)
        return result + ".component.ts"

    # E.g. DocViewer --> doc-viewer.component.spec.ts
    def spec_file_name(self, input_string):
        result = self.convert_to_kebab(input_string)
        return result + ".component.spec.ts"


def test():
    converter = KebabCaseConverter(False)
    while True:
        try:
            print(converter.convert_to_kebab(input()))
        except EOFError:
            break


def component_class_name(input_string):
    return input_string if (str(input_string).endswith("Component")) else input_string + "Component"


def generate(converter, line, safe_mode = False):
    # Auto detect a different "mode", where input is just case
    # insensitive but words are delimited by spaces; build the string to
    # CamelCase style, then proceed as normal
    dprint(f"Inside generate : line = {line}, safe_mode = {safe_mode}")
    if (line.find(" ") != -1):
        line = "".join(map(lambda x: x.capitalize(), line.split(" ")))
        # line = string.capwords(line, "")
        dprint(f"capwords : {line}")
    assert(line.find(" ") is -1)

    print("")
    print("> Computed substitutions")
    print("-" * 40)
    print("Input        : %s" % (line))
    print("Class        : %s" % (component_class_name(line)))
    print("Base name    : %s" % (converter.convert_to_kebab(line)))
    print("Selector     : %s" % (converter.selector(line)))
    print("Template     : %s" % (converter.template_file_name(line)))
    print("Component    : %s" % (converter.component_file_name(line)))
    print("")

    classname = component_class_name(line)
    base_kebab = converter.convert_to_kebab(line)
    selector = converter.selector(line)
    template_filename = converter.template_file_name(line)
    component_filename = converter.component_file_name(line)
    spec_filename = converter.spec_file_name(line)

    try:
        # ========================================================
        # BEGIN : OUTPUT LIST OF COMPUTED VALUES
        # ========================================================

        # Setup, print computed values
        destination = os.path.join(os.getcwd(), base_kebab)
        template = os.path.join(destination, template_filename)
        component = os.path.join(destination, component_filename)
        spec = os.path.join(destination, spec_filename)
        index = os.path.join(destination, "index.ts")
        print("> Targets")
        print("-" * 40)
        print("Destination  : %s" % (destination))
        print("Template     : %s" % (template))
        print("Component    : %s" % (component))
        print("Spec         : %s" % (spec))
        print("Index        : %s" % (index))
        print("")

        # For dry-runs, i.e. "safe_mode", stop here
        if (safe_mode is True):
            print("Exiting... (dry-run only)")
            return

        # ========================================================
        # BEGIN : CREATE FILES
        # ========================================================

        # Create the destination directory
        assert(not os.path.exists(destination))
        assert(os.path.exists(os.path.dirname(destination)))
        os.mkdir(destination)
        assert(os.path.exists(destination))

        # Create .component.html
        content_html = ng_component_html_template()
        with open(template, "w") as text_file:
            print(f"{content_html}", file=text_file)

        # Create .component.ts
        content_ts = ng_component_ts_template(
            selector, template_filename, classname)
        with open(component, "w") as text_file:
            print(f"{content_ts}", file=text_file)

        # Create .spec.ts
        content_spec = ng_component_spec_template(
            base_kebab, classname)
        with open(spec, "w") as text_file:
            print(f"{content_spec}", file=text_file)

        # Create .index.ts
        content_index_ts = ng_component_index_template(base_kebab)
        with open(index, "w") as text_file:
            print(f"{content_index_ts}", file=text_file)

        # ========================================================
        # BEGIN : APPEND/MODIFY FILES
        # ========================================================

        # Update parent index
        parent_cwd = os.path.realpath(os.path.join(destination, ".."))
        parent_index = os.path.join(parent_cwd, "index.ts")
        print("parent_cwd : %s" % (parent_cwd))
        print("parent_index : %s" % (parent_index))
        index_line = textwrap.dedent("""\
            export * from "./%s/%s.component";""" % (base_kebab, base_kebab))
        with open(parent_index, "a") as text_file:
            print(f"{index_line}", file=text_file)

        # Checks
        assert(os.path.exists(os.path.join(destination, component_filename)))
        assert(os.path.exists(os.path.join(destination, template_filename)))
        assert(os.path.exists(os.path.join(destination, spec_filename)))
        print("Files successfully created.")
        print("All done!")
        print("")

    except Exception:
        print("ERROR: Must exit...")
        exit(2)


def preamble():
    print("")
    print("=================== Angular Component Generator ===================")
    print("Usage: gen.cmd [--dry-run] [optional space delimited list of words]")
    print("===================================================================")
    print("")

# ========================================
# toggle DEBUG print statements here!!!
# ========================================
def dprint(s):
    DEBUG_MODE = False
    if (DEBUG_MODE):
        print(s)

def main():
    converter = NgKebabConverter()
    safe_mode = False

    # If run with args, use the arg list as a single line of input
    # E.g. gen.py hello world
    if (len(sys.argv) > 1):
        raw_args = sys.argv[1:]
        dprint(f"sys.argv : {raw_args}")

        if ("--help" in raw_args):
            raw_args.remove("--help")
            dprint(f"After --help option removed: {raw_args}")
            preamble()

        if ("--dry-run" in raw_args):
            raw_args.remove("--dry-run")
            dprint(f"After --dry-run option removed: {raw_args}")
            safe_mode = True


        # Post-option removal, if still have args, run once with them, else move to the general loop below
        dprint(f"len(raw_args) : {len(raw_args)}")
        if (len(raw_args) > 0):
            # Space-separated list of the command line arguments, after options are removed
            args = " ".join(raw_args)
            dprint(f"line : {args}")
            try:
                dprint(f"safe_mode : {safe_mode}")
                generate(converter, args, safe_mode)
            except Exception:
                exit(3)
            return

    # For invocation without command line arguments (that are NOT options)
    while True:
        try:
            line = input("New component (e.g. my new item, MyNewItem)\nPlease enter name (empty RETURN to quit):").strip()
            if (line is ""):
                print("Exiting...")
                break

            print("line : %s" % (line))
            generate(converter, line, safe_mode)

        except EOFError:
            print("ERROR: Must exit...")
            exit(1)


if __name__ == "__main__":
    # test()
    main()
