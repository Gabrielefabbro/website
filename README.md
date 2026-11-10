# Personal website

All content is in **`content.toml`**. Edit it, then:

```bash
make preview                 # rebuild + open http://localhost:8000
make publish m="add paper"   # commit + push → live in ~1 min
```

- Photo: put it in `assets/` and set `photo = "assets/photo.jpg"` in `[person]`.
- CV: replace `assets/cv_gfabbro.pdf`.
- Styling: `theme/style.css`. Page structure: `build.py`.
- Requires only Python ≥ 3.11 (no packages).
