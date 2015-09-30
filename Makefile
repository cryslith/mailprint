all: test.pdf

test.pdf: test.tex
	pdflatex -interaction=nonstopmode test.tex

clean:
	-rm test.log test.aux test.pdf

.PHONY: all clean
