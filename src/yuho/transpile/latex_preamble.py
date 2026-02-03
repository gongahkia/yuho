"""
LaTeX preamble generation for legal documents.

Contains all the LaTeX document setup including:
- Document class and packages
- Custom commands and environments
- Style definitions for legal documents
"""

from typing import List

from yuho.transpile.latex_utils import escape_latex


def generate_preamble(
    document_title: str = "Legal Statutes",
    author: str = "",
    use_margins: bool = True,
) -> List[str]:
    """
    Generate LaTeX preamble for legal documents.
    
    Args:
        document_title: Title for the document
        author: Document author
        use_margins: Whether to use margin notes
        
    Returns:
        List of preamble lines
    """
    lines: List[str] = []
    
    def emit(text: str) -> None:
        lines.append(text)
    
    def emit_blank() -> None:
        lines.append("")
    
    # Document class
    emit(r"\documentclass[11pt,a4paper]{article}")
    emit_blank()

    # Essential packages
    emit(r"% Essential packages")
    emit(r"\usepackage[utf8]{inputenc}")
    emit(r"\usepackage[T1]{fontenc}")
    emit(r"\usepackage{lmodern}")
    emit_blank()

    # Page geometry
    emit(r"% Page layout")
    if use_margins:
        emit(r"\usepackage[a4paper,left=3cm,right=4cm,top=2.5cm,bottom=2.5cm,marginparwidth=3cm]{geometry}")
    else:
        emit(r"\usepackage[a4paper,margin=2.5cm]{geometry}")
    emit_blank()

    # Typography
    emit(r"% Typography")
    emit(r"\usepackage{microtype}")
    emit(r"\usepackage{parskip}")
    emit(r"\setlength{\parindent}{0pt}")
    emit_blank()

    # Colors and boxes
    emit(r"% Colors and boxes for illustrations")
    emit(r"\usepackage{xcolor}")
    emit(r"\usepackage{tcolorbox}")
    emit(r"\tcbuselibrary{skins}")
    emit_blank()

    # Define illustration box style
    emit(r"% Illustration box style")
    emit(r"\newtcolorbox{illustrationbox}[1][]{")
    emit(r"  enhanced,")
    emit(r"  colback=gray!10,")
    emit(r"  colframe=gray!50,")
    emit(r"  fontupper=\itshape,")
    emit(r"  boxrule=0.5pt,")
    emit(r"  left=10pt,")
    emit(r"  right=10pt,")
    emit(r"  top=8pt,")
    emit(r"  bottom=8pt,")
    emit(r"  #1")
    emit(r"}")
    emit_blank()

    # Tables
    emit(r"% Tables for penalties")
    emit(r"\usepackage{booktabs}")
    emit(r"\usepackage{array}")
    emit(r"\usepackage{longtable}")
    emit_blank()

    # Margin notes
    if use_margins:
        emit(r"% Margin notes")
        emit(r"\usepackage{marginnote}")
        emit(r"\renewcommand*{\marginfont}{\footnotesize\sffamily}")
        emit_blank()

    # Hyperlinks and cross-references
    emit(r"% Hyperlinks")
    emit(r"\usepackage{hyperref}")
    emit(r"\hypersetup{")
    emit(r"  colorlinks=true,")
    emit(r"  linkcolor=blue!60!black,")
    emit(r"  urlcolor=blue!60!black,")
    emit(r"  pdftitle={" + escape_latex(document_title) + "},")
    if author:
        emit(r"  pdfauthor={" + escape_latex(author) + "},")
    emit(r"}")
    emit_blank()

    # Section formatting for statutes
    emit(r"% Statute section formatting")
    emit(r"\usepackage{titlesec}")
    emit(r"\titleformat{\section}")
    emit(r"  {\normalfont\Large\bfseries}")
    emit(r"  {Section \thesection}")
    emit(r"  {1em}")
    emit(r"  {}")
    emit_blank()

    # Custom commands for legal formatting
    emit(r"% Custom commands for legal formatting")
    emit(r"\newcommand{\statute}[2]{%")
    emit(r"  \subsection[Section #1 --- #2]{Section #1 --- #2}%")
    emit(r"  \label{sec:#1}%")
    emit(r"}")
    emit_blank()

    emit(r"\newcommand{\sectionref}[1]{Section~\ref{sec:#1}}")
    emit_blank()

    emit(r"\newcommand{\element}[2]{%")
    emit(r"  \textbf{#1:} #2%")
    emit(r"}")
    emit_blank()

    # Definition list environment
    emit(r"% Definition list for legal definitions")
    emit(r"\newenvironment{legaldefs}{%")
    emit(r"  \begin{description}[leftmargin=2em,style=nextline]")
    emit(r"}{%")
    emit(r"  \end{description}")
    emit(r"}")
    emit(r"\usepackage{enumitem}")
    emit_blank()

    # Document metadata
    emit(r"% Document metadata")
    emit(r"\title{" + escape_latex(document_title) + "}")
    if author:
        emit(r"\author{" + escape_latex(author) + "}")
    else:
        emit(r"\author{}")
    emit(r"\date{\today}")
    emit_blank()
    
    return lines
