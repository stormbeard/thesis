rm *.bbl *.log *.pdf *.toc *.lot *.blg *.aux *.lof
pdflatex thesis && bibtex thesis && pdflatex thesis && pdflatex thesis
