Source FirmFlow logo (`logo.png`).

Web assets in `website-base/public/` are generated from it:

- `logo.png` — trimmed, transparent-background mark used by `components/logo.tsx`
- `icon-32x32.png` — favicon
- `apple-icon.png` — 180x180 Apple touch icon (white background)

To regenerate after replacing the source (from the repo root):

```sh
P=website-base/public
magick assets/logo.png -shave 0x5 -fuzz 8% -trim +repage -transparent white -bordercolor none -border 6 $P/logo.png
magick $P/logo.png -background none -gravity center -extent 240x240 -resize 32x32 $P/icon-32x32.png
magick $P/logo.png -background white -gravity center -resize 140x140 -extent 180x180 -alpha remove $P/apple-icon.png
```
