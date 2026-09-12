// Re-inject content script into all existing tabs when the extension starts or updates.
// Without this, tabs open before the extension installed/reloaded have no content script.
async function reinjectContentScript() {
  const tabs = await chrome.tabs.query({ url: '<all_urls>' });
  for (const tab of tabs) {
    if (!tab.id || tab.id === chrome.tabs.TAB_ID_NONE) continue;
    if (!tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) continue;
    try {
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
    } catch (_) { /* tab may not be injectable — ignore */ }
  }
}

chrome.runtime.onInstalled.addListener(reinjectContentScript);
chrome.runtime.onStartup.addListener(reinjectContentScript);

// Opens the full view tab when requested from content script
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'OPEN_FULLVIEW') {
    const url = chrome.runtime.getURL('fullview.html');
    // Reuse existing fullview tab if already open
    chrome.tabs.query({ url }, tabs => {
      if (tabs.length > 0) {
        chrome.tabs.update(tabs[0].id, { active: true });
        chrome.windows.update(tabs[0].windowId, { focused: true });
      } else {
        chrome.tabs.create({ url });
      }
    });
  }
});
