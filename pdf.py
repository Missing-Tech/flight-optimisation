import os


def convert_to_tex(directory, output_tex):
    with open(output_tex, "w", encoding="utf-8") as tex_file:
        for filename in os.listdir(directory):
            if filename.endswith(".py"):
                tex_file.write(r"\section{" + filename + r"}" + "\n")
                with open(
                    os.path.join(directory, filename), "r", encoding="utf-8"
                ) as file:
                    code = file.read()
                    tex_file.write(
                        r"\begin{minted}[breaklines,fontsize=\small]{python}" + "\n"
                    )
                    tex_file.write(code + "\n")
                    tex_file.write(r"\end{minted}" + "\n")


# Usage example:
convert_to_tex(".", "output_file.tex")
