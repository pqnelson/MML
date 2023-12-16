TEX=pdflatex
FILE=handout

all: index
	$(TEX) $(FILE)
	$(TEX) $(FILE)

index:
	-rm $(FILE).ilg
	-rm $(FILE).ind
	-rm $(FILE).idx
	$(TEX) $(FILE)
	makeindex $(FILE)