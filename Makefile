.PHONY: all  clean
.DEFAULT_GOAL := default

Date := $(shell date +"%Y-%m-%d")
Output := ./build/
Style := include/style.css
PaperSize := Letter
SourceDocs := $(wildcard *.md)
SourceCast := $(wildcard *.cast)
All := $(basename $(SourceDocs)) $(SourceCast:.cast=.gif)

default:
	@echo "Usage: make all"
	@$(foreach f, clean $(All), \
		echo "       make $f";)

clean:
	@$(foreach f, $(wildcard ./*.md), \
		rm -f -v $(Output)$(basename $f)-*.pdf;)
	@$(foreach f, $(wildcard ./*.md), \
		rm -f -v $(Output)$(basename $f)-*.html;)
	@$(foreach f, $(wildcard ./*.cast), \
		rm -f -v $(Output)$(basename $f).gif;)

%: %.md
	@echo "Source: '$<', Output folder: '$(Output)'"
	@pandoc --to html --standalone --self-contained \
		--css $(Style) \
		-o $(Output)$(basename $<)-$(Date).html $<
	@echo "Build '$(basename $<)-$(Date).html'"
	@wkhtmltopdf -q --page-size $(PaperSize) \
		$(Output)$(basename $< )-$(Date).html \
		$(Output)$(basename $< )-$(Date).pdf
	@echo "Build '$(basename $<)-$(Date).pdf'"

%.gif: %.cast
	@echo "Source: '$<', Output folder: '$(Output)'"
	@if [ "$<" = "$(shell find $< -type f -size -1024000c )" ]; then \
		docker run --user $(id -u):$(id -g) \
			--rm -v $$PWD:/data asciinema/asciicast2gif \
			$< $(Output)$(basename $<).gif ; \
			docker run -it --rm -v $(realpath $(Output)):/root \
				alpine chown $(shell id -u):$(shell id -g) \
				/root/$(basename $<).gif ; \
		echo "Build '$(Output)$(basename $<).gif'"; \
	else \
		echo "Skip '$<', file > 1M"; \
	fi

all: $(All)

