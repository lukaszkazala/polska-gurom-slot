# Local UX artwork — 20.10.2026

## Graphic finish v2 — 20.10.2026

The current presentation adds two original images generated from text with built-in imagegen. Exact prompts: `GRAPHICS_V2_PROMPTS.json`.

- `tlo-husaria-v2.png`: quiet historical oil painting with cavalry at the edges and plain burgundy standards; source `exec-70a328bb-49d2-4d54-9b43-c480a3d38c1d.png`. No downloaded painting was used as input. This is an original generated interpretation of the requested historical painting atmosphere, not Matejko's painting.
- `skarbiec-v2.png`: seven clean isolated treasury symbols (diamond, spade, heart, club, botanical lily, goblet, crown), replacing the former mockup crops in the Classic and Legends skins; source `exec-f6948653-86f8-4165-9094-d0a0f210a884.png`. The generated alpha is preserved unchanged. The other eleven illustrations remain in use.

Only the image catalog, one stylesheet link and the new surface-finish stylesheet changed. Engine, settlement, line handling, controls, layout dimensions and skin mappings remain unchanged. Original assets are retained for rollback. Local demo only; no platform submission or legal approval is implied.

## Earlier image history

All four images were generated with the built-in imagegen tool for this project. Exact prompts and generation/edit history are in the project conversation. No downloaded third-party photographs or museum reproductions were supplied to the generation calls. This is provenance documentation, not a licence grant or legal clearance.

- `polskie-motywy.png`: texture atlas generated from text, nine illustrated objects. Game uses eight new folklore subjects from it; the ninth hussar drawing is not used. Generated file: exec-03b8e55d-a275-41f7-94ca-43650ded0fba.png.
- `rama.png`: ornamental frame generated from text. Generated file: exec-ce639e46-74ec-463e-8389-60eecac2214d.png. Browser uses nine-slice borders and excludes the centre.
- `husarz.png`: original helmet-and-wing shield, generated from text. Generated file: exec-002cf92e-5095-498c-945b-bd644ecbb365.png.
- `klasyczne-motywy.png`: the project's generated v5 concept, edited from earlier project-generated concepts. Generated file: exec-5e1387c7-60aa-42b0-af87-8b22323edf50.png. Only the existing card suits, lily, goblet and crown regions are displayed.
- `symbole-specjalne.png`: original transparent texture atlas with WILD lettering and plain burgundy banner SCATTER; generated from text as exec-33058cae-0102-4a28-b158-f67ea876aca7.png. Replaces the rectangular mockup crops for the two special symbols in v0.5.

Images are stored unchanged. `art-catalog.js` defines rectangular source viewports. SVG clipping isolates the required regions during display, without editing source pixels. The gallery contains 18 distinct used illustrations, not every object or ornament visible in the source atlases.

No official eagle emblems were deliberately included in the displayed art. No manufacturer names, logos or model labels are used for the small car illustration. The car's appearance and name, regional food names, similarity to other art, applicable tool terms and commercial distribution rights remain subject to final review before publication. A missing logo does not alone clear a vehicle design. These assets are provided here for the user's local, virtual-balance UX testing.
