import os


def convert_to_tex(directory, output_tex):
    with open(output_tex, "w", encoding="utf-8") as tex_file:
        for root, dirs, _ in os.walk(directory):
            # Skip .venv and __pycache__ directories
            if ".venv" in dirs:
                dirs.remove(".venv")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            if ".git" in dirs:
                dirs.remove(".git")

            # Write a section for the current directory
            current_dir = os.path.relpath(root, directory)
            if current_dir != "." and "tests" not in current_dir:
                tex_file.write(r"\section{" + current_dir + r"}" + "\n")

            # Include Python files within the current directory
            for filename in os.listdir(root):
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    tex_file.write(r"\subsection{" + filename + r"}" + "\n")
                    with open(filepath, "r", encoding="utf-8") as file:
                        code = file.read()
                        tex_file.write(
                            r"\begin{minted}[breaklines,fontsize=\small]{python}" + "\n"
                        )
                        tex_file.write(code + "\n")
                        tex_file.write(r"\end{minted}" + "\n")

            # Include Python files from tests folders within the current directory
            tests_dir = os.path.join(root, "tests")
            if os.path.exists(tests_dir):
                tex_file.write(r"\subsection{Tests}" + "\n")
                for filename in os.listdir(tests_dir):
                    if filename.endswith(".py"):
                        filepath = os.path.join(tests_dir, filename)
                        tex_file.write(r"\subsubsection{" + filename + r"}" + "\n")
                        with open(filepath, "r", encoding="utf-8") as file:
                            code = file.read()
                            tex_file.write(
                                r"\begin{minted}[breaklines,fontsize=\small]{python}"
                                + "\n"
                            )
                            tex_file.write(code + "\n")
                            tex_file.write(r"\end{minted}" + "\n")


convert_to_tex(".", "code.tex")
