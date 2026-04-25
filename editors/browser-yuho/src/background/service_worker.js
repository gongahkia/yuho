// Yuho service worker.
//
// Manifest V3 background. Today the only behaviour is on toolbar-icon click:
// if the active tab is already on sso.agc.gov.sg/Act/PC1871, do nothing
// (the content script is already running). Otherwise, open the Penal Code
// landing page in a new tab so the user lands somewhere the extension is
// useful.

chrome.action.onClicked.addListener(async (tab) => {
  const isPC = tab.url && tab.url.startsWith("https://sso.agc.gov.sg/Act/PC1871");
  if (isPC) return;
  await chrome.tabs.create({
    url: "https://sso.agc.gov.sg/Act/PC1871",
    active: true,
  });
});
