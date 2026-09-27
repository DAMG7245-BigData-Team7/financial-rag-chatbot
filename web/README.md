# AURELIA web frontend

Next.js site with the live demo. The browser calls the FastAPI backend directly.

```bash
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL
npm install
npm run dev                  # http://localhost:3000
```

`npm run build` produces a static export in `out/`, which Caddy serves on the VPS.
`NEXT_PUBLIC_API_URL` is inlined at build time, so rebuild after changing it.
See `../deploy/README.md`.

Links and credits live in `src/lib/site.ts`.
