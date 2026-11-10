.PHONY: build preview publish

build:            ## rebuild _site/ from content.toml
	@python3 build.py

preview: build    ## build and open a local preview at http://localhost:8000
	@echo "→ http://localhost:8000  (Ctrl-C to stop)"
	@(sleep 1 && open http://localhost:8000) &
	@python3 -m http.server 8000 -d _site

publish: build    ## commit everything and push (GitHub rebuilds the live site)
	@git add -A && git commit -m "$${m:-Update website}" && git push
