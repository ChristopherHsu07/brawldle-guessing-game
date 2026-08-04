const SPECIAL_SLUGS = {
  '8-Bit': '8bit',
  'Mr. P': 'mrp',
  'El Primo': 'primo',
  'Larry & Lawrie': 'larry&lawrie',
  'R-T': 'rt',
}

const pinModules = import.meta.glob('./brawl_pins/*_pin.png', {
  eager: true,
  import: 'default',
})

const pinsBySlug = Object.fromEntries(
  Object.entries(pinModules).map(([path, url]) => {
    const file = path.split('/').pop() ?? ''
    const slug = file.replace(/_pin\.png$/i, '')
    return [slug, url]
  }),
)

export function toPinSlug(name) {
  if (SPECIAL_SLUGS[name]) return SPECIAL_SLUGS[name]
  return name
    .toLowerCase()
    .replaceAll(' ', '')
    .replaceAll('.', '')
    .replaceAll("'", '')
    .replaceAll('-', '')
}

export function getPinUrl(brawlerName) {
  if (!brawlerName) return null
  return pinsBySlug[toPinSlug(brawlerName)] ?? null
}
