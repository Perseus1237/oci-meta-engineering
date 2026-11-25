.PHONY: demo test

demo:
	python3 -B demo.py

test:
	python3 -B -m unittest discover -s tests -v
