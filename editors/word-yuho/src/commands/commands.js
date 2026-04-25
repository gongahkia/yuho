// Yuho ribbon commands.
//
// Backs the manifest's <Action xsi:type="ExecuteFunction"> entries.
// Currently exposes a single command, `insertStatute`, which prompts
// the user via the taskpane to pick a section then inserts the
// citation at the current cursor position. If no section is selected
// in the taskpane, it inserts a placeholder citation.

/* global Office, Word */

Office.onReady(() => {
  // Required: associate every ExecuteFunction name in manifest.xml.
  Office.actions.associate("insertStatute", insertStatute);
});

async function insertStatute(event) {
  try {
    const stored = readSelectedFromSettings();
    const cite = stored
      ? formatCitation(stored)
      : "Penal Code 1871 (open the Yuho panel and pick a section first)";
    await Word.run(async (context) => {
      const range = context.document.getSelection();
      range.insertText(cite, Word.InsertLocation.replace);
      await context.sync();
    });
  } catch (err) {
    console.error("[Yuho] insertStatute failed", err);
  } finally {
    // Required: ribbon command must call event.completed() so Word
    // knows the function has finished, even on failure.
    event.completed();
  }
}

function readSelectedFromSettings() {
  try {
    const settings = Office.context.document.settings;
    const raw = settings.get("yuho.lastSelected");
    if (!raw) return null;
    return typeof raw === "string" ? JSON.parse(raw) : raw;
  } catch (err) {
    return null;
  }
}

function formatCitation(rec) {
  const num = rec.section_number || rec.number || "?";
  const title = rec.section_title || rec.title || "";
  const url = rec.sso_url
    || `https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr${num}-#pr${num}-`;
  return `Penal Code 1871, s.${num} (${title}), available at ${url}`;
}
