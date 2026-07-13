# LICENSE-POLICY

Governs what goes in the **public core** (this repo) vs the **private
annex** vs **pointer-only**. Not legal advice; when in doubt, demote a
source one tier and flag for human review.

## 1. Track assignment

| Source license | Raw content | Digest | Assignment |
|---|---|---|---|
| Public domain, CC0, CC-BY, CC-BY-SA, MIT/BSD/Apache docs, GPL docs | may be excerpted in core with attribution | core | `track: core` |
| Freely readable but all-rights-reserved (most blogs, Agner Fog, vendor guides) | annex only (private research copy) | core (original prose only) | `track: digest` |
| ND-licensed (CC-BY-NC-ND, e.g. Google SRE books) | annex only | conservative: short factual notes + pointer; no structural paraphrase | `track: conservative` |
| Paywalled / ToS-restricted (LWN current, SPEC, O'Reilly books) | do not store unless personally licensed; if stored, annex, never sync | pointer + independently-written concept notes | `track: pointer` |
| Auto-generated talk transcripts | annex only | core | `track: digest` |

## 2. Provenance

Every unit (core or annex) carries `source_url`, `source_license`,
`license_verified`, and fetch date. The harvester verifies licenses against
the source itself, not the registry's initial guess.

## 3. What makes a digest publishable

A core digest must be **original expression**: written from understanding,
in this repo's own structure and voice, conveying facts, mechanisms, and
methods (not copyrightable) rather than condensing the source's prose.
Rules for the distiller:

- No quotation over 15 words; at most one short attributed quote per unit.
- Do not mirror the source's section structure or narrative order.
- Numbers, commands, flag names, and API signatures are facts — fine.
- For `track: conservative` sources, restrict to bullet-level factual notes
  and rely on the pointer.
- Code from permissively-licensed repos may be excerpted with the license
  header noted; GPL code excerpts are fine in a repo that acknowledges the
  mixed licensing in `NOTICES.md` (create when first needed).

## 4. Annex hygiene

The annex is a private research corpus for the distillation pipeline and
for agents you run yourself. It is never published, never bundled into
model training sets you distribute, and access-controlled. Registry entries
mark `annex_ok: false` for anything whose ToS forbids even private
retention — those are pointer-only.
