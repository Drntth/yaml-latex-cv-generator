PY := .venv/bin/python
VARIANT ?= developer
LNG ?= en
# Photo: PHOTO=1 (on) or PHOTO=0 (off); empty means the variant/application file decides.
PHOTO ?=
PHOTO_ARG := $(if $(filter 1,$(PHOTO)),--photo)$(if $(filter 0,$(PHOTO)),--no-photo)

.PHONY: all cv letter app venv clean lint test preview

all:
	$(PY) build.py all $(PHOTO_ARG)

cv:
	$(PY) build.py cv --variant $(VARIANT) --lang $(LNG) $(PHOTO_ARG)

letter:
	$(PY) build.py letter --variant $(VARIANT) --lang $(LNG) $(PHOTO_ARG)

app:
	$(if $(APP),,$(error Usage: make app APP=applications/<file>.yaml))
	$(PY) build.py app $(APP) $(PHOTO_ARG)

venv:
	python3.14 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt

lint:
	.venv/bin/ruff check build.py tests && .venv/bin/ruff format --check build.py tests

test:
	.venv/bin/pytest -q

# README preview: first page of the developer CVs as PNG (poppler-utils: pdftoppm).
preview:
	pdftoppm -png -r 80 -f 1 -l 1 -singlefile dist/cv_developer_en.pdf docs/preview_cv_developer_en
	pdftoppm -png -r 80 -f 1 -l 1 -singlefile dist/cv_developer_hu.pdf docs/preview_cv_developer_hu

clean:
	rm -rf build
