# Optional: upgrade the legacy 439 cards (non-destructive)

Out of scope for the initial build. When you want the old Lektion 0-1 cards in the new
Recognition + Production + Cloze format **without losing review history**:

1. Read `spanish/cards.legacy.json` (old schema: `front`/`back`/`grammar`/`notes`, types
   `vocab` / `grammar_table`).
2. For each entry, author a new-schema entry in `spanish/cards.json`: map `front`→`spanish`,
   `back`→`german`, `grammar`→`grammar`; generate an `example_cloze` + `example_de`. Convert
   `grammar_table` entries to `grammar_cloze`/`grammar_reference`.
3. Run the normal `/spanish` pipeline — dedup will skip anything already present, so only the
   new cloze/production cards get added.
4. **Do not delete** the originals. If you want them out of rotation, **suspend** them in Anki
   (select in Browser → right-click → Toggle Suspend). Never `deleteNotes` the legacy cards.
