# Deploying the KLEX site

## GitHub Pages (free, zero config path)

1. Push this repo to GitHub (public).
2. Repo → Settings → Pages → Source: "Deploy from a branch" → `main`,
   folder `/site` → Save.
3. The site lives at `https://<username>.github.io/klex-coin/`.

## Custom .de domain (the one he already owns)

At your domain registrar's DNS panel, add ONE of these:

**Option A — apex domain (A records):**
```
type  name  value
A     @     185.199.108.153
A     @     185.199.109.153
A     @     185.199.110.153
A     @     185.199.111.153
```

**Option B — www subdomain (CNAME):**
```
type   name  value
CNAME  www   <username>.github.io
```

4. Add a file named `CNAME` to `/site` containing exactly the domain, e.g.:
   `example.de`
5. Wait for DNS propagation (minutes to hours), re-check Settings → Pages.

## Notes

- HTTPS: GitHub Pages issues a certificate automatically once DNS is set.
- The explorer is NOT deployed here — it runs locally with `klex explore` by
  design (localhost only). A public explorer is a v1.1 roadmap item on a
  free-tier VPS.
- Nothing on the page claims price, market, or returns — keep it that way.