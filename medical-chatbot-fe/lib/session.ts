import { v4 as uuidv4 } from "uuid";

// Session id is generated once and persisted in localStorage so it survives
// a page refresh (PRD Section 6). All /chat and /reset calls carry this id.

const STORAGE_KEY = "medical-chatbot:session-id";

/**
 * Return the persisted session id, creating one on first use.
 * Safe to call on the server (returns an empty string there); real value is
 * resolved on the client inside a useEffect.
 */
export function getSessionId(): string {
  if (typeof window === "undefined") return "";

  let id = window.localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = uuidv4();
    window.localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}

/**
 * Force-create a brand new session id (used if the user wants a truly fresh
 * conversation). Not required by the PRD reset flow, but handy.
 */
export function regenerateSessionId(): string {
  if (typeof window === "undefined") return "";
  const id = uuidv4();
  window.localStorage.setItem(STORAGE_KEY, id);
  return id;
}
