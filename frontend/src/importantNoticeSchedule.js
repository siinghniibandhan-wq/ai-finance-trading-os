export const IMPORTANT_NOTICE_STORAGE_KEY = "financial-os-important-notice-dismissed-on";

export function getLocalDateStamp(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function shouldShowImportantNotice(storage, now = new Date()) {
  try {
    return storage.getItem(IMPORTANT_NOTICE_STORAGE_KEY) !== getLocalDateStamp(now);
  } catch {
    return true;
  }
}

export function dismissImportantNotice(storage, now = new Date()) {
  try {
    storage.setItem(IMPORTANT_NOTICE_STORAGE_KEY, getLocalDateStamp(now));
    return true;
  } catch {
    return false;
  }
}
