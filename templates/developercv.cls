%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Developer CV - LaTeX class (single-column, ATS-friendly version)
%
% Origin: http://www.LaTeXTemplates.com (Developer CV v2.0)
% Authors: Omar Roldan; based on templates by Jan Vorisek, Jan Küster and Vel
% License: MIT (see LICENSE)
%
% Changes: Source Sans Pro font, single-column layout, contact line without icons,
% searchable text (cmap, ligatures disabled), shared header for CV and letter.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{developercv}[2026/10/07 Developer CV class v3.0]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\ProcessOptions\relax
\LoadClass{extarticle}

%----------------------------------------------------------------------------------------
%	PACKAGES
%----------------------------------------------------------------------------------------

\usepackage{cmap} % Searchable, copyable PDF text (must precede fontenc)
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[default,semibold]{sourcesanspro}
\renewcommand*\familydefault{\sfdefault}

\usepackage{microtype}
\DisableLigatures{encoding = *, family = *} % fi/fl ligatures would break keyword search

\usepackage[hidelinks]{hyperref}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{enumitem}
\usepackage{geometry}

\geometry{
	paper=a4paper,
	top=1.3cm,
	bottom=1.3cm,
	left=1.6cm,
	right=1.6cm,
}

\setlength{\parindent}{0mm}
\setlength{\parskip}{0mm}
\pagestyle{empty}
\frenchspacing % Uniform spacing between sentences

\definecolor{accent}{HTML}{000000}
\definecolor{muted}{HTML}{444444}

\setlist[itemize]{leftmargin=4mm, noitemsep, topsep=1pt, parsep=0pt, partopsep=0pt, label={\textbullet}}

%----------------------------------------------------------------------------------------
%	HEADER: photo, name, title, contact line
%----------------------------------------------------------------------------------------

% Round photo; #1 = image file
\newcommand{\cvphoto}[1]{%
	\begin{tikzpicture}[baseline=(current bounding box.center)]
		\clip (0,0) circle (1.1cm);
		\node at (0,0) {\includegraphics[width=2.2cm]{#1}};
		\draw[accent, line width=0.4mm] (0,0) circle (1.1cm);
	\end{tikzpicture}%
}

% Name, title (may be empty) and contact line(s)
\newcommand{\cvname}[1]{{\fontsize{18}{22}\selectfont\textbf{\MakeUppercase{#1}}}}
\newcommand{\cvtitle}[1]{{\large #1}}
\newcommand{\cvcontact}[1]{{\small\color{muted} #1}}
\newcommand{\sep}{\unskip\nobreak\hspace{1.5mm}|\hspace{1.5mm}\allowbreak} % the "|" never starts a line

%----------------------------------------------------------------------------------------
%	SECTIONS AND ENTRIES
%----------------------------------------------------------------------------------------

\def\Vhrulefill{\leavevmode\leaders\hrule height 0.7ex depth \dimexpr0.4pt-0.7ex\hfill\kern0pt}

% Section title with a rule
\newcommand{\cvsect}[1]{%
	\par\vspace{1.8mm}%
	{\color{accent}\MakeUppercase{\textbf{#1}}}\hspace{4pt}\Vhrulefill\par
	\vspace{0.8mm}%
}

% Entry: #1 = title, #2 = period, #3 = organization / subtitle, #4 = body (list or text)
% The organization follows the title; if it does not fit, the line wraps and the period stays right.
\newcommand{\cventry}[4]{%
	\par\noindent
	\parbox[t]{\dimexpr\textwidth-2.6cm}{\raggedright\textbf{#1}%
		\if\relax\detokenize{#3}\relax\else{\small\color{muted}\hspace{1.5mm}|\hspace{1.5mm}#3}\fi}%
	\hfill\parbox[t]{2.5cm}{\raggedleft\small #2}\par
	#4\par\vspace{1.1mm}%
}

% Labelled line: #1 = label, #2 = content
\newcommand{\cvline}[2]{%
	\par\hangindent=4mm\hangafter=1\textbf{#1:} #2\par\vspace{0.5mm}%
}
