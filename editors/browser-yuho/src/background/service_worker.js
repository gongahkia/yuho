// Yuho service worker.
//
// Manifest V3 background. Behaviours:
//
// 1. Toolbar action click — if the active tab is already on
//    sso.agc.gov.sg/Act/PC1871, do nothing (the content script is already
//    running). Otherwise open the Penal Code landing page so the user
//    lands somewhere the extension is useful.
//
// 2. Per-tab action badge — receive `yuho_section_active` messages from
//    the content script and update the toolbar badge text + background
//    colour to reflect the section's coverage tier. When the panel
//    closes, the badge clears.

// ---------------------------------------------------------------------
// Toolbar click
// ---------------------------------------------------------------------

chrome.action.onClicked.addListener(async (tab) => {
  const isPC = tab.url && tab.url.startsWith("https://sso.agc.gov.sg/Act/PC1871");
  if (isPC) return;
  await chrome.tabs.create({
    url: "https://sso.agc.gov.sg/Act/PC1871",
    active: true,
  });
});

// ---------------------------------------------------------------------
// Per-tab badge
// ---------------------------------------------------------------------

const TIER_COLOURS = {
  L3:   "#1a8b3a",
  L2:   "#1976d2",
  L1:   "#b07020",
  FLAG: "#c43d3d",
};

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.type !== "yuho_section_active") return;
  const tabId = sender?.tab?.id;
  if (!tabId) return;
  const text = (msg.badge || "").slice(0, 4);
  const colour = TIER_COLOURS[msg.badge] || "#3a86ff";
  try {
    chrome.action.setBadgeText({ tabId, text });
    chrome.action.setBadgeBackgroundColor({ tabId, color: colour });
    if (msg.section) {
      chrome.action.setTitle({
        tabId,
        title: `Yuho — s${msg.section} (${msg.badge || "no encoding"})`,
      });
    } else {
      chrome.action.setTitle({ tabId, title: "Yuho" });
    }
  } catch (err) {
    // Older browsers may not support all action methods; fail silently.
  }
});

// Clear badges when a tab navigates away from SSO PC pages.
chrome.tabs.onUpdated.addListener((tabId, info, tab) => {
  if (info.status !== "loading" || !tab.url) return;
  if (!tab.url.startsWith("https://sso.agc.gov.sg/Act/PC1871")) {
    try {
      chrome.action.setBadgeText({ tabId, text: "" });
      chrome.action.setTitle({ tabId, title: "Yuho" });
    } catch (err) {
      /* ignore */
    }
  }
});
