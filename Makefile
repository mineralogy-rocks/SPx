.PHONY: build clean

build:
	pip install ".[desktop]"
	pyinstaller SPx.spec

clean:
	rm -rf build dist
